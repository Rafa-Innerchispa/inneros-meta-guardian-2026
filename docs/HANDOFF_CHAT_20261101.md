> **NUEVO PROTOCOLO META API, 2026-11-01:** El owner ya CREÓ una clave API (sin compartirla en ChatGPT). Para comprobar la API SIN tarjeta, se ha publicado un operador aislado, seguro, con un solo POST y mediciones: src/inneros_meta_guardian/meta_probe.py y la guía docs/META_API_FIRST_RUN_20261101.md. TESTS: tests/test_meta_probe.py (10 pruebas, añadidas a las 40 anteriores), CI verificada verde en commit 07255d9f723c6aed3af034b2b6357489a9c47722. Siguiente acción en IDE Antigravity: (1) capturar la clave con prompt local protegido / vault, NUNCA pegarla en chats, (2) correr PYTHONPATH=src python -m inneros_meta_guardian.meta_probe --check-key, (3) solo una vez, con la autorización dada por el owner, PYTHONPATH=src python -m inneros_meta_guardian.meta_probe --one-shot --probe-id meta-no-card-20261101 --owner-authorized. El POST usa un prompt FICTICIO, store=false, max_output_tokens=192, timeout 12s, cero retries. Si devuelve 402/billing_not_configured, PARAR: método de pago obligatorio y solo el propietario decide. Si REAL_SUCCESS, guardar provider_response.json y receipt.json privados (runtime/meta_trials) con response id, tokens, latencia, salida y hashes, y preparar RESUMEN SANITIZADO para evidencia pública. NO tocar el interfaz web anónimo, no habilitar gasto de Meta en otros agentes.

> **ACTUALIZACIÓN DE CRÉDITOS — 2026-11-01:** El propietario aportó una captura de Meta Model API **Billing → Overview** que muestra **Free credits in use: $150.00**, **Current balance: $0.00** y **Please add a payment method**. Los créditos ESTÁN acreditados. Falta agregar método de pago por el propietario, revisar Business information, crear/recuperar API key en el vault del servidor, comprobar Usage y ejecutar la primera llamada real solo tras controles de gasto y grant seguro. Meta advierte que el contenido enviado mientras se usen créditos gratuitos puede emplearse para mejorar sus productos. No enviar datos de clientes, topología, telemetría privada ni memoria confidencial a modelos externos. Consultar documentación oficial: https://dev.meta.ai/help/billing/set-up-billing ; https://dev.meta.ai/docs/authentication ; https://dev.meta.ai/docs/api-reference/responses/create-response .

> **ACTUALIZACIÓN POSTERIOR A LA AUDITORÍA — 2026-11-01:** Código corregido en commit `ef3e6d65e07923098f6ef8d9d483480bd6114a0a`. GitHub Actions `41316087563` **SUCCESS**. Se BLOQUEARON las rutas web anónimas para crear grants o llamar Meta (403), se etiquetó SAM como `SIMULATED_FIXTURE` con `model_executed=false`, se etiquetó la memoria hardcodeada como `UNVERIFIED_STATIC_EXAMPLE` y se eliminó la fabricación de IDs de respuesta Meta faltantes. **Persisten como P0**: saldo de créditos en Billing, endpoint de operador realmente autenticado, grant entre procesos, memoria real Cognee/AG-60, primera llamada auténtica a Meta y evidencia E2E. Los hallazgos históricos de abajo describen lo observado ANTES de estos fixes y se conservan para trazabilidad. 

# HANDOFF CANÓNICO | InnerOS Meta Global AI Hackathon 2026
**Auditoría:** 2026-11-01 (Ecuador) · **Destino:** nuevo chat ChatGPT / Antigravity IDE · **Prioridad:** cierre y entrega

> Este documento contiene hechos observados y distingue expresamente la implementación de las pruebas reales. Leerlo al iniciar cualquier sesión; volver a consultar GitHub antes de editar porque `main` puede avanzar. No sustituye las reglas autenticadas del evento.

