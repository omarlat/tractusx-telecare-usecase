# README - Extensión de Tractus-X Umbrella: Portal + Data Exchange

## Objetivo

Documentar la segunda fase del montaje de **Tractus-X Umbrella** en el VPS, en la que se pasó de un despliegue estable de **Portal** a un despliegue combinado de:

* **Portal**
* **IAM** (`centralidp`, `sharedidp`)
* **Data Exchange básico**

  * `dataconsumerOne`
  * `tx-data-provider`
  * `identity-and-trust-bundle`
  * `submodelserver`

Este documento recoge:

* qué se intentó inicialmente
* por qué no funcionó como se esperaba
* qué hace realmente `helm upgrade`
* cómo se creó un `values` combinado
* qué problemas salieron en Data Exchange
* cómo se diagnosticaron y resolvieron
* cómo se verificó que el resultado final estaba bien

---

## Situación inicial

Antes de esta fase ya estaba funcionando correctamente el subset **Portal** de Tractus-X Umbrella.

Eso implicaba que estaban operativos:

* `portal.tx.test`
* `portal-backend.tx.test`
* `centralidp.tx.test`
* `sharedidp.tx.test`
* el acceso desde Windows a través de **Nginx** en el VPS

---

## Qué se intentó primero

Se lanzó este comando:

```bash
helm upgrade -f values-adopter-data-exchange.yaml umbrella . -n umbrella
```

La idea inicial era “añadir” Data Exchange sobre el despliegue existente de Portal.

---

## Qué hace realmente `helm upgrade`

Ese comando **no añade otra instalación independiente**.

Sobre una release existente (`umbrella`), `helm upgrade`:

* vuelve a renderizar el chart
* aplica los `values` que se le pasan en ese momento
* y actualiza la release con esa nueva configuración

En la práctica, eso significa que:

* no se estaba instalando “Portal + Data Exchange” automáticamente
* se estaba reconfigurando la release `umbrella` con el subset **Data Exchange**

Por eso al hacer el upgrade desaparecieron recursos del Portal del mismo modo que habían aparecido los de Data Exchange.

---

## Conclusión de esa prueba

Los ficheros predefinidos:

* `values-adopter-portal.yaml`
* `values-adopter-data-exchange.yaml`

no deben entenderse como capas acumulativas, sino como **subsets alternativos preconfigurados**.

Si se quiere una instalación combinada, lo correcto es construir un fichero propio.

---

## Solución adoptada: values combinado

Se creó un fichero propio para mantener Portal y añadir solo lo necesario de Data Exchange.

### Componentes que se decidieron mantener activos

#### De Portal

* `portal`
* `centralidp`
* `sharedidp`
* `pgadmin4`

#### De Data Exchange

* `dataconsumerOne`
* `tx-data-provider`
* `identity-and-trust-bundle`

### Componentes que se dejaron desactivados

* `dataconsumerTwo`
* `bdrs-server-memory`
* `bpdm`
* `selfdescription`
* `smtp4dev`
* `bpndiscovery`
* `discoveryfinder`
* `ssi-credential-issuer`

### Aplicación del values combinado

```bash
helm upgrade -f my-values-portal-data-exchange.yaml umbrella . -n umbrella
```

---

## Primer problema al desplegar Data Exchange

Después del `helm upgrade`, varios pods quedaron en estados como:

* `ImagePullBackOff`
* `ErrImagePull`

### Síntoma observado

En los eventos de Kubernetes aparecían errores como:

```text
Get "https://registry-1.docker.io/v2/": context deadline exceeded
```

### Primer sospecha descartada

Se pensó si la configuración de Nginx en el VPS podía haber roto la conectividad, pero no era así.

### Diagnóstico real

* desde el VPS, `curl -I https://registry-1.docker.io/v2/` respondía correctamente
* desde el VPS, `docker pull ...` funcionaba
* dentro de `minikube ssh`, el `curl` a Docker Hub no respondía

Esto confirmó que:

* el VPS sí tenía salida a Internet
* el problema estaba en la **red del nodo Minikube**, no en Nginx

---

## Solución aplicada al problema de red de Minikube

Se reinició Docker y Minikube para recuperar la conectividad del nodo.

### Pasos usados

```bash
minikube stop
sudo systemctl restart docker
minikube start --driver=docker --cpus=6 --memory=12g
```

### Verificación posterior

Dentro de `minikube ssh` ya respondía:

```bash
curl -I https://registry-1.docker.io/v2/
```

Con eso los pulls pudieron volver a completarse.

---

## Segundo problema: submodelserver en CrashLoopBackOff

