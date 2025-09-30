"""Track cohort statistics during generation and provide correction guidance."""

import numpy as np
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from ..models.cohort_params import CohortParameters


@dataclass
class CohortStats:
    """Running statistics for generated cohort."""

    # Counts
    total_observations: int = 0
    follicular_count: int = 0
    luteal_count: int = 0
    intervention_count: int = 0

    # Demographics
    ages: List[int] = field(default_factory=list)

    # Insulin delivery
    pump_count: int = 0
    injection_count: int = 0

    # Cycle regularity
    very_regular_count: int = 0
    somewhat_regular_count: int = 0
    irregular_count: int = 0

    # Phase-specific measurements
    follicular_glucose: List[float] = field(default_factory=list)
    luteal_glucose: List[float] = field(default_factory=list)
    luteal_glucose_non_intervention: List[float] = field(default_factory=list)
    luteal_glucose_intervention: List[float] = field(default_factory=list)

    follicular_basal: List[float] = field(default_factory=list)
    luteal_basal: List[float] = field(default_factory=list)

    follicular_awakenings: List[float] = field(default_factory=list)
    luteal_awakenings: List[float] = field(default_factory=list)

    # Symptoms
    follicular_night_sweats: int = 0
    follicular_palpitations: int = 0
    follicular_dizziness: int = 0

    luteal_night_sweats: int = 0
    luteal_palpitations: int = 0
    luteal_dizziness: int = 0


