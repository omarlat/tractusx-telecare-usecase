# Instalación de Apache Guacamole sobre Docker

Nota de infraestructura sobre el acceso remoto al VPS; para la visión general del proyecto ver el [README](../README.md).

## Objetivo

Desplegar una instancia funcional de Apache Guacamole utilizando Docker Compose y PostgreSQL como backend de autenticación, permitiendo el acceso remoto vía navegador a escritorios y terminales del VPS.

---

# 1. Estructura de despliegue

Arquitectura desplegada:

```text
Navegador
   ↓
Nginx Proxy
   ↓
Guacamole (Docker)
   ↓
guacd (Docker)
   ↓
RDP / SSH / VNC
   ↓
Servidor Ubuntu VPS
```

Componentes utilizados:

* guacamole/guacamole
* guacamole/guacd
* postgres:16
* nginx

---

# 2. Docker Compose

Fichero `docker-compose.yml`:

```yaml
services:

  guacd:
    image: guacamole/guacd
    container_name: guacd
    restart: unless-stopped

  postgres:
    image: postgres:16
    container_name: guac-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: guacamole_db
      POSTGRES_USER: guacamole_user
      POSTGRES_PASSWORD: <POSTGRES_PASSWORD>
    volumes:
      - postgres_data:/var/lib/postgresql/data

  guacamole:
    image: guacamole/guacamole
    container_name: guacamole
    restart: unless-stopped
    ports:
      - "8090:8080"
    environment:
      GUACD_HOSTNAME: guacd
      POSTGRESQL_HOSTNAME: postgres
      POSTGRESQL_DATABASE: guacamole_db
      POSTGRESQL_USERNAME: guacamole_user
      POSTGRESQL_PASSWORD: <POSTGRES_PASSWORD>
      EXTENSION_PRIORITY: postgresql
    depends_on:
      - guacd
      - postgres

volumes:
  postgres_data:
```

---

# 3. Inicialización de PostgreSQL

## Generación del schema

```bash
docker run --rm guacamole/guacamole /opt/guacamole/bin/initdb.sh --postgresql > initdb.sql
```

---

## Arranque inicial de PostgreSQL

```bash
docker compose up -d postgres
```

---

## Importación del schema

```bash
cat initdb.sql | docker exec -i guac-postgres psql -U guacamole_user -d guacamole_db
```

---

# 4. Arranque completo

```bash
docker compose up -d
```

---

# 5. Configuración de Nginx

## Instalación

```bash
sudo apt update
sudo apt install -y nginx
```

---

## Configuración VirtualHost

Fichero:

```text
/etc/nginx/sites-available/guacamole
```

Contenido:

```nginx
server {

    listen 80;

    server_name guacamole.tx.test;

    location / {

        proxy_pass http://127.0.0.1:8090/guacamole/;

        proxy_buffering off;

        proxy_http_version 1.1;

        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $http_connection;
        proxy_cookie_path /guacamole/ /;

        access_log off;

    }

}
```

---

## Activación del site

```bash
sudo ln -s /etc/nginx/sites-available/guacamole /etc/nginx/sites-enabled/
```

---

## Validación de configuración

```bash
sudo nginx -t
```

---

## Reinicio de Nginx

```bash
sudo systemctl restart nginx
```

---

# 6. Configuración DNS local

Entrada añadida al fichero `hosts` del equipo cliente:

```text
IP_VPS guacamole.tx.test
```

Ejemplo Windows:

```text
C:\Windows\System32\drivers\etc\hosts
```

---

# 7. Acceso a Guacamole

URL de acceso:

```text
http://IP_VPS:8090/guacamole
```

o mediante DNS:

```text
http://guacamole.tx.test/guacamole
```

Credenciales por defecto:

```text
usuario: <USUARIO_ADMIN>
password: <PASSWORD_ADMIN>
```

---

# 8. Configuración de Bitdefender

Se añadieron excepciones en Bitdefender para evitar interferencias con:

* autenticación web
* WebSockets
* tráfico HTTP local

Excepciones añadidas:

```text
http://guacamole.tx.test
```

y:

```text
http://IP_VPS:8090
```

---

# 9. Instalación de escritorio remoto Ubuntu

## Instalación de XRDP

```bash
sudo apt update
sudo apt install -y xrdp
```

---

## Instalación de entorno gráfico XFCE

```bash
sudo apt install -y xfce4 xfce4-goodies
```

---

## Configuración de sesión XFCE

```bash
echo xfce4-session > ~/.xsession
```

---

## Permisos XRDP

```bash
sudo adduser xrdp ssl-cert
```

---

## Reinicio de XRDP

```bash
sudo systemctl restart xrdp
```

---

## Verificación del puerto RDP

```bash
sudo ss -tulpn | grep 3389
```

---

# 10. Configuración de conexión RDP en Guacamole

## Parámetros utilizados

### Protocolo

```text
RDP
```

### Hostname

```text
172.17.0.1
```

### Puerto

```text
3389
```

### Usuario

```text
<USUARIO_RDP>
```

### Modo seguridad

```text
RDP
```

---

# 11. Resultado final

Se consiguió acceso remoto al escritorio Ubuntu del VPS directamente desde navegador mediante Apache Guacamole.
