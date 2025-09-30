#!/usr/bin/env python3
"""Post-generation cohort retrofitting to meet statistical boundaries."""

import json
from pathlib import Path
from typing import Dict, List, Any
import numpy as np
from dataclasses import dataclass

from .models.cohort_params import CohortParameters, DEFAULT_COHORT_PARAMS


@dataclass
class CohortStats:
    """Computed statistics from the cohort."""
    # Phase counts
    num_follicular: int
    num_luteal: int
    num_intervention: int
    num_intervention_luteal: int

    # Demographics
    ages: List[float]

    # Delivery method
    num_pump: int
    num_injection: int

    # Cycle regularity
    num_very_regular: int
    num_somewhat_regular: int
    num_irregular: int

    # Glucose & insulin by phase
    follicular_glucose: List[float]
    follicular_insulin: List[float]
    luteal_glucose: List[float]
    luteal_insulin: List[float]

    # Intervention luteal
    intervention_luteal_glucose: List[float]
    intervention_follicular_glucose: List[float]

    # Awakenings
    follicular_awakenings: List[int]
    luteal_awakenings: List[int]

    # Symptoms (boolean lists)
    follicular_night_sweats: List[bool]
    follicular_palpitations: List[bool]
    follicular_dizziness: List[bool]
    luteal_night_sweats: List[bool]
    luteal_palpitations: List[bool]
    luteal_dizziness: List[bool]


def load_cohort(output_dir: Path) -> List[Dict[str, Any]]:
    """Load all responses from output directory."""
    responses = []
    for json_file in sorted(output_dir.glob("response-*.json")):
        with open(json_file) as f:
            responses.append(json.load(f))
    return responses


def save_cohort(responses: List[Dict[str, Any]], output_dir: Path) -> None:
    """Save all responses back to output directory."""
    for response in responses:
        # Extract patient ID from subject reference
        subject_ref = response.get("subject", {}).get("reference", "")
        patient_id = subject_ref.replace("Patient/", "")

        output_path = output_dir / f"response-{patient_id}.json"
        with open(output_path, "w") as f:
            json.dump(response, f, indent=2)


def extract_stats(responses: List[Dict[str, Any]]) -> CohortStats:
    """Extract statistics from cohort."""

    # Storage
    follicular_responses = []
    luteal_responses = []
    intervention_responses = []

    ages = []
    pump_count = 0
    injection_count = 0
    very_regular_count = 0
    somewhat_regular_count = 0
    irregular_count = 0

    follicular_glucose = []
    follicular_insulin = []
    follicular_awakenings = []
    follicular_night_sweats = []
    follicular_palpitations = []
    follicular_dizziness = []

    luteal_glucose = []
    luteal_insulin = []
    luteal_awakenings = []
    luteal_night_sweats = []
    luteal_palpitations = []
    luteal_dizziness = []

    intervention_luteal_glucose = []
    intervention_follicular_glucose = []

    for response in responses:
        items = {item["linkId"]: item for item in response["item"]}

        # Demographics
        age = items["1"]["answer"][0]["valueInteger"]
        ages.append(age)

        # Delivery method (stored as valueString)
        delivery = items["3"]["answer"][0]["valueString"].lower()
        if "pump" in delivery:
            pump_count += 1
        else:
            injection_count += 1

        # Cycle regularity (stored as valueString)
        regularity = items["5"]["answer"][0]["valueString"].lower()
        if "very regular" in regularity:
            very_regular_count += 1
        elif "somewhat regular" in regularity:
            somewhat_regular_count += 1
        else:
            irregular_count += 1

        # Glucose and insulin (get before phase determination)
        glucose = items["7"]["answer"][0]["valueDecimal"]
        insulin = items["6"]["answer"][0]["valueDecimal"]

        # Current phase - use glucose as proxy (follicular ~118, luteal ~126)
        phase = "follicular" if glucose < 122 else "luteal"

        # Awakenings
        awakenings = items["8"]["answer"][0]["valueInteger"]

        # Symptoms (stored as valueString, can be empty list)
        symptom_answers = items["9"].get("answer", [])
        symptom_text = " ".join(ans["valueString"].lower() for ans in symptom_answers)
        night_sweats = "sweat" in symptom_text
        palpitations = "palpitation" in symptom_text
        dizziness = "dizziness" in symptom_text

        # Check if intervention
        subjective = items["10"]["answer"][0]["valueString"]
        is_intervention = "cycle-aware" in subjective.lower()

        if is_intervention:
            intervention_responses.append(response)
            if phase == "luteal":
                intervention_luteal_glucose.append(glucose)
            else:
                intervention_follicular_glucose.append(glucose)

        if phase == "follicular":
            follicular_responses.append(response)
            follicular_glucose.append(glucose)
            follicular_insulin.append(insulin)
            follicular_awakenings.append(awakenings)
            follicular_night_sweats.append(night_sweats)
            follicular_palpitations.append(palpitations)
            follicular_dizziness.append(dizziness)
        else:  # luteal
            luteal_responses.append(response)
            luteal_glucose.append(glucose)
            luteal_insulin.append(insulin)
            luteal_awakenings.append(awakenings)
            luteal_night_sweats.append(night_sweats)
            luteal_palpitations.append(palpitations)
            luteal_dizziness.append(dizziness)

    intervention_luteal = sum(1 for r in intervention_responses
                              if extract_phase(r) == "luteal")

    return CohortStats(
        num_follicular=len(follicular_responses),
        num_luteal=len(luteal_responses),
        num_intervention=len(intervention_responses),
        num_intervention_luteal=intervention_luteal,
        ages=ages,
        num_pump=pump_count,
        num_injection=injection_count,
        num_very_regular=very_regular_count,
        num_somewhat_regular=somewhat_regular_count,
        num_irregular=irregular_count,
        follicular_glucose=follicular_glucose,
        follicular_insulin=follicular_insulin,
        luteal_glucose=luteal_glucose,
        luteal_insulin=luteal_insulin,
        intervention_luteal_glucose=intervention_luteal_glucose,
        intervention_follicular_glucose=intervention_follicular_glucose,
        follicular_awakenings=follicular_awakenings,
        luteal_awakenings=luteal_awakenings,
        follicular_night_sweats=follicular_night_sweats,
        follicular_palpitations=follicular_palpitations,
        follicular_dizziness=follicular_dizziness,
        luteal_night_sweats=luteal_night_sweats,
        luteal_palpitations=luteal_palpitations,
        luteal_dizziness=luteal_dizziness,
    )


