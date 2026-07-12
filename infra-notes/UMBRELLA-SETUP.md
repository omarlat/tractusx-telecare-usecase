# Tractus-X Umbrella Portal en Ubuntu 24.04 sobre VPS

## Objetivo

Montar **Tractus-X Umbrella** en un **VPS con Ubuntu 24.04**, usando:

* **Minikube** como clúster Kubernetes local
* **Docker** como driver de Minikube
* **Helm** para desplegar el chart Umbrella
* **Nginx** en el VPS como proxy inverso para exponer los hosts `*.tx.test`

Este documento deja anotado qué se hizo, qué problemas aparecieron y cómo se resolvieron.

---

## Entorno usado

* Sistema operativo del VPS: **Ubuntu 24.04**
* Recursos del VPS:

  * **8 vCPU**
  * **24 GB RAM**
    
* Host público del VPS: `IP_PUBLICA_VPS`

---

## Herramientas necesarias antes de Tractus-X Umbrella

Antes de arrancar Minikube y desplegar Umbrella, se necesitó instalar:

* Docker
* Minikube
* kubectl
* Helm
* git
* curl
* nginx

---

## Dependencias básicas

```bash
sudo apt update
sudo apt install -y curl ca-certificates gnupg git
```

---

## Minikube - instalación oficial por binario

```bash
curl -LO https://github.com/kubernetes/minikube/releases/latest/download/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
rm minikube-linux-amd64
```

### Verificación

```bash
minikube version
```

---

## kubectl - instalación oficial

```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl.sha256"
echo "$(cat kubectl.sha256)  kubectl" | sha256sum --check
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
rm -f kubectl kubectl.sha256
```

### Verificación

```bash
kubectl version --client
```

---

## Helm - importante usar Helm 3

Durante la instalación apareció un problema porque inicialmente se instaló **Helm 4**, pero **Tractus-X Umbrella requiere Helm 3.8+**.

### Instalar Helm 3

```bash
sudo rm -f /usr/local/bin/helm
curl -fsSL -o helm-v3.19.0-linux-amd64.tar.gz https://get.helm.sh/helm-v3.19.0-linux-amd64.tar.gz
tar -xzf helm-v3.19.0-linux-amd64.tar.gz
sudo install linux-amd64/helm /usr/local/bin/helm
rm -rf linux-amd64 helm-v3.19.0-linux-amd64.tar.gz
```

### Limpiar caché/config previa de Helm

```bash
rm -rf ~/.cache/helm ~/.config/helm ~/.local/share/helm
```

### Verificación

```bash
helm version
```

Debe devolver una versión `v3.x`.

---

## Docker y permisos para el usuario

Al arrancar Minikube apareció este error:

```text
permission denied while trying to connect to the Docker daemon socket
```

La causa era que el usuario no tenía permisos sobre el socket de Docker.

### Solución

