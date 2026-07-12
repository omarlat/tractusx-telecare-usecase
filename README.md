# tractusx-telecare-usecase

Prueba de concepto de un espacio de datos de **teleasistencia** inspirado en [Eclipse Tractus-X](https://eclipse-tractusx.github.io/), realizada como Trabajo de Fin de Grado (UNIR).

El proyecto simula el intercambio de datos de eventos de teleasistencia (caídas, niveles de oxígeno, etc.) entre dos organizaciones a través de un espacio de datos soberano real: los datos se generan, se enriquecen semánticamente (HL7 FHIR), se publican y se consumen mediante un **Eclipse Dataspace Connector (EDC)** desplegado sobre **Tractus-X Umbrella**, y finalmente se analizan — igual que ocurriría en un caso de uso real de intercambio de datos de salud entre proveedores.

## Arquitectura

Cinco servicios FastAPI independientes:

| Servicio | Puerto | Descripción |
|---|---|---|
| `generator` | 8000 | Generador sintético de eventos de teleasistencia |
| `semantic-adapter` | 8001 | Enriquece los eventos y los serializa a HL7 FHIR |
| `analytics` | 8002 | Genera activos derivados a partir de los eventos analizados |
| `dataspace-connector` | 8004 | Cliente EDC: publica el dato como Entidad A y lo consume como Entidad B a través del espacio de datos real |
| `demo-ui` | 8003 | Interfaz web que enlaza todo el flujo |

El flujo es: `generator` → `semantic-adapter` → `dataspace-connector` (publica en el EDC de Entidad A, consume desde el EDC de Entidad B) → `analytics`. La `demo-ui` presenta cada paso.

## Puesta en marcha

- **Entorno local (Python):** ver [DEV.md](DEV.md).
- **Despliegue en VPS (Docker):** ver [DEPLOY.md](DEPLOY.md).
- **Despliegue de Tractus-X Umbrella y del espacio de datos (EDC) sobre el que corre la demo:** ver [infra-notes/](infra-notes/).
- **Colección Bruno con el flujo EDC probado a mano:** ver [brunoExamples/](brunoExamples/README.md).

## Documentación adicional

- [infra-notes/UMBRELLA-SETUP.md](infra-notes/UMBRELLA-SETUP.md) — instalación de Tractus-X Umbrella (Minikube + Helm) en el VPS.
- [infra-notes/PORTAL-DATA-EXCHANGE.md](infra-notes/PORTAL-DATA-EXCHANGE.md) — ampliación del despliegue con el subset de Data Exchange (los dos EDC usados por `dataspace-connector`).
- [infra-notes/GUACAMOLE.md](infra-notes/GUACAMOLE.md) — acceso remoto de escritorio al VPS vía navegador.

## Licencia

[Apache License 2.0](LICENSE).
