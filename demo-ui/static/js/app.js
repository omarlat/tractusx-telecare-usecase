// Estado de la última generación: compartido entre showProviderStep,
// showConsumerStep y generateScenario para no repetir llamadas a la API
let lastRawEvents = null
let lastSemanticEvents = null
let lastFhirEvents = null
let lastDerivedAssets = null

// lastRawEvents, lastSemanticEvents y lastFhirEvents son arrays paralelos
// (mismo evento en cada etapa de transformación); providerEventIndex es
// la posición que se muestra en las tarjetas del Provider Organization,
// navegable con las flechas para no limitarse siempre al primer evento
let providerEventIndex = 0
let currentProviderStep = "synthetic"

// Última ejecución del intercambio real vía dataspace-connector (EDC):
// se actualiza en vivo durante el polling y se conserva para poder
// inspeccionar cada paso después de que termine
let lastExchangeRun = null

// Ejecución del intercambio EDC en curso: se crea al generar el
// escenario pero sus pasos se disparan uno a uno con cada click
let currentRunId = null


// Nombre legible de cada paso real del dataspace-connector (Provide_Data
// + Consume_Data), usado tanto en el listado detallado de #dataspace-status
// como al inspeccionar un paso concreto
const STEP_LABELS = {
    publish_data: "Publish Case Data",
    ensure_asset: "Register Asset",
    ensure_access_policy: "Create Access Policy",
    ensure_usage_policy: "Create Usage Policy",
    ensure_contract_definition: "Create Contract Definition",
    request_catalog: "Discover Catalog",
    negotiate_contract: "Negotiate Contract",
    wait_for_edr: "Await Contract Agreement",
    get_authorization: "Get Transfer Authorization",
    fetch_data: "Fetch Data",
}

// A qué tarjeta del pipeline EDC (los 4 pasos conceptuales ya existentes
// en el HTML) pertenece cada paso real, para resaltarla mientras avanza
const STEP_GROUP = {
    publish_data: "asset",
    ensure_asset: "asset",
    ensure_access_policy: "asset",
    ensure_usage_policy: "asset",
    ensure_contract_definition: "asset",
    request_catalog: "catalog",
    negotiate_contract: "contract",
    wait_for_edr: "contract",
    get_authorization: "transfer",
    fetch_data: "transfer",
}


// Etiqueta con color de semáforo para el nivel de riesgo.
// El icono (punto de color) se aplica vía CSS sobre la clase risk-${riskLevel},
// no aquí: este valor es solo texto.
function getRiskLabel(riskLevel) {

    const labels = {
        high: "HIGH RISK",
        medium: "MEDIUM RISK",
        low: "LOW RISK"
    }

    return labels[riskLevel] || riskLevel
}


// Nombre legible del aspecto funcional resuelto por el semantic-adapter
function getAspectLabel(aspectName) {

    const labels = {
        VitalSignsAspect: "Vital Signs",
        TeleassistanceAlertAspect: "Teleassistance Alert",
        TechnicalEventAspect: "Technical Event",
        FunctionalStatusAspect: "Functional Status",
        AnalyticalResultAspect: "Analytical Result",
        CommonCaseAspect: "Common Case",
        UnmappedEventAspect: "Unmapped Event"
    }

    return labels[aspectName] || aspectName
}


// Descripción breve para el resumen del caso en el Case Overview.
// El icono por tipo de evento se aplica vía CSS (ver .event-icon en style.css)
// a partir del atributo data-icon; este valor es solo texto.
function getEventDescription(eventType) {

    const descriptions = {
        oxygen_saturation:      "Oxygen saturation below threshold",
        fall_detected:          "Fall detected at home",
        technical_alarm:        "Technical alarm reported by device",
        functional_status_change: "Functional status change reported"
    }

    return descriptions[eventType] || eventType
}


// Muestra u oculta el bloque Aspect Catalog; por defecto está colapsado
// para no ocupar espacio en el flujo principal de la demo
function toggleAspectCatalog() {

    const content = document.getElementById("aspect-catalog-content")
    const arrow = document.getElementById("catalog-arrow")

    content.classList.toggle("catalog-hidden")
    arrow.classList.toggle("catalog-arrow-open")
}


