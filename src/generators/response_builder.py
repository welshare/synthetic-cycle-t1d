"""Build FHIR QuestionnaireResponse resources from patient profiles."""

import json
from datetime import datetime
from typing import Dict, Any
from fhir.resources.questionnaireresponse import (
    QuestionnaireResponse,
    QuestionnaireResponseItem,
    QuestionnaireResponseItemAnswer,
)
from fhir.resources.coding import Coding


class ResponseBuilder:
    """Constructs FHIR R4 QuestionnaireResponse from patient data."""

    def __init__(self, questionnaire_id: str = "menstrual-cycle-t1d-questionnaire"):
        self.questionnaire_id = questionnaire_id

    def build_response(
        self, patient_profile: Dict[str, Any], patient_id: str
    ) -> QuestionnaireResponse:
        """Build a complete FHIR QuestionnaireResponse from patient profile."""

        items = [
            self._build_age_item(patient_profile["age"]),
            self._build_years_since_diagnosis_item(
                patient_profile["years_since_diagnosis"]
            ),
            self._build_insulin_delivery_item(
                patient_profile["insulin_delivery_method"]
            ),
            self._build_lmp_item(patient_profile["lmp"]),
            self._build_cycle_regularity_item(patient_profile["cycle_regularity"]),
            self._build_basal_insulin_item(patient_profile["basal_insulin"]),
            self._build_glucose_item(patient_profile["nighttime_glucose"]),
            self._build_awakenings_item(patient_profile["sleep_awakenings"]),
            self._build_symptoms_item(patient_profile["symptoms"]),
            self._build_subjective_text_item(),
        ]

        response = QuestionnaireResponse(
            id=f"response-{patient_id}",
            questionnaire=f"Questionnaire/{self.questionnaire_id}",
            status="completed",
            authored=datetime.now().astimezone().isoformat(),
            item=items,
        )

        return response

    def _build_age_item(self, age: int) -> QuestionnaireResponseItem:
        """Build item for age (linkId=1)."""
        return QuestionnaireResponseItem(
            linkId="1",
            text="Age (years)",
            answer=[QuestionnaireResponseItemAnswer(valueInteger=age)],
        )

    def _build_years_since_diagnosis_item(
        self, years: int
    ) -> QuestionnaireResponseItem:
        """Build item for years since T1D diagnosis (linkId=2)."""
        return QuestionnaireResponseItem(
            linkId="2",
            text="How many years since your Type 1 Diabetes diagnosis?",
            answer=[QuestionnaireResponseItemAnswer(valueInteger=years)],
        )

    def _build_insulin_delivery_item(self, method: str) -> QuestionnaireResponseItem:
        """Build item for insulin delivery method (linkId=3)."""
        return QuestionnaireResponseItem(
            linkId="3",
            text="Which insulin delivery method do you use? (Pump or injections)",
            answer=[QuestionnaireResponseItemAnswer(valueString=method)],
        )

    def _build_lmp_item(self, lmp_date: str) -> QuestionnaireResponseItem:
        """Build item for last menstrual period (linkId=4)."""
        return QuestionnaireResponseItem(
            linkId="4",
            text="First day of your last menstrual period (LMP)",
            answer=[QuestionnaireResponseItemAnswer(valueDate=lmp_date)],
        )

    def _build_cycle_regularity_item(
        self, regularity: str
    ) -> QuestionnaireResponseItem:
        """Build item for cycle regularity (linkId=5)."""
        return QuestionnaireResponseItem(
            linkId="5",
            text="How regular is your menstrual cycle?",
            answer=[QuestionnaireResponseItemAnswer(valueString=regularity)],
        )

    def _build_basal_insulin_item(self, dose: float) -> QuestionnaireResponseItem:
        """Build item for basal insulin dose (linkId=6)."""
        return QuestionnaireResponseItem(
            linkId="6",
            text="What is your average nightly basal insulin dose (units)?",
            answer=[QuestionnaireResponseItemAnswer(valueDecimal=dose)],
        )

    def _build_glucose_item(self, glucose: float) -> QuestionnaireResponseItem:
        """Build item for nighttime glucose (linkId=7)."""
        return QuestionnaireResponseItem(
            linkId="7",
            text="What was your average nighttime CGM glucose (00:00–06:00) in mg/dL?",
            answer=[QuestionnaireResponseItemAnswer(valueDecimal=glucose)],
        )

    def _build_awakenings_item(self, awakenings: int) -> QuestionnaireResponseItem:
        """Build item for sleep awakenings (linkId=8)."""
        return QuestionnaireResponseItem(
            linkId="8",
            text="How many times do you usually wake up at night (00:00–06:00)?",
            answer=[QuestionnaireResponseItemAnswer(valueInteger=awakenings)],
        )

    def _build_symptoms_item(self, symptoms: list[str]) -> QuestionnaireResponseItem:
        """Build item for nighttime symptoms (linkId=9, repeats=true)."""
        answers = [
            QuestionnaireResponseItemAnswer(valueString=symptom)
            for symptom in symptoms
        ]

        return QuestionnaireResponseItem(
            linkId="9",
            text="Have you experienced any of these symptoms at night? (select all that apply)",
            answer=answers if answers else None,
        )

    def _build_subjective_text_item(self) -> QuestionnaireResponseItem:
        """Build item for subjective experience text (linkId=10)."""
        # For now, leaving this empty or with placeholder text
        return QuestionnaireResponseItem(
            linkId="10",
            text="In your own words, have you noticed changes in glucose stability depending on your menstrual cycle phase?",
            answer=[
                QuestionnaireResponseItemAnswer(
                    valueString="My glucose levels tend to be higher during certain times of the month."
                )
            ],
        )

    def save_response(self, response: QuestionnaireResponse, output_path: str):
        """Save QuestionnaireResponse to JSON file."""
        with open(output_path, "w") as f:
            json.dump(json.loads(response.json()), f, indent=2)