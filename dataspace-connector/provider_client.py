import requests

import config
from http_utils import run_step


def _entity_a_headers():

    return {
        "X-Api-Key": config.ENTITY_A_API_KEY
    }


# Reúne lo que semantic-adapter ya calculó (eventos semánticos + su
# serialización FHIR) en el bundle que se publicará en el submodel server.
# Es la única llamada de Entidad A a su propio semantic-adapter: ambos
# están del lado de Entidad A, así que no es el atajo cross-entidad que
# se está eliminando (ese era analytics llamando directamente a
# semantic-adapter).
def build_publish_payload():

    semantic_events = requests.get(
        f"{config.SEMANTIC_ADAPTER_URL}/semantic-events",
        timeout=10
    ).json()

    fhir_events = requests.get(
        f"{config.SEMANTIC_ADAPTER_URL}/fhir-events",
        timeout=10
    ).json()

    return {
        "semantic_events": semantic_events,
        "fhir_events": fhir_events,
    }


# Publica el contenido del caso en el submodel server de Entidad A, bajo
# la URN fija DATA_URN. Es lo único que cambia entre ejecuciones de la demo.
def publish_data(payload):

    url = f"{config.ENTITY_A_DATA_SERVER}/{config.DATA_URN}"

    return run_step(
        "publish_data", "POST", url,
        json_body=payload,
        ok_statuses=(200, 201, 204)
    )


# Asset EDC apuntando al submodel server de Entidad A (proxy completo:
# la URN concreta se resuelve en el momento del fetch, no aquí). ID fijo:
# un 409 significa que ya existe de una ejecución anterior, lo que cuenta
# como éxito.
def ensure_asset():

    url = f"{config.ENTITY_A}/assets"

    body = {
        "@context": {
            "@vocab": "https://w3id.org/edc/v0.0.1/ns/",
            "edc": "https://w3id.org/edc/v0.0.1/ns/",
            "tx": "https://w3id.org/tractusx/v0.0.1/ns/",
            "tx-auth": "https://w3id.org/tractusx/auth/",
            "cx-policy": "https://w3id.org/catenax/policy/",
            "odrl": "http://www.w3.org/ns/odrl/2/"
        },
        "@id": config.ASSET_ID,
        "properties": {
            "description": "Telecare FHIR Asset (Entidad A)"
        },
        "dataAddress": {
            "@type": "DataAddress",
            "type": "HttpData",
            "proxyPath": "true",
            "proxyMethod": "true",
            "proxyQueryParams": "true",
            "proxyBody": "true",
            "baseUrl": config.ENTITY_A_DATA_SERVER
        }
    }

    return run_step(
        "ensure_asset", "POST", url,
        headers=_entity_a_headers(), json_body=body,
        ok_statuses=(200, 201), exists_statuses=(409,)
    )


# Política de acceso: solo Entidad B (por BPN) puede ver el asset en su catálogo.
def ensure_access_policy():

    url = f"{config.ENTITY_A}/policydefinitions"

    body = {
        "@context": [
            "https://w3id.org/dspace/2025/1/odrl-profile.jsonld",
            "https://w3id.org/catenax/2025/9/policy/context.jsonld",
            {
                "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
            }
        ],
        "@id": config.ACCESS_POLICY_ID,
        "@type": "PolicyDefinition",
        "policy": {
            "@type": "Set",
            "permission": [
                {
                    "action": "access",
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
                                    "leftOperand": "BusinessPartnerNumber",
                                    "operator": "isAnyOf",
                                    "rightOperand": [config.ENTITY_B_BPN]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    }

    return run_step(
        "ensure_access_policy", "POST", url,
        headers=_entity_a_headers(), json_body=body,
        ok_statuses=(200, 201), exists_statuses=(409,)
    )


# Política de uso: condiciones bajo las que el activo puede usarse una vez
# transferido (framework agreement + propósito de uso).
def ensure_usage_policy():

    url = f"{config.ENTITY_A}/policydefinitions"

    body = {
        "@context": [
            "https://w3id.org/dspace/2025/1/odrl-profile.jsonld",
            "https://w3id.org/catenax/2025/9/policy/context.jsonld",
            {
                "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
            },
            {}
        ],
        "@type": "PolicyDefinition",
        "@id": config.USAGE_POLICY_ID,
        "policy": {
            "@type": "Set",
            "permission": [
                {
                    "action": "use",
                    "constraint": {
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
                                "rightOperand": ["cx.core.industrycore:1"]
                            }
                        ]
                    }
                }
            ],
            "prohibition": [],
            "obligation": []
        }
    }

    return run_step(
        "ensure_usage_policy", "POST", url,
        headers=_entity_a_headers(), json_body=body,
        ok_statuses=(200, 201), exists_statuses=(409,)
    )


# Vincula asset + políticas: lo que hace que el asset aparezca en el
# catálogo que ve Entidad B.
def ensure_contract_definition():

    url = f"{config.ENTITY_A}/contractdefinitions"

    body = {
        "@context": {
            "edc": "https://w3id.org/edc/v0.0.1/ns/"
        },
        "@id": config.CONTRACT_ID,
        "@type": "ContractDefinition",
        "accessPolicyId": config.ACCESS_POLICY_ID,
        "contractPolicyId": config.USAGE_POLICY_ID,
        "assetsSelector": [
            {
                "@type": "CriterionDto",
                "operandLeft": "https://w3id.org/edc/v0.0.1/ns/id",
                "operator": "=",
                "operandRight": config.ASSET_ID
            }
        ]
    }

    return run_step(
        "ensure_contract_definition", "POST", url,
        headers=_entity_a_headers(), json_body=body,
        ok_statuses=(200, 201), exists_statuses=(409,)
    )


# Ejecuta los 5 pasos de Provide_Data en orden, cortando en el primer
# paso que falle. Los ensure_* son idempotentes: repetir la demo no
# acumula recursos EDC nuevos, solo refresca el contenido publicado en
# DATA_URN. Solo para pruebas manuales vía /provider/publish: el flujo
# guiado de la demo (exchange.py) ejecuta cada paso por separado.
def publish():

    payload = build_publish_payload()

    steps = []

    for name, func, args in (
        ("publish_data", publish_data, (payload,)),
        ("ensure_asset", ensure_asset, ()),
        ("ensure_access_policy", ensure_access_policy, ()),
        ("ensure_usage_policy", ensure_usage_policy, ()),
        ("ensure_contract_definition", ensure_contract_definition, ()),
    ):
        result = func(*args)
        steps.append(result)

        if result["status"] == "error":
            break

    return steps