// Muestra u oculta el detalle real (request/response) del paso EDC
// seleccionado; colapsado por defecto para no tapar el flujo (botón +
// tarjetas) cuando el JSON de la respuesta es grande
function toggleDataspaceDetails(forceOpen) {

    const content = document.getElementById("dataspace-details-content")
    const arrow = document.getElementById("dataspace-details-arrow")

    const shouldOpen = forceOpen !== undefined
        ? forceOpen
        : content.classList.contains("catalog-hidden")

    content.classList.toggle("catalog-hidden", !shouldOpen)
    arrow.classList.toggle("catalog-arrow-open", shouldOpen)
}


// Genera el HTML de la tabla de propiedades de un aspecto.
// Distingue tres tipos de regla: con unidad/rango (signos vitales),
// cualitativo (sin valor numérico) y descriptivo (metadatos del caso)
function renderAspectProperties(properties) {

    if (!properties || Object.keys(properties).length === 0) {
        return ""
    }

    let rows = ""

    for (const [key, rules] of Object.entries(properties)) {

        let meta = ""

        if (rules.unit !== undefined) {
            meta += `${rules.unit}`
            if (rules.min !== undefined && rules.max !== undefined) {
                meta += ` &nbsp;[${rules.min} – ${rules.max}]`
            }
        } else if (rules.expectsValue === false) {
            meta = "cualitativo"
        } else if (rules.description) {
            meta = rules.description
        }

        rows += `
            <div class="aspect-property-row">
                <span class="prop-name">${key}</span>
                <span class="prop-meta">${meta}</span>
            </div>
        `
    }

    return `<div class="aspect-properties">${rows}</div>`
}


// Carga el catálogo de aspectos desde el semantic-adapter y lo renderiza
// en un grid de tarjetas, incluyendo las propiedades de cada aspecto
async function loadAspectCatalog() {

    const response = await fetch(`${SERVICE_URLS.semanticAdapter}/aspects`)

    const aspects = await response.json()

    let html = `<div class="catalog-grid">`

    aspects.forEach(aspect => {

        html += `
            <div class="card">
                <h3>${aspect.aspectName}</h3>

                <p>
                    <strong>Categoría:</strong> ${aspect.category}
                </p>

                <p>${aspect.description}</p>

                <p>
                    <strong>Tipos semánticos:</strong>
                    ${aspect.semanticTypes.length ? aspect.semanticTypes.join(", ") : "—"}
                </p>

                ${renderAspectProperties(aspect.properties)}
            </div>
        `
    })

    html += `</div>`

    document.getElementById("aspect-catalog").innerHTML = html
}


// Descripción conceptual de cada fase del pipeline EDC, usada como
// fallback antes de que exista una ejecución real que inspeccionar
const STATIC_DATASPACE_DETAILS = {

    asset: `
        <h3>EDC Publication</h3>
        <p><strong>Purpose:</strong> Register the Telecare FHIR Asset.</p>
        <p><strong>Asset:</strong> telecare-fhir-asset</p>
        <p><strong>Content Type:</strong> application/json</p>
    `,

    catalog: `
        <h3>Catalog Discovery</h3>
        <p><strong>Purpose:</strong> Discover assets available from the provider.</p>
        <p><strong>Endpoint:</strong> POST /catalog/request</p>
        <p><strong>Result:</strong> Telecare FHIR Asset discovered.</p>
    `,

    contract: `
        <h3>Contract Negotiation</h3>
        <p><strong>Purpose:</strong> Establish a data sharing agreement.</p>
        <p><strong>Endpoint:</strong> POST /edrs</p>
        <p><strong>Result:</strong> Contract agreement created.</p>
    `,

    transfer: `
        <h3>Data Transfer</h3>
        <p><strong>Purpose:</strong> Transfer the asset to the consumer.</p>
        <p><strong>Endpoint:</strong> GET /edrs/{id}/dataaddress</p>
        <p><strong>Result:</strong> Asset successfully consumed.</p>
    `
}


