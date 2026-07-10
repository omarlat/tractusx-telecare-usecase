// Datos reales de la última generación, usados por showProviderStep y showConsumerStep
let lastRawEvents = null
let lastSemanticEvents = null
let lastFhirEvents = null
let lastDerivedAssets = null

function getEventIcon(eventType) {

    const icons = {
        oxygen_saturation: "🩺",
        fall_detected: "🚨",
        technical_alarm: "⚙",
        functional_status_change: "🚶"
    }

    return icons[eventType] || "📄"
}

function getRiskLabel(riskLevel) {

    const labels = {
        high: "🔴 HIGH RISK",
        medium: "🟠 MEDIUM RISK",
        low: "🟢 LOW RISK"
    }

    return labels[riskLevel] || riskLevel
}

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

function getEventDescription(eventType) {

    const descriptions = {

        oxygen_saturation:
            "🩺 Oxygen saturation below threshold",

        fall_detected:
            "🚨 Fall detected at home",

        technical_alarm:
            "⚙ Technical alarm reported by device",

        functional_status_change:
            "🚶 Functional status change reported"

    }

    return descriptions[eventType] || eventType
}

function toggleAspectCatalog() {

    const content = document.getElementById("aspect-catalog-content")
    const arrow = document.getElementById("catalog-arrow")
    const isHidden = content.classList.contains("catalog-hidden")

    content.classList.toggle("catalog-hidden")
    arrow.textContent = isHidden ? "▼" : "▶"
}

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