## 1. Identidad, evento y plazo
- Proyecto: **InnerOS Autonomous Infrastructure Guardian**. Narrativa: **The Infrastructure That Remembers and Responds**.
- Empresa: InnerChispa LLC. Categoría propuesta: Startup Track. Tema: Push the Frontier, con aplicación Build for Your World.
- Organizador y portal: https://cerebralvalley.ai/e/meta-ai-developer-hackathon
- Detalles/Discord: https://cerebralvalley.ai/e/meta-ai-developer-hackathon/details y https://cerebralvalley.ai/e/meta-ai-developer-hackathon/discord
- **Fecha límite oficial: miércoles 2026-11-04, 21:00 Eastern/Guayaquil (ambos UTC-5 ese día).** Aceptación de inscripción confirmada por correo 2026-10-20. No hay evidencia de entrega final.
- Regla operacional: separar el producto preexistente de las contribuciones específicas de este hackathon, fechas 2026-10-26 a 2026-11-04. Confirmar todas las condiciones de envío en portal autenticado antes de publicar.

## 2. Créditos Meta Model API
- El owner confirmó en el chat que **completó el formulario** de US$150. Esto acredita su declaración, no un recibo externo del formulario.
- Correo oficial 2026-10-26 "Claim your $150 in Meta Model API credits" indicó: distribución por lotes; verificar saldo en **Billing**; se requiere un método de pago para hacer llamadas aun consumiendo créditos; plazo formulario 2026-11-04 21:00 ET.
- Búsqueda de Gmail hasta 2026-11-01: **sin correo nuevo de aplicación de créditos** y **sin recibo de respuesta de Google Forms**. No volver a enviar por duplicado sin comprobar.
- **CRÉDITOS META CONFIRMADOS EN CAPTURA DEL OWNER EL 2026-11-01:** pantalla Billing → Overview indica `Free credits in use: $150.00` en verde, `Current balance: $0.00` y `How you'll pay: Please add a payment method`. Por tanto, **la promoción de US$150 está aplicada/activa; el método de pago aún NO está registrado**. El saldo por cobrar es cero, pero esta captura NO demuestra que no haya habido uso previo ni revela el saldo restante por modelo; consultar Usage y actividad de pagos. **API key operativa: UNKNOWN.** Falta comprobar Business information, método de pago y API key. La cuenta Meta Model API empresarial tuvo correo de bienvenida 2026-10-26.
- Verificación efectiva: iniciar sesión con la cuenta empresarial correcta en https://dev.meta.ai/ → **Meta Model API** → seleccionar equipo → **Billing** → consultar Promotional/Free credits (aplicado, saldo y vencimiento), Payment methods y Spend Limits; consultar **Usage** por modelo y fecha; comprobar equipo/proyecto correctos.
- **ALERTA IMPORTANTE:** la alerta de gasto no constituye un bloqueo duro. Fuente oficial: https://dev.meta.ai/help/billing/spend-limit-alert. Si Billing aún no muestra créditos, documentar captura con datos de pago ocultos y consultar soporte/Discord de organizadores. No agregar una tarjeta ni hacer llamadas pagadas sin una decisión explícita del propietario.

## 3. GitHub verificado (2026-11-01)
- Repositorio exclusivo **privado**: https://github.com/Rafa-Innerchispa/inneros-meta-guardian-2026
- `main` HEAD observado: `4c97855f3b0e9b0bcb08ee2e7593b543a131a067`. Árbol: **37 archivos de contenido**.
- GitHub Actions `offline-demo-tests` run **41315324466**: **SUCCESS** en Python **3.10** y **3.12**. Logs: **40 tests por versión**, todos ejecutados con mocks/fixtures o interfaces offline; aproximadamente 0.6 s por suite. No son 40 demostraciones reales de Meta/Guardian. https://github.com/Rafa-Innerchispa/inneros-meta-guardian-2026/actions/runs/41315324466
- Fuente técnica: `README.md`, `src/inneros_meta_guardian/`, `tests/`, `docs/`, `scripts/`.
- El commit `f58f7de5` recuperó el simulador, y el HEAD `4c97855` añadió adaptadores/pruebas. Un workspace previo reportó 60 tests, pero **esa versión no equivale al HEAD actual**: no repetir el número 60 como prueba de GitHub.
- Repositorios anteriores se usan por contratos/read-only; no editar `main` del antiguo Nebius ni la rama `meta-global-guardian-20261026`. Cualquier limpieza de rama antigua solo tras validar la migración y con aprobación.

