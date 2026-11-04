# Matriz de Identidad de Modelos y Procedencia Criptográfica (`bench_20261104`)

- **Fecha de Auditoría:** 4 de noviembre de 2026 (`2026-11-04T22:05:00Z`)
- **Repositorio de Evidencia:** `Rafa-Innerchispa/inneros-meta-guardian-2026`
- **Repositorio de Código Objetivo:** `Rafa-Innerchispa/innerops-agentic-platform` (Baseline: `beccbd495dc2ab33e5c8cf3abe5fa988047cc15f`)
- **Sesión de Antigravity IDE:** `56250828-9f3d-47ae-94bc-16cdb57b9c91` (`Antigravity IDE 1.107.0`, `agy 1.4.12`)

---

## 1. Hallazgo Forense sobre el Historial de Selección de Modelo en Antigravity IDE

La inspección directa del registro del sistema `transcript_full.jsonl` (`C:\Users\hrlg\.gemini\antigravity\brain\56250828-9f3d-47ae-94bc-16cdb57b9c91\.system_generated\logs\transcript_full.jsonl`) reveló la secuencia exacta de eventos `<USER_SETTINGS_CHANGE>` emitidos por el IDE:

1. **Step 0 (`2026-11-03T20:54:57Z`):**
   - `The user changed setting Model Selection from None to Gemini 4 Argon (Medium).`
2. **Step 388 (`2026-11-04T03:09:54Z`):**
   - `The user changed setting Model Selection from Gemini 4 Argon (Medium) to Gemini 3.8 Flash (Medium).`
3. **Steps 559–585 (`2026-11-04T03:23:03Z` – `2026-11-04T03:25:13Z`):**
   - Generación y aplicación del parche histórico `94d90d34ce5542f0a152f071852b2b2be4fadfd1` (`experiment/argon-repair-20261103`).
   - **Conclusión Forense:** El parche histórico `94d90d34` se ejecutó mientras el selector del IDE estaba en **`Gemini 3.8 Flash (Medium)`**, NO en Argon. Dado que el IDE no expone el header del modelo interno de la API en `transcript_full.jsonl`, su identificador efectivo se clasifica como `ANTIGRAVITY_HISTORICAL_MODEL_UNVERIFIED` con etiqueta de selector confirmada `Gemini 3.8 Flash (Medium)`.
4. **Step 2524 (`2026-11-04T21:51:22Z`):**
   - `The user changed setting Model Selection from Gemini 3.8 Flash (Medium) to Gemini 4 Argon (Medium).`
   - En el **Step 2525 (`2026-11-04T21:51:22Z`)**, el transcript registra `cache_read_tokens: 0` e `input_tokens: 134,400`, confirmando la invalidación del caché KV por cambio real de modelo en el backend.
5. **Steps 2576–2618 (`2026-11-04T21:57:54Z` – `2026-11-04T22:03:14Z`):**
   - Ejecución del nuevo experimento independiente **`argon_independent_repair_20261104`** (commit aislado `c62153893d9d82aa015b7105665397736d1cc64b`) bajo la selección explícita **`Gemini 4 Argon (Medium)`**.

---

## 2. Matriz Integral de Identidad, Modalidad, Tiempos, Costos y Pruebas

> **Nota Metodológica:** No se presenta un ranking único general porque las condiciones de ejecución difieren estructuralmente entre agentes interactivos de IDE (multi-paso con acceso al árbol de archivos y ejecución local de tests) y llamadas directas de inferencia por API (un solo turno o bucle acotado de herramientas con límite de tokens de salida).