// Renderiza el detalle (request/response reales, capturados por el
// dataspace-connector) de uno o varios pasos del intercambio
function renderStepDetail(stepNames) {

    if (!lastExchangeRun) {
        return `<p style="color:#999">Genera un escenario para preparar el intercambio con el EDC.</p>`
    }

    let html = ""

    stepNames.forEach(name => {

        const step = lastExchangeRun.steps.find(s => s.step === name)

        if (!step || step.status === "pending") {
            return
        }

        html += `
            <div class="card">
                <h3>${STEP_LABELS[name] || name}</h3>
                <p class="${step.status === "error" ? "invalid" : "valid"}">
                    ${step.status.toUpperCase()}
                </p>
                ${step.request ? `<p><strong>Request</strong></p><pre>${JSON.stringify(step.request, null, 2)}</pre>` : ""}
                ${step.response !== undefined ? `<p><strong>Response</strong></p><pre>${JSON.stringify(step.response, null, 2)}</pre>` : ""}
            </div>
        `
    })

    return html || `<p style="color:#999">Este paso todavía no se ha ejecutado.</p>`
}


// Resalta el paso conceptual EDC activo (uno de los 4 grupos del
// pipeline) y muestra el detalle real de sus pasos si ya hay una
// ejecución en curso o terminada; si no, la descripción conceptual.
// userTriggered=false se usa solo en la inicialización de la página,
// para no desplegar la caja de detalle antes de que el usuario interactúe.
function showDataspaceStep(step, userTriggered = true) {

    document
        .querySelectorAll(".edc")
        .forEach(el => el.classList.remove("active"))

    document
        .getElementById(step + "-step")
        .classList.add("active")

    if (!lastExchangeRun) {
        document.getElementById("dataspace-details").innerHTML = STATIC_DATASPACE_DETAILS[step]
    } else {
        const namesInGroup = Object.keys(STEP_GROUP).filter(name => STEP_GROUP[name] === step)
        document.getElementById("dataspace-details").innerHTML = renderStepDetail(namesInGroup)
    }

    if (userTriggered) {
        toggleDataspaceDetails(true)
    }
}


// Inspecciona un paso concreto del intercambio (una tarjeta de
// #dataspace-status), despliega la caja de detalle y sincroniza el
// resaltado del grupo al que pertenece
function showExchangeStepDetail(stepName) {

    document.getElementById("dataspace-details").innerHTML = renderStepDetail([stepName])
    toggleDataspaceDetails(true)

    document
        .querySelectorAll(".edc")
        .forEach(el => el.classList.remove("active"))

    const group = STEP_GROUP[stepName]

    if (group) {
        document.getElementById(group + "-step").classList.add("active")
    }
}


// Dibuja una tarjeta por cada paso real del intercambio en
// #dataspace-status, con su estado actual. La tarjeta del paso que toca
// ejecutar a continuación es clicable para lanzarlo (igual que el botón
// "Ejecutar siguiente paso"); las ya terminadas son clicables para
// inspeccionar su request/response real
function renderExchangeStatusCards(run) {

    let html = ""

    run.steps.forEach(step => {

        let cssStatus = "pending"
        let icon = "○"
        let onclick = ""

        if (step.status === "created" || step.status === "exists") {
            cssStatus = "completed"
            icon = "✓"
            onclick = `onclick="showExchangeStepDetail('${step.step}')"`
        } else if (step.status === "in_progress") {
            cssStatus = "active"
            icon = "…"
        } else if (step.status === "error") {
            cssStatus = "error"
            icon = "✗"
            onclick = `onclick="showExchangeStepDetail('${step.step}')"`
        } else if (step.step === run.next_step && run.status === "ready") {
            cssStatus = "next"
            icon = "▶"
            onclick = `onclick="advanceExchangeStep()"`
        }

        html += `
            <div class="exchange-card ${cssStatus}" ${onclick}>
                ${icon} ${STEP_LABELS[step.step] || step.step}
            </div>
        `
    })

    document.getElementById("dataspace-status").innerHTML = html
}


