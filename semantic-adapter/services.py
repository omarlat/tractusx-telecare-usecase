import requests
import json
from pathlib import Path

from pydantic import ValidationError

from models import (
    FunctionalEvent,
    SemanticEvent
)


GENERATOR_URL = "http://localhost:8000/events"

BASE_PATH = Path(__file__).parent

ASPECT_FILES = [
    "common-case.aspect.json",
    "vital-signs.aspect.json",
    "teleassistance-alert.aspect.json",
    "technical-event.aspect.json",
    "functional-status.aspect.json",
    "analytical-result.aspect.json"
]

FALLBACK_ASPECT = {
    "aspectName": "UnmappedEventAspect",
    "semanticTypes": [],
    "category": "generic",
    "description": "Fallback aspect for semantic types not mapped to any known aspect model"
}


def load_aspect(file_name):

    aspect_path = (
        BASE_PATH
        / "aspects"
        / file_name
    )

    with open(aspect_path, "r", encoding="utf-8") as file:

        return json.load(file)


ASPECT_REGISTRY = [load_aspect(file_name) for file_name in ASPECT_FILES]

COMMON_CASE_ASPECT = next(
    aspect for aspect in ASPECT_REGISTRY
    if aspect["aspectName"] == "CommonCaseAspect"
)


def load_vital_signs_aspect():

    aspect_path = (
        BASE_PATH
        / "aspects"
        / "vital-signs.aspect.json"
    )

    with open(aspect_path, "r", encoding="utf-8") as file:

        return json.load(file)


def resolve_aspect(semantic_type: str):

    for aspect in ASPECT_REGISTRY:

        if semantic_type in aspect["semanticTypes"]:

            return aspect, False

    return FALLBACK_ASPECT, True


def list_aspects():

    return ASPECT_REGISTRY + [FALLBACK_ASPECT]


def validate_structure(raw_event: dict) -> list[str]:

    try:

        FunctionalEvent(**raw_event)

        return []

    except ValidationError as exc:

        errors = []

        for error in exc.errors():

            field = ".".join(str(part) for part in error["loc"])

            errors.append(
                f"structural: {field} - {error['msg']}"
            )

        return errors


def validate_semantics(functional_event, aspect, is_fallback) -> list[str]:

    if is_fallback:

        return [
            f"semantic: unmapped semantic_type '{functional_event.semantic_type}'"
        ]

    errors = []

    if functional_event.category != aspect["category"]:

        errors.append(
            f"semantic: category '{functional_event.category}' does not match "
            f"expected category '{aspect['category']}' for {aspect['aspectName']}"
        )

    rules = aspect.get("properties", {}).get(functional_event.semantic_type)

    if rules is None:

        return errors

    if rules.get("expectsValue", True):

        if functional_event.observed_value is None:

            errors.append(
                f"semantic: '{functional_event.semantic_type}' requires an observed_value"
            )

        else:

            min_value = rules.get("min")
            max_value = rules.get("max")

            if min_value is not None and functional_event.observed_value < min_value:

                errors.append(
                    f"semantic: observed_value {functional_event.observed_value} "
                    f"is below the minimum {min_value} for '{functional_event.semantic_type}'"
                )

            if max_value is not None and functional_event.observed_value > max_value:

                errors.append(
                    f"semantic: observed_value {functional_event.observed_value} "
                    f"is above the maximum {max_value} for '{functional_event.semantic_type}'"
                )

        expected_unit = rules.get("unit")

        if expected_unit is not None and functional_event.unit != expected_unit:

            errors.append(
                f"semantic: unit '{functional_event.unit}' does not match "
                f"expected unit '{expected_unit}' for '{functional_event.semantic_type}'"
            )

    else:

        if functional_event.observed_value is not None or functional_event.unit is not None:

            errors.append(
                f"semantic: '{functional_event.semantic_type}' should not include "
                f"observed_value/unit"
            )

    return errors


def get_semantic_events():

    response = requests.get(GENERATOR_URL)

    raw_events = response.json()

    semantic_events = []

    for raw_event in raw_events:

        structural_errors = validate_structure(raw_event)

        if structural_errors:

            event_data = raw_event

            aspect = FALLBACK_ASPECT

            semantic_errors = []

        else:

            functional_event = FunctionalEvent(**raw_event)

            event_data = functional_event.model_dump()

            aspect, is_fallback = resolve_aspect(functional_event.semantic_type)

            semantic_errors = validate_semantics(functional_event, aspect, is_fallback)

        errors = structural_errors + semantic_errors

        semantic_event = SemanticEvent.model_construct(
            **event_data,
            aspect=aspect,
            common_case_aspect=COMMON_CASE_ASPECT,
            semantic_context="Tractus-X Telecare Demo",
            semantic_version="1.0.0",
            validation_status="valid" if not errors else "invalid",
            validation_errors=errors
        )

        semantic_events.append(semantic_event)

    return semantic_events


def build_fhir_observation(semantic_event):

    observation = {
        "resourceType": "Observation",

        "status": "final",

        "code": {
            "text": semantic_event.semantic_type
        },

        "category": [
            {"text": semantic_event.category}
        ],

        "subject": {
            "reference": semantic_event.case_id
        },

        "effectiveDateTime": semantic_event.timestamp.isoformat(),

        "interpretation": [
            {"text": semantic_event.severity}
        ],

        "device": {
            "display": semantic_event.source
        },

        "note": [
            {"text": semantic_event.description}
        ]
    }

    if semantic_event.observed_value is not None:
        observation["valueQuantity"] = {
            "value": semantic_event.observed_value,
            "unit": semantic_event.unit
        }
    else:
        observation["valueCodeableConcept"] = {
            "text": semantic_event.description
        }

    return observation