Después de resolverse los pulls, el pod del submodel server seguía fallando.

### Síntoma

```text
umbrella-dataprovider-submodelserver ... CrashLoopBackOff
```

### Observación inicial

El host:

```text
dataprovider-submodelserver.tx.test
```

devoldía primero `503 Service Temporarily Unavailable`.

Eso indicaba que el ingress estaba funcionando, pero el backend no estaba sano.

---

## Diagnóstico del submodelserver

### Eventos observados

* la imagen se había descargado bien
* el contenedor arrancaba
* Kubernetes fallaba las probes:

  * readiness
  * liveness

Con mensajes tipo:

```text
connect: connection refused
```

y después reinicios del contenedor.

### Logs del contenedor

Los logs mostraron que la aplicación Spring Boot **sí arrancaba**, pero tardaba mucho:

* arranque completo en ~87 segundos
* Tomcat levantado en el puerto 8080
* aplicación iniciada correctamente

### Conclusión

La app no estaba rota.

El problema era que Kubernetes empezaba a probarla demasiado pronto y la mataba antes de darle tiempo suficiente para arrancar.

---

## Reintento y estabilización del submodelserver

Se forzó un reintento del pod una vez arreglada la red de Minikube.

Tras ello, el submodel server terminó quedando en:

```text
1/1 Running
```

Y el host:

```bash
curl -I -H "Host: dataprovider-submodelserver.tx.test" http://127.0.0.1
```

pasó de `503` a:

```text
HTTP/1.1 404
```

### Interpretación

Ese `404` significó que:

* el backend ya estaba vivo
* el ingress llegaba correctamente
* la raíz `/` simplemente no ofrecía un recurso

Es decir: infraestructura sana.

---

## Tercer problema: Data Consumer 1 no quedaba listo

Más adelante, el provider estaba ya bastante bien, pero el consumer 1 seguía con pods en:

* `0/1 Running`

Concretamente:

* `umbrella-dataconsumer-1-edc-controlplane`
* `umbrella-dataconsumer-1-edc-dataplane`

---

## Diagnóstico del controlplane del consumer

### Eventos observados

Primero sufrió problemas de `ImagePullBackOff`, pero eso quedó resuelto al arreglar la conectividad del nodo Minikube.

Después, el patrón pasó a ser otro:

* el contenedor arrancaba
* la readiness probe fallaba
* la liveness probe había fallado antes en arranques previos

La pista más importante fue esta:

```text
Readiness probe failed: HTTP probe failed with statuscode: 404
```

### Interpretación

El proceso estaba vivo, pero la probe configurada en Kubernetes no coincidía con un endpoint “listo” tal y como respondía realmente el contenedor.

### Solución

Se retiraron/ajustaron temporalmente las probes del deployment del controlplane.

Tras ello, el pod pasó a:

```text
1/1 Running
```

---

## Diagnóstico del dataplane del consumer

El dataplane mostró un patrón muy similar:

* problemas iniciales de pull por la red de Minikube
* después arrancaba
* luego las probes fallaban con:

  * `connection refused`
  * y más tarde `503`

Finalmente, también se trató como un problema de probes demasiado agresivas o mal alineadas con el comportamiento real del contenedor.

### Solución

Se aplicó el mismo enfoque que con el controlplane:

* relajar o retirar temporalmente las probes
* dejar que el servicio quedara estable

### Resultado

El dataplane terminó también en:

```text
1/1 Running
```

Y su host respondió correctamente por ingress.

---

## Validaciones realizadas

### Estado de pods

Se verificó que los componentes clave de Data Exchange quedaran en `1/1 Running`, incluyendo:

* `umbrella-dataprovider-dtr`
* `umbrella-dataprovider-edc-controlplane`
* `umbrella-dataprovider-edc-dataplane`
* `umbrella-dataprovider-submodelserver`
* `umbrella-dataconsumer-1-edc-controlplane`
* `umbrella-dataconsumer-1-edc-dataplane`

Y también sus bases de datos y Vault.

---

## Verificación de ingress de Data Exchange

Se comprobó que existían ingress para:

* `dataconsumer-1-controlplane.tx.test`
* `dataconsumer-1-dataplane.tx.test`
* `dataprovider-dtr.tx.test`
* `dataprovider-controlplane.tx.test`
* `dataprovider-dataplane.tx.test`
* `dataprovider-submodelserver.tx.test`

---

## Validación HTTP de endpoints

Desde el VPS, pasando por Nginx y manteniendo el `Host`, se hicieron pruebas tipo:

```bash
curl -I -H "Host: dataconsumer-1-controlplane.tx.test" http://127.0.0.1
curl -I -H "Host: dataconsumer-1-dataplane.tx.test" http://127.0.0.1
curl -I -H "Host: dataprovider-controlplane.tx.test" http://127.0.0.1
curl -I -H "Host: dataprovider-dataplane.tx.test" http://127.0.0.1
curl -I -H "Host: dataprovider-submodelserver.tx.test" http://127.0.0.1
curl -I -H "Host: dataprovider-dtr.tx.test" http://127.0.0.1
```

En varios casos la respuesta fue `404`, que se consideró válida como comprobación de que:

* el host estaba bien publicado
* Nginx funcionaba
* el ingress funcionaba
* el backend respondía

Un `404` en `/` no implicó problema de infraestructura, solo ausencia de recurso en esa ruta concreta.

---

## Estado final alcanzado

Al final de esta fase quedó operativa una instalación combinada de:

### Portal

* `portal`
* `portal-backend`
* `centralidp`
* `sharedidp`

### Data Exchange básico

* `dataconsumerOne`
* `tx-data-provider`
* `identity-and-trust-bundle`
* `submodelserver`
* `dtr`
* `vault`
* bases de datos asociadas

Todo ello publicado mediante:

* `Minikube ingress`
* `Nginx` en el VPS
* resolución de `*.tx.test` desde Windows hacia la IP pública del VPS

---

## Comandos útiles usados en esta fase

### Upgrade con values combinado

```bash
helm upgrade -f my-values-portal-data-exchange.yaml umbrella . -n umbrella
```

### Revisar pods

```bash
kubectl get pods -n umbrella
kubectl get pods -n umbrella -w
```

### Revisar ingress

```bash
kubectl get ingress -n umbrella
kubectl describe ingress -n umbrella
```

### Revisar eventos de un pod

```bash
kubectl describe pod -n umbrella NOMBRE_DEL_POD
```

### Revisar logs

```bash
kubectl logs -n umbrella NOMBRE_DEL_POD
kubectl logs -n umbrella NOMBRE_DEL_POD --previous
kubectl logs -n umbrella NOMBRE_DEL_POD --all-containers=true
```

### Probar conectividad de Docker Hub

```bash
curl -I https://registry-1.docker.io/v2/
docker pull busybox:1.36
minikube ssh
curl -I https://registry-1.docker.io/v2/
```

### Reinicio limpio de Minikube cuando perdió salida

```bash
minikube stop
sudo systemctl restart docker
minikube start --driver=docker --cpus=6 --memory=12g
```

### Probar hosts a través de Nginx local

```bash
curl -I -H "Host: portal.tx.test" http://127.0.0.1
curl -I -H "Host: dataprovider-submodelserver.tx.test" http://127.0.0.1
curl -I -H "Host: dataconsumer-1-controlplane.tx.test" http://127.0.0.1
```

---

## Lecciones aprendidas

### 1. `helm upgrade` no “suma subsets” automáticamente

Cambiar de un values file a otro en la misma release sustituye la configuración efectiva de la release.

Para combinar Portal y Data Exchange hay que usar un **fichero propio**.

### 2. Nginx no causó el problema de pulls

El fallo de `ImagePullBackOff` se debía a la conectividad del nodo Minikube hacia Docker Hub, no al reverse proxy del VPS.

### 3. Un `404` puede ser buena señal

En este tipo de servicios API, un `404` en `/` puede significar simplemente que el backend está vivo pero esa ruta no expone recurso.

### 4. Las probes pueden ser el verdadero problema

Varios componentes no estaban realmente “rotos”; simplemente sus probes estaban matándolos o manteniéndolos en `0/1` aunque el servicio ya respondiera.

---

## Ficheros recomendados para guardar

Además del values combinado, conviene conservar:

### Values efectivos de la release

```bash
helm get values umbrella -n umbrella -a > umbrella-effective-values.yaml
```

### Estado de servicios e ingress

```bash
kubectl get pods -n umbrella > pods-umbrella.txt
kubectl get svc -n umbrella > svc-umbrella.txt
kubectl get ingress -n umbrella > ingress-umbrella.txt
```

---

## Estado funcional resumido

A la finalización de esta fase, el entorno quedó con:

* **Portal funcional**
* **IAM funcional**
* **Data Provider funcional**
* **Data Consumer 1 funcional**
* **Submodel server funcional**
* publicación correcta de `*.tx.test` desde Windows hacia el VPS mediante Nginx

Lo que queda ya como siguiente paso no es “levantarlo”, sino **probar flujos reales de Data Exchange**.