// Muestra u oculta el botón "Ejecutar siguiente paso" según el estado
// del intercambio: oculto si aún no hay ejecución, si ya terminó o si
// falló; deshabilitado mientras un paso está en curso.
function updateEdcNextButton(run) {

    const button = document.getElementById("edc-next-button")

    if (!run || run.status === "done" || run.status === "error") {
        button.style.display = "none"
        return
    }

    button.style.display = "inline-block"
    button.disabled = run.status === "running"
    button.innerText = run.status === "running"
        ? `Ejecutando: ${STEP_LABELS[run.steps.find(s => s.status === "in_progress")?.step] || "..."}`
        : `▶ Ejecutar paso: ${STEP_LABELS[run.next_step] || run.next_step}`
}


// Ejecuta el siguiente paso pendiente del intercambio (un click = un
// paso real contra el EDC) y hace polling hasta que ese paso concreto
// termine, para reflejarlo en vivo en la tarjeta correspondiente
async function advanceExchangeStep() {

    if (!currentRunId) {
        return
    }

    await fetch(
        `${SERVICE_URLS.dataspaceConnector}/exchange/${currentRunId}/next`,
        { method: "POST" }
    )

    const deadline = Date.now() + 40000

    while (Date.now() < deadline) {

        const run = await (
            await fetch(`${SERVICE_URLS.dataspaceConnector}/exchange/${currentRunId}`)
        ).json()

        lastExchangeRun = run
        renderExchangeStatusCards(run)
        updateEdcNextButton(run)

        if (run.status !== "running") {

            if (run.status === "error") {
                alert(`El intercambio con el espacio de datos falló en el paso "${run.error}". Revisa los detalles en el bloque Tractus-X Dataspace.`)
            }

            if (run.status === "done") {
                await finishExchangeAndAnalyze(run)
            }

            return
        }

        await new Promise(resolve => setTimeout(resolve, 500))
    }

    alert("Timeout esperando la respuesta del EDC")
}


// Última tarjeta del intercambio (fetch_data) ya terminada: recupera lo
// que Entidad B recibió de verdad vía EDC y dispara el análisis, que
// hasta ahora estaba pendiente
async function finishExchangeAndAnalyze(run) {

    const exchangedData = await (
        await fetch(`${SERVICE_URLS.dataspaceConnector}/exchange/${run.run_id}/data`)
    ).json()

    lastDerivedAssets = await (
        await fetch(`${SERVICE_URLS.analytics}/analyze`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ semantic_events: exchangedData.semantic_events })
        })
    ).json()

    renderConsumerResults(lastDerivedAssets)
    renderCaseOverview(lastSemanticEvents, lastDerivedAssets[0])
    showConsumerStep("consume")
}


// Tarjeta de resumen analítico + tarjetas de activos derivados en la
// columna del consumidor, una vez que Entidad B ha analizado lo recibido
function renderConsumerResults(data) {

    const asset0 = data[0]

    document.getElementById("analytics-summary").innerHTML = `
        <p><strong>Caso:</strong> ${asset0.case_id}</p>
        <p><strong>Eventos procesados:</strong> ${lastRawEvents.length}</p>
        <p>
            <strong>Nivel de riesgo:</strong>
            <span class="risk-${asset0.risk_level}">
                ${getRiskLabel(asset0.risk_level)}
            </span>
        </p>
        <p><strong>Prioridad:</strong> ${asset0.priority}</p>
        <p>${asset0.summary}</p>
    `

    let html = ""

    data.forEach(asset => {

        html += `
            <div class="card ${asset.risk_level}">
                <h3>${asset.case_id}</h3>
                <p>
                    <strong>Risk level:</strong>
                    <span class="risk-${asset.risk_level}">
                        ${getRiskLabel(asset.risk_level)}
                    </span>
                </p>
                <p><strong>Priority:</strong> ${asset.priority}</p>
                <p>${asset.summary}</p>
                <p><strong>Generated at:</strong> ${asset.generated_at}</p>
                <p><strong>Source:</strong> ${asset.source}</p>
            </div>
        `
    })

    document.getElementById("results").innerHTML = html
}


