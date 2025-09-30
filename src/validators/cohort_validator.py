"""Validation functions to verify synthetic cohort meets probabilistic boundary conditions."""

import json
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from src.models.cohort_params import CohortParameters, DEFAULT_COHORT_PARAMS
from src.models.cycle_utils import calculate_phase_from_lmp


@dataclass
class ValidationResult:
    """Result of a validation check."""
    metric: str
    expected: float
    observed: float
    tolerance: float
    passed: bool
    message: str


class CohortValidator:
    """Validates generated questionnaire responses against expected population parameters."""

    def __init__(self, params: CohortParameters = DEFAULT_COHORT_PARAMS):
        """Initialize validator with cohort parameters.

        Args:
            params: Expected population parameters
        """
        self.params = params
        self.responses: List[Dict] = []
        self.results: List[ValidationResult] = []

    def load_responses(self, output_dir: str = "output") -> int:
        """Load all JSON responses from output directory.

        Args:
            output_dir: Directory containing response JSON files

        Returns:
            Number of responses loaded
        """
        output_path = Path(output_dir)
        self.responses = []

        for json_file in output_path.glob("response-*.json"):
            with open(json_file, 'r') as f:
                self.responses.append(json.load(f))

        return len(self.responses)

    def _extract_answer(self, response: Dict, link_id: str) -> Any:
        """Extract answer value for a specific linkId from response.

        Args:
            response: FHIR QuestionnaireResponse resource
            link_id: Question identifier

        Returns:
            Answer value (type depends on question)
        """
        for item in response.get("item", []):
            if item.get("linkId") == link_id:
                answers = item.get("answer", [])
                if not answers:
                    return None

                answer = answers[0]

                # Return appropriate value type
                if "valueDecimal" in answer:
                    return answer["valueDecimal"]
                elif "valueInteger" in answer:
                    return answer["valueInteger"]
                elif "valueString" in answer:
                    return answer["valueString"]
                elif "valueDate" in answer:
                    return answer["valueDate"]
                elif "valueCoding" in answer:
                    return answer["valueCoding"].get("code")

        return None

    def _calculate_phase(self, response: Dict) -> str:
        """Calculate cycle phase from LMP date and authored date.

        Args:
            response: FHIR QuestionnaireResponse resource

        Returns:
            "follicular" or "luteal" or None if dates unavailable
        """
        lmp_str = self._extract_answer(response, "4")
        authored_str = response.get("authored")

        if not lmp_str or not authored_str:
            return None

        try:
            # Parse dates - LMP is date only (naive), authored has timezone
            lmp_date = datetime.fromisoformat(lmp_str)

            # Parse authored date and remove timezone info for comparison
            authored_date = datetime.fromisoformat(authored_str.replace('Z', '+00:00'))
            if authored_date.tzinfo is not None:
                authored_date = authored_date.replace(tzinfo=None)

            # Calculate phase
            return calculate_phase_from_lmp(lmp_date, authored_date)
        except (ValueError, AttributeError):
            return None

    def _check_metric(self, metric: str, expected: float, observed: float,
                     tolerance: float = 0.10) -> ValidationResult:
        """Check if observed metric is within tolerance of expected value.

        Args:
            metric: Metric name
            expected: Expected value
            observed: Observed value
            tolerance: Relative tolerance (default 10%)

        Returns:
            ValidationResult object
        """
        if expected == 0:
            abs_diff = abs(observed - expected)
            passed = abs_diff <= tolerance
            message = f"Absolute difference: {abs_diff:.3f} (tolerance: {tolerance})"
        else:
            rel_diff = abs(observed - expected) / expected
            passed = rel_diff <= tolerance
            message = f"Relative difference: {rel_diff:.1%} (tolerance: {tolerance:.1%})"

        return ValidationResult(
            metric=metric,
            expected=expected,
            observed=observed,
            tolerance=tolerance,
            passed=passed,
            message=message
        )

    def validate_cohort_size(self, expected_total: int = 187,
                            tolerance: float = 0.05) -> ValidationResult:
        """Validate total number of responses.

        Args:
            expected_total: Expected number of responses
            tolerance: Relative tolerance

        Returns:
            ValidationResult
        """
        observed = len(self.responses)
        result = self._check_metric("Total Responses", expected_total, observed, tolerance)
        self.results.append(result)
        return result

    def validate_age_distribution(self) -> List[ValidationResult]:
        """Validate age range and distribution."""
        ages = [self._extract_answer(r, "1") for r in self.responses]
        ages = [a for a in ages if a is not None]

        results = []

        # Check min age
        min_age = min(ages)
        result = self._check_metric("Minimum Age", self.params.age_range[0],
                                    min_age, tolerance=1.0)
        results.append(result)
        self.results.append(result)

        # Check max age
        max_age = max(ages)
        result = self._check_metric("Maximum Age", self.params.age_range[1],
                                    max_age, tolerance=1.0)
        results.append(result)
        self.results.append(result)

        # Check mean age
        mean_age = np.mean(ages)
        result = self._check_metric("Mean Age", self.params.age_mean,
                                    mean_age, tolerance=0.10)
        results.append(result)
        self.results.append(result)

        return results

    def validate_insulin_delivery_ratio(self) -> ValidationResult:
        """Validate pump vs injection distribution."""
        delivery_methods = [self._extract_answer(r, "3") for r in self.responses]
        delivery_methods = [d for d in delivery_methods if d is not None]

        pump_count = sum(1 for d in delivery_methods if d == "Insulin Pump")
        observed_ratio = pump_count / len(delivery_methods)

        result = self._check_metric("Pump Usage Ratio", self.params.pump_ratio,
                                    observed_ratio, tolerance=0.10)
        self.results.append(result)
        return result

    def validate_cycle_regularity_distribution(self) -> List[ValidationResult]:
        """Validate menstrual cycle regularity distribution."""
        regularities = [self._extract_answer(r, "5") for r in self.responses]
        regularities = [r for r in regularities if r is not None]

        total = len(regularities)
        results = []

        # Very regular
        very_regular_count = sum(1 for r in regularities if "Very regular" in r)
        observed_ratio = very_regular_count / total
        result = self._check_metric("Very Regular Ratio",
                                    self.params.very_regular_ratio,
                                    observed_ratio, tolerance=0.15)
        results.append(result)
        self.results.append(result)

        # Somewhat regular
        somewhat_count = sum(1 for r in regularities if "Somewhat regular" in r)
        observed_ratio = somewhat_count / total
        result = self._check_metric("Somewhat Regular Ratio",
                                    self.params.somewhat_regular_ratio,
                                    observed_ratio, tolerance=0.15)
        results.append(result)
        self.results.append(result)

        # Irregular
        irregular_count = sum(1 for r in regularities if "Irregular" in r)
        observed_ratio = irregular_count / total
        result = self._check_metric("Irregular Ratio",
                                    self.params.irregular_ratio,
                                    observed_ratio, tolerance=0.15)
        results.append(result)
        self.results.append(result)

        return results

    def validate_phase_distribution(self) -> ValidationResult:
        """Validate follicular vs luteal phase balance."""
        phases = [self._calculate_phase(r) for r in self.responses]
        phases = [p for p in phases if p is not None]

        follicular_count = sum(1 for p in phases if p == "follicular")
        observed_ratio = follicular_count / len(phases)

        # Should be approximately 50/50
        result = self._check_metric("Follicular Phase Ratio", 0.50,
                                    observed_ratio, tolerance=0.10)
        self.results.append(result)
        return result

    def validate_follicular_glucose(self) -> ValidationResult:
        """Validate mean nighttime glucose in follicular phase."""
        follicular_responses = [
            r for r in self.responses
            if self._calculate_phase(r) == "follicular"
        ]

        glucose_values = [self._extract_answer(r, "7") for r in follicular_responses]
        glucose_values = [g for g in glucose_values if g is not None]

        mean_glucose = np.mean(glucose_values)
        result = self._check_metric("Follicular Mean Glucose (mg/dL)",
                                    self.params.glucose_follicular_mean,
                                    mean_glucose, tolerance=0.10)
        self.results.append(result)
        return result

    def validate_luteal_glucose(self) -> ValidationResult:
        """Validate mean nighttime glucose in luteal phase."""
        luteal_responses = [
            r for r in self.responses
            if self._calculate_phase(r) == "luteal"
        ]

        glucose_values = [self._extract_answer(r, "7") for r in luteal_responses]
        glucose_values = [g for g in glucose_values if g is not None]

        mean_glucose = np.mean(glucose_values)
        expected_glucose = (self.params.glucose_follicular_mean +
                           self.params.luteal_glucose_increase)

        result = self._check_metric("Luteal Mean Glucose (mg/dL)",
                                    expected_glucose, mean_glucose, tolerance=0.10)
        self.results.append(result)
        return result

    def validate_follicular_basal_insulin(self) -> ValidationResult:
        """Validate mean basal insulin in follicular phase."""
        follicular_responses = [
            r for r in self.responses
            if self._calculate_phase(r) == "follicular"
        ]

        basal_values = [self._extract_answer(r, "6") for r in follicular_responses]
        basal_values = [b for b in basal_values if b is not None]

        mean_basal = np.mean(basal_values)
        result = self._check_metric("Follicular Mean Basal Insulin (units)",
                                    self.params.basal_insulin_mean,
                                    mean_basal, tolerance=0.10)
        self.results.append(result)
        return result

    def validate_luteal_basal_insulin(self) -> ValidationResult:
        """Validate mean basal insulin in luteal phase."""
        luteal_responses = [
            r for r in self.responses
            if self._calculate_phase(r) == "luteal"
        ]

        basal_values = [self._extract_answer(r, "6") for r in luteal_responses]
        basal_values = [b for b in basal_values if b is not None]

        mean_basal = np.mean(basal_values)
        expected_basal = (self.params.basal_insulin_mean *
                         (1 + self.params.luteal_insulin_increase))

        result = self._check_metric("Luteal Mean Basal Insulin (units)",
                                    expected_basal, mean_basal, tolerance=0.10)
        self.results.append(result)
        return result

    def validate_follicular_sleep_awakenings(self) -> ValidationResult:
        """Validate mean sleep awakenings in follicular phase."""
        follicular_responses = [
            r for r in self.responses
            if self._calculate_phase(r) == "follicular"
        ]

        awakenings = [self._extract_answer(r, "8") for r in follicular_responses]
        awakenings = [a for a in awakenings if a is not None]

        mean_awakenings = np.mean(awakenings)
        result = self._check_metric("Follicular Mean Awakenings",
                                    self.params.awakenings_follicular_mean,
                                    mean_awakenings, tolerance=0.15)
        self.results.append(result)
        return result

    def validate_luteal_sleep_awakenings(self) -> ValidationResult:
        """Validate mean sleep awakenings in luteal phase."""
        luteal_responses = [
            r for r in self.responses
            if self._calculate_phase(r) == "luteal"
        ]

        awakenings = [self._extract_answer(r, "8") for r in luteal_responses]
        awakenings = [a for a in awakenings if a is not None]

        mean_awakenings = np.mean(awakenings)
        expected_awakenings = (self.params.awakenings_follicular_mean +
                              self.params.luteal_awakenings_increase)

        result = self._check_metric("Luteal Mean Awakenings",
                                    expected_awakenings, mean_awakenings,
                                    tolerance=0.15)
        self.results.append(result)
        return result

    def validate_follicular_symptoms(self) -> List[ValidationResult]:
        """Validate symptom rates in follicular phase."""
        follicular_responses = [
            r for r in self.responses
            if self._calculate_phase(r) == "follicular"
        ]

        total = len(follicular_responses)
        results = []

        # Night sweats
        night_sweats_count = sum(
            1 for r in follicular_responses
            if "Night sweats" in str(self._extract_answer(r, "9"))
        )
        observed_rate = night_sweats_count / total
        result = self._check_metric("Follicular Night Sweats Rate",
                                    self.params.night_sweats_prob_follicular,
                                    observed_rate, tolerance=0.25)
        results.append(result)
        self.results.append(result)

        # Palpitations
        palpitations_count = sum(
            1 for r in follicular_responses
            if "Palpitations" in str(self._extract_answer(r, "9"))
        )
        observed_rate = palpitations_count / total
        result = self._check_metric("Follicular Palpitations Rate",
                                    self.params.palpitations_prob_follicular,
                                    observed_rate, tolerance=0.30)
        results.append(result)
        self.results.append(result)

        # Dizziness
        dizziness_count = sum(
            1 for r in follicular_responses
            if "Dizziness" in str(self._extract_answer(r, "9"))
        )
        observed_rate = dizziness_count / total
        result = self._check_metric("Follicular Dizziness Rate",
                                    self.params.dizziness_prob_follicular,
                                    observed_rate, tolerance=0.30)
        results.append(result)
        self.results.append(result)

        return results

    def validate_luteal_symptoms(self) -> List[ValidationResult]:
        """Validate symptom rates in luteal phase."""
        luteal_responses = [
            r for r in self.responses
            if self._calculate_phase(r) == "luteal"
        ]

        total = len(luteal_responses)
        results = []

        # Night sweats
        night_sweats_count = sum(
            1 for r in luteal_responses
            if "Night sweats" in str(self._extract_answer(r, "9"))
        )
        observed_rate = night_sweats_count / total
        result = self._check_metric("Luteal Night Sweats Rate",
                                    self.params.night_sweats_prob_luteal,
                                    observed_rate, tolerance=0.20)
        results.append(result)
        self.results.append(result)

        # Palpitations
        palpitations_count = sum(
            1 for r in luteal_responses
            if "Palpitations" in str(self._extract_answer(r, "9"))
        )
        observed_rate = palpitations_count / total
        result = self._check_metric("Luteal Palpitations Rate",
                                    self.params.palpitations_prob_luteal,
                                    observed_rate, tolerance=0.25)
        results.append(result)
        self.results.append(result)

        # Dizziness
        dizziness_count = sum(
            1 for r in luteal_responses
            if "Dizziness" in str(self._extract_answer(r, "9"))
        )
        observed_rate = dizziness_count / total
        result = self._check_metric("Luteal Dizziness Rate",
                                    self.params.dizziness_prob_luteal,
                                    observed_rate, tolerance=0.25)
        results.append(result)
        self.results.append(result)

        return results

    def validate_intervention_subgroup_size(self, expected_count: int = 64) -> ValidationResult:
        """Validate number of patients in intervention subgroup.

        Note: Requires analysis of subjective text in linkId=10 to identify intervention patients.
        The text should contain phrases like "cycle-aware" or "adjusted my basal".

        Args:
            expected_count: Expected number of intervention patients

        Returns:
            ValidationResult
        """
        intervention_keywords = [
            "cycle-aware",
            "adjusted my basal",
            "cycle tracking",
            "menstrual phase",
            "reduced my basal"
        ]

        intervention_count = 0
        for response in self.responses:
            text = self._extract_answer(response, "10")
            if text and any(keyword.lower() in text.lower() for keyword in intervention_keywords):
                intervention_count += 1

        result = self._check_metric("Intervention Subgroup Size",
                                    expected_count, intervention_count,
                                    tolerance=0.10)
        self.results.append(result)
        return result

    def validate_intervention_glucose_improvement(self) -> ValidationResult:
        """Validate that intervention patients show improved glucose in luteal phase.

        Intervention patients should show ~90% reduction in luteal glucose increase
        (mean glucose increase should be ~0.8 mg/dL instead of 8.1 mg/dL).
        """
        # Identify intervention patients
        intervention_keywords = [
            "cycle-aware",
            "adjusted my basal",
            "cycle tracking",
            "menstrual phase",
            "reduced my basal"
        ]

        # Get luteal responses for intervention vs non-intervention
        intervention_luteal = []
        non_intervention_luteal = []

        for response in self.responses:
            phase = self._calculate_phase(response)
            if phase != "luteal":
                continue

            text = self._extract_answer(response, "10")
            is_intervention = text and any(
                keyword.lower() in text.lower()
                for keyword in intervention_keywords
            )

            glucose = self._extract_answer(response, "7")
            if glucose is not None:
                if is_intervention:
                    intervention_luteal.append(glucose)
                else:
                    non_intervention_luteal.append(glucose)

        if not intervention_luteal or not non_intervention_luteal:
            return ValidationResult(
                metric="Intervention Glucose Improvement",
                expected=0.0,
                observed=0.0,
                tolerance=0.0,
                passed=False,
                message="Insufficient data to validate intervention effect"
            )

        # Calculate difference from follicular baseline
        follicular_mean = self.params.glucose_follicular_mean
        intervention_mean = np.mean(intervention_luteal)
        intervention_increase = intervention_mean - follicular_mean

        # Expected: ~90% reduction means ~0.8 mg/dL increase (10% of 8.1)
        expected_increase = self.params.luteal_glucose_increase * 0.1

        result = self._check_metric(
            "Intervention Luteal Glucose Increase (mg/dL)",
            expected_increase,
            intervention_increase,
            tolerance=0.30
        )
        self.results.append(result)
        return result

    def validate_all(self, output_dir: str = "output",
                    expected_intervention_count: int = 64) -> Tuple[int, int]:
        """Run all validation checks.

        Args:
            output_dir: Directory containing response JSON files
            expected_intervention_count: Expected number of intervention patients

        Returns:
            Tuple of (passed_count, total_count)
        """
        self.results = []

        # Load responses
        count = self.load_responses(output_dir)
        if count == 0:
            raise ValueError(f"No responses found in {output_dir}")

        # Run all validations
        self.validate_cohort_size()
        self.validate_age_distribution()
        self.validate_insulin_delivery_ratio()
        self.validate_cycle_regularity_distribution()
        self.validate_phase_distribution()

        self.validate_follicular_glucose()
        self.validate_luteal_glucose()
        self.validate_follicular_basal_insulin()
        self.validate_luteal_basal_insulin()
        self.validate_follicular_sleep_awakenings()
        self.validate_luteal_sleep_awakenings()

        self.validate_follicular_symptoms()
        self.validate_luteal_symptoms()

        # Intervention subgroup validations
        self.validate_intervention_subgroup_size(expected_intervention_count)
        self.validate_intervention_glucose_improvement()

        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)

        return passed, total

    def print_report(self, verbose: bool = False):
        """Print validation report.

        Args:
            verbose: If True, show all checks; if False, only show failures
        """
        if not self.results:
            print("No validation results. Run validate_all() first.")
            return

        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)

        print(f"\n{'='*80}")
        print(f"COHORT VALIDATION REPORT")
        print(f"{'='*80}")
        print(f"Responses analyzed: {len(self.responses)}")
        print(f"Checks passed: {passed}/{total} ({passed/total*100:.1f}%)")
        print(f"{'='*80}\n")

        # Group results by category
        categories = {
            "Demographics": ["Total Responses", "Minimum Age", "Maximum Age", "Mean Age"],
            "Insulin Delivery": ["Pump Usage Ratio"],
            "Cycle Characteristics": ["Very Regular Ratio", "Somewhat Regular Ratio",
                                     "Irregular Ratio", "Follicular Phase Ratio"],
            "Follicular Phase - Glucose & Insulin": [
                "Follicular Mean Glucose (mg/dL)",
                "Follicular Mean Basal Insulin (units)"
            ],
            "Luteal Phase - Glucose & Insulin": [
                "Luteal Mean Glucose (mg/dL)",
                "Luteal Mean Basal Insulin (units)"
            ],
            "Sleep Quality": [
                "Follicular Mean Awakenings",
                "Luteal Mean Awakenings"
            ],
            "Follicular Phase - Symptoms": [
                "Follicular Night Sweats Rate",
                "Follicular Palpitations Rate",
                "Follicular Dizziness Rate"
            ],
            "Luteal Phase - Symptoms": [
                "Luteal Night Sweats Rate",
                "Luteal Palpitations Rate",
                "Luteal Dizziness Rate"
            ],
            "Intervention Subgroup": [
                "Intervention Subgroup Size",
                "Intervention Luteal Glucose Increase (mg/dL)"
            ]
        }

        for category, metrics in categories.items():
            category_results = [r for r in self.results if r.metric in metrics]
            if not category_results:
                continue

            print(f"{category}:")
            print("-" * 80)

            for result in category_results:
                if verbose or not result.passed:
                    status = "✓ PASS" if result.passed else "✗ FAIL"
                    print(f"  [{status}] {result.metric}")
                    print(f"          Expected: {result.expected:.3f}")
                    print(f"          Observed: {result.observed:.3f}")
                    print(f"          {result.message}")
                    print()

            if not verbose:
                passed_in_category = sum(1 for r in category_results if r.passed)
                if passed_in_category > 0:
                    print(f"  [✓] {passed_in_category} check(s) passed (hidden)")
                    print()

        print(f"{'='*80}")