async function loadAspectCatalog() {

    const response = await fetch(
        "http://localhost:8001/aspects"
    )

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

function showDataspaceStep(step) {

    document
        .querySelectorAll(".edc")
        .forEach(el => el.classList.remove("active"))

    document
        .getElementById(step + "-step")
        .classList.add("active")

    const details = {

        asset: `
            <h3>EDC Publication</h3>

            <p>
                <strong>Purpose:</strong>
                Register the Telecare FHIR Asset.
            </p>

            <p>
                <strong>Asset:</strong>
                telecare-fhir-asset
            </p>

            <p>
                <strong>Content Type:</strong>
                application/json
            </p>
        `,

        catalog: `
            <h3>Catalog Discovery</h3>

            <p>
                <strong>Purpose:</strong>
                Discover assets available from the provider.
            </p>

            <p>
                <strong>Endpoint:</strong>
                POST /catalog/request
            </p>

            <p>
                <strong>Result:</strong>
                Telecare FHIR Asset discovered.
            </p>
        `,

        contract: `
            <h3>Contract Negotiation</h3>

            <p>
                <strong>Purpose:</strong>
                Establish a data sharing agreement.
            </p>

            <p>
                <strong>Endpoint:</strong>
                POST /contractnegotiations
            </p>

            <p>
                <strong>Result:</strong>
                Contract agreement created.
            </p>
        `,

        transfer: `
            <h3>Data Transfer</h3>

            <p>
                <strong>Purpose:</strong>
                Transfer the asset to the consumer.
            </p>

            <p>
                <strong>Endpoint:</strong>
                POST /transferprocesses
            </p>

            <p>
                <strong>Result:</strong>
                Asset successfully consumed.
            </p>
        `
    }

    document
        .getElementById("dataspace-details")
        .innerHTML = details[step]
}

async function generateScenario() {

    const overlay = document.getElementById("loading-overlay")
    overlay.classList.add("visible")

    try {

    const scenario = document.getElementById("scenario-select").value

    const generateResponse = await fetch(
        `http://localhost:8000/generate/${scenario}`,
        { method: "POST" }
    )

    lastRawEvents = await generateResponse.json()

    const response = await fetch(
        "http://localhost:8002/derived-assets"
    )

    lastDerivedAssets = await response.json()

    const data = lastDerivedAssets

    const asset0 = data[0]

    document.getElementById("analytics-summary").innerHTML = `
        <p>
            <strong>Caso:</strong> ${asset0.case_id}
        </p>
        <p>
            <strong>Eventos procesados:</strong> ${lastRawEvents.length}
        </p>
        <p>
            <strong>Nivel de riesgo:</strong>
            <span class="risk-${asset0.risk_level}">
                ${getRiskLabel(asset0.risk_level)}
            </span>
        </p>
        <p>
            <strong>Prioridad:</strong> ${asset0.priority}
        </p>
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

                <p>
                    <strong>Priority:</strong>
                    ${asset.priority}
                </p>

                <p>
                    ${asset.summary}
                </p>

                <p>
                    <strong>Generated at:</strong>
                    ${asset.generated_at}
                </p>

                <p>
                    <strong>Source:</strong>
                    ${asset.source}
                </p>
            </div>
        `
    })

    document.getElementById("results").innerHTML = html

    const semanticResponse = await fetch(
        "http://localhost:8001/semantic-events"
    )

    lastSemanticEvents = await semanticResponse.json()

    const semanticData = lastSemanticEvents

    const caseId = semanticData[0].case_id

    const asset = data[0]

    let overviewHtml = `
        <div class="case-card case-${asset.risk_level}">

            <h2>Case ${caseId}</h2>
            <p>
                Synthetic teleassistance monitoring case.
            </p>

            <ul>
    `

    semanticData.forEach(event => {

        overviewHtml += `
            <li>
                ${getEventDescription(
                    event.semantic_type
                )}
            </li>
        `
    })

    overviewHtml += `
            </ul>

            <h4>Risk Assessment</h4>

            <p>
                ${getRiskLabel(asset.risk_level)}
            </p>

            <p>
                <strong>Priority:</strong>
                ${asset.priority}
            </p>
        </div>
    `
    document.getElementById(
        "case-overview"
    ).innerHTML = overviewHtml

    let semanticHtml = ""

    semanticData.forEach(event => {

        semanticHtml += `
        <div class="card">

            <h3>
                ${getEventIcon(event.semantic_type)}
                ${event.semantic_type}
            </h3>

            <p>
                ${getAspectLabel(event.aspect.aspectName)}
            </p>

            <p class="${event.validation_status}">
                ${
                    event.validation_status === "valid"
                        ? "✅ VALID"
                        : "❌ INVALID"
                }
            </p>

            ${
                event.validation_errors.length
                    ? `<ul class="validation-errors">${
                        event.validation_errors.map(error => `<li>${error}</li>`).join("")
                    }</ul>`
                    : ""
            }

        </div>
        `
    })

    document.getElementById("semantic-events").innerHTML = semanticHtml

    const fhirResponse = await fetch(

        "http://localhost:8001/fhir-events"
    )

    lastFhirEvents = await fhirResponse.json()
    
    document.getElementById("summary").innerHTML = `
        <h3>
            ${semanticData.length} semantic events processed
        </h3>
    `

    showProviderStep("synthetic")
    showConsumerStep("consume")

    } finally {
        overlay.classList.remove("visible")
    }
}

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
            <p>
                <strong>Purpose:</strong>
                Receive the Telecare FHIR Asset from the dataspace.
            </p>
            <p>
                <strong>Input:</strong>
                HL7 FHIR Observation resources.
            </p>
            <p>
                <strong>Result:</strong>
                Asset available for analysis.
            </p>
        `,

        analytics: asset ? `
            <h3>Analytics Processing</h3>
            <p>
                <strong>Caso analizado:</strong> ${asset.case_id}
            </p>
            <p>
                <strong>Eventos procesados:</strong> ${lastRawEvents ? lastRawEvents.length : "—"}
            </p>
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

function showProviderStep(step) {

    document
        .querySelectorAll(".provider-step")
        .forEach(el => el.classList.remove("active"))

    document
        .getElementById(step + "-step")
        .classList.add("active")

    let content

    if (step === "synthetic" && lastRawEvents) {
        content = `<pre>${JSON.stringify(lastRawEvents[0], null, 2)}</pre>`
    } else if (step === "semantic" && lastSemanticEvents) {
        content = `<pre>${JSON.stringify(lastSemanticEvents[0], null, 2)}</pre>`
    } else if (step === "fhir" && lastFhirEvents) {
        content = `<pre>${JSON.stringify(lastFhirEvents[0], null, 2)}</pre>`
    } else {
        content = `<p style="color:#999">Genera un escenario para ver los datos.</p>`
    }

    document
        .getElementById("provider-details")
        .innerHTML = content
}

showDataspaceStep("asset")
showConsumerStep("consume")
showProviderStep("synthetic")
loadAspectCatalog()