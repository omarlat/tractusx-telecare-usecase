import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="Telecare Demo UI"
)

templates = Jinja2Templates(
    directory="templates"
)


# Única ruta de la UI: devuelve el HTML de la demo.
# Toda la lógica de presentación y las llamadas a los servicios
# se realizan en el cliente (static/js/app.js)
@app.get("/", response_class=HTMLResponse)
def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


# Rutas de los servicios que consume el navegador, generadas a partir de
# variables de entorno (localhost:800X como default, igual que hoy).
# Registrada antes del mount de /static para interceptar solo este path;
# el resto de /static/js, /static/css, etc. sigue sirviéndose como fichero.
@app.get("/static/js/config.js")
def config_js():

    content = f"""// Rutas de los servicios que consume la demo-ui. En local (sin variables
// de entorno definidas) apuntan a los mismos localhost:800X de siempre;
// en un despliegue Docker se sobreescriben con las URLs públicas (ver DEPLOY.md).
const SERVICE_URLS = {{
    generator: "{os.environ.get('GENERATOR_URL', 'http://localhost:8000')}",
    semanticAdapter: "{os.environ.get('SEMANTIC_ADAPTER_URL', 'http://localhost:8001')}",
    analytics: "{os.environ.get('ANALYTICS_URL', 'http://localhost:8002')}",
    dataspaceConnector: "{os.environ.get('DATASPACE_CONNECTOR_URL', 'http://localhost:8004')}",
}}
"""

    return Response(content=content, media_type="application/javascript")


# Archivos estáticos (CSS, el resto de JS) servidos desde /static
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)
