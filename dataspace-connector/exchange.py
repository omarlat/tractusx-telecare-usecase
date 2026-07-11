import threading
import uuid

import consumer_client
import provider_client

PROVIDER_STEPS = [
    "publish_data",
    "ensure_asset",
    "ensure_access_policy",
    "ensure_usage_policy",
    "ensure_contract_definition",
]

CONSUMER_STEPS = [
    "request_catalog",
    "negotiate_contract",
    "wait_for_edr",
    "get_authorization",
    "fetch_data",
]

ALL_STEPS = PROVIDER_STEPS + CONSUMER_STEPS

# Qué función ejecuta cada paso: las de Entidad A no llevan argumentos
# propios (publish_data usa el payload guardado en el run), las de
# Entidad B encadenan la salida extraída del paso anterior (ver _step_args)
STEP_FUNC = {
    "publish_data": provider_client.publish_data,
    "ensure_asset": provider_client.ensure_asset,
    "ensure_access_policy": provider_client.ensure_access_policy,
    "ensure_usage_policy": provider_client.ensure_usage_policy,
    "ensure_contract_definition": provider_client.ensure_contract_definition,
    "request_catalog": consumer_client.request_catalog,
    "negotiate_contract": consumer_client.negotiate_contract,
    "wait_for_edr": consumer_client.wait_for_edr,
    "get_authorization": consumer_client.get_authorization,
    "fetch_data": consumer_client.fetch_data,
}

# Estado de todas las ejecuciones, en memoria: suficiente para una demo
# local de un único usuario. run_id -> run dict.
_runs = {}
_lock = threading.Lock()


def _blank_steps():

    return {
        name: {"step": name, "status": "pending"}
        for name in ALL_STEPS
    }


# Crea la ejecución y reúne de inmediato lo que se va a publicar (el caso
# ya generado y enriquecido por semantic-adapter), pero no ejecuta ningún
# paso EDC todavía: eso ocurre uno a uno, cada vez que se llama a advance().
def start_run():

    payload = provider_client.build_publish_payload()

    run = {
        "run_id": str(uuid.uuid4()),
        "status": "ready",  # ready | running | done | error
        "error": None,
        "cursor": 0,
        "payload": payload,
        "extracted": {},
        "data": None,
        "steps": _blank_steps(),
    }

    with _lock:
        _runs[run["run_id"]] = run

    return run["run_id"]


def _step_args(run, name):

    extracted = run["extracted"]

    if name == "publish_data":
        return (run["payload"],)

    if name == "negotiate_contract":
        return (extracted["offer_id"],)

    if name == "wait_for_edr":
        return (extracted["negotiation_id"],)

    if name == "get_authorization":
        return (extracted["transfer_process_id"],)

    if name == "fetch_data":
        return (extracted["endpoint"], extracted["token"])

    return ()


def _execute_step(run, name):

    with _lock:
        run["steps"][name] = {"step": name, "status": "in_progress"}

    try:
        result = STEP_FUNC[name](*_step_args(run, name))
    except Exception as exc:
        result = {
            "step": name,
            "status": "error",
            "http_status": None,
            "request": None,
            "response": str(exc),
        }

    with _lock:

        run["steps"][name] = result

        if result["status"] == "error":
            run["status"] = "error"
            run["error"] = name
            return

        if result.get("extracted"):
            run["extracted"].update(result["extracted"])

        run["cursor"] += 1

        if name == "fetch_data":
            run["data"] = result["response"]
            run["status"] = "done"
        else:
            run["status"] = "ready"


# Ejecuta en segundo plano el siguiente paso pendiente de la ejecución.
# No hace nada si ya hay un paso en curso o si la ejecución ya terminó:
# el front decide cuándo avanzar, un paso por click.
def advance(run_id):

    with _lock:

        run = _runs.get(run_id)

        if run is None:
            return None

        if run["status"] != "ready":
            return _view(run)

        run["status"] = "running"
        name = ALL_STEPS[run["cursor"]]

    threading.Thread(
        target=_execute_step, args=(run, name), daemon=True
    ).start()

    return _view(run)


def _view(run):

    return {
        "run_id": run["run_id"],
        "status": run["status"],
        "error": run["error"],
        "next_step": ALL_STEPS[run["cursor"]] if run["cursor"] < len(ALL_STEPS) else None,
        "steps": [run["steps"][name] for name in ALL_STEPS],
    }


def get_run(run_id):

    with _lock:

        run = _runs.get(run_id)

        return _view(run) if run else None


def get_run_data(run_id):

    with _lock:

        run = _runs.get(run_id)

        return run["data"] if run else None
