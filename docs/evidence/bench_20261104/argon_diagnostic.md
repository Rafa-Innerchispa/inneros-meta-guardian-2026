# Argon Independent Blind Forensic Diagnosis (`argon_independent_repair_20261104`)

- **Experiment ID:** `argon_independent_repair_20261104`
- **Model Selector Setting:** `Gemini 4 Argon (Medium)` (Verified via `<USER_SETTINGS_CHANGE>` at step `2524`, `2026-11-04T21:51:22Z`, with KV cache invalidation `cache_read_tokens: 0` at step `2525`)
- **Effective Backend Model ID:** `MODEL_ID_UNVERIFIED` (Internal API model string not exposed in IDE transcript headers)
- **Session ID:** `56250828-9f3d-47ae-94bc-16cdb57b9c91`
- **IDE Version:** `Antigravity IDE 1.107.0` (`agy 1.4.12`)
- **Diagnostic Timestamp (UTC):** `2026-11-04T21:58:15Z`
- **Baseline Commit:** `beccbd495dc2ab33e5c8cf3abe5fa988047cc15f`
- **Input Dossier:** `inneros_blind_diagnosis_20261104`

---

## 1. Identificación de las Causas del Bloqueo

Al analizar el estado del clúster (`0 active_workers`, `260 blocked_workers` con razón dominante `stale_worker_retry_budget_exhausted`, tareas atrapadas como `ops_4e977fd8ec43` y `ops_fcd8686d7fc6`) junto con el código fuente original en `beccbd495dc2ab33e5c8cf3abe5fa988047cc15f`, se identifican **cinco defectos estructurales** en el subsistema de recuperación y reclamo interactivo:

1. **Exclusión de tareas con `claim_token` no vacío pero lease vencido en la consulta MongoDB (`ops_interactive_recovery.py`, líneas 87–94 y 113):**
   - La función `recover_orphan_interactive_ops_tasks` filtra exclusivamente documentos donde `claim_token` no existe, es `None` o es `""` (`"$or": [{"claim_token": {"$exists": False}}, {"claim_token": None}, {"claim_token": ""}]`).
   - Cuando un worker interactivo reclama una tarea (ej. `ops_fcd8686d7fc6`), le asigna un `claim_token` válido y un `lease_until`. Si el worker muere o la sesión se interrumpe y el `lease_until` expira (hace 15 días en el caso de `ops_fcd8686d7fc6`), la tarea conserva su `claim_token` no vacío.
   - Como resultado, la consulta MongoDB de `recover_orphan_interactive_ops_tasks` **jamás selecciona** las tareas con `status="claimed"` y lease expirado que poseen `claim_token`, dejándolas bloqueadas indefinidamente.

2. **Pérdida de precedencia de proveedor/carril en tareas orquestadas (`ops_awaiting_claim.py`, líneas 25–32):**
   - `awaiting_claim_status_for_task(task)` evalúa `task.get("assignee") or task.get("assigned_to") or task.get("preferred_provider") or task.get("owner") or "cursor"`.
   - En tareas despachadas por el orquestador, `assignee` vale `"inneros_orchestrator"`, el cual es un valor truthy en Python. Por cortocircuito del operador `or`, `prov` toma el valor `"inneros_orchestrator"` e ignora `preferred_provider` (`"antigravity"` o `"cursor"`) y `execution_lane` (`"antigravity_interactive"` / `"cursor_interactive"`).
   - Al pasar `"inneros_orchestrator"` a `awaiting_claim_status_for_provider`, no coincide con ninguna clave de `_PROVIDER_AWAITING` y cae en el fallback genérico `"awaiting_ide_claim"`, perdiendo el carril específico (`awaiting_antigravity_claim` o `awaiting_cursor_claim`).

3. **Ausencia total de verificación de liveness de proceso (PID) y latido (heartbeat) antes de recuperar:**
   - `ops_interactive_recovery.py` no comprueba si el worker que posee el reclamo sigue vivo localmente (`headless_execution_pid`) ni si ha emitido un `heartbeat_at` reciente (`< 180s`).
   - Si simplemente se eliminara el filtro de `claim_token` vacío para recuperar leases vencidos, un worker activo que sufrió un retraso temporal en renovar su lease pero sigue ejecutándose (PID activo o heartbeat reciente) sufriría el robo de su tarea en plena ejecución.

