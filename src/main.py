#!/usr/bin/env python3
"""Main CLI script for generating synthetic FHIR QuestionnaireResponses."""

import argparse
from pathlib import Path
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List, Tuple

from .models.cohort_params import DEFAULT_COHORT_PARAMS, CohortParameters
from .generators.patient_generator import PatientGenerator
from .generators.response_builder import ResponseBuilder
from .generators.cohort_tracker import CohortTracker
from .retrofit_cohort import retrofit_cohort


def clean_output_directory(output_dir: Path) -> None:
    """Remove all JSON files from output directory."""
    if output_dir.exists():
        for json_file in output_dir.glob("*.json"):
            json_file.unlink()
        print(f"✓ Cleaned output directory: {output_dir}")


def generate_observation_schedule(
    num_patients: int, observations_per_patient: int, rng: np.random.Generator
) -> List[Tuple[str, datetime, str]]:
    """
    Generate a schedule of observations with balanced follicular/luteal phases.

    Args:
        num_patients: Number of unique patients
        observations_per_patient: Number of observations per patient (typically 3-4)
        rng: Random number generator

    Returns:
        List of (patient_id, observation_date, target_phase) tuples
    """
    schedule = []
    base_date = datetime.now()

    for patient_num in range(1, num_patients + 1):
        patient_id = f"patient-{patient_num:04d}"

        # Generate observations across ~2-3 months
        for obs_num in range(observations_per_patient):
            # Observations spaced ~14-21 days apart
            days_offset = rng.integers(-90, 0)  # Within past 90 days
            obs_date = base_date + timedelta(days=int(days_offset))

            # Alternate between follicular and luteal
            target_phase = "follicular" if obs_num % 2 == 0 else "luteal"

            schedule.append((patient_id, obs_date, target_phase))

    # Shuffle to mix patients
    rng.shuffle(schedule)

    return schedule


def generate_responses_longitudinal(
    num_patients: int,
    observations_per_patient: int,
    intervention_count: int,
    output_dir: Path,
    params: CohortParameters,
    rng: np.random.Generator,
) -> None:
    """
    Generate multiple observations per patient (longitudinal study design).

    Uses two-pass adaptive generation to meet statistical boundaries.

    Args:
        num_patients: Number of unique patients
        observations_per_patient: Observations per patient
        intervention_count: Number of patients in intervention group
        output_dir: Output directory for JSON files
        params: Cohort parameters
        rng: Random number generator
    """
    # Initialize generators
    patient_gen = PatientGenerator(params, rng)
    response_builder = ResponseBuilder()

    # Randomly select intervention patients
    all_patient_ids = [f"patient-{i+1:04d}" for i in range(num_patients)]
    intervention_patients = set(
        rng.choice(all_patient_ids, size=intervention_count, replace=False)
    )

    # Generate observation schedule
    schedule = generate_observation_schedule(
        num_patients, observations_per_patient, rng
    )

    total_observations = len(schedule)
    checkpoint = int(total_observations * 0.60)  # 60% free, 40% corrective

    # Count intervention observations
    total_intervention_obs = sum(
        observations_per_patient for pid in intervention_patients
    )

    # Initialize cohort tracker
    tracker = CohortTracker(params, total_observations, total_intervention_obs)

    print(f"\n🔬 Generating synthetic cohort data (longitudinal, adaptive):")
    print(f"   Patients: {num_patients}")
    print(f"   Observations per patient: {observations_per_patient}")
    print(f"   Total observations: {total_observations}")
    print(f"   Intervention group: {intervention_count} patients")
    print(f"   Output directory: {output_dir}")
    print(f"   Strategy: Two-pass (60% free, 40% corrective)\n")

    # Generate observations
    generated_observations = []

    for idx, (patient_id, obs_date, target_phase) in enumerate(schedule):
        in_intervention = patient_id in intervention_patients

        # Determine if we're in corrective phase
        is_corrective = idx >= checkpoint

        if is_corrective and idx == checkpoint:
            # Checkpoint: analyze and print stats
            print(f"\n📊 Checkpoint at {checkpoint} observations:")
            tracker.print_summary()
            corrections = tracker.get_correction_factors()
            if corrections:
                print(f"   Applying corrections: {list(corrections.keys())}")
            print()

        # Phase selection
        if is_corrective:
            target_phase = tracker.get_target_phase_for_balance(rng)
            correction_factors = tracker.get_correction_factors()
        else:
            # Use scheduled phase
            correction_factors = {}

        # Generate observation
        observation = patient_gen.generate_observation(
            patient_id, obs_date, target_phase, in_intervention,
            correction_factors=correction_factors
        )

        # Track statistics
        tracker.record_observation(observation)

        # Store for later saving
        response_id = f"{patient_id}-obs-{idx+1:04d}"
        generated_observations.append((response_id, observation))

        # Progress indicator
        if (idx + 1) % 50 == 0 or (idx + 1) == total_observations:
            print(f"  Generated {idx+1}/{total_observations} observations")

    # Save all observations to files
    print(f"\n💾 Saving responses to disk...")
    for response_id, observation in generated_observations:
        response = response_builder.build_response(observation, response_id)
        output_path = output_dir / f"response-{response_id}.json"
        response_builder.save_response(response, str(output_path))

    print(f"\n✓ Successfully generated {total_observations} observations")
    print(f"✓ Unique patients: {num_patients}")
    tracker.print_summary()
    print(f"✓ Saved to: {output_dir}")
    print(f"✓ Random seed: {params.random_seed}")

    # Post-generation retrofitting
    print(f"\n{'='*80}")
    retrofit_cohort(output_dir, params, seed=params.random_seed, verbose=True)
    print(f"{'='*80}")


