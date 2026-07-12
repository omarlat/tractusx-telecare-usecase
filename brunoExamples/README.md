# Colección Bruno: flujo EDC manual

Colección de [Bruno](https://www.usebruno.com/) (cliente de peticiones HTTP, alternativa a Postman) usada para explorar y probar a mano, contra el Tractus-X Umbrella real, el mismo flujo EDC de 10 pasos que automatiza `dataspace-connector` (ver [DEV.md](../DEV.md)). Sirvió como base para implementar `provider_client.py` y `consumer_client.py`.

Para la visión general del proyecto ver el [README](../README.md) principal.

## Cómo usarla

1. Instalar [Bruno](https://www.usebruno.com/) (aplicación de escritorio).
2. "Open Collection" y seleccionar la carpeta `brunoExamples/`.
3. Las variables de conexión (URLs, BPN, API keys, DIDs) están en `collection.bru` (`vars:pre-request`) y ya apuntan al Umbrella desplegado — mismos valores por defecto que `dataspace-connector/config.py`.
4. Ejecutar las peticiones en orden dentro de cada carpeta (`seq` en cada `.bru`).

## Carpetas

### `01-Provide_Data` — Entidad A (provider)

Publica un dato en el espacio de datos: crea el contenido en el submodel server, crea el asset que lo referencia, la política de acceso y de uso, y la contract definition que las une. Equivale a `POST /provider/publish` en `dataspace-connector`.

### `02-Consume_Data` — Entidad B (consumer)

Consume ese dato desde el otro participante: consulta el catálogo de contratos ofrecidos, negocia y obtiene un EDR (Endpoint Data Reference), y usa ese EDR para pedir los datos reales. Equivale a `POST /consumer/fetch` en `dataspace-connector`.
