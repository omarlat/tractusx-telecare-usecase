function getEventIcon(eventType) {

    const icons = {
        oxygen_saturation: "🩺",
        fall_detected: "🚨",
        technical_alarm: "⚙"
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

        CommonCaseAspect: "Generic Event"

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
            "⚙ Technical alarm reported by device"

    }

    return descriptions[eventType] || eventType
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