```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Verificación

```bash
docker version
docker ps
```

---

## Arranque de Minikube

La guía de Tractus-X mostraba un mínimo de `4 CPU / 6 GB`, pero como el VPS tenía más recursos se decidió usar una configuración más holgada.

### Comando usado

```bash
minikube start --driver=docker --cpus=6 --memory=12g
```

### Verificaciones útiles

```bash
minikube status
kubectl get nodes
kubectl get pods -A
```

---

## Red de Tractus-X en Minikube

Antes del despliegue de Umbrella hubo que activar los addons de red:

```bash
minikube addons enable ingress
minikube addons enable ingress-dns
```

### Obtener IP de Minikube

```bash
minikube ip
```

En este caso quedó:

```text
192.168.49.2
```

---

## Hosts internos en el VPS

En `/etc/hosts` del VPS se añadieron los hostnames `*.tx.test` apuntando a la IP de Minikube.

### Ejemplo de entradas usadas

```text
192.168.49.2 centralidp.tx.test
192.168.49.2 sharedidp.tx.test
192.168.49.2 portal.tx.test
192.168.49.2 portal-backend.tx.test
192.168.49.2 semantics.tx.test
192.168.49.2 sdfactory.tx.test
192.168.49.2 ssi-credential-issuer.tx.test
192.168.49.2 dataconsumer-1-dataplane.tx.test
192.168.49.2 dataconsumer-1-controlplane.tx.test
192.168.49.2 dataprovider-dataplane.tx.test
192.168.49.2 dataprovider-controlplane.tx.test
192.168.49.2 dataprovider-submodelserver.tx.test
192.168.49.2 dataconsumer-2-dataplane.tx.test
192.168.49.2 dataconsumer-2-controlplane.tx.test
192.168.49.2 bdrs-server.tx.test
192.168.49.2 business-partners.tx.test
192.168.49.2 pgadmin4.tx.test
192.168.49.2 ssi-dim-wallet-stub.tx.test
192.168.49.2 smtp.tx.test
```

---

## Clonar Tractus-X Umbrella

```bash
cd ~
git clone https://github.com/eclipse-tractusx/tractus-x-umbrella.git
cd tractus-x-umbrella
```

---

## Problema con dependencias Helm de Umbrella

Al ejecutar el script de dependencias apareció este error:

```text
Error: no cached repository for helm-manager-... found
```

### Causa

El chart `umbrella-infrastructure` necesitaba repositorios Helm que no estaban añadidos o cacheados correctamente.

### Solución aplicada

```bash
helm repo add external-secrets https://charts.external-secrets.io
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
bash ./hack/helm-dependencies.bash
```

### Verificación

```bash
helm repo list
```

---

## Despliegue del subset Portal

Se optó por instalar el subset **Portal** para tener algo visible en navegador.

### Ir al chart principal

```bash
cd ~/tractus-x-umbrella/charts/umbrella
```

### Instalar Portal

```bash
helm install -f values-adopter-portal.yaml umbrella . --namespace umbrella --create-namespace
```

### Comprobaciones

```bash
kubectl get pods -n umbrella
kubectl get svc -n umbrella
kubectl get ingress -n umbrella
```

### Estado final observado

* Pods principales en `Running`
* Jobs de migración y seeding en `Completed`
* Ingress creados correctamente para:

  * `portal.tx.test`
  * `centralidp.tx.test`
  * `sharedidp.tx.test`
  * `portal-backend.tx.test`
  * `pgadmin4.tx.test`

---

## Verificaciones internas dentro del VPS

### Portal

```bash
getent hosts portal.tx.test
curl -I http://portal.tx.test
```

Resultado esperado: `HTTP/1.1 200 OK`

### Central IDP

```bash
curl -I http://centralidp.tx.test/auth/realms/CX-Central/protocol/openid-connect/3p-cookies/step1.html
```

Resultado observado:

```text
HTTP/1.1 405 Method Not Allowed
```

Eso confirmó que el servicio respondía y que la ruta existía, aunque no aceptara `HEAD`.

---

## Problema al acceder desde Windows

Al principio se probó con:

* `ssh -L ...`
* `kubectl port-forward`
* puertos altos como `8080`

El frontend del portal cargaba, pero el login fallaba porque el navegador intentaba acceder a hosts reales como:

* `portal.tx.test`
* `centralidp.tx.test`
* `sharedidp.tx.test`
* `portal-backend.tx.test`

El flujo de autenticación con Keycloak no funcionaba correctamente si se accedía por `localhost:8080` o por rutas que no respetaban los hostnames reales.

---

## Solución final: Nginx en el VPS como reverse proxy

La solución que funcionó fue instalar **Nginx** en el VPS y hacer que escuchara en el puerto 80 del servidor, reenviando todas las peticiones `*.tx.test` a la IP de Minikube (`192.168.49.2`) y conservando el `Host` original.

### Instalar Nginx

```bash
sudo apt update
sudo apt install -y nginx
```

### Crear configuración

Archivo:

```text
/etc/nginx/sites-available/tx-test
```

Contenido:

```nginx
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name .tx.test;

    location / {
        proxy_pass http://192.168.49.2;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Activar configuración

```bash
sudo ln -s /etc/nginx/sites-available/tx-test /etc/nginx/sites-enabled/tx-test
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### Verificación interna

```bash
curl -I -H "Host: portal.tx.test" http://127.0.0.1
curl -I -H "Host: centralidp.tx.test" http://127.0.0.1
```

Con esto quedó resuelto el acceso web.

---

## Hosts en Windows

En el archivo `hosts` de Windows se añadieron los dominios `*.tx.test` apuntando a la IP pública del VPS.

### Ejemplo usado

```text
IP_PUBLICA_VPS centralidp.tx.test
IP_PUBLICA_VPS sharedidp.tx.test
IP_PUBLICA_VPS portal.tx.test
IP_PUBLICA_VPS portal-backend.tx.test
IP_PUBLICA_VPS semantics.tx.test
IP_PUBLICA_VPS sdfactory.tx.test
IP_PUBLICA_VPS ssi-credential-issuer.tx.test
IP_PUBLICA_VPS dataconsumer-1-dataplane.tx.test
IP_PUBLICA_VPS dataconsumer-1-controlplane.tx.test
IP_PUBLICA_VPS dataprovider-dataplane.tx.test
IP_PUBLICA_VPS dataprovider-controlplane.tx.test
IP_PUBLICA_VPS dataprovider-submodelserver.tx.test
IP_PUBLICA_VPS dataconsumer-2-dataplane.tx.test
IP_PUBLICA_VPS dataconsumer-2-controlplane.tx.test
IP_PUBLICA_VPS bdrs-server.tx.test
IP_PUBLICA_VPS business-partners.tx.test
IP_PUBLICA_VPS pgadmin4.tx.test
IP_PUBLICA_VPS ssi-dim-wallet-stub.tx.test
IP_PUBLICA_VPS smtp.tx.test
```

**Nota:** `smtp.tx.test` no se resuelve con este proxy HTTP de Nginx. Ese host no forma parte del tráfico web normal.

---

## Resultado final

Con esta configuración quedó accesible desde Windows:

```text
http://portal.tx.test
```

Y el flujo de autenticación dejó de romperse porque:

* el navegador usaba los hostnames reales
* Nginx preservaba la cabecera `Host`
* el ingress de Minikube podía enrutar correctamente cada petición
* Keycloak y el portal recibían el tráfico como esperaban

---

## Comandos de diagnóstico útiles

### Estado general

```bash
minikube status
kubectl get nodes
kubectl get pods -A
```

### Tractus-X Umbrella

```bash
kubectl get pods -n umbrella
kubectl get svc -n umbrella
kubectl get ingress -n umbrella
kubectl get events -n umbrella --sort-by=.lastTimestamp | tail -n 30
helm list -n umbrella
```

### Nginx

```bash
sudo nginx -t
sudo systemctl status nginx --no-pager
curl -I -H "Host: portal.tx.test" http://127.0.0.1
```

### Docker

```bash
docker version
docker ps
```

---

## Qué quedó pendiente o mejorable

* Añadir **HTTPS** si se quiere un entorno más realista
* Exponer solo los hosts necesarios según el subset instalado
* Revisar si en el futuro interesa automatizar el arranque de Minikube tras reinicio

---

