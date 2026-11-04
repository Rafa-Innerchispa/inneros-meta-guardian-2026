# EXPEDIENTE UNIFICADO DE AUDITORÍA INNEROS (2026-11-04)
## Infraestructura, Coordinación Multi-Agente, Modelo Financiero y Evaluación Comparativa
**Organización:** InnerChispa LLC  
**Responsable:** Rafael López, CEO  
**Auditoría Independiente:** Meta Muse Wonder 1.0 vs. Argon (Antigravity) vs. GPT-6 Astra vs. Qwen Local  
**Estado de Privacidad:** Sanitizado al 100%, 0 secretos filtrados, 0 IPs privadas expuestas.

---

## 1. Arquitectura y Topología del Clúster
- **Nodo Primario AMD (`inneros-5`):** AMD Ryzen 9 + Radeon AI PRO R9700 (32 GB VRAM). Ejecuta vLLM con Qwen3-Coder-30B-AWQ sobre ROCm 10.1 en puerto `:8000`, y el servicio público `inneros-meta-guardian.service` en puerto `:8793`.
- **Nodo Secundario Intel (`inneros-4`):** Intel Core i9 / Xeon con 64 GB RAM. Aloja MongoDB en puerto `:27017`, host del túnel Cloudflare `opportunityops`, y los gateways MCP Small (`:8001`) y Monolítico (`:8102`).
- **MCP Small vs. MCP Monolítico:** MCP Small atiende telemetría rápida y lectura de leases; MCP Monolítico atiende mutaciones de base de datos y orquestación general.

---

## 2. Diagnóstico del Incidente de Coordinación Real
- **Tarea Atrapada:** `ops_4e977fd8ec43` en estado `awaiting_claim` con lease interactivo expirado.
- **Tarea Secundaria:** `ops_fcd8686d7fc6` con lease de reclamo vencido por 15 días sin recolección de basura.
- **Workers DevSwarm:** 260 workers bloqueados (0 activos) por agotamiento de presupuesto de reintentos sin liberación de lease.
- **Riesgo Crítico de Proceso Cruzado (Cross-Host PID Hazard):** `ops_interactive_recovery.py` ejecutaba `os.kill(pid, 0)` sin verificar si el PID pertenecía al host local o al nodo secundario Intel, arriesgando matar procesos activos legítimos tras un reinicio de leases.
- **Puntero de Git Worktree (`.git` File Lock):** Los worktrees vinculados en `var/local_execution/worktrees/` utilizan un archivo `.git` que apunta a `gitdir: ...`. El recuperador intentaba buscar `.git/index.lock` asumiendo que `.git` era un directorio, fallando con `NotADirectoryError`.

---

## 3. Matriz de Auditoría Independiente Multi-Modelo

| Criterio | Meta Muse Wonder 1.0 | Argon (Antigravity IDE) | GPT-6 Astra (OpenAI) | Local Qwen3-Coder-30B |
|---|---|---|---|---|
| **Endpoint** | `api.meta.ai/v1/responses` | Local Antigravity IDE | `api.openai.com/v1` | AMD vLLM (`:8000`) |
| **Modo de Operación** | Live 2-Turn Tool Calling | Workspace Repair Agent | API Query | Soberano On-Premises |
| **Tokens / Latencia** | 3,843 tokens (822 CoT) / 25.8s | 1,950 tokens / 3.2s | N/A | 1,522 tokens / 6.44s |
| **Costo Operativo** | $0.0019 USD (Gobernado) | $0.00 USD | $0.00 USD | **$0.00 USD** |
| **Detección PID Cruzado** | Detectado en Turno 2 | Detectado y parcheado | N/A | Heurístico |
| **Detección Git Worktree** | Detectado en Turno 2 | Detectado y parcheado | N/A | Heurístico |
| **Resultado de Reparación** | Diseña matriz de 7 tests | **10/10 Tests Green (0.13s)** | N/A | 43 targeted tests green |
| **Estado Verificado** | `AUTHENTIC_RECEIPT_VERIFIED` | **`VERIFIED_PASS`** (Commit `94d90d34`) | `BLOCKED_API_ACCESS` | `ONLINE_SOVEREIGN_AWQ` |

---

## 4. Matriz Financiera Verificada de Proveedores

| Proveedor | Organización | Saldo Disponible | Uso / Costo | Auto-Reload | Presupuesto Propuesto | Estado |
|---|---|---|---|---|---|---|
| **Fireworks AI** | InnerChispa LLC | **$20.30 USD** | $0.00 | **Desactivado** | $1.00 USD | `TESTED_OFFLINE` |
| **Baseten Model APIs** | InnerChispa LLC | **$5.00 USD (Free)** | $0.00 | N/A | $0.50 USD | `TESTED_OFFLINE` |
| **Baseten Tool Calls** | InnerChispa LLC | **$2.00 USD (Free)** | $0.00 | N/A | Separado ($0.00) | `TESTED_OFFLINE` |
| **Baseten Dedicated** | InnerChispa LLC | **$0.00 USD** | $0.00 | **Sin tarjeta** | $0.00 (Prohibido) | `BLOCKED` |
| **Modal CPU Sandbox** | InnerChispa LLC | **$1.00 USD (Free)** | $0.00 | N/A ($29 denegado) | $0.25 USD | `TESTED_OFFLINE` |
| **Meta Model API** | InnerChispa LLC | Ventana 10 días | $0.0019 USD | N/A | $0.50 USD / Grant | `TESTED_LIVE` |
| **Local AMD ROCm** | InnerChispa LLC | **Ilimitado ($0.00)** | $0.00 | N/A | $0.00 | `TESTED_LIVE` |
| **OpenAI Astra** | InnerChispa LLC | $0.00 (Sin key) | $0.00 | N/A | $0.00 | `BLOCKED` |

---

## 5. Plan de Reparación Local y Verificación
1. **Regla de Precedencia:** En `ops_awaiting_claim.py`, priorizar `awaiting_antigravity_claim` sobre auto-recovery genérico.
2. **Aislamiento de Host:** En `ops_interactive_recovery.py`, exigir `claim_host == current_node_host` antes de ejecutar cualquier verificación o limpieza de PID local.
3. **Resolución de Puntero Worktree:** Parsear `gitdir: ` en archivos `.git` para localizar `index.lock` en el repositorio raíz compartido.
4. **CAS Atómico:** Requerir `modified_count == 1` en la actualización de MongoDB para prevenir condiciones de carrera.
5. **Verificación Determinista:** 10/10 pruebas verdes en `tests/test_ops_expired_claim_lease_recovery.py` sin regresiones.