4. **Riesgo de comprobación de PID entre nodos distintos (Cross-Host PID Collision) y bloqueos de Git en worktrees vinculados (`.git` pointer file):**
   - El clúster opera sobre múltiples hosts (`ralfiia-amd` y `ralphi-ia-ver-10`). Verificar un `headless_execution_pid` mediante `os.kill(pid, 0)` en el host local cuando `claim_host` o `headless_execution_host` pertenece a un nodo remoto es inválido y peligroso: puede matar/sondear un proceso ajeno o asumir falsamente que el proceso remoto murió (`ProcessLookupError`), provocando corrupción concurrente.
   - Asimismo, `_usable_worktree(task)` (líneas 52–59) sólo comprueba `Path(wt).is_dir()`, sin inspeccionar si el worktree tiene una operación Git activa (`index.lock`), ni resolver archivos `.git` tipo puntero (`gitdir: ...`) propios de `git worktree` vinculados.

5. **Falta de Compare-And-Swap (CAS) atómico en `update_one` (`ops_interactive_recovery.py`, líneas 112–133):**
   - El `update_one` actual filtra únicamente por `{"task_id": tid, "claim_token": {"$in": [None, ""]}}`, no incluye el estado esperado (`status`), el `claim_token` específico, el `lease_until` observado ni la `revision` del documento, y **tampoco verifica `res.modified_count == 1`** antes de añadir la tarea a `recovered`.
   - Si dos procesos de recuperación compiten simultáneamente o si el worker renueva su lease justo antes del `update_one`, se producen condiciones de carrera y falsos positivos en la lista `recovered`.

---

## 2. Relación de Cada Hallazgo con Evidencia

| Hallazgo | Archivo y Líneas | Evidencia en Dossier / Clúster |
|---|---|---|
| **H-1: Filtro excluye `claim_token` con lease vencido** | `ops_interactive_recovery.py:87-94` | Tarea `ops_fcd8686d7fc6` permanece en `status: "claimed"` con `lease_until: "2026-10-19T14:32:00Z"` (vencido hace 15 días) sin ser recuperada. |
| **H-2: `assignee="inneros_orchestrator"` oculta `preferred_provider` y `execution_lane`** | `ops_awaiting_claim.py:25-32` | Tareas orquestadas con `assignee: "inneros_orchestrator"` y `preferred_provider: "antigravity"` transicionan erróneamente a `"awaiting_ide_claim"` en lugar de `"awaiting_antigravity_claim"`. |
| **H-3: Sin guarda de `headless_execution_pid` ni `heartbeat_at`** | `ops_interactive_recovery.py:62-75, 97-111` | `has_active_valid_claim` sólo mira `claim_token` y `lease_until`; ignora por completo `headless_execution_pid` y `heartbeat_at`. |
| **H-4: Sin verificación de `claim_host` remoto ni resolución de `gitdir:` / `index.lock`** | `ops_interactive_recovery.py:52-60` | Topología multi-nodo (`ralfiia-amd` + `ralphi-ia-ver-10`) y uso de worktrees vinculados donde `.git` es un archivo de texto con `gitdir: <path>`. |
| **H-5: `update_one` no atómico y sin chequeo de `modified_count`** | `ops_interactive_recovery.py:112-133` | `recovered.append(...)` se ejecuta incondicionalmente tras `update_one`, incluso si ningún documento coincidió o si otro proceso ya modificó la revisión. |

---

## 3. Distinción entre Síntomas y Causas Raíz

- **Síntomas Observados:**
  - `blocked_workers: 260` con `stale_worker_retry_budget_exhausted`: Los workers del swarm reintentan encontrar trabajo o reclamar tareas atascadas hasta agotar su presupuesto de reintentos.
  - `ops_4e977fd8ec43` en `awaiting_antigravity_claim` con `do_not_auto_dispatch: true`: No es un fallo de los workers de `dev_swarm`; por diseño (`external_repair_may_auto_claim`, líneas 77–82), las tareas con `do_not_auto_dispatch=True` o carril `*_interactive` están reservadas exclusivamente para reclamo interactivo del IDE y prohibidas para auto-dispatch del swarm.
  - `ops_fcd8686d7fc6` atrapada en `claimed` durante 15 días: Síntoma directo de que el recolector de huérfanos ignora tareas con `claim_token` aunque su `lease_until` haya expirado.

