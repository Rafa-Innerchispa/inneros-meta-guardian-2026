# Model provenance audit / Auditoría de identidad del modelo

**Fecha:** 2026-11-04  
**Estado:** CORRECCIÓN DE ATRIBUCIÓN; identidad histórica NO VERIFICADA.

## Hallazgo confirmado
- La evidencia `docs/evidence/repair_benchmark_comparison_20261103.json` identifica el agente como `Argon Comparative Agent (Google Antigravity IDE)`, pero el campo `model` contiene la cadena ambigua `gemini-3.8-flash-medium / gemini-4-argon`. Esto **no prueba** qué modelo produjo realmente el código.
- El usuario reporta que mantuvo seleccionado **Gemini 3.8 Flash Medium** en Antigravity y que nunca seleccionó Argon explícitamente. Es testimonio del operador y no reemplaza un recibo de inferencia.
- El commit experimental citado como `94d90d34ce5542f0a152f071852b2b2be4fadfd1` no se pudo resolver mediante la API de GitHub en `Rafa-Innerchispa/innerops-agentic-platform` durante esta auditoría. Puede existir solo en un worktree local/no publicado. **No usarlo como prueba pública accesible hasta subirlo o aportar un diff con hashes y logs.**
- Los informes registran `10/10` para un parche de dos módulos, y `8/10` para una aplicación de un solo módulo. Estas son configuraciones distintas y no deben combinarse como si fueran una única evaluación.
- La ejecución documentada de **Meta Muse Wonder 1.0** sí incluye un modelo explícito de API y `response_id` en los recibos correspondientes. No confundir diagnóstico y reparación, ni atribuir a Wonder un parche completo cuando hubo truncamiento.
- Fireworks y Baseten ofrecen rutas **Muse Spark Open**, no Muse Wonder. Modal es sandbox, no un modelo.

## Convención de nombres obligatoria
| Contexto | Etiqueta pública correcta | Evidencia mínima |
|---|---|---|
| Parche histórico de Antigravity | **Antigravity IDE repair (exact model unverified)** | sesión/trace IDE, provider, exact model ID, hash del patch, resultado independiente |
| Corrida nueva seleccionada Argon | **Antigravity IDE / Argon (verified model only after receipt)** | captura de selector más metadata de run/respuesta; si faltan, `MODEL_ID_UNVERIFIED` |
| Corrida nueva Gemini Flash | **Antigravity IDE / Gemini Flash (verified model only after receipt)** | metadata de run + captura configuracion, hash |
| Meta Muse Wonder | **Meta Model API / muse-wonder-1.0** | response_id, usage, raw sanitized receipts |
| Muse Spark Fireworks | **Fireworks / accounts/fireworks/models/muse-spark-open** | response_id, raw receipt |
| Muse Spark Baseten | **Baseten / meta-models/muse-spark-open** | response_id, raw receipt |
| Qwen local AMD | **vLLM local / exact model_id servido** | /v1/models, generation ID, usage, host/GPU |

## Benchmark válido: tres planos separados
1. **Comparación de modelos por API:** runner InnerOS en AMD, snapshot, prompt, baseline, tools y tests idénticos; proveedor/modelo verificados por request/response. Diferenciar latencia de inferencia y total de ciclo. Registrar SHA256 input/prompt/diff, temperatura, max tokens, tools, run IDs, token usage, precios y coste real vs estimado.
2. **Comparación de agentes/IDEs:** Antigravity con modelo seleccionado explícitamente; registrar IDE version, exact model ID devuelto/visible, session ID, timestamps, contexto, acciones, tool invocations, Git diff, tests y límites. **No comparar latencia de una sesión de IDE con latencia de una llamada API como si fueran equivalentes.**
3. **Verificación independiente:** aplicar cada patch en worktree de mismo baseline, ejecutar tests idénticos en sandbox local o Modal, guardar stdout/stderr, exit codes, riesgos AST/zero-writes-before-liveness, regresiones. Etiquetar intervenciones asistidas como assisted; no dar crédito al modelo inicial por las reparaciones del evaluador.

## Próximos pasos para cerrar atribución
1. Consultar registros locales de sesión de Antigravity (config del modelo, request/response metadata y eventos, no confiar solo en alias usado en informes).
2. Buscar el commit `94d90...` en los worktrees locales y, si existe, publicar diff sanitizado con SHA y evidencia del test run. No hacer merge productivo.
3. Si se desea evaluar **Argon** como modelo separado, ejecutar **nueva sesión explícita** en rama limpia; congelar baseline, recopilar selector y recibo de modelo real. Ejecutar también Gemini Flash en condiciones equivalentes si se desea compararlos.
4. Exigir `provider`, `model_id_actual`, `model_id_requested`, `runner_type`, `session_id`, `prompt_hash`, `baseline_sha`, `patch_sha`, `test_run_id` por corrida. Si falta provenance, reportar `MODEL_ID_UNVERIFIED`, no inventar.
5. Poner en frontend la aclaración visible junto al resultado histórico 10/10; preservar recibos originales, con este documento como errata.

## Regla editorial para jueces y video
Hasta completar la validación de la sesión: **“An Antigravity IDE repair candidate passed 10/10 targeted tests in the recorded two-module evaluation; exact model attribution remains unverified.”** Nunca “Argon won”, “Argon model ran” o “Meta Muse repaired the code” sin evidencia nueva.

La etiqueta equivocada no invalida el hallazgo de seguridad ni los recibos de Muse, pero sí impide un ranking atribuido inequívocamente a Argon.
