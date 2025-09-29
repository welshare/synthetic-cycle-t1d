"""Generate synthetic patient demographics and baseline characteristics."""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any
from ..models.cohort_params import CohortParameters


class PatientGenerator:
    """Generates realistic patient profiles for T1D women aged 18-45."""

    def __init__(self, params: CohortParameters, rng: np.random.Generator):
        self.params = params
        self.rng = rng

    def generate_age(self) -> int:
        """Generate age within 18-45 range using normal distribution."""
        age = self.rng.normal(self.params.age_mean, self.params.age_std)
        age = np.clip(age, self.params.age_range[0], self.params.age_range[1])
        return int(round(age))

    def generate_years_since_diagnosis(self, age: int) -> int:
        """Generate years since T1D diagnosis (must be < age)."""
        years = self.rng.normal(
            self.params.years_since_diagnosis_mean,
            self.params.years_since_diagnosis_std,
        )
        years = np.clip(
            years,
            self.params.years_since_diagnosis_min,
            min(age - 1, self.params.years_since_diagnosis_max),
        )
        return int(round(years))

    def generate_insulin_delivery_method(self) -> str:
        """Generate insulin delivery method (pump vs injections)."""
        if self.rng.random() < self.params.pump_ratio:
            return "Insulin Pump"
        return "Multiple Daily Injections"

    def generate_cycle_regularity(self) -> str:
        """Generate menstrual cycle regularity pattern."""
        r = self.rng.random()
        if r < self.params.very_regular_ratio:
            return "Very regular (predictable)"
        elif r < self.params.very_regular_ratio + self.params.somewhat_regular_ratio:
            return "Somewhat regular"
        return "Irregular"

    def generate_lmp(self) -> str:
        """Generate last menstrual period date (within last 35 days)."""
        days_ago = int(self.rng.integers(1, 36))
        lmp = datetime.now() - timedelta(days=days_ago)
        return lmp.strftime("%Y-%m-%d")

    def generate_basal_insulin(self) -> float:
        """Generate baseline basal insulin dose (follicular phase)."""
        dose = self.rng.normal(
            self.params.basal_insulin_mean, self.params.basal_insulin_std
        )
        dose = np.clip(
            dose, self.params.basal_insulin_min, self.params.basal_insulin_max
        )
        return round(dose, 1)

    def generate_nighttime_glucose(self, phase: str = "follicular") -> float:
        """Generate average nighttime CGM glucose (00:00-06:00)."""
        if phase == "follicular":
            glucose = self.rng.normal(
                self.params.glucose_follicular_mean,
                self.params.glucose_follicular_std,
            )
        else:  # luteal
            glucose = self.rng.normal(
                self.params.glucose_follicular_mean + self.params.luteal_glucose_increase,
                self.params.glucose_follicular_std,
            )
        return round(max(50.0, glucose), 1)

    def generate_sleep_awakenings(self, phase: str = "follicular") -> int:
        """Generate number of nighttime awakenings."""
        if phase == "follicular":
            awakenings = self.rng.normal(
                self.params.awakenings_follicular_mean,
                self.params.awakenings_follicular_std,
            )
        else:  # luteal
            awakenings = self.rng.normal(
                self.params.awakenings_follicular_mean
                + self.params.luteal_awakenings_increase,
                self.params.awakenings_follicular_std,
            )
        return int(round(max(0, awakenings)))

    def generate_symptoms(self, phase: str = "follicular") -> list[str]:
        """Generate nighttime symptoms based on phase-specific probabilities."""
        symptoms = []

        if phase == "follicular":
            probs = {
                "Night sweats": self.params.night_sweats_prob_follicular,
                "Dizziness": self.params.dizziness_prob_follicular,
                "Palpitations": self.params.palpitations_prob_follicular,
                "Weakness/Fatigue": self.params.fatigue_prob_follicular,
            }
        else:  # luteal
            probs = {
                "Night sweats": self.params.night_sweats_prob_luteal,
                "Dizziness": self.params.dizziness_prob_luteal,
                "Palpitations": self.params.palpitations_prob_luteal,
                "Weakness/Fatigue": self.params.fatigue_prob_luteal,
            }

        for symptom, prob in probs.items():
            if self.rng.random() < prob:
                symptoms.append(symptom)

        return symptoms

    def generate_patient_profile(self) -> Dict[str, Any]:
        """Generate a complete patient profile with baseline characteristics."""
        age = self.generate_age()

        profile = {
            "age": age,
            "years_since_diagnosis": self.generate_years_since_diagnosis(age),
            "insulin_delivery_method": self.generate_insulin_delivery_method(),
            "lmp": self.generate_lmp(),
            "cycle_regularity": self.generate_cycle_regularity(),
            "basal_insulin": self.generate_basal_insulin(),
            "nighttime_glucose": self.generate_nighttime_glucose("follicular"),
            "sleep_awakenings": self.generate_sleep_awakenings("follicular"),
            "symptoms": self.generate_symptoms("follicular"),
        }

        return profile