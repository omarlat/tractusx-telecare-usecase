# Entorno de desarrollo local

Este documento cubre la puesta en marcha del **stack Python** del caso de uso telecare en local.  
Para la visión general del proyecto ver el [README](README.md).  
Para el despliegue del Data Space (Tractus-X Umbrella en VPS) ver [infra-notes/UMBRELLA-SETUP.md](infra-notes/UMBRELLA-SETUP.md).  
Para desplegar este mismo stack Python como contenedores Docker en el VPS ver [DEPLOY.md](DEPLOY.md).

---

## Arquitectura de servicios

| Servicio | Puerto | Descripción |
|---|---|---|
| `generator` | 8000 | Generador sintético de eventos de teleasistencia |
| `semantic-adapter` | 8001 | Adaptador semántico: enriquece eventos y los serializa a HL7 FHIR |
| `analytics` | 8002 | Motor de análisis: genera activos derivados a partir de los eventos |
| `demo-ui` | 8003 | Interfaz web de demostración |
| `dataspace-connector` | 8004 | Cliente EDC: publica el activo como Entidad A y lo consume como Entidad B a través del espacio de datos real |

Todos los servicios son APIs FastAPI independientes. El `semantic-adapter` y el `analytics` consumen los datos del `generator`. El `dataspace-connector` publica lo generado por `semantic-adapter` en el EDC de Entidad A y lo recupera vía el EDC de Entidad B; `analytics` analiza los datos recibidos por ese camino, no los de `semantic-adapter` directamente. La `demo-ui` presenta todo el flujo.

---

## Requisitos previos

- Python 3.12+ (el proyecto usa 3.14)
- VS Code con la extensión **Python** instalada

---

## Primera vez: crear el entorno virtual e instalar dependencias

Desde la raíz del repositorio:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

El `.venv` es compartido por todos los servicios.

---

## Arrancar todos los servicios

El repositorio incluye una configuración de tareas de VS Code.

**`Ctrl+Shift+P` → "Tasks: Run Task" → "Start All Services"**

Esto abre cuatro terminales en paralelo, una por servicio, con el entorno virtual ya activado:

```
generator :8000          → http://localhost:8000
semantic-adapter :8001   → http://localhost:8001
analytics :8002          → http://localhost:8002
demo-ui :8003            → http://localhost:8003
```

Para arrancar un único servicio, elegir su tarea individual en el mismo menú.

---

## Explorar las APIs

Cada servicio expone documentación interactiva automática (Swagger UI) en `/docs`:

| Servicio | Swagger |
|---|---|
| generator | http://localhost:8000/docs |
| semantic-adapter | http://localhost:8001/docs |
| analytics | http://localhost:8002/docs |
| demo-ui | http://localhost:8003 |
| dataspace-connector | http://localhost:8004/docs |

---

## Endpoints principales

### generator (8000)

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/scenarios` | Lista los escenarios disponibles |
| `POST` | `/generate/{scenario}` | Genera eventos para un escenario |
| `GET` | `/events` | Devuelve todos los eventos en memoria |
| `GET` | `/events/{case_id}` | Devuelve los eventos de un caso concreto |

Escenarios disponibles: `low-oxygen`, `fall-alert`, `mixed-risk`.

### semantic-adapter (8001)

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/semantic-events` | Eventos enriquecidos semánticamente y validados |
| `GET` | `/aspects` | Catálogo de aspectos del modelo de datos |
| `GET` | `/fhir-events` | Eventos serializados como recursos HL7 FHIR Observation |

### analytics (8002)

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/derived-assets` | Activos derivados calculados llamando directamente a semantic-adapter (solo pruebas manuales) |
| `POST` | `/analyze` | Analiza el body `{"semantic_events": [...]}`; es lo que usa la demo con los eventos llegados vía EDC |

### dataspace-connector (8004)

Cliente EDC contra el Tractus-X Umbrella real (Entidad A = provider, Entidad B = consumer). IDs de asset/políticas/contrato fijos y reutilizados entre ejecuciones (ver `config.py`).

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/health` | Configuración cargada (rutas, credenciales enmascaradas) |
| `POST` | `/provider/publish` | Publica el caso actual en el EDC de Entidad A (contenido + asset + políticas + contract definition), los 5 pasos de golpe. Solo pruebas manuales. |
| `POST` | `/consumer/fetch` | Consume el activo desde Entidad B (catálogo → negociación → EDR → fetch), los 5 pasos de golpe. Solo pruebas manuales. |
| `POST` | `/exchange/run` | Crea una ejecución guiada y reúne el payload a publicar; no ejecuta ningún paso EDC todavía |
| `POST` | `/exchange/{run_id}/next` | Ejecuta en segundo plano el siguiente paso pendiente (uno por llamada) |
| `GET` | `/exchange/{run_id}` | Estado del intercambio y detalle real (request/response, credenciales enmascaradas) de cada paso, más `next_step` |
| `GET` | `/exchange/{run_id}/data` | El bundle `{semantic_events, fhir_events}` recibido vía EDC (404 si el run no existe, 409 si aún no ha terminado) |

---

## Flujo típico de prueba

1. Abrir http://localhost:8000/docs y lanzar `POST /generate/fall-alert`
2. Verificar los eventos brutos en `GET /events`
3. Abrir http://localhost:8001/docs y consultar `GET /semantic-events` para ver el enriquecimiento semántico
4. Consultar `GET /fhir-events` para ver la serialización FHIR
5. Abrir http://localhost:8004/docs y lanzar `POST /exchange/run`; luego `POST /exchange/{run_id}/next` repetidamente (uno por paso, 10 en total) para ver el intercambio real avanzar por el EDC del VPS (requiere conectividad a `*.tx.test`)
6. Consultar `GET /exchange/{run_id}/data` para ver el bundle recibido, y `POST /analyze` en http://localhost:8002/docs con `{"semantic_events": [...]}` de ese bundle para ver el análisis
7. Abrir http://localhost:8003 para ver la interfaz de demostración completa: un click genera el escenario y la adaptación semántica, y a partir de ahí cada paso del EDC se ejecuta con su propio click en el bloque "Tractus-X Dataspace"