| ID Candidato / Experimento | Proveedor / Entorno | Modelo Solicitado / Selector | Modelo Efectivo Confirmado | Tipo de Ejecución | Diagnóstico Ciego (Defectos) | Reparación Original (10 Tests) | Reparación Multi-Módulo / Asistida | Tiempo de Inferencia / Generación | Tiempo Total Agente | Costo Observado / Facturado | Seguridad Pre-Escritura (INV-5) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **`argon_independent_repair_20261104`** *(Nuevo)* | Antigravity IDE `1.107.0` | `Gemini 4 Argon (Medium)` *(Verificado en Step 2524)* | `MODEL_ID_UNVERIFIED` *(KV cache reset verificado en Step 2525)* | Agente IDE (Diagnóstico Ciego + Reparación Guiada en worktree aislado) | **5 / 5 (100%)** (`argon_diagnostic.md`, 65.0s) | **8 / 10** *(Single-module)* / **10 / 10** *(Multi-module `attempt_1`)* | **10 / 10** *(Target)* · **19 / 19** *(Regresión extendida `attempt_2`)* | `71.0s` (`attempt_1`) + `16.0s` (`attempt_2`) | `712.0s` (Flujo completo) | `NOT_EXPOSED` (Suscripción IDE; `$0.00` cargo API extra) | **PASS** (Cero escrituras en aborto verificado) |
| **`antigravity_historical_gemini_flash`** *(Histórico `94d90d34`)* | Antigravity IDE `1.107.0` | `Gemini 3.8 Flash (Medium)` *(Verificado en Step 388)* | `ANTIGRAVITY_HISTORICAL_MODEL_UNVERIFIED` | Agente IDE (Reparación histórica en worktree) | No ejecutado por separado | **8 / 10** *(Single-module)* / **10 / 10** *(Multi-module)* | **10 / 10** (0.09s–0.36s test) | ~`130.0s` (Steps 559–585, 11 pasos planner) | `NOT_EXPOSED` | `NOT_EXPOSED` (Suscripción IDE; `$0.00` cargo API extra) | **PASS** (Cero escrituras en aborto verificado) |
| **`meta_muse_wonder_1_0`** | Meta Model API (`api.meta.ai`) | `muse-wonder-1.0` | `muse-wonder-1.0` (**Confirmado por API receipt**) | API REST (`v1/responses`, 2 turnos tool-calling + 1 turno reparación) | **5 / 5 (100%)** (4 tool calls reales en vivo) | `TRUNCATED_BY_MAX_OUTPUT_TOKENS` (3,600 tokens) | No aplicable (sin parche asistido) | `25.82s` (Diag) / `23.81s` (Repair gen) | `49.63s` | **$0.0019 USD** (Diag) / **$0.005554 USD** (Repair) | **PASS** (Frontera de sólo lectura) |
| **`meta_muse_spark_open_baseten`** | Baseten (`bridge.baseten.co`) | `meta-models/muse-spark-open` | `meta-models/muse-spark-open` (**Confirmado por API receipt**) | API Serverless (1 turno diag + 1 turno repair + retry 3,800 tok) | **5 / 5 (100%)** (En CoT de 1 turn) | `TRUNCATED` (2,800 tok) / `BLOCKED_BY_PROVIDER_LIMIT` (3,800 tok) | No aplicable | `3.21s` (Diag) / `9.08s` (Repair 2800 tok) | `12.29s` | **$0.000271 USD** (Diag) | N/A (No produjo módulo completo) |
| **`meta_muse_spark_open_fireworks`** | Fireworks AI (`api.fireworks.ai`) | `accounts/fireworks/models/muse-spark-open` | `accounts/fireworks/models/muse-spark-open` (**Confirmado por API receipt**) | API Serverless (1 turno diag + 1 turno repair + retry 3,800 tok) | **5 / 5 (100%)** (En CoT de 1 turn) | `TRUNCATED` (2,800 tok) / `BLOCKED_BY_PROVIDER_LIMIT` (Timeout 120s) | No aplicable | `5.30s` (Diag) / `46.18s` (Repair 2800 tok) | `51.48s` | **$0.000317 USD** (Diag) | N/A (No produjo módulo completo) |
| **`qwen3_coder_original`** | Local AMD ROCm vLLM (`:8000`) | `QuantTrio/Qwen3-Coder-30B-A3B-Instruct-AWQ` | `QuantTrio/Qwen3-Coder-30B-A3B-Instruct-AWQ` (**Confirmado en vLLM local**) | Inferencia Soberana Local (1 turno diag + 1 turno repair sin asistencia) | **5 / 5 (100%)** (`6.44s`–`15.16s`) | **0 / 10** (Firma incompatible + violación INV-5) | Ver fila `qwen3_coder_assisted_v2` | `12.59s` (Repair gen, 777 tokens) | `19.03s` | **$0.00 USD** marginal API (~`$0.00007` energía amortizada) | **CRITICAL FLAW** (`update_one` en línea 54 antes de heartbeat en línea 70) |
| **`qwen3_coder_assisted_v2`** | Local AMD ROCm + Remediación Asistida | `QuantTrio/Qwen3-Coder-30B-A3B-Instruct-AWQ` (+ corrección humana/agente) | `QuantTrio/Qwen3-Coder-30B-A3B-Instruct-AWQ` (**Híbrido asistido**) | Parche Local Remediado tras Auditoría de Seguridad | Hereda diagnóstico local 5/5 | **6 / 10** *(Single-module)* | **8 / 10** *(Multi-module)* | N/A (Remediación post-auditoría) | N/A | **$0.00 USD** marginal API | **PASS REMEDIATED** (Pre-verificación estricta antes de `update_one`) |
| **`modal_ephemeral_sandbox`** | Modal Cloud (`modal.com`) | `debian_slim` container (`ap-kxAe14gbo36ToQZDEKhNn3`) | **NO ES UN LLM** (`ISOLATED_TEST_SANDBOX`) | Sandbox Efímero de Verificación de Pruebas | N/A | **5 / 5** invariantes verificadas en contenedor aislado | N/A | `3.80s` (Ejecución de contenedor) | `3.80s` | **$0.000045 USD** | **PASS** (Contenedor destruido al finalizar) |

---

## 3. Veredicto Comparativo: Nueva Sesión Argon vs. Antigravity Histórico (`Gemini 3.8 Flash`)

1. **Identidad Aclarada con Evidencia Primaria:**
   - La corrida histórica (`94d90d34`) que obtuvo 10/10 pruebas fue ejecutada en los pasos `559–585` del transcript después de que el selector cambiara a `Gemini 3.8 Flash (Medium)` en el paso `388`. Por tanto, se preserva en el benchmark como `ANTIGRAVITY_HISTORICAL_MODEL_UNVERIFIED` (selector `Gemini 3.8 Flash (Medium)`) y **no se adjudica a Argon**.
2. **Desempeño de la Nueva Corrida Independiente de Argon (`argon_independent_repair_20261104`):**
   - Con `Gemini 4 Argon (Medium)` seleccionado explícitamente (paso `2524`), Argon realizó primero el **diagnóstico ciego completo** (identificando 5/5 causas raíz sin contaminarse con soluciones previas) y luego generó desde cero su propio parche (`c62153893d9d82aa015b7105665397736d1cc64b`).
   - En la suite objetivo de 10 pruebas (`test_ops_expired_claim_lease_recovery.py`), Argon empató el **10/10 (100% verde)** en modo multi-módulo desde el primer intento (`attempt_1`, `0.36s`) y **8/10** en modo de módulo único.
   - Adicionalmente, al validar contra las suites extendidas de regresión del repositorio (`test_ops_antigravity_claim_node_recovery.py` y `test_ops_interactive_claim_release.py`), `attempt_2` superó **19/19 pruebas (100% verde)** y verificó explícitamente la invariante de **cero escrituras cuando una recuperación es rechazada**.
