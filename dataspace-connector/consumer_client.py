import time

import config
from http_utils import run_step


def _entity_b_headers():

    return {
        "X-Api-Key": config.ENTITY_B_API_KEY
    }


# El catálogo devuelve JSON-LD, donde un único elemento puede aparecer
# como objeto suelto en vez de lista de un elemento (compactación JSON-LD)
def _as_list(value):

    if value is None:
        return []

    if isinstance(value, list):
        return value

    return [value]


def _extract_offer_id(catalog_response):

    if not isinstance(catalog_response, dict):
        return None

    datasets = _as_list(catalog_response.get("dataset"))

    if not datasets:
        return None

    policies = _as_list(datasets[0].get("hasPolicy"))

    if not policies:
        return None

    return policies[0].get("@id")


# Paso 1: pide a Entidad B el catálogo de Entidad A filtrado por nuestro
# asset y extrae el id de la oferta (policy) que hay que negociar
def request_catalog():

    url = f"{config.ENTITY_B}/catalog/request"

    body = {
        "@context": [
            {
                "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
            }
        ],
        "@type": "CatalogRequest",
        "counterPartyAddress": f"{config.ENTITY_A_DSP}/2025-1",
        "counterPartyId": config.ENTITY_A_DID,
        "protocol": config.DSP_PROTOCOL,
        "querySpec": {
            "offset": 0,
            "limit": 50,
            "sortOrder": "DESC",
            "sortField": "fieldName",
            "filterExpression": [
                {
                    "operandLeft": "https://w3id.org/edc/v0.0.1/ns/id",
                    "operator": "=",
                    "operandRight": config.ASSET_ID
                }
            ]
        }
    }

    result = run_step(
        "request_catalog", "POST", url,
        headers=_entity_b_headers(), json_body=body,
        ok_statuses=(200,)
    )

    offer_id = _extract_offer_id(result.get("response"))
    result["extracted"] = {"offer_id": offer_id}

    if result["status"] != "error" and not offer_id:
        result["status"] = "error"

    return result


# Paso 2: negocia el contrato a partir de la oferta descubierta
def negotiate_contract(offer_id):

    url = f"{config.ENTITY_B}/edrs"

    body = {
        "@context": [
            "http://www.w3.org/ns/odrl.jsonld",
            "https://w3id.org/catenax/2025/9/policy/context.jsonld",
            {
                "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
            }
        ],
        "@type": "ContractRequest",
        "counterPartyAddress": f"{config.ENTITY_A_DSP}/2025-1",
        "protocol": config.DSP_PROTOCOL,
        "policy": {
            "@id": offer_id,
            "@type": "Offer",
            "assigner": config.ENTITY_A_DID,
            "target": config.ASSET_ID,
            "permission": [
                {
                    "action": "use",
                    "constraint": [
                        {
                            "and": [
                                {
                                    "leftOperand": "Membership",
                                    "operator": "eq",
                                    "rightOperand": "active"
                                },
                                {
                                    "leftOperand": "FrameworkAgreement",
                                    "operator": "eq",
                                    "rightOperand": "DataExchangeGovernance:1.0"
                                },
                                {
                                    "leftOperand": "UsagePurpose",
                                    "operator": "isAnyOf",
                                    "rightOperand": "cx.core.industrycore:1"
                                }
                            ]
                        }
                    ]
                }
            ],
            "prohibition": [],
            "obligation": []
        },
        "callbackAddresses": []
    }

    result = run_step(
        "negotiate_contract", "POST", url,
        headers=_entity_b_headers(), json_body=body,
        ok_statuses=(200,)
    )

    response = result.get("response")
    negotiation_id = response.get("@id") if isinstance(response, dict) else None
    result["extracted"] = {"negotiation_id": negotiation_id}

    if result["status"] != "error" and not negotiation_id:
        result["status"] = "error"

    return result


# Paso 3: la negociación es asíncrona en el EDC real, así que hay que
# hacer polling a /edrs/request hasta que aparezca el transfer process
def wait_for_edr(negotiation_id, timeout=30, interval=2):

    url = f"{config.ENTITY_B}/edrs/request"

    body = {
        "@context": {
            "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
        },
        "@type": "QuerySpec",
        "filterExpression": [
            {
                "operandLeft": "contractNegotiationId",
                "operator": "=",
                "operandRight": negotiation_id
            }
        ]
    }

    deadline = time.time() + timeout
    result = None

    while time.time() < deadline:

        result = run_step(
            "wait_for_edr", "POST", url,
            headers=_entity_b_headers(), json_body=body,
            ok_statuses=(200,)
        )

        entries = _as_list(result.get("response"))
        transfer_process_id = entries[0].get("transferProcessId") if entries else None

        if transfer_process_id:
            result["extracted"] = {"transfer_process_id": transfer_process_id}
            return result

        time.sleep(interval)

    if result is None:
        result = {
            "step": "wait_for_edr",
            "status": "error",
            "http_status": None,
            "request": {"method": "POST", "url": url, "headers": {}, "body": body},
            "response": None,
        }

    result["status"] = "error"
    result["extracted"] = {"transfer_process_id": None}

    return result


# Paso 4: intercambia el transfer process por el endpoint público del
# EDC de Entidad A + el token con el que autenticarse ante él
def get_authorization(transfer_process_id):

    url = f"{config.ENTITY_B}/edrs/{transfer_process_id}/dataaddress?auto_refresh=true"

    result = run_step(
        "get_authorization", "GET", url,
        headers=_entity_b_headers(),
        ok_statuses=(200,)
    )

    response = result.get("response")
    endpoint = response.get("endpoint") if isinstance(response, dict) else None
    token = response.get("authorization") if isinstance(response, dict) else None
    result["extracted"] = {"endpoint": endpoint, "token": token}

    if result["status"] != "error" and not (endpoint and token):
        result["status"] = "error"

    return result


# Paso 5: descarga el contenido real a través del proxy del EDC, usando
# la misma URN bajo la que Entidad A lo publicó
def fetch_data(endpoint, token):

    url = f"{endpoint}/{config.DATA_URN}"

    return run_step(
        "fetch_data", "GET", url,
        headers={"Authorization": token},
        ok_statuses=(200,)
    )


# Ejecuta los 5 pasos de Consume_Data en orden, cortando en el primer
# paso que falle. Solo para pruebas manuales vía /consumer/fetch: el
# flujo guiado de la demo (exchange.py) ejecuta cada paso por separado.
def fetch():

    steps = []

    catalog = request_catalog()
    steps.append(catalog)
    if catalog["status"] == "error":
        return steps

    negotiation = negotiate_contract(catalog["extracted"]["offer_id"])
    steps.append(negotiation)
    if negotiation["status"] == "error":
        return steps

    edr = wait_for_edr(negotiation["extracted"]["negotiation_id"])
    steps.append(edr)
    if edr["status"] == "error":
        return steps

    authorization = get_authorization(edr["extracted"]["transfer_process_id"])
    steps.append(authorization)
    if authorization["status"] == "error":
        return steps

    data = fetch_data(
        authorization["extracted"]["endpoint"],
        authorization["extracted"]["token"]
    )
    steps.append(data)

    return steps