// Case Overview del proveedor: la lista de eventos está disponible en
// cuanto se genera el escenario, pero el bloque "Risk Assessment" es el
// resultado del análisis de Entidad B, así que se muestra como
// pendiente hasta que el intercambio EDC termina y asset ya no es null
function renderCaseOverview(semanticData, asset) {

    const caseId = semanticData[0].case_id

    let html = `
        <div class="case-card ${asset ? "case-" + asset.risk_level : ""}">
            <h2>Case ${caseId}</h2>
            <p>Synthetic teleassistance monitoring case.</p>
            <ul>
    `

    semanticData.forEach(event => {
        html += `<li class="event-icon" data-icon="${event.semantic_type}">${getEventDescription(event.semantic_type)}</li>`
    })

    html += `</ul>`

    if (asset) {
        html += `
            <h4>Risk Assessment</h4>
            <p>${getRiskLabel(asset.risk_level)}</p>
            <p><strong>Priority:</strong> ${asset.priority}</p>
        `
    } else {
        html += `
            <h4>Risk Assessment</h4>
            <p style="color:#999">Pendiente: completa los pasos del espacio de datos para que Entidad B lo analice.</p>
        `
    }

    html += `</div>`

    document.getElementById("case-overview").innerHTML = html
}


// Orquesta la parte de un solo click: generación + adaptación semántica
// (todo del lado de Entidad A, dentro de su propio backend). A partir de
// ahí, el intercambio EDC con Entidad B se prepara (se crea el run) pero
// no se ejecuta: cada uno de sus 10 pasos reales se dispara con un click
// en el botón "Ejecutar siguiente paso" o en la tarjeta correspondiente.
async function generateScenario() {

    const overlay = document.getElementById("loading-overlay")
    overlay.classList.add("visible")
    document.getElementById("loading-text").innerText = "Generando escenario..."

    try {

        const scenario = document.getElementById("scenario-select").value

        // El POST devuelve los eventos generados; el generator limpia el store
        // antes de generar para que la demo muestre siempre un único escenario activo
        const generateResponse = await fetch(
            `${SERVICE_URLS.generator}/generate/${scenario}`,
            { method: "POST" }
        )

        lastRawEvents = await generateResponse.json()
        providerEventIndex = 0

        lastSemanticEvents = await (
            await fetch(`${SERVICE_URLS.semanticAdapter}/semantic-events`)
        ).json()

        lastFhirEvents = await (
            await fetch(`${SERVICE_URLS.semanticAdapter}/fhir-events`)
        ).json()

        // Todavía no hay análisis: Risk Assessment se muestra como pendiente
        // hasta que Entidad B reciba el caso a través del EDC
        lastDerivedAssets = null

        renderCaseOverview(lastSemanticEvents, null)

        // Semantic Events Summary: una tarjeta por evento con su aspecto y estado de validación
        let semanticHtml = ""

        lastSemanticEvents.forEach(event => {

            semanticHtml += `
                <div class="card">
                    <h3 class="event-icon" data-icon="${event.semantic_type}">${event.semantic_type}</h3>
                    <p>${getAspectLabel(event.aspect.aspectName)}</p>
                    <p class="${event.validation_status}">
                        ${event.validation_status === "valid" ? "VALID" : "INVALID"}
                    </p>
                    ${
                        event.validation_errors.length
                            ? `<ul class="validation-errors">${
                                event.validation_errors.map(e => `<li>${e}</li>`).join("")
                            }</ul>`
                            : ""
                    }
                </div>
            `
        })

        document.getElementById("semantic-events").innerHTML = semanticHtml

        document.getElementById("summary").innerHTML = `
            <h3>${lastSemanticEvents.length} semantic events processed</h3>
        `

        document.getElementById("analytics-summary").innerHTML = `
            <p style="color:#999">Ejecuta los pasos del espacio de datos para ver el análisis de Entidad B.</p>
        `
        document.getElementById("results").innerHTML = ""

        // Prepara el intercambio EDC (reúne el payload a publicar) sin
        // ejecutar todavía ningún paso real
        const runResponse = await fetch(
            `${SERVICE_URLS.dataspaceConnector}/exchange/run`,
            { method: "POST" }
        )

        const { run_id } = await runResponse.json()
        currentRunId = run_id

        lastExchangeRun = await (
            await fetch(`${SERVICE_URLS.dataspaceConnector}/exchange/${run_id}`)
        ).json()

        renderExchangeStatusCards(lastExchangeRun)
        updateEdcNextButton(lastExchangeRun)

        // Volver al primer paso de cada pipeline para reflejar los nuevos datos
        showProviderStep("synthetic")
        showConsumerStep("consume")

    } finally {
        overlay.classList.remove("visible")
    }
}


