# Despliegue de los servicios Python en el VPS (Docker)

## Objetivo

Levantar los 5 servicios del stack Python (`generator`, `semantic-adapter`,
`analytics`, `demo-ui`, `dataspace-connector` — ver `DEV.md`) como
contenedores Docker en el mismo VPS que ya aloja el Tractus-X Umbrella
(ver `README.md`), y exponerlos con Nginx bajo un subdominio por servicio,
para poder acceder a la demo sin depender de tener nada arrancado en local.

Este documento describe los pasos a ejecutar **en el VPS**; no se ha
ejecutado nada de esto de forma remota al escribirlo.

---

## Prerrequisitos

El VPS ya tiene Docker instalado (se usa como driver de Minikube, ver
`README.md`). Falta comprobar el plugin `docker compose`:

```bash
docker compose version
```

Si no está disponible:

```bash
sudo apt update
sudo apt install -y docker-compose-plugin
```

---

## 1. Copiar el proyecto al VPS

Basta con el repositorio completo (o, como mínimo, las carpetas de los
5 servicios + `requirements.txt` + `docker-compose.yml` + `.env.example`).

```bash
git clone <url-del-repo> tractusx-telecare-usecase
cd tractusx-telecare-usecase
```

---

## 2. Configurar el `.env`

```bash
cp .env.example .env
```

Por defecto, `PUBLIC_*` apunta a los subdominios `*.tx.test` que se
configuran en el paso 4. Las variables `ENTITY_A*`/`ENTITY_B*` (comentadas
en `.env.example`) solo hace falta descomentarlas si el EDC real cambia
de host o de API keys — los defaults ya son los del Umbrella actual.

---

## 3. Construir y levantar los contenedores

```bash
docker compose build
docker compose up -d
```

Comprobación rápida (todo debería responder desde el propio VPS):

```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8001/health
curl -s http://127.0.0.1:8002/health
curl -s http://127.0.0.1:8003/static/js/config.js
curl -s http://127.0.0.1:8004/health
```

`ver logs` si algo no responde:

```bash
docker compose logs -f <servicio>
```

---

## 4. Exponer con Nginx

Mismo patrón que ya usa `README.md` para `*.tx.test`, pero apuntando a
`127.0.0.1` (los contenedores, en el propio VPS) en vez de a la IP de
Minikube.

Nuevo fichero `/etc/nginx/sites-available/telecare-demo`:

```nginx
server {
    listen 80;
    server_name generator.tx.test;
    location / { proxy_pass http://127.0.0.1:8000; }
}

server {
    listen 80;
    server_name semantic-adapter.tx.test;
    location / { proxy_pass http://127.0.0.1:8001; }
}

server {
    listen 80;
    server_name analytics.tx.test;
    location / { proxy_pass http://127.0.0.1:8002; }
}

server {
    listen 80;
    server_name demo-ui.tx.test;
    location / { proxy_pass http://127.0.0.1:8003; }
}

server {
    listen 80;
    server_name dataspace-connector.tx.test;
    location / { proxy_pass http://127.0.0.1:8004; }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/telecare-demo /etc/nginx/sites-enabled/telecare-demo
sudo nginx -t
sudo systemctl reload nginx
```

---

## 5. Añadir los subdominios al `hosts` de las máquinas cliente

Igual que ya se hizo para `*.tx.test` (ver `README.md`, sección "Hosts en
Windows"), añadir en el `hosts` de cada máquina desde la que se quiera
acceder a la demo:

```text
IP_PUBLICA_VPS generator.tx.test
IP_PUBLICA_VPS semantic-adapter.tx.test
IP_PUBLICA_VPS analytics.tx.test
IP_PUBLICA_VPS demo-ui.tx.test
IP_PUBLICA_VPS dataspace-connector.tx.test
```

---

## 6. Verificación

Desde una máquina cliente con el `hosts` del paso 5:

```text
http://demo-ui.tx.test
```

Debe cargar la demo igual que en local, con la diferencia de que el
bloque "Tractus-X Dataspace" ahora habla con el EDC real desde el VPS en
vez de desde tu máquina.

---

## Actualizar tras cambios de código

```bash
git pull
docker compose build
docker compose up -d
```

`docker compose up -d` sustituye solo los contenedores cuya imagen cambió.