def extract_phase(response: Dict[str, Any]) -> str:
    """
    Extract phase from response using glucose level.

    Since subjective text is identical across responses, we use glucose
    as a proxy: follicular typically <120 mg/dL, luteal >120 mg/dL.
    """
    items = {item["linkId"]: item for item in response["item"]}
    glucose = items["7"]["answer"][0]["valueDecimal"]

    # Use glucose as proxy: follicular ~118, luteal ~126
    # Split at 122 (midpoint)
    if glucose < 122:
        return "follicular"
    else:
        return "luteal"


def is_intervention(response: Dict[str, Any]) -> bool:
    """Check if response is from intervention group."""
    items = {item["linkId"]: item for item in response["item"]}
    subjective = items["10"]["answer"][0]["valueString"]
    return "cycle-aware" in subjective.lower()


def get_symptoms(response: Dict[str, Any]) -> List[str]:
    """Get symptom strings from response (normalized)."""
    items = {item["linkId"]: item for item in response["item"]}
    symptoms = []
    symptom_answers = items["9"].get("answer", [])
    for ans in symptom_answers:
        text = ans["valueString"].lower()
        if "sweat" in text:
            symptoms.append("night-sweats")
        elif "palpitation" in text:
            symptoms.append("palpitations")
        elif "dizziness" in text:
            symptoms.append("dizziness")
    return symptoms


def set_symptoms(response: Dict[str, Any], symptoms: List[str]) -> None:
    """Set symptom strings in response."""
    items = {item["linkId"]: item for item in response["item"]}

    symptom_answers = []
    symptom_display = {
        "night-sweats": "Night sweats",
        "palpitations": "Heart palpitations",
        "dizziness": "Dizziness on standing"
    }

    for symptom in symptoms:
        symptom_answers.append({
            "valueString": symptom_display[symptom]
        })

    # Set or replace answer array
    if len(symptom_answers) > 0:
        items["9"]["answer"] = symptom_answers
    else:
        # Remove answer key if no symptoms
        if "answer" in items["9"]:
            del items["9"]["answer"]


