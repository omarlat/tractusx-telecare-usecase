// Rutas de los servicios que consume la demo-ui. Todas apuntan a
// localhost porque en desarrollo cada servicio corre en su propio
// puerto (ver DEV.md); en un despliegue real cada URL se ajustaría aquí.
const SERVICE_URLS = {
    generator: "http://localhost:8000",
    semanticAdapter: "http://localhost:8001",
    analytics: "http://localhost:8002",
    dataspaceConnector: "http://localhost:8004",
}
