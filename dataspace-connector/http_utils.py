import requests


# Enmascara valores sensibles (API keys) antes de exponer una request
# capturada a la UI para inspección
def mask_headers(headers):

    if not headers:
        return {}

    masked = dict(headers)

    if "X-Api-Key" in masked:
        masked["X-Api-Key"] = masked["X-Api-Key"][:2] + "***"

    if "Authorization" in masked and masked["Authorization"]:
        masked["Authorization"] = masked["Authorization"][:8] + "***"

    return masked


# Ejecuta una llamada HTTP contra el EDC y la envuelve en un resultado
# uniforme (status/request/response), reutilizado tanto para exponer cada
# paso a la UI como para decidir cuándo un 409 ("ya existe") cuenta como
# éxito en los ensure_* idempotentes.
def run_step(
    name,
    method,
    url,
    headers=None,
    json_body=None,
    ok_statuses=(200, 201, 204),
    exists_statuses=()
):

    response = requests.request(
        method,
        url,
        headers=headers,
        json=json_body,
        timeout=30
    )

    if response.status_code in ok_statuses:
        status = "created"
    elif response.status_code in exists_statuses:
        status = "exists"
    else:
        status = "error"

    try:
        response_body = response.json()
    except ValueError:
        response_body = response.text

    return {
        "step": name,
        "status": status,
        "http_status": response.status_code,
        "request": {
            "method": method,
            "url": url,
            "headers": mask_headers(headers),
            "body": json_body,
        },
        "response": response_body,
    }
