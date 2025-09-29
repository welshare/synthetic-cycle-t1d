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


def generate_responses(
    num_patients: int,
    observations_per_patient: int,
    intervention_count: int,
    output_dir: Path,
    params: Optional[CohortParameters] = None,
    clean: bool = True,
) -> None:
    """
    Generate synthetic FHIR QuestionnaireResponses with multiple observations per patient.

    Args:
        num_patients: Number of unique patients (default: 187)
        observations_per_patient: Observations per patient (default: 4, yields ~750 total)
        intervention_count: Number of patients in intervention group (default: 64)
        output_dir: Output directory for JSON files
        params: Cohort parameters
        clean: Whether to clean output directory first
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
    follicular_count = sum(1 for _, _, phase in schedule if phase == "follicular")
    luteal_count = total_observations - follicular_count

    print(f"\n🔬 Generating synthetic cohort data:")
    print(f"   Patients: {num_patients}")
    print(f"   Observations per patient: {observations_per_patient}")
    print(f"   Total observations: {total_observations}")
    print(f"   - Follicular phase: {follicular_count}")
    print(f"   - Luteal phase: {luteal_count}")
    print(f"   Intervention group: {intervention_count} patients")
    print(f"   Output directory: {output_dir}\n")

    # Generate observations
    for idx, (patient_id, obs_date, target_phase) in enumerate(schedule):
        in_intervention = patient_id in intervention_patients

        # Generate observation
        observation = patient_gen.generate_observation(
            patient_id, obs_date, target_phase, in_intervention
        )

        # Build FHIR response
        response_id = f"{patient_id}-obs-{idx+1:04d}"
        response = response_builder.build_response(observation, response_id)

        # Save to file
        output_path = output_dir / f"response-{response_id}.json"
        response_builder.save_response(response, str(output_path))

        # Progress indicator
        if (idx + 1) % 50 == 0 or (idx + 1) == total_observations:
            print(f"  Generated {idx+1}/{total_observations} observations")

    print(f"\n✓ Successfully generated {total_observations} observations")
    print(f"✓ Unique patients: {num_patients}")
    print(f"✓ Saved to: {output_dir}")


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
        "--seed", type=int, default=42, help="Random seed for reproducibility"
    )

    args = parser.parse_args()

    # Calculate intervention count if not provided (34% = 64/187)
    if args.intervention_count is None:
        args.intervention_count = int(args.num_patients * 0.34)

    # Create custom params with seed if provided
    params = CohortParameters(random_seed=args.seed)

    # Generate responses
    generate_responses(
        num_patients=args.num_patients,
        observations_per_patient=args.observations_per_patient,
        intervention_count=args.intervention_count,
        output_dir=args.output_dir,
        params=params,
        clean=not args.no_clean,
    )


if __name__ == "__main__":
    main()