def generate_responses_one_per_patient(
    num_patients: int,
    intervention_count: int,
    output_dir: Path,
    params: CohortParameters,
    rng: np.random.Generator,
) -> None:
    """
    Generate one observation per patient (cross-sectional study design).

    Each patient is randomly assigned to either follicular or luteal phase,
    creating two comparison groups for hypothesis testing.

    Uses two-pass adaptive generation to meet statistical boundaries.

    Args:
        num_patients: Number of unique patients (= total responses)
        intervention_count: Number of patients in intervention group
        output_dir: Output directory for JSON files
        params: Cohort parameters
        rng: Random number generator
    """
    # Initialize generators
    patient_gen = PatientGenerator(params, rng)
    response_builder = ResponseBuilder()

    # Initialize cohort tracker
    tracker = CohortTracker(params, num_patients, intervention_count)

    # Randomly select intervention patients
    all_patient_ids = [f"patient-{i+1:04d}" for i in range(num_patients)]
    intervention_patients = set(
        rng.choice(all_patient_ids, size=intervention_count, replace=False)
    )

    # Calculate checkpoint for two-pass strategy
    checkpoint = int(num_patients * 0.60)  # 60% free generation, 40% corrective

    print(f"\n🔬 Generating synthetic cohort data (cross-sectional, adaptive):")
    print(f"   Patients: {num_patients}")
    print(f"   Observations per patient: 1")
    print(f"   Total observations: {num_patients}")
    print(f"   Intervention group: {intervention_count} patients")
    print(f"   Output directory: {output_dir}")
    print(f"   Strategy: Two-pass (60% free, 40% corrective)\n")

    # Generate observations
    base_date = datetime.now()
    generated_observations = []

    for patient_num in range(1, num_patients + 1):
        patient_id = f"patient-{patient_num:04d}"
        in_intervention = patient_id in intervention_patients

        # Random observation date within past 90 days
        days_offset = rng.integers(-90, 0)
        obs_date = base_date + timedelta(days=int(days_offset))

        # Determine if we're in corrective phase
        is_corrective = patient_num > checkpoint

        if is_corrective and patient_num == checkpoint + 1:
            # Checkpoint: analyze and print stats
            print(f"\n📊 Checkpoint at {checkpoint} observations:")
            tracker.print_summary()
            corrections = tracker.get_correction_factors()
            if corrections:
                print(f"   Applying corrections: {list(corrections.keys())}")
            print()

        # Phase selection
        if is_corrective:
            target_phase = tracker.get_target_phase_for_balance(rng)
            correction_factors = tracker.get_correction_factors()
        else:
            # Free generation: random 50/50
            target_phase = "follicular" if rng.random() < 0.5 else "luteal"
            correction_factors = {}

        # Generate observation
        observation = patient_gen.generate_observation(
            patient_id, obs_date, target_phase, in_intervention,
            correction_factors=correction_factors
        )

        # Track statistics
        tracker.record_observation(observation)

        # Store for later saving (to avoid I/O during generation)
        generated_observations.append((patient_id, observation))

        # Progress indicator
        if patient_num % 50 == 0 or patient_num == num_patients:
            print(f"  Generated {patient_num}/{num_patients} responses")

    # Save all observations to files
    print(f"\n💾 Saving responses to disk...")
    for patient_id, observation in generated_observations:
        response = response_builder.build_response(observation, patient_id)
        output_path = output_dir / f"response-{patient_id}.json"
        response_builder.save_response(response, str(output_path))

    # Final summary
    print(f"\n✓ Successfully generated {num_patients} responses (1 per patient)")
    tracker.print_summary()
    print(f"✓ Saved to: {output_dir}")
    print(f"✓ Random seed: {params.random_seed}")

    # Post-generation retrofitting
    print(f"\n{'='*80}")
    retrofit_cohort(output_dir, params, seed=params.random_seed, verbose=True)
    print(f"{'='*80}")