class CohortTracker:
    """Tracks cohort statistics and provides adaptive generation guidance."""

    def __init__(self, params: CohortParameters, target_total: int,
                 target_intervention: int):
        """Initialize tracker.

        Args:
            params: Expected cohort parameters
            target_total: Total number of observations to generate
            target_intervention: Target number of intervention observations
        """
        self.params = params
        self.target_total = target_total
        self.target_intervention = target_intervention
        self.stats = CohortStats()

    def record_observation(self, observation: Dict) -> None:
        """Record a generated observation's statistics.

        Args:
            observation: Generated observation dictionary
        """
        self.stats.total_observations += 1
        phase = observation['phase']
        in_intervention = observation['in_intervention']

        # Count phases
        if phase == 'follicular':
            self.stats.follicular_count += 1
        else:
            self.stats.luteal_count += 1

        # Count intervention
        if in_intervention:
            self.stats.intervention_count += 1

        # Demographics (only count once per unique patient for stable chars)
        self.stats.ages.append(observation['age'])

        # Insulin delivery
        if observation['insulin_delivery_method'] == "Insulin Pump":
            self.stats.pump_count += 1
        else:
            self.stats.injection_count += 1

        # Cycle regularity
        regularity = observation['cycle_regularity']
        if "Very regular" in regularity:
            self.stats.very_regular_count += 1
        elif "Somewhat regular" in regularity:
            self.stats.somewhat_regular_count += 1
        else:
            self.stats.irregular_count += 1

        # Phase-specific measurements
        if phase == 'follicular':
            self.stats.follicular_glucose.append(observation['nighttime_glucose'])
            self.stats.follicular_basal.append(observation['basal_insulin'])
            self.stats.follicular_awakenings.append(observation['sleep_awakenings'])

            # Symptoms
            symptoms = observation['symptoms']
            if "Night sweats" in symptoms:
                self.stats.follicular_night_sweats += 1
            if "Palpitations" in symptoms:
                self.stats.follicular_palpitations += 1
            if "Dizziness" in symptoms:
                self.stats.follicular_dizziness += 1
        else:  # luteal
            glucose = observation['nighttime_glucose']
            self.stats.luteal_glucose.append(glucose)
            self.stats.luteal_basal.append(observation['basal_insulin'])
            self.stats.luteal_awakenings.append(observation['sleep_awakenings'])

            if in_intervention:
                self.stats.luteal_glucose_intervention.append(glucose)
            else:
                self.stats.luteal_glucose_non_intervention.append(glucose)

            # Symptoms
            symptoms = observation['symptoms']
            if "Night sweats" in symptoms:
                self.stats.luteal_night_sweats += 1
            if "Palpitations" in symptoms:
                self.stats.luteal_palpitations += 1
            if "Dizziness" in symptoms:
                self.stats.luteal_dizziness += 1

    def get_correction_factors(self) -> Dict[str, float]:
        """Calculate correction factors for remaining samples.

        Returns:
            Dictionary of correction factors to adjust generation
        """
        if self.stats.total_observations == 0:
            return {}

        remaining = self.target_total - self.stats.total_observations
        if remaining <= 0:
            return {}

        corrections = {}

        # Phase balance correction (very strict enforcement)
        current_follicular_ratio = (self.stats.follicular_count /
                                   self.stats.total_observations)
        target_follicular_ratio = 0.50
        diff = abs(current_follicular_ratio - target_follicular_ratio)

        # Stronger bias based on how far off we are
        if current_follicular_ratio < target_follicular_ratio - 0.02:
            corrections['prefer_follicular'] = 3.0 if diff > 0.08 else 2.5
        elif current_follicular_ratio > target_follicular_ratio + 0.02:
            corrections['prefer_luteal'] = 3.0 if diff > 0.08 else 2.5

        # Pump ratio correction
        total_delivery = self.stats.pump_count + self.stats.injection_count
        if total_delivery > 0:
            current_pump_ratio = self.stats.pump_count / total_delivery
            if current_pump_ratio < self.params.pump_ratio - 0.05:
                corrections['prefer_pump'] = 1.5
            elif current_pump_ratio > self.params.pump_ratio + 0.05:
                corrections['prefer_injection'] = 1.5

        # Age mean correction
        if len(self.stats.ages) > 10:
            current_age_mean = np.mean(self.stats.ages)
            age_diff = self.params.age_mean - current_age_mean
            if abs(age_diff) > 1.5:
                corrections['age_shift'] = age_diff * 0.7

        # Glucose mean correction (follicular)
        if len(self.stats.follicular_glucose) > 5:
            current_mean = np.mean(self.stats.follicular_glucose)
            glucose_diff = self.params.glucose_follicular_mean - current_mean
            if abs(glucose_diff) > 3.0:
                corrections['follicular_glucose_shift'] = glucose_diff * 0.7

        # Glucose mean correction (luteal non-intervention)
        if len(self.stats.luteal_glucose_non_intervention) > 5:
            current_mean = np.mean(self.stats.luteal_glucose_non_intervention)
            expected_mean = (self.params.glucose_follicular_mean +
                           self.params.luteal_glucose_increase)
            glucose_diff = expected_mean - current_mean
            if abs(glucose_diff) > 3.0:
                corrections['luteal_glucose_shift'] = glucose_diff * 0.7

        # Basal insulin correction (follicular) - stronger
        if len(self.stats.follicular_basal) > 5:
            current_mean = np.mean(self.stats.follicular_basal)
            basal_diff = self.params.basal_insulin_mean - current_mean
            if abs(basal_diff) > 1.0:
                corrections['basal_insulin_shift'] = basal_diff * 1.0

        # Basal insulin correction (luteal non-intervention)
        if len(self.stats.luteal_basal) > 5:
            # Split luteal basal by intervention status if possible
            # For now, just track the mean and ensure luteal is higher
            current_mean = np.mean(self.stats.luteal_basal)
            expected_mean = self.params.basal_insulin_mean * (1 + self.params.luteal_insulin_increase)
            basal_diff = expected_mean - current_mean
            if abs(basal_diff) > 1.0:
                corrections['luteal_basal_shift'] = basal_diff * 0.8

        # Awakenings correction (follicular) - very aggressive
        if len(self.stats.follicular_awakenings) > 5:
            current_mean = np.mean(self.stats.follicular_awakenings)
            awake_diff = self.params.awakenings_follicular_mean - current_mean
            if abs(awake_diff) > 0.10:
                # Extremely strong correction for awakenings (they're integer counts)
                corrections['follicular_awakenings_shift'] = awake_diff * 2.0

        # Awakenings correction (luteal) - very aggressive
        if len(self.stats.luteal_awakenings) > 5:
            current_mean = np.mean(self.stats.luteal_awakenings)
            expected_mean = (self.params.awakenings_follicular_mean +
                           self.params.luteal_awakenings_increase)
            awake_diff = expected_mean - current_mean
            if abs(awake_diff) > 0.10:
                corrections['luteal_awakenings_shift'] = awake_diff * 2.0

        # Symptom rate corrections (follicular) - very aggressive
        if self.stats.follicular_count > 5:
            current_sweats = self.stats.follicular_night_sweats / self.stats.follicular_count
            target_sweats = self.params.night_sweats_prob_follicular
            if current_sweats < target_sweats - 0.02:
                # Boost more aggressively when below target
                corrections['follicular_sweats_boost'] = 3.5
            elif current_sweats > target_sweats + 0.02:
                corrections['follicular_sweats_reduce'] = 0.2

            current_palp = self.stats.follicular_palpitations / self.stats.follicular_count
            target_palp = self.params.palpitations_prob_follicular
            if current_palp < target_palp - 0.01:
                corrections['follicular_palpitations_boost'] = 4.0
            elif current_palp > target_palp + 0.02:
                corrections['follicular_palpitations_reduce'] = 0.2

            current_dizzy = self.stats.follicular_dizziness / self.stats.follicular_count
            target_dizzy = self.params.dizziness_prob_follicular
            if current_dizzy < target_dizzy - 0.01:
                corrections['follicular_dizziness_boost'] = 4.0
            elif current_dizzy > target_dizzy + 0.02:
                corrections['follicular_dizziness_reduce'] = 0.2

        # Symptom rate corrections (luteal) - very aggressive
        if self.stats.luteal_count > 5:
            current_sweats = self.stats.luteal_night_sweats / self.stats.luteal_count
            target_sweats = self.params.night_sweats_prob_luteal
            if current_sweats < target_sweats - 0.03:
                corrections['luteal_sweats_boost'] = 3.0
            elif current_sweats > target_sweats + 0.03:
                corrections['luteal_sweats_reduce'] = 0.3

            current_palp = self.stats.luteal_palpitations / self.stats.luteal_count
            target_palp = self.params.palpitations_prob_luteal
            if current_palp < target_palp - 0.02:
                corrections['luteal_palpitations_boost'] = 3.5
            elif current_palp > target_palp + 0.03:
                corrections['luteal_palpitations_reduce'] = 0.3

            current_dizzy = self.stats.luteal_dizziness / self.stats.luteal_count
            target_dizzy = self.params.dizziness_prob_luteal
            if current_dizzy < target_dizzy - 0.02:
                corrections['luteal_dizziness_boost'] = 3.5
            elif current_dizzy > target_dizzy + 0.03:
                corrections['luteal_dizziness_reduce'] = 0.3

        return corrections

    def should_use_intervention(self, remaining: int) -> bool:
        """Determine if next patient should be in intervention group.

        Args:
            remaining: Number of observations remaining to generate

        Returns:
            True if next observation should be intervention
        """
        # Calculate needed intervention count
        needed = self.target_intervention - self.stats.intervention_count

        if needed <= 0:
            return False

        if needed >= remaining:
            return True

        # Probability based on remaining ratio
        return (needed / remaining) > 0.5

    def get_target_phase_for_balance(self, rng: np.random.Generator) -> str:
        """Get target phase biased toward maintaining 50/50 balance.

        Args:
            rng: Random number generator

        Returns:
            "follicular" or "luteal"
        """
        if self.stats.total_observations == 0:
            return "follicular" if rng.random() < 0.5 else "luteal"

        current_ratio = self.stats.follicular_count / self.stats.total_observations
        target_ratio = 0.50

        # Strong bias if significantly off
        if current_ratio < target_ratio - 0.10:
            return "follicular"
        elif current_ratio > target_ratio + 0.10:
            return "luteal"

        # Gentle bias
        if current_ratio < target_ratio:
            follicular_prob = 0.60
        elif current_ratio > target_ratio:
            follicular_prob = 0.40
        else:
            follicular_prob = 0.50

        return "follicular" if rng.random() < follicular_prob else "luteal"

    def print_summary(self) -> None:
        """Print current cohort statistics summary."""
        print(f"\n📊 Cohort Statistics (n={self.stats.total_observations}):")
        print(f"   Phase balance: {self.stats.follicular_count} follicular, "
              f"{self.stats.luteal_count} luteal")
        print(f"   Intervention: {self.stats.intervention_count} observations "
              f"(target: {self.target_intervention})")

        if self.stats.ages:
            print(f"   Mean age: {np.mean(self.stats.ages):.1f} "
                  f"(target: {self.params.age_mean})")

        total_delivery = self.stats.pump_count + self.stats.injection_count
        if total_delivery > 0:
            pump_ratio = self.stats.pump_count / total_delivery
            print(f"   Pump ratio: {pump_ratio:.2f} (target: {self.params.pump_ratio})")

        if self.stats.follicular_glucose:
            print(f"   Follicular glucose: {np.mean(self.stats.follicular_glucose):.1f} mg/dL "
                  f"(target: {self.params.glucose_follicular_mean})")

        if self.stats.luteal_glucose_non_intervention:
            expected = (self.params.glucose_follicular_mean +
                       self.params.luteal_glucose_increase)
            print(f"   Luteal glucose (non-int): {np.mean(self.stats.luteal_glucose_non_intervention):.1f} mg/dL "
                  f"(target: {expected:.1f})")