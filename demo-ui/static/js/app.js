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

async function loadAspectCatalog() {

    const response = await fetch(
        "http://localhost:8001/aspects"
    )

    const aspects = await response.json()

    let html = ""

    aspects.forEach(aspect => {

        html += `
            <div class="card">
                <h3>${aspect.aspectName}</h3>

                <p>
                    <strong>Category:</strong>
                    ${aspect.category}
                </p>

                <p>
                    ${aspect.description}
                </p>

                <p>
                    <strong>Semantic types:</strong>
                    ${
                        aspect.semanticTypes.length
                            ? aspect.semanticTypes.join(", ")
                            : "—"
                    }
                </p>
            </div>
        `
    })

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

    await fetch(
        "http://localhost:8000/generate/mixed-risk",
        {
            method: "POST"
        }
    )

    const response = await fetch(
        "http://localhost:8002/derived-assets"
    )

    const data = await response.json()

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

    const semanticData = await semanticResponse.json()

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

    const fhirData = await fhirResponse.json()

    let fhirHtml = ""

    fhirData.forEach(resource => {

        const value = resource.valueQuantity
            ? `${resource.valueQuantity.value} ${resource.valueQuantity.unit || ""}`.trim()
            : resource.valueCodeableConcept.text

        fhirHtml += `
            <div class="card">

                <h3>${resource.code.text}</h3>

                <p>
                    <strong>Type:</strong>
                    ${resource.resourceType}
                </p>

                <p>
                    <strong>Status:</strong>
                    ${resource.status}
                </p>

                <p>
                    <strong>Category:</strong>
                    ${resource.category[0].text}
                </p>

                <p>
                    <strong>Effective:</strong>
                    ${resource.effectiveDateTime}
                </p>

                <p>
                    <strong>Value:</strong>
                    ${value}
                </p>

                <p>
                    <strong>Interpretation:</strong>
                    ${resource.interpretation[0].text}
                </p>

                <p>
                    <strong>Device:</strong>
                    ${resource.device.display}
                </p>

                <p>
                    <strong>Note:</strong>
                    ${resource.note[0].text}
                </p>

            </div>
        `
    })

    document.getElementById("fhir-events").innerHTML = fhirHtml
    
    document.getElementById("summary").innerHTML = `
        <h3>
            ${semanticData.length} semantic events processed
        </h3>
    `
}

function showConsumerStep(step) {

    document
        .querySelectorAll(".consumer-step")
        .forEach(el => el.classList.remove("active"))

    document
        .getElementById(step + "-step")
        .classList.add("active")

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

        analytics: `
            <h3>Analytics Processing</h3>

            <p>
                <strong>Purpose:</strong>
                Evaluate teleassistance events.
            </p>

            <p>
                <strong>Rules applied:</strong>
            </p>

            <ul>
                <li>Low oxygen saturation</li>
                <li>Fall detection</li>
                <li>Technical alarm evaluation</li>
            </ul>

            <p>
                <strong>Output:</strong>
                HIGH risk level and priority 1.
            </p>
        `,

        derived: `
            <h3>Derived Asset Generation</h3>

            <p>
                <strong>Generated asset:</strong>
            </p>

            <pre>
{
  "caseId": "USR-0099",
  "riskLevel": "HIGH",
  "priority": 1,
  "summary": "Preventive intervention recommended"
}
            </pre>
        `
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

    const details = {

        synthetic: `
<pre>{
  "case_id": "USR-0099",
  "semantic_type": "oxygen_saturation",
  "observed_value": 89,
  "unit": "%",
  "severity": "high"
}</pre>
        `,

        semantic: `
<pre>{
  "case_id": "USR-0099",
  "semantic_type": "oxygen_saturation",
  "observed_value": 89,
  "unit": "%",
  "severity": "high",
  "aspect": {
    "aspectName": "VitalSignsAspect"
  },
  "semantic_context": "Tractus-X Telecare Demo",
  "semantic_version": "1.0.0",
  "validation_status": "valid"
}</pre>
        `,

        fhir: `
<pre>{
  "resourceType": "Observation",
  "status": "final",
  "code": {
    "text": "oxygen_saturation"
  },
  "category": [
    { "text": "physiological_observation" }
  ],
  "subject": {
    "reference": "USR-0099"
  },
  "effectiveDateTime": "2026-06-15T08:42:00+00:00",
  "valueQuantity": {
    "value": 89,
    "unit": "%"
  },
  "interpretation": [
    { "text": "high" }
  ],
  "device": {
    "display": "home_oximeter"
  },
  "note": [
    { "text": "Low oxygen saturation detected" }
  ]
}</pre>
        `
    }

    document
        .getElementById("provider-details")
        .innerHTML = details[step]
}

showDataspaceStep("asset")

showConsumerStep("consume")

showProviderStep("synthetic")

loadAspectCatalog()