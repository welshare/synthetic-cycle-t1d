"""Generate synthetic patient demographics and baseline characteristics."""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from ..models.cohort_params import CohortParameters


class PatientGenerator:
    """Generates realistic patient profiles for T1D women aged 18-45."""

    def __init__(self, params: CohortParameters, rng: np.random.Generator):
        self.params = params
        self.rng = rng
        self._baseline_characteristics = {}  # Cache per-patient stable traits

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

    def generate_lmp_for_phase(
        self, observation_date: datetime, target_phase: str
    ) -> str:
        """
        Generate LMP date that results in target phase at observation time.

        Args:
            observation_date: When the survey is taken
            target_phase: "follicular" or "luteal"

        Returns:
            LMP date as string (YYYY-MM-DD)
        """
        if target_phase == "follicular":
            # Days 1-14: LMP was 0-13 days ago
            days_ago = int(self.rng.integers(0, 14))
        else:  # luteal
            # Days 15-28: LMP was 14-27 days ago
            days_ago = int(self.rng.integers(14, 28))

        lmp = observation_date - timedelta(days=days_ago)
        return lmp.strftime("%Y-%m-%d")

    def generate_basal_insulin(
        self, patient_id: str, phase: str, in_intervention: bool = False
    ) -> float:
        """
        Generate basal insulin dose for a specific observation.

        Args:
            patient_id: Unique patient identifier (for baseline consistency)
            phase: "follicular" or "luteal"
            in_intervention: Whether patient uses cycle-aware adjustment

        Returns:
            Basal insulin dose in units/night
        """
        # Get or create patient's baseline follicular dose
        if patient_id not in self._baseline_characteristics:
            self._baseline_characteristics[patient_id] = {}

        if "basal_baseline" not in self._baseline_characteristics[patient_id]:
            baseline = self.rng.normal(
                self.params.basal_insulin_mean, self.params.basal_insulin_std
            )
            baseline = np.clip(
                baseline, self.params.basal_insulin_min, self.params.basal_insulin_max
            )
            self._baseline_characteristics[patient_id]["basal_baseline"] = baseline

        baseline = self._baseline_characteristics[patient_id]["basal_baseline"]

        # Apply phase adjustment
        if phase == "luteal":
            if in_intervention:
                # Intervention patients reduce dose by 10-20%
                reduction = self.rng.uniform(0.10, 0.20)
                dose = baseline * (1 - reduction)
            else:
                # Non-intervention: increase by ~14%
                dose = baseline * (1 + self.params.luteal_insulin_increase)
        else:
            dose = baseline

        # Add small observation noise
        dose += self.rng.normal(0, 0.5)
        dose = np.clip(
            dose, self.params.basal_insulin_min, self.params.basal_insulin_max
        )

        return round(dose, 1)

    def generate_nighttime_glucose(
        self, phase: str, in_intervention: bool = False
    ) -> float:
        """
        Generate average nighttime CGM glucose (00:00-06:00).

        Args:
            phase: "follicular" or "luteal"
            in_intervention: Whether patient uses cycle-aware adjustment

        Returns:
            Glucose level in mg/dL
        """
        if phase == "follicular":
            glucose = self.rng.normal(
                self.params.glucose_follicular_mean,
                self.params.glucose_follicular_std,
            )
        else:  # luteal
            if in_intervention:
                # Intervention reduces luteal glucose increase by ~90% (7.3 of 8.1 mg/dL)
                adjusted_increase = self.params.luteal_glucose_increase * 0.1
                glucose = self.rng.normal(
                    self.params.glucose_follicular_mean + adjusted_increase,
                    self.params.glucose_follicular_std,
                )
            else:
                # Non-intervention: full +8.1 mg/dL increase
                glucose = self.rng.normal(
                    self.params.glucose_follicular_mean
                    + self.params.luteal_glucose_increase,
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

    def generate_stable_patient_characteristics(self, patient_id: str) -> Dict[str, Any]:
        """
        Generate stable patient characteristics that don't change across observations.

        Args:
            patient_id: Unique patient identifier

        Returns:
            Dictionary with age, diagnosis, delivery method, cycle regularity
        """
        if patient_id not in self._baseline_characteristics:
            age = self.generate_age()
            self._baseline_characteristics[patient_id] = {
                "age": age,
                "years_since_diagnosis": self.generate_years_since_diagnosis(age),
                "insulin_delivery_method": self.generate_insulin_delivery_method(),
                "cycle_regularity": self.generate_cycle_regularity(),
            }

        return self._baseline_characteristics[patient_id]

    def generate_observation(
        self,
        patient_id: str,
        observation_date: datetime,
        target_phase: str,
        in_intervention: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate a single observation (survey response) for a patient.

        Args:
            patient_id: Unique patient identifier
            observation_date: Date when survey was taken
            target_phase: "follicular" or "luteal"
            in_intervention: Whether patient is in cycle-aware intervention group

        Returns:
            Complete observation profile
        """
        # Get stable characteristics
        stable = self.generate_stable_patient_characteristics(patient_id)

        # Generate observation-specific data
        observation = {
            "patient_id": patient_id,
            "observation_date": observation_date.strftime("%Y-%m-%d"),
            "phase": target_phase,
            "in_intervention": in_intervention,
            # Stable characteristics
            "age": stable["age"],
            "years_since_diagnosis": stable["years_since_diagnosis"],
            "insulin_delivery_method": stable["insulin_delivery_method"],
            "cycle_regularity": stable["cycle_regularity"],
            # Phase-specific LMP
            "lmp": self.generate_lmp_for_phase(observation_date, target_phase),
            # Phase and intervention-specific measurements
            "basal_insulin": self.generate_basal_insulin(
                patient_id, target_phase, in_intervention
            ),
            "nighttime_glucose": self.generate_nighttime_glucose(
                target_phase, in_intervention
            ),
            "sleep_awakenings": self.generate_sleep_awakenings(target_phase),
            "symptoms": self.generate_symptoms(target_phase),
        }

        return observation