def retrofit_cohort(
    output_dir: Path,
    params: CohortParameters = DEFAULT_COHORT_PARAMS,
    seed: int = 42,
    verbose: bool = False
) -> None:
    """
    Retrofit cohort to meet statistical boundaries.

    Modifies existing responses in-place to adjust:
    - Sleep awakenings (quantized integer values)
    - Symptom rates (binary outcomes)
    - Intervention effect size

    Args:
        output_dir: Directory containing response JSON files
        params: Cohort parameters with target statistics
        seed: Random seed for reproducibility
        verbose: Print detailed correction information
    """
    rng = np.random.default_rng(seed)

    print(f"\n🔧 Retrofitting cohort to meet statistical boundaries...")
    print(f"   Output directory: {output_dir}")
    print(f"   Random seed: {seed}\n")

    # Load cohort
    responses = load_cohort(output_dir)
    stats = extract_stats(responses)

    if verbose:
        print(f"Initial stats:")
        print(f"  Follicular: {stats.num_follicular}, Luteal: {stats.num_luteal}")
        print(f"  Intervention: {stats.num_intervention}")

    # Separate responses by phase and intervention status
    follicular = [r for r in responses if extract_phase(r) == "follicular"]
    luteal = [r for r in responses if extract_phase(r) == "luteal"]
    luteal_intervention = [r for r in luteal if is_intervention(r)]
    luteal_control = [r for r in luteal if not is_intervention(r)]

    # ===== AWAKENINGS CORRECTION =====
    # Target: follicular=0.8, luteal=1.4 (0.8 + 0.6)
    target_fol_awakenings = params.awakenings_follicular_mean
    target_lut_awakenings = params.awakenings_follicular_mean + params.luteal_awakenings_increase

    current_fol_mean = np.mean(stats.follicular_awakenings)
    current_lut_mean = np.mean(stats.luteal_awakenings)

    if verbose:
        print(f"\nAwakenings correction:")
        print(f"  Follicular: {current_fol_mean:.2f} → {target_fol_awakenings}")
        print(f"  Luteal: {current_lut_mean:.2f} → {target_lut_awakenings}")

    # Adjust follicular awakenings
    adjust_awakenings(follicular, target_fol_awakenings, rng, verbose)

    # Adjust luteal awakenings
    adjust_awakenings(luteal, target_lut_awakenings, rng, verbose)

    # ===== SYMPTOM RATE CORRECTION =====
    # Target rates from params
    fol_targets = {
        "night-sweats": params.night_sweats_prob_follicular,
        "palpitations": params.palpitations_prob_follicular,
        "dizziness": params.dizziness_prob_follicular,
    }

    lut_targets = {
        "night-sweats": params.night_sweats_prob_luteal,
        "palpitations": params.palpitations_prob_luteal,
        "dizziness": params.dizziness_prob_luteal,
    }

    if verbose:
        print(f"\nSymptom rate correction:")

    adjust_symptom_rates(follicular, fol_targets, rng, verbose, "Follicular")
    adjust_symptom_rates(luteal, lut_targets, rng, verbose, "Luteal")

    # ===== INTERVENTION EFFECT CORRECTION =====
    # Target: intervention group shows only 10% of luteal glucose increase
    # Expected luteal increase: 8.1 mg/dL
    # Intervention should show: 0.81 mg/dL increase

    if verbose:
        print(f"\nIntervention effect correction:")

    adjust_intervention_effect(
        luteal_intervention,
        luteal_control,
        params,
        rng,
        verbose
    )

    # Save retrofitted cohort
    save_cohort(responses, output_dir)

    # Recompute stats
    final_stats = extract_stats(responses)

    print(f"\n✓ Cohort retrofitting complete")
    print(f"  Responses modified: {len(responses)}")

    if verbose:
        print(f"\nFinal stats:")
        print(f"  Follicular awakenings: {np.mean(final_stats.follicular_awakenings):.2f}")
        print(f"  Luteal awakenings: {np.mean(final_stats.luteal_awakenings):.2f}")
        print(f"  Follicular night sweats: {np.mean(final_stats.follicular_night_sweats):.2%}")
        print(f"  Luteal night sweats: {np.mean(final_stats.luteal_night_sweats):.2%}")


def adjust_awakenings(
    responses: List[Dict[str, Any]],
    target_mean: float,
    rng: np.random.Generator,
    verbose: bool
) -> None:
    """Adjust awakenings to match target mean (linkId 8)."""
    items_list = [{item["linkId"]: item for item in r["item"]} for r in responses]
    current_values = [items["8"]["answer"][0]["valueInteger"] for items in items_list]
    current_mean = np.mean(current_values)

    if abs(current_mean - target_mean) < 0.01:
        return  # Already close enough

    # Determine direction
    need_increase = target_mean > current_mean

    # Calculate how many changes needed
    n = len(responses)
    gap = abs(target_mean - current_mean)
    num_changes = int(gap * n)  # Each change moves mean by ~1/n

    if num_changes == 0:
        return

    # Select responses to modify
    if need_increase:
        # Find responses with 0 or 1 awakenings to increase
        candidates = [i for i, v in enumerate(current_values) if v <= 1]
    else:
        # Find responses with 2+ awakenings to decrease
        candidates = [i for i, v in enumerate(current_values) if v >= 2]

    if len(candidates) == 0:
        return  # No suitable candidates

    # Randomly select candidates
    num_to_change = min(num_changes, len(candidates))
    to_change = rng.choice(candidates, size=num_to_change, replace=False)

    for idx in to_change:
        items = items_list[idx]
        current = items["8"]["answer"][0]["valueInteger"]
        if need_increase:
            items["8"]["answer"][0]["valueInteger"] = current + 1
        else:
            items["8"]["answer"][0]["valueInteger"] = max(0, current - 1)

    if verbose:
        new_values = [items["8"]["answer"][0]["valueInteger"] for items in items_list]
        print(f"    Changed {num_to_change} responses: {current_mean:.2f} → {np.mean(new_values):.2f}")