- **Causas Raíz Verdaderas:**
  1. Predicado de consulta y actualización en `ops_interactive_recovery.py` que impide recuperar reclamos con `claim_token` cuyo lease ya venció.
  2. Orden de evaluación en `awaiting_claim_status_for_task` que no descarta identificadores de orquestador genéricos (`inneros_orchestrator`) ni inspecciona `execution_lane` / `preferred_provider` con prioridad cuando el `assignee` no es un proveedor IDE válido.
  3. Carencia de invariantes de seguridad previas a la escritura (heartbeat, PID local vs host remoto, `index.lock` en `gitdir` real y filtro CAS con `revision` + `modified_count == 1`).

---

## 4. Priorización de Riesgos

1. **PRIORIDAD CRÍTICA (P0 — Integridad de Datos y Cero Escrituras Prematuras):**
   - Nunca ejecutar `update_one` en MongoDB antes de validar todas las precondiciones de liveness (heartbeat reciente `< 180s`, PID local activo, host remoto sin verificador explícito de ausencia y `index.lock` en el worktree/gitdir). Una escritura previa al aborto corrompe el estado de coordinación en vivo.
2. **PRIORIDAD ALTA (P0 — Seguridad Cross-Host):**
   - Nunca invocar `os.kill(pid, 0)` localmente cuando `claim_host` o `headless_execution_host` indica otro nodo (ej. `ralphi-ia-ver-10` vs `ralfiia-amd`). Si el host es remoto y no se provee `remote_liveness_verifier` (o éste no retorna explícitamente `False`), abortar la recuperación de esa tarea con cero escrituras.
3. **PRIORIDAD ALTA (P0 — Atomicidad CAS):**
   - Evitar condiciones de carrera exigiendo coincidencia exacta de `task_id`, `status`, `claim_token`, `lease_until` y `revision` en el filtro de `update_one`, contabilizando la tarea como recuperada únicamente si `result.modified_count == 1`.
4. **PRIORIDAD MEDIA-ALTA (P1 — Enrutamiento Correcto de Carril):**
   - Garantizar que las tareas recuperadas vuelvan a su estado específico (`awaiting_antigravity_claim` o `awaiting_cursor_claim`) corrigiendo la resolución de proveedor en `ops_awaiting_claim.py`.

---

## 5. Estrategia Segura de Reparación

1. **En `platform/inneros_core_runtime/ops_awaiting_claim.py`:**
   - Actualizar `awaiting_claim_status_for_task(task)` para evaluar candidatos en orden seguro: si `assignee`/`assigned_to` no se normaliza a un proveedor conocido en `_PROVIDER_AWAITING` (por ejemplo, cuando es `"inneros_orchestrator"`), evaluar `preferred_provider`, el prefijo de `execution_lane` (ej. `"antigravity_interactive"` -> `"antigravity"`) y `claimed_by`, garantizando que retorne `awaiting_antigravity_claim` o `awaiting_cursor_claim` según corresponda.