## 4. Componentes y datos reutilizables
1. **Guardian existente**: https://github.com/Rafa-Innerchispa/inneros-nebius-nvidia-physical-ai-2026 y https://guardian.creatorcore.ai/ . Ya tiene lecturas reales Casa/Bellini, `GET /api/guardian/live/readings/{site}/{category}`, receipts y llamadas de VoiceOps con aprobación HA. Ver `GUARDIAN_HANDOFF_CHATGPT_20261030.md`, `examples/verified-live-acceptance-20261030.json`. **Es producto previo, no evidencia de que el nuevo repo Meta ya esté conectado en vivo.**
2. **Memoria preexistente**: https://github.com/Rafa-Innerchispa/inneros-personal-brain , `GET /api/internal/shared-memory/recall` solo desde loopback del host correcto; no publicar a Internet. AG-60 en `Rafa-Innerchispa/innerops-agentic-platform`, `platform/inneros_core_runtime/network_engineer_memory.py`.
3. **Autoridad**: Home Assistant y VoiceOps existentes; llamadas/acciones autorizadas individualmente; sin reinicios, puertas ni cambios físicos por decisión autónoma de un modelo.
4. Hardware AMD local Qwen/vLLM, Ollama como inferencia local; Meta como capacidad específica y acotada del concurso.

## 5. Hallazgos críticos de auditoría del repo Meta actual
**P0 VERACIDAD:** `sam_inspector.py` contiene `LAB_FIXTURES` con cajas, probabilidades (98%, 94%...) y notas fijas; `inspect_lab_asset` NO llama a SAM 3.1. Pese a ello responde `LAB_VERIFIED_VISUAL`, `meta-sam-3.1` y `AUTHORIZED_LAB_BENCH_TEST`. Las detecciones actuales son **fixtures simuladas**, no resultados verificables del modelo. El storyboard describe falsamente un SAM real. Reetiquetar en UI/API como `SIMULATED_FIXTURE / SAM_NOT_RUN` de inmediato; solo permitir `REAL` con imagen autorizada + respuesta y metadatos reales. Una caja no mide por sí sola el radio de curvatura de fibra sin escala/calibración.

**P0 VERACIDAD DE MEMORIA:** `VerifiedMemoryClient.VERIFIED_KNOWLEDGE_BASE` en `integrations.py` es una lista hardcodeada; `Guardian.remember` la etiqueta `VERIFIED_HISTORICAL_MEMORY`. **No es recuperación viva de Cognee/AG-60.** Reetiquetar como ejemplos/historia no verificada y reemplazar por consulta real vía servicio local y procedencia. No mandar esos textos duros a Meta ni atribuirles 0.99 de confianza real.

**P0 SEGURIDAD/GASTO:** `web.py` acepta `POST /api/grants` y `POST /api/incidents/{id}/analyze` con Meta sin autenticación de propietario. Aunque el servidor escucha en loopback por defecto, habilitar un túnel público o `GUARDIAN_UNSAFE_BIND` sería peligroso con una clave pagada. **NO desplegar públicamente esa API ni habilitar clave** hasta implementar autenticación, límites y permisos del operador; preferir endpoint pagado **solo CLI/local protegido**, sin grants anónimos en la UI de jueces.

**P0 PERMISOS ROTOS:** `OneShotGrantStore` usa diccionario `_grants` en memoria. `scripts/make_one_shot_grant.py` y `scripts/operator_meta_once.py` se ejecutan en **procesos distintos**; el segundo no encuentra el token del primero. Corregir usando una única ejecución owner-confirmed o almacén persistente atómico con CAS y expiración, incluyendo tests multiproceso y replay.

**P0 RECIBOS REALES:** `meta_once.py` asigna un ID sintético cuando la API no devuelve `id` y, en caso de un HTTP 200 incompleto, puede marcar `REAL` sin una salida válida. **Fail closed**: exigir response_id real, contenido y uso verificados; no fabricar IDs ni recibos de gasto. El test de `REAL` usa `unittest.mock`.

**P0 PRIVACIDAD:** el redactor de `integrations.py` filtra IP y MAC, pero campos libres de memoria (`fact`, `title`) pueden contener secretos en texto sin una clave JSON llamada `password`. Emplear allowlist de atributos compartibles y memoria curada; nunca enviar informes privados, topología, clientes o credenciales al endpoint externo.

