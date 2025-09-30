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

    def generate_age(self, shift: float = 0.0) -> int:
        """Generate age within 18-45 range using normal distribution.

        Args:
            shift: Optional mean shift for adaptive correction
        """
        age = self.rng.normal(self.params.age_mean + shift, self.params.age_std)
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

    def generate_insulin_delivery_method(self, prefer_pump: bool = False,
                                         prefer_injection: bool = False) -> str:
        """Generate insulin delivery method (pump vs injections).

        Args:
            prefer_pump: If True, bias toward pump selection
            prefer_injection: If True, bias toward injection selection
        """
        pump_prob = self.params.pump_ratio

        if prefer_pump:
            pump_prob = min(0.95, pump_prob * 1.3)
        elif prefer_injection:
            pump_prob = max(0.05, pump_prob * 0.7)

        if self.rng.random() < pump_prob:
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
        self, patient_id: str, phase: str, in_intervention: bool = False,
        shift: float = 0.0
    ) -> float:
        """
        Generate basal insulin dose for a specific observation.

        Args:
            patient_id: Unique patient identifier (for baseline consistency)
            phase: "follicular" or "luteal"
            in_intervention: Whether patient uses cycle-aware adjustment
            shift: Optional mean shift for adaptive correction

        Returns:
            Basal insulin dose in units/night
        """
        # Get or create patient's baseline follicular dose
        if patient_id not in self._baseline_characteristics:
            self._baseline_characteristics[patient_id] = {}

        if "basal_baseline" not in self._baseline_characteristics[patient_id]:
            baseline = self.rng.normal(
                self.params.basal_insulin_mean + shift, self.params.basal_insulin_std
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
                # Apply luteal-specific shift if provided
                dose += shift
        else:
            dose = baseline

        # Add small observation noise (reduced for better control)
        dose += self.rng.normal(0, 0.3)
        dose = np.clip(
            dose, self.params.basal_insulin_min, self.params.basal_insulin_max
        )

        return round(dose, 1)

    def generate_nighttime_glucose(
        self, phase: str, in_intervention: bool = False, shift: float = 0.0
    ) -> float:
        """
        Generate average nighttime CGM glucose (00:00-06:00).

        Args:
            phase: "follicular" or "luteal"
            in_intervention: Whether patient uses cycle-aware adjustment
            shift: Optional mean shift for adaptive correction

        Returns:
            Glucose level in mg/dL
        """
        if phase == "follicular":
            glucose = self.rng.normal(
                self.params.glucose_follicular_mean + shift,
                self.params.glucose_follicular_std,
            )
        else:  # luteal
            if in_intervention:
                # Intervention reduces luteal glucose increase by ~90% (7.3 of 8.1 mg/dL)
                adjusted_increase = self.params.luteal_glucose_increase * 0.1
                glucose = self.rng.normal(
                    self.params.glucose_follicular_mean + adjusted_increase + shift,
                    self.params.glucose_follicular_std,
                )
            else:
                # Non-intervention: full +8.1 mg/dL increase
                glucose = self.rng.normal(
                    self.params.glucose_follicular_mean
                    + self.params.luteal_glucose_increase + shift,
                    self.params.glucose_follicular_std,
                )
        return round(max(50.0, glucose), 1)

    def generate_sleep_awakenings(self, phase: str = "follicular",
                                  shift: float = 0.0) -> int:
        """Generate number of nighttime awakenings.

        Args:
            phase: "follicular" or "luteal"
            shift: Optional mean shift for adaptive correction
        """
        if phase == "follicular":
            awakenings = self.rng.normal(
                self.params.awakenings_follicular_mean + shift,
                self.params.awakenings_follicular_std,
            )
        else:  # luteal
            awakenings = self.rng.normal(
                self.params.awakenings_follicular_mean
                + self.params.luteal_awakenings_increase + shift,
                self.params.awakenings_follicular_std,
            )
        return int(round(max(0, awakenings)))

    def generate_symptoms(self, phase: str = "follicular",
                         prob_modifiers: dict = None) -> list[str]:
        """Generate nighttime symptoms based on phase-specific probabilities.

        Args:
            phase: "follicular" or "luteal"
            prob_modifiers: Optional dict with probability multipliers for adaptive correction
        """
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

        # Apply modifiers if provided
        if prob_modifiers:
            for symptom, modifier in prob_modifiers.items():
                if symptom in probs:
                    probs[symptom] = np.clip(probs[symptom] * modifier, 0.0, 1.0)

        for symptom, prob in probs.items():
            if self.rng.random() < prob:
                symptoms.append(symptom)

        return symptoms

    def generate_stable_patient_characteristics(self, patient_id: str,
                                                correction_factors: dict = None) -> Dict[str, Any]:
        """
        Generate stable patient characteristics that don't change across observations.

        Args:
            patient_id: Unique patient identifier
            correction_factors: Optional dict with correction factors for adaptive generation

        Returns:
            Dictionary with age, diagnosis, delivery method, cycle regularity
        """
        if patient_id not in self._baseline_characteristics:
            corrections = correction_factors or {}

            age_shift = corrections.get('age_shift', 0.0)
            age = self.generate_age(shift=age_shift)

            prefer_pump = corrections.get('prefer_pump', False)
            prefer_injection = corrections.get('prefer_injection', False)

            self._baseline_characteristics[patient_id] = {
                "age": age,
                "years_since_diagnosis": self.generate_years_since_diagnosis(age),
                "insulin_delivery_method": self.generate_insulin_delivery_method(
                    prefer_pump=prefer_pump, prefer_injection=prefer_injection
                ),
                "cycle_regularity": self.generate_cycle_regularity(),
            }

        return self._baseline_characteristics[patient_id]

    def generate_observation(
        self,
        patient_id: str,
        observation_date: datetime,
        target_phase: str,
        in_intervention: bool = False,
        correction_factors: dict = None,
    ) -> Dict[str, Any]:
        """
        Generate a single observation (survey response) for a patient.

        Args:
            patient_id: Unique patient identifier
            observation_date: Date when survey was taken
            target_phase: "follicular" or "luteal"
            in_intervention: Whether patient is in cycle-aware intervention group
            correction_factors: Optional dict with correction factors for adaptive generation

        Returns:
            Complete observation profile
        """
        corrections = correction_factors or {}

        # Get stable characteristics
        stable = self.generate_stable_patient_characteristics(patient_id, corrections)

        # Extract correction shifts
        glucose_shift = corrections.get(f'{target_phase}_glucose_shift', 0.0)

        # Use phase-specific basal shift
        if target_phase == 'follicular':
            basal_shift = corrections.get('basal_insulin_shift', 0.0)
        else:
            basal_shift = corrections.get('luteal_basal_shift', 0.0)

        # Build symptom modifiers
        symptom_mods = {}
        if target_phase == 'follicular':
            if 'follicular_sweats_boost' in corrections:
                symptom_mods['Night sweats'] = corrections['follicular_sweats_boost']
            elif 'follicular_sweats_reduce' in corrections:
                symptom_mods['Night sweats'] = corrections['follicular_sweats_reduce']

            if 'follicular_palpitations_boost' in corrections:
                symptom_mods['Palpitations'] = corrections['follicular_palpitations_boost']
            elif 'follicular_palpitations_reduce' in corrections:
                symptom_mods['Palpitations'] = corrections['follicular_palpitations_reduce']

            if 'follicular_dizziness_boost' in corrections:
                symptom_mods['Dizziness'] = corrections['follicular_dizziness_boost']
            elif 'follicular_dizziness_reduce' in corrections:
                symptom_mods['Dizziness'] = corrections['follicular_dizziness_reduce']

            awakenings_shift = corrections.get('follicular_awakenings_shift', 0.0)
        else:  # luteal
            if 'luteal_sweats_boost' in corrections:
                symptom_mods['Night sweats'] = corrections['luteal_sweats_boost']
            elif 'luteal_sweats_reduce' in corrections:
                symptom_mods['Night sweats'] = corrections['luteal_sweats_reduce']

            if 'luteal_palpitations_boost' in corrections:
                symptom_mods['Palpitations'] = corrections['luteal_palpitations_boost']
            elif 'luteal_palpitations_reduce' in corrections:
                symptom_mods['Palpitations'] = corrections['luteal_palpitations_reduce']

            if 'luteal_dizziness_boost' in corrections:
                symptom_mods['Dizziness'] = corrections['luteal_dizziness_boost']
            elif 'luteal_dizziness_reduce' in corrections:
                symptom_mods['Dizziness'] = corrections['luteal_dizziness_reduce']

            awakenings_shift = corrections.get('luteal_awakenings_shift', 0.0)

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
                patient_id, target_phase, in_intervention, shift=basal_shift
            ),
            "nighttime_glucose": self.generate_nighttime_glucose(
                target_phase, in_intervention, shift=glucose_shift
            ),
            "sleep_awakenings": self.generate_sleep_awakenings(
                target_phase, shift=awakenings_shift
            ),
            "symptoms": self.generate_symptoms(target_phase, prob_modifiers=symptom_mods),
        }

        return observation