2. **En `platform/inneros_core_runtime/ops_interactive_recovery.py`:**
   - Ampliar la firma a `recover_orphan_interactive_ops_tasks(limit: int = 20, *, remote_liveness_verifier: Any = None) -> dict[str, Any]` aceptando tanto argumento posicional como keyword `limit` y el verificador opcional `remote_liveness_verifier`.
   - Consultar tareas en `ORPHAN_STATUSES` (incluyendo aquellas con `claim_token` cuyo lease haya expirado).
   - Antes de cualquier escritura en base de datos, verificar secuencialmente:
     1. `requires_manual_interactive_lane(task)` y que el lease no esté vigente (`has_active_valid_claim(task)`).
     2. **Heartbeat reciente:** Si `heartbeat_at` (o `last_heartbeat_at`) es menor a 180 segundos respecto a `now`, abortar recuperación (0 writes).
     3. **Host remoto vs local y PID activo:** Comparar `claim_host` / `headless_execution_host` con `socket.gethostname()`. Si pertenece a un host remoto: si `remote_liveness_verifier` es `None` o si `remote_liveness_verifier(remote_host, pid)` no retorna explícitamente `False`, abortar (0 writes). Si el host es local y existe `headless_execution_pid`, comprobar `os.kill(pid, 0)`: si no lanza `ProcessLookupError` (proceso vivo o `PermissionError`), abortar (0 writes).
     4. **Worktree y linked `.git` lock:** Si la tarea define `worktree` o `local_worktree`, resolver `.git`: si `.git` es directorio, revisar `.git/index.lock`; si `.git` es archivo con `gitdir: <target>`, resolver la ruta (relativa o absoluta) y revisar `<target>/index.lock` (además de `index.lock` directo). Si existe bloqueo, abortar (0 writes).
   - **Actualización CAS Atómica:**
     - Construir el filtro CAS con `task_id`, `status: task.get("status")`, `claim_token: task.get("claim_token")`, `lease_until: task.get("lease_until")` y (si está presente) `revision: task.get("revision")`.
     - Ejecutar `update_one(cas_filter, update_doc)` e incluir la tarea en `recovered` **únicamente si `res.modified_count == 1`**.


---

## 6. Evaluación Post-Hoc Contra el Ground Truth (Realizada tras finalizar el diagnóstico ciego)

Una vez concluido y almacenado el diagnóstico ciego sin editar, se contrastaron los cinco hallazgos (`H-1` a `H-5`) contra las cinco invariantes canónicas del benchmark (`INV-1` a `INV-5`):

| Invariante Ground Truth | Hallazgo en Diagnóstico Ciego Argon | Coincidencia Exacta | Evidencia Verificada |
|---|---|---|---|
| **INV-1 (`LANE_PRECEDENCE`)** | **H-2:** Cortocircuito por `assignee="inneros_orchestrator"` en `ops_awaiting_claim.py:25-32` que oculta `preferred_provider` y `execution_lane`. | **SÍ (1/1)** | Identificó archivo, líneas exactas y mecanismo de cortocircuito booleano. |
| **INV-2 (`REMOTE_HOST_SAFETY`)** | **H-4:** Peligro de invocar `os.kill(pid, 0)` localmente cuando `claim_host` o `headless_execution_host` pertenece a un nodo remoto (`ralphi-ia-ver-10`). | **SÍ (1/1)** | Propuso prohibir `os.kill` en hosts remotos y requerir verificador explícito (`remote_liveness_verifier`). |
| **INV-3 (`LINKED_WORKTREE_LOCK`)** | **H-4:** `_usable_worktree` sólo comprueba `is_dir()` e ignora archivos `.git` tipo puntero (`gitdir: <path>`) e `index.lock`. | **SÍ (1/1)** | Propuso resolver `gitdir:` y abortar con cero escrituras si existe `index.lock`. |
| **INV-4 (`ATOMIC_CAS`)** | **H-1 y H-5:** Consulta inicial excluye `claim_token` no vacío y `update_one` carece de filtro multi-campo (`status`, `claim_token`, `lease_until`, `revision`) y de verificación `modified_count == 1`. | **SÍ (1/1)** | Identificó tanto el defecto de consulta como la condición de carrera en `update_one`. |
| **INV-5 (`PRE_MUTATION_HEARTBEAT_CHECK`)** | **H-3 y Prioridad P0-1:** Ausencia de guarda de `heartbeat_at` (`< 180s`) y PID local vivo ejecutada estrictamente antes de cualquier `update_one`. | **SÍ (1/1)** | Estableció como Prioridad Crítica P0 validar heartbeat y PID antes de tocar MongoDB (0 writes on abort). |

- **Resultado de Descubrimiento Ciego:** **5 / 5 causas raíz reales identificadas (100%)**, **0 hallazgos falsos**, distinguiendo correctamente entre síntomas operativos (`260 blocked_workers`, `do_not_auto_dispatch` en `ops_4e977fd8ec43`) y defectos de código.
