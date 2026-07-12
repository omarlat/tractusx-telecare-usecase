import os

# Configuración del espacio de datos: rutas y credenciales de los dos
# participantes EDC de la demo — Entidad A (provider) y Entidad B
# (consumer) — ver brunoExamples/collection.bru. Todo es sobreescribible
# por variable de entorno, con los valores del EDC real desplegado como
# default, para poder desplegar este servicio en Docker sin tocar código.

ENTITY_A = os.environ.get(
    "ENTITY_A", "http://dataprovider-controlplane.tx.test/management/v3"
)
ENTITY_A_DSP = os.environ.get(
    "ENTITY_A_DSP", "http://dataprovider-controlplane.tx.test/api/v1/dsp"
)
ENTITY_A_DATA_SERVER = os.environ.get(
    "ENTITY_A_DATA_SERVER", "http://dataprovider-submodelserver.tx.test"
)
ENTITY_A_BPN = os.environ.get("ENTITY_A_BPN", "BPNL00000003AYRE")
ENTITY_A_DID = os.environ.get(
    "ENTITY_A_DID", "did:web:ssi-dim-wallet-stub.tx.test:BPNL00000003AYRE"
)
ENTITY_A_API_KEY = os.environ.get("ENTITY_A_API_KEY", "TEST2")

ENTITY_B = os.environ.get(
    "ENTITY_B", "http://dataconsumer-1-controlplane.tx.test/management/v3"
)
ENTITY_B_BPN = os.environ.get("ENTITY_B_BPN", "BPNL00000003AZQP")
ENTITY_B_DID = os.environ.get(
    "ENTITY_B_DID", "did:web:ssi-dim-wallet-stub.tx.test:BPNL00000003AZQP"
)
ENTITY_B_API_KEY = os.environ.get("ENTITY_B_API_KEY", "TEST1")

# IDs de recursos EDC fijos: se crean una única vez de forma idempotente
# (ver ensure_* en provider_client.py) y se reutilizan en cada ejecución
# de la demo. Solo el contenido publicado en DATA_URN cambia por ejecución.
ASSET_ID = os.environ.get("ASSET_ID", "telecare-fhir-asset")
ACCESS_POLICY_ID = os.environ.get("ACCESS_POLICY_ID", "telecare-access-policy")
USAGE_POLICY_ID = os.environ.get("USAGE_POLICY_ID", "telecare-usage-policy")
CONTRACT_ID = os.environ.get("CONTRACT_ID", "telecare-contract-definition")
DATA_URN = os.environ.get("DATA_URN", "urn:uuid:telecare-case-data")

DSP_PROTOCOL = "dataspace-protocol-http:2025-1"

# Servicio propio del que Entidad A reúne lo que va a publicar (no es
# parte del espacio de datos: es el backend de Entidad A leyendo sus
# propios datos)
SEMANTIC_ADAPTER_URL = os.environ.get(
    "SEMANTIC_ADAPTER_URL", "http://localhost:8001"
)