**P0 ETIQUETADO LIVE:** los tests de lecturas Guardian usan `patch.object(... fetch_reading)` o `urlopen` mock. Por tanto, hasta capturar petición real/response con timestamp, la integración **del nuevo repo** es `NOT_LIVE_VERIFIED`. Mantener fuente/edad reales e impedir que datos atrasados se presenten como eventos nuevos.

**P1 TELEFONÍA:** `VoiceOpsRecordedReceipt.get_verified_call_receipt()` devuelve un registro histórico precargado. Debe seguir marcado **HISTORIC/REPLAY**, nunca llamada Meta en tiempo real.

**P1 DOCUMENTACIÓN:** `docs/RECOVERY_STATUS_20261101.md` y `docs/ARCHITECTURE.md` describen la BASE anterior y contradicen el README/40 tests. `docs/SUBMISSION.md` marca como completos varios elementos que solo existen como simulaciones. Conciliar documentación con hechos antes de grabar video. No publicar como real una demo basada en fixtures.

**P1 ACCESO DEL JURADO:** repo privado; revisar si jueces necesitarán acceso público o demo pública separada y segura. No cambiar privacidad sin comprobar reglas y qué código/activos se expondrán.

## 6. Orden de trabajo para los próximos 3 días
1. **AHORA:** créditos de US$150 YA CONFIRMADOS por captura del usuario. Falta agregar método de pago (Meta lo exige para acceder a API), revisar Business information, API keys y Usage; no repetir formulario. Acción de tarjeta solo por owner, nunca por agente ni pegando datos en chat.
2. **AHORA:** cerrar vulnerabilidad de grants anónimos, falsos `REAL`, SAM simulado y memoria hardcodeada; proteger el operador Meta pagado. Commit + CI.
3. **SIGUIENTE:** captura E2E real de solo lectura desde Guardian existente, recuperación real de memoria curada con procedencia, y una sola inferencia Muse Spark autorizada **después** de conocer crédito y costo; guardar recibo real (o `NOT_RUN` explícito).
4. **DESPUÉS:** SAM 3.1 solo con fotografía del laboratorio y consentimiento y respuesta real. Si falta tiempo, dejarlo `NOT_RUN`, no inventar datos.
5. **PARA ENTREGA:** demo protegida y estable, desktop/móvil, artefacto de evidencia JSON/PDF saneado, métricas, storyboard y video en inglés de hasta 3 minutos si las reglas lo exigen; terminar envío en portal Cerebral Valley con acuse real. No esperar último minuto.

## 7. Definición de terminado
- [x] Registro aprobado y cuenta Meta Model API registrada.
- [x] Owner declara formulario US$150 enviado.
- [x] GitHub exclusivo en `main`, CI offline 40/40 Python 3.10 y 40/40 Python 3.12.
- [x] Créditos promocionales US$150 **comprobados visualmente** en Billing (captura del propietario, 2026-11-01).
- [ ] Registrar método de pago + completar Business information SOLO por el propietario; después verificar API key, Usage, vigencia y estrategia de gasto seguro.
- [ ] Endpoint pago autenticado, grant seguro en procesos múltiples, recibos sin IDs inventados.
- [ ] Guardian real + memoria verdadera E2E en el nuevo proyecto, sin fuga de datos.
- [ ] Muse Spark realmente ejecutado y recibo original.
- [ ] SAM realmente ejecutado, o marcado honestamente `NOT_RUN`.
- [ ] Demo de jueces autenticada y probada, accesibilidad confirmada.
- [ ] Video final con material real, pruebas y declaraciones precisas.
- [ ] Entrega Cerebral Valley confirmada.

## 8. Protocolo del siguiente chat
1. Abrir este archivo en GitHub y pedir: **"Continúa el Meta Hackathon desde docs/HANDOFF_CHAT_20261101.md. Créditos US$150 ya acreditados según captura del propietario; falta método de pago, API key y primera inferencia real. Verifica main y CI, cierra P0 sin delegar en RalfIA/Temporal."**
2. Actualizar primero SHA y pruebas para evitar usar evidencia vieja.
3. Usar el IDE de Antigravity o ejecución directa, no despachar a agentes internos ni entrar en loops.
4. Si Billing no se puede ver desde herramientas, el owner debe entrar al panel Meta autenticado y abrir la pestaña para inspección. Nunca pegar números de tarjeta, API key ni tokens en un chat.
5. Reportar **hechos verificados**, blockers exactos y URL de entrega; no prometer ejecución posterior automática.
