from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import config
import consumer_client
import exchange
import provider_client

app = FastAPI(
    title="Dataspace Connector"
)

# CORS abierto para permitir llamadas desde la demo-ui y herramientas
# de desarrollo sin restricción de origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Enmascara las API keys para poder exponer el resto de la configuración
# (rutas, BPNs, IDs de recursos) sin filtrar credenciales
def mask_key(key: str) -> str:

    return key[:2] + "***" if key else key


@app.get("/health")
def health():

    return {
        "status": "ok",
        "entity_a": config.ENTITY_A,
        "entity_a_dsp": config.ENTITY_A_DSP,
        "entity_a_data_server": config.ENTITY_A_DATA_SERVER,
        "entity_a_bpn": config.ENTITY_A_BPN,
        "entity_a_api_key": mask_key(config.ENTITY_A_API_KEY),
        "entity_b": config.ENTITY_B,
        "entity_b_bpn": config.ENTITY_B_BPN,
        "entity_b_api_key": mask_key(config.ENTITY_B_API_KEY),
        "asset_id": config.ASSET_ID,
        "access_policy_id": config.ACCESS_POLICY_ID,
        "usage_policy_id": config.USAGE_POLICY_ID,
        "contract_id": config.CONTRACT_ID,
        "data_urn": config.DATA_URN,
    }


# Publica el caso actual (leído de semantic-adapter) en el EDC de
# Entidad A: contenido + asset + políticas + contract definition.
# Solo para pruebas manuales; el flujo guiado usa /exchange/*.
@app.post("/provider/publish")
def provider_publish():

    return provider_client.publish()


# Consume el activo publicado por Entidad A desde el lado de Entidad B:
# catálogo → negociación de contrato → EDR → autorización → descarga real.
# Solo para pruebas manuales; el flujo guiado usa /exchange/*.
@app.post("/consumer/fetch")
def consumer_fetch():

    return consumer_client.fetch()


# Crea una ejecución guiada del intercambio (Provide_Data + Consume_Data)
# y reúne el payload a publicar, pero no ejecuta ningún paso EDC todavía.
@app.post("/exchange/run")
def exchange_run():

    run_id = exchange.start_run()

    return {"run_id": run_id}


# Ejecuta en segundo plano el siguiente paso pendiente de la ejecución
# (un paso por llamada); el progreso se sigue vía GET /exchange/{run_id}
@app.post("/exchange/{run_id}/next")
def exchange_next(run_id: str):

    run = exchange.advance(run_id)

    if run is None:
        raise HTTPException(status_code=404, detail="run not found")

    return run


@app.get("/exchange/{run_id}")
def exchange_status(run_id: str):

    run = exchange.get_run(run_id)

    if run is None:
        raise HTTPException(status_code=404, detail="run not found")

    return run


# El bundle {semantic_events, fhir_events} recibido vía EDC, disponible
# solo cuando la ejecución ha terminado con éxito
@app.get("/exchange/{run_id}/data")
def exchange_data(run_id: str):

    run = exchange.get_run(run_id)

    if run is None:
        raise HTTPException(status_code=404, detail="run not found")

    if run["status"] != "done":
        raise HTTPException(status_code=409, detail=f"run status is '{run['status']}'")

    return exchange.get_run_data(run_id)