// Resalta el paso activo del pipeline del consumidor y muestra su detalle.
// Los pasos "analytics" y "derived" usan datos reales de lastDerivedAssets
// cuando están disponibles; antes de generar muestran un mensaje de espera.
function showConsumerStep(step) {

    document
        .querySelectorAll(".consumer-step")
        .forEach(el => el.classList.remove("active"))

    document
        .getElementById(step + "-step")
        .classList.add("active")

    const asset = lastDerivedAssets ? lastDerivedAssets[0] : null

    const details = {

        consume: `
            <h3>Asset Consumption</h3>
            <p><strong>Purpose:</strong> Receive the Telecare FHIR Asset from the dataspace.</p>
            <p><strong>Input:</strong> HL7 FHIR Observation resources.</p>
            <p><strong>Result:</strong> Asset available for analysis.</p>
        `,

        analytics: asset ? `
            <h3>Analytics Processing</h3>
            <p><strong>Caso analizado:</strong> ${asset.case_id}</p>
            <p><strong>Eventos procesados:</strong> ${lastRawEvents ? lastRawEvents.length : "—"}</p>
            <p>
                <strong>Resultado:</strong>
                <span class="risk-${asset.risk_level}">
                    ${getRiskLabel(asset.risk_level)}
                </span>
                — Prioridad ${asset.priority}
            </p>
            <p>${asset.summary}</p>
        ` : `<p style="color:#999">Genera un escenario para ver los datos.</p>`,

        derived: asset ? `
            <h3>Derived Asset Generation</h3>
            <p><strong>Activo derivado generado:</strong></p>
            <pre>${JSON.stringify(asset, null, 2)}</pre>
        ` : `<p style="color:#999">Genera un escenario para ver los datos.</p>`
    }

    document
        .getElementById("consumer-details")
        .innerHTML = details[step]
}


// Array correspondiente a cada paso del pipeline del proveedor; los tres
// son paralelos (misma posición = mismo evento en distinta etapa)
function providerEventsFor(step) {

    if (step === "synthetic") return lastRawEvents
    if (step === "semantic") return lastSemanticEvents
    if (step === "fhir") return lastFhirEvents

    return null
}


// Resalta el paso activo del pipeline del proveedor y muestra el evento
// en providerEventIndex de esa capa de transformación, con navegación
// para recorrer todo el lote (no solo el primero)
function showProviderStep(step) {

    currentProviderStep = step

    document
        .querySelectorAll(".provider-step")
        .forEach(el => el.classList.remove("active"))

    document
        .getElementById(step + "-step")
        .classList.add("active")

    const events = providerEventsFor(step)

    let content

    if (events && events.length) {

        const total = events.length
        const index = Math.min(providerEventIndex, total - 1)

        content = `
            <div class="event-nav">
                <button onclick="prevProviderEvent()" ${index === 0 ? "disabled" : ""}>◀</button>
                <span>Evento ${index + 1} de ${total}</span>
                <button onclick="nextProviderEvent()" ${index === total - 1 ? "disabled" : ""}>▶</button>
            </div>
            <pre>${JSON.stringify(events[index], null, 2)}</pre>
        `

    } else {
        content = `<p style="color:#999">Genera un escenario para ver los datos.</p>`
    }

    document
        .getElementById("provider-details")
        .innerHTML = content
}


// Navega al evento anterior/siguiente del lote, dentro del paso del
// proveedor que esté activo en ese momento
function prevProviderEvent() {

    if (providerEventIndex > 0) {
        providerEventIndex -= 1
        showProviderStep(currentProviderStep)
    }
}


function nextProviderEvent() {

    const events = providerEventsFor(currentProviderStep)

    if (events && providerEventIndex < events.length - 1) {
        providerEventIndex += 1
        showProviderStep(currentProviderStep)
    }
}


// Inicialización: selecciona el primer paso de cada pipeline y carga el catálogo
showDataspaceStep("asset", false)
showConsumerStep("consume")
showProviderStep("synthetic")
loadAspectCatalog()
