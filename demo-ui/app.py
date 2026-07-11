from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="Telecare Demo UI"
)

# Archivos estáticos (CSS, JS) servidos desde /static
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
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
