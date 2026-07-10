# Entorno de desarrollo local

Este documento cubre la puesta en marcha del **stack Python** del caso de uso telecare en local.  
Para el despliegue del Data Space (Tractus-X Umbrella en VPS) ver [README.md](README.md).

---

## Arquitectura de servicios

| Servicio | Puerto | Descripción |
|---|---|---|
| `generator` | 8000 | Generador sintético de eventos de teleasistencia |
| `semantic-adapter` | 8001 | Adaptador semántico: enriquece eventos y los serializa a HL7 FHIR |
| `analytics` | 8002 | Motor de análisis: genera activos derivados a partir de los eventos |
| `demo-ui` | 8003 | Interfaz web de demostración |

Todos los servicios son APIs FastAPI independientes. El `semantic-adapter` y el `analytics` consumen los datos del `generator`. La `demo-ui` los presenta.

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
| `GET` | `/derived-assets` | Activos derivados calculados a partir de los eventos |

---

## Flujo típico de prueba

1. Abrir http://localhost:8000/docs y lanzar `POST /generate/fall-alert`
2. Verificar los eventos brutos en `GET /events`
3. Abrir http://localhost:8001/docs y consultar `GET /semantic-events` para ver el enriquecimiento semántico
4. Consultar `GET /fhir-events` para ver la serialización FHIR
5. Abrir http://localhost:8002/docs y consultar `GET /derived-assets` para ver el análisis
6. Abrir http://localhost:8003 para ver la interfaz de demostración
