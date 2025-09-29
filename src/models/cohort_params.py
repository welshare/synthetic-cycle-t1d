"""Population-level parameters for synthetic cohort generation."""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class CohortParameters:
    """Statistical parameters defining the synthetic T1D population."""

    # Demographics
    age_range: Tuple[int, int] = (18, 45)
    age_mean: float = 31.5
    age_std: float = 7.0

    # T1D diagnosis
    years_since_diagnosis_min: int = 1
    years_since_diagnosis_max: int = 30
    years_since_diagnosis_mean: float = 12.0
    years_since_diagnosis_std: float = 8.0

    # Insulin delivery method distribution
    pump_ratio: float = 0.65  # 65% pump, 35% injections

    # Menstrual cycle regularity distribution
    very_regular_ratio: float = 0.55
    somewhat_regular_ratio: float = 0.30
    irregular_ratio: float = 0.15

    # Basal insulin doses (units/night) - Follicular phase baseline
    basal_insulin_mean: float = 14.0
    basal_insulin_std: float = 3.5
    basal_insulin_min: float = 5.0
    basal_insulin_max: float = 30.0

    # Nighttime glucose (mg/dL) - Follicular phase baseline
    glucose_follicular_mean: float = 118.0
    glucose_follicular_std: float = 20.0

    # Sleep awakenings - Follicular phase baseline
    awakenings_follicular_mean: float = 0.8
    awakenings_follicular_std: float = 0.6

    # Symptom probabilities - Follicular phase
    night_sweats_prob_follicular: float = 0.12
    dizziness_prob_follicular: float = 0.04
    palpitations_prob_follicular: float = 0.05
    fatigue_prob_follicular: float = 0.18

    # Luteal phase adjustments (multiplicative or additive)
    luteal_insulin_increase: float = 0.14  # +14%
    luteal_glucose_increase: float = 8.1  # +8.1 mg/dL
    luteal_awakenings_increase: float = 0.6  # +0.6 awakenings

    # Symptom probability increases in luteal phase
    night_sweats_prob_luteal: float = 0.22
    dizziness_prob_luteal: float = 0.09
    palpitations_prob_luteal: float = 0.11
    fatigue_prob_luteal: float = 0.25

    # Random seed for reproducibility
    random_seed: int = 42


# Default cohort parameters
DEFAULT_COHORT_PARAMS = CohortParameters()