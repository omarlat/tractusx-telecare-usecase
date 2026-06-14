import requests
import json
from pathlib import Path

from models import (
    FunctionalEvent,
    SemanticEvent
)


GENERATOR_URL = "http://localhost:8000/events"

BASE_PATH = Path(__file__).parent

def load_aspect(file_name):

    aspect_path = (
        BASE_PATH
        / "aspects"
        / file_name
    )

    with open(aspect_path, "r") as file:

        return json.load(file)


def load_vital_signs_aspect():

    aspect_path = (
        BASE_PATH
        / "aspects"
        / "vital-signs.aspect.json"
    )

    with open(aspect_path, "r") as file:

        return json.load(file)


def resolve_aspect(semantic_type: str):

    aspect_files = [
        "vital-signs.aspect.json",
        "teleassistance-alert.aspect.json",
        "technical-event.aspect.json"
    ]

    for aspect_file in aspect_files:

        aspect = load_aspect(aspect_file)

        if semantic_type in aspect["semanticTypes"]:

            return aspect

    return {
        "aspectName": "CommonCaseAspect",
        "semanticTypes": [],
        "category": "generic",
        "description": "Fallback aspect"
    }


def get_semantic_events():

    response = requests.get(GENERATOR_URL)

    raw_events = response.json()

    semantic_events = []

    for raw_event in raw_events:

        functional_event = FunctionalEvent(**raw_event)

        validation_status = "valid"

        try:

            validate_semantic_event(functional_event)

        except ValueError:

            validation_status = "invalid"

        semantic_event = SemanticEvent(
            **functional_event.model_dump(),
            aspect=resolve_aspect(functional_event.semantic_type),
            semantic_context="Tractus-X Telecare Demo",
            semantic_version="1.0.0",
            validation_status=validation_status
        )

        semantic_events.append(semantic_event)

    return semantic_events

def validate_semantic_event(functional_event):

    if (
        functional_event.semantic_type == "oxygen_saturation"
        and functional_event.unit != "%"
    ):

        raise ValueError(
            "oxygen_saturation must use % as unit"
        )

def build_fhir_observation(semantic_event):

    return {
        "resourceType": "Observation",

        "status": "final",

        "code": {
            "text": semantic_event.semantic_type
        },

        "subject": {
            "reference": semantic_event.case_id
        },

        "valueQuantity": {
            "value": semantic_event.observed_value,
            "unit": semantic_event.unit
        }
    }