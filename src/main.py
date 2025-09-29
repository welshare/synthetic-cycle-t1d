#!/usr/bin/env python3
"""Main CLI script for generating synthetic FHIR QuestionnaireResponses."""

import argparse
import shutil
from pathlib import Path
import numpy as np
from typing import Optional

from .models.cohort_params import DEFAULT_COHORT_PARAMS, CohortParameters
from .generators.patient_generator import PatientGenerator
from .generators.response_builder import ResponseBuilder


def clean_output_directory(output_dir: Path) -> None:
    """Remove all JSON files from output directory."""
    if output_dir.exists():
        for json_file in output_dir.glob("*.json"):
            json_file.unlink()
        print(f"✓ Cleaned output directory: {output_dir}")


def generate_responses(
    num_responses: int,
    output_dir: Path,
    params: Optional[CohortParameters] = None,
    clean: bool = True,
) -> None:
    """Generate synthetic FHIR QuestionnaireResponses."""

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

    print(f"\nGenerating {num_responses} synthetic responses...")
    print(f"Output directory: {output_dir}\n")

    # Generate responses
    for i in range(num_responses):
        patient_id = f"patient-{i+1:04d}"

        # Generate patient profile
        profile = patient_gen.generate_patient_profile()

        # Build FHIR response
        response = response_builder.build_response(profile, patient_id)

        # Save to file
        output_path = output_dir / f"response-{patient_id}.json"
        response_builder.save_response(response, str(output_path))

        # Progress indicator
        if (i + 1) % 10 == 0 or (i + 1) == num_responses:
            print(f"  Generated {i+1}/{num_responses} responses")

    print(f"\n✓ Successfully generated {num_responses} responses")
    print(f"✓ Saved to: {output_dir}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic FHIR QuestionnaireResponses for T1D menstrual cycle study"
    )
    parser.add_argument(
        "-n",
        "--num-responses",
        type=int,
        default=20,
        help="Number of responses to generate (default: 20)",
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

    # Create custom params with seed if provided
    params = CohortParameters(random_seed=args.seed)

    # Generate responses
    generate_responses(
        num_responses=args.num_responses,
        output_dir=args.output_dir,
        params=params,
        clean=not args.no_clean,
    )


if __name__ == "__main__":
    main()