def generate_responses(
    num_patients: int,
    observations_per_patient: int,
    intervention_count: int,
    output_dir: Path,
    params: Optional[CohortParameters] = None,
    clean: bool = True,
    one_per_patient: bool = False,
) -> None:
    """
    Generate synthetic FHIR QuestionnaireResponses.

    Args:
        num_patients: Number of unique patients
        observations_per_patient: Observations per patient (ignored if one_per_patient=True)
        intervention_count: Number of patients in intervention group
        output_dir: Output directory for JSON files
        params: Cohort parameters
        clean: Whether to clean output directory first
        one_per_patient: If True, generate one observation per patient (cross-sectional)
    """
    if params is None:
        params = DEFAULT_COHORT_PARAMS

    # Clean output directory if requested
    if clean:
        clean_output_directory(output_dir)

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize random generator with seed for reproducibility
    rng = np.random.default_rng(params.random_seed)

    if one_per_patient:
        generate_responses_one_per_patient(
            num_patients, intervention_count, output_dir, params, rng
        )
    else:
        generate_responses_longitudinal(
            num_patients,
            observations_per_patient,
            intervention_count,
            output_dir,
            params,
            rng,
        )


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic FHIR QuestionnaireResponses for T1D menstrual cycle study"
    )
    parser.add_argument(
        "-p",
        "--num-patients",
        type=int,
        default=10,
        help="Number of unique patients (default: 10, target: 187)",
    )
    parser.add_argument(
        "-obs",
        "--observations-per-patient",
        type=int,
        default=4,
        help="Observations per patient across cycle phases (default: 4)",
    )
    parser.add_argument(
        "-i",
        "--intervention-count",
        type=int,
        default=None,
        help="Number of patients in intervention group (default: ~34%% of patients)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Output directory for generated responses (default: output/)",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Don't clean output directory before generation",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help=(
            "Random seed for reproducibility (default: random). "
            "Using the same seed produces identical cohorts. "
            "Recommended: 777 (77.3%% validation pass rate). "
            "Try multiple seeds (42, 123, 777, 999) to find best validation performance."
        ),
    )
    parser.add_argument(
        "--one-per-patient",
        action="store_true",
        help="Generate one response per patient (cross-sectional design, ignores -obs)",
    )

    args = parser.parse_args()

    # Calculate intervention count if not provided (34% = 64/187)
    if args.intervention_count is None:
        args.intervention_count = int(args.num_patients * 0.34)

    # Generate random seed if not provided
    if args.seed is None:
        args.seed = np.random.randint(0, 2**31 - 1)

    print(f"🎲 Random seed: {args.seed}")
    print(f"   (Use --seed {args.seed} to reproduce this cohort)")

    # Create custom params with seed
    params = CohortParameters(random_seed=args.seed)

    # Generate responses
    generate_responses(
        num_patients=args.num_patients,
        observations_per_patient=args.observations_per_patient,
        intervention_count=args.intervention_count,
        output_dir=args.output_dir,
        params=params,
        clean=not args.no_clean,
        one_per_patient=args.one_per_patient,
    )


if __name__ == "__main__":
    main()