#!/usr/bin/env python3
"""CLI script to validate generated questionnaire responses against expected parameters."""

import argparse
import sys
from pathlib import Path

from src.validators.cohort_validator import CohortValidator
from src.models.cohort_params import DEFAULT_COHORT_PARAMS


def main():
    parser = argparse.ArgumentParser(
        description="Validate synthetic cohort data against probabilistic boundary conditions"
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default="output",
        help="Directory containing generated response JSON files (default: output/)",
    )
    parser.add_argument(
        "-i",
        "--intervention-count",
        type=int,
        default=64,
        help="Expected number of patients in intervention group (default: 64)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show all validation checks (default: only show failures)",
    )
    parser.add_argument(
        "--no-fail",
        action="store_true",
        help="Don't exit with error code on validation failures",
    )

    args = parser.parse_args()

    # Check if output directory exists
    output_path = Path(args.output_dir)
    if not output_path.exists():
        print(f"Error: Output directory '{args.output_dir}' does not exist")
        sys.exit(1)

    # Initialize validator
    validator = CohortValidator(params=DEFAULT_COHORT_PARAMS)

    print(f"Loading responses from {args.output_dir}...")

    try:
        # Run validation
        passed, total = validator.validate_all(
            output_dir=args.output_dir,
            expected_intervention_count=args.intervention_count,
        )

        # Print report
        validator.print_report(verbose=args.verbose)

        # Summary
        if passed == total:
            print("\n✓ All validation checks passed!")
            sys.exit(0)
        else:
            failed = total - passed
            print(f"\n✗ {failed} validation check(s) failed")

            if not args.no_fail:
                sys.exit(1)
            else:
                sys.exit(0)

    except Exception as e:
        print(f"\nError during validation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()