def adjust_symptom_rates(
    responses: List[Dict[str, Any]],
    target_rates: Dict[str, float],
    rng: np.random.Generator,
    verbose: bool,
    label: str
) -> None:
    """Adjust symptom rates to match targets."""
    for symptom, target_rate in target_rates.items():
        current_count = sum(1 for r in responses if symptom in get_symptoms(r))
        current_rate = current_count / len(responses)

        if abs(current_rate - target_rate) < 0.01:
            continue  # Close enough

        target_count = int(target_rate * len(responses))
        gap = target_count - current_count

        if gap == 0:
            continue

        if gap > 0:
            # Need to add symptom
            candidates = [r for r in responses if symptom not in get_symptoms(r)]
            num_to_add = min(gap, len(candidates))
            to_modify = rng.choice(candidates, size=num_to_add, replace=False)

            for response in to_modify:
                symptoms = get_symptoms(response)
                symptoms.append(symptom)
                set_symptoms(response, symptoms)
        else:
            # Need to remove symptom
            candidates = [r for r in responses if symptom in get_symptoms(r)]
            num_to_remove = min(abs(gap), len(candidates))
            to_modify = rng.choice(candidates, size=num_to_remove, replace=False)

            for response in to_modify:
                symptoms = get_symptoms(response)
                symptoms.remove(symptom)
                set_symptoms(response, symptoms)

        if verbose:
            final_count = sum(1 for r in responses if symptom in get_symptoms(r))
            final_rate = final_count / len(responses)
            print(f"  {label} {symptom}: {current_rate:.2%} → {final_rate:.2%}")


def adjust_intervention_effect(
    luteal_intervention: List[Dict[str, Any]],
    luteal_control: List[Dict[str, Any]],
    params: CohortParameters,
    rng: np.random.Generator,
    verbose: bool
) -> None:
    """
    Adjust intervention group to show reduced luteal glucose increase.

    Strategy: Reduce glucose values in intervention luteal responses
    to achieve ~0.81 mg/dL increase vs follicular baseline.
    """
    if len(luteal_intervention) == 0:
        return

    # Target: intervention shows 10% of luteal increase = 0.81 mg/dL
    # Baseline follicular glucose: 118 mg/dL
    # Target intervention luteal: 118 + 0.81 = 118.81 mg/dL

    baseline_glucose = params.glucose_follicular_mean
    intervention_reduction_factor = 0.10  # Intervention shows only 10% of increase
    target_increase = params.luteal_glucose_increase * intervention_reduction_factor
    target_glucose = baseline_glucose + target_increase

    # Get current intervention luteal glucose (linkId 7, not 8)
    current_values = []
    items_list = []
    for response in luteal_intervention:
        items = {item["linkId"]: item for item in response["item"]}
        glucose = items["7"]["answer"][0]["valueDecimal"]
        current_values.append(glucose)
        items_list.append(items)

    current_mean = np.mean(current_values)

    if verbose:
        print(f"  Intervention luteal glucose: {current_mean:.1f} → {target_glucose:.1f} mg/dL")

    if abs(current_mean - target_glucose) < 0.5:
        return  # Close enough

    # Apply shift to all intervention luteal responses
    shift = target_glucose - current_mean

    for items in items_list:
        current = items["7"]["answer"][0]["valueDecimal"]
        new_value = max(70, min(180, current + shift))  # Clamp to reasonable range
        items["7"]["answer"][0]["valueDecimal"] = round(new_value, 1)

    if verbose:
        new_values = [items["7"]["answer"][0]["valueDecimal"] for items in items_list]
        print(f"    Applied shift: {shift:.1f} mg/dL")
        print(f"    Final mean: {np.mean(new_values):.1f} mg/dL")