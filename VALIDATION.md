# Cohort Validation

This document explains how to use the validation functions to verify that generated questionnaire responses meet the expected probabilistic boundary conditions.

## Overview

The validation system performs **probabilistic boundary validation** on the generated synthetic cohort to ensure statistical fidelity to predefined population parameters. It compares observed distributions against expected values with configurable tolerance thresholds, accounting for Monte Carlo sampling variability expected from stochastic generation with finite sample sizes (n≈187).

The validator checks that synthetic data matches the population parameters defined in `CLAUDE.md`:

- **Demographics**: Cohort size (187), age distribution (18-45, mean ~31.5)
- **Insulin delivery**: Pump vs injection ratio (~65%/35%)
- **Cycle characteristics**: Regularity distribution, phase balance
- **Physiological patterns by phase**:
  - Follicular: Glucose ~118 mg/dL, basal insulin ~14.0 units
  - Luteal: Glucose ~126 mg/dL (+8.1), basal insulin ~16.0 units (+14%)
- **Sleep quality**: Awakenings by phase
- **Symptom rates**: Night sweats, palpitations, dizziness by phase
- **Intervention subgroup**: Size (64 patients), glucose improvement (~90% reduction)

## Generation Rules

The synthetic data generator (`patient_generator.py` & `cohort_params.py`) uses the following statistical rules:

### 1. Demographics
- **Age**: Normal distribution N(μ=31.5, σ=7.0), truncated to [18, 45]
- **Years since T1D diagnosis**: Normal distribution N(μ=12.0, σ=8.0), bounded by [1, min(age-1, 30)]

### 2. Insulin Delivery Method
- Bernoulli trial with p=0.65 for pump, p=0.35 for injections
- Stable per patient (doesn't change across observations)

### 3. Menstrual Cycle Regularity
- Categorical distribution: Very regular (55%), Somewhat regular (30%), Irregular (15%)
- Stable per patient

### 4. Cycle Phase Assignment
- Last Menstrual Period (LMP) date calculated backwards from observation date:
  - **Follicular phase** (days 1-14): LMP was 0-13 days ago
  - **Luteal phase** (days 15-28): LMP was 14-27 days ago

### 5. Physiological Parameters (Phase-Dependent)

**Basal Insulin (units/night):**
- Follicular baseline: N(μ=14.0, σ=3.5), bounded [5.0, 30.0]
- Luteal (non-intervention): baseline × 1.14 (+14% increase)
- Luteal (intervention): baseline × (1 - U[0.10, 0.20]) (10-20% reduction)
- Small observation noise: N(0, 0.5)

**Nighttime Glucose (mg/dL, 00:00-06:00):**
- Follicular: N(μ=118.0, σ=20.0)
- Luteal (non-intervention): N(μ=126.1, σ=20.0) (+8.1 mg/dL additive shift)
- Luteal (intervention): N(μ=118.81, σ=20.0) (only +0.81 mg/dL, i.e., 10% of the increase)

**Sleep Awakenings:**
- Follicular: N(μ=0.8, σ=0.6), truncated at 0
- Luteal: N(μ=1.4, σ=0.6) (+0.6 awakenings)

**Nocturnal Symptoms (Bernoulli trials):**

| Symptom | Follicular p | Luteal p |
|---------|-------------|----------|
| Night sweats | 0.12 | 0.22 |
| Dizziness | 0.04 | 0.09 |
| Palpitations | 0.05 | 0.11 |
| Fatigue | 0.18 | 0.25 |

## Usage

### Basic Validation

```bash
# Activate virtual environment
source venv/bin/activate

# Validate default output directory
python -m src.validate

# Validate specific directory
python -m src.validate -o output
```

### Verbose Mode

Show all validation checks (not just failures):

```bash
python -m src.validate -v
```

### Custom Intervention Count

If you generated data with a different intervention count:

```bash
python -m src.validate -i 64
```

### Exit Codes

- **0**: All checks passed (or `--no-fail` flag used)
- **1**: One or more checks failed

```bash
# Don't exit with error on failures (useful for CI)
python -m src.validate --no-fail
```

## Interpreting Results

### Sample Output

```
================================================================================
COHORT VALIDATION REPORT
================================================================================
Responses analyzed: 187
Checks passed: 16/22 (72.7%)
================================================================================

Demographics:
--------------------------------------------------------------------------------
  [✓] 4 check(s) passed (hidden)

Luteal Phase - Symptoms:
--------------------------------------------------------------------------------
  [✗ FAIL] Luteal Palpitations Rate
          Expected: 0.110
          Observed: 0.076
          Relative difference: 30.8% (tolerance: 25.0%)
```

### Tolerance Levels

Each metric has an appropriate tolerance based on expected variance:

- **Counts/ratios**: ±5-15% (e.g., cohort size, phase distribution)
- **Mean values**: ±10% (e.g., glucose, insulin)
- **Low-probability events**: ±25-30% (e.g., rare symptoms)

### Common Validation Issues

1. **Small cohort sizes**: With <100 responses, random variance may cause failures
2. **Symptom rates**: Low-probability events (5-15%) show high variance with small samples
3. **Intervention detection**: Requires meaningful text in linkId=10 (currently placeholder)

## Programmatic Usage

You can also use the validator in your own Python scripts:

```python
from src.validators.cohort_validator import CohortValidator
from src.models.cohort_params import DEFAULT_COHORT_PARAMS

# Initialize validator
validator = CohortValidator(params=DEFAULT_COHORT_PARAMS)

# Run all validations
passed, total = validator.validate_all(
    output_dir="output",
    expected_intervention_count=64
)

# Print report
validator.print_report(verbose=True)

# Access individual results
for result in validator.results:
    print(f"{result.metric}: {'PASS' if result.passed else 'FAIL'}")
    print(f"  Expected: {result.expected:.3f}")
    print(f"  Observed: {result.observed:.3f}")
```

## Validation Checks

The validator (`cohort_validator.py`) performs the following checks:

### 1. Structural Validation
- **Total response count** (default expected: 187, tolerance: 5%)

### 2. Demographics (3 checks)
- Min/max age within [18, 45] (absolute tolerance: ±1 year)
- Mean age within 10% of 31.5

### 3. Categorical Distributions (4 checks)
- Pump ratio within 10% of 0.65
- Cycle regularity ratios within 15% of [0.55, 0.30, 0.15]
- Phase balance (follicular:luteal) within 10% of 0.50

### 4. Follicular Phase Parameters (6 checks)
- Mean glucose within 10% of 118.0 mg/dL
- Mean basal insulin within 10% of 14.0 units
- Mean awakenings within 15% of 0.8
- Night sweats rate within 25% tolerance
- Palpitations rate within 30% tolerance
- Dizziness rate within 30% tolerance

### 5. Luteal Phase Parameters (6 checks)
- Mean glucose within 10% of 126.1 mg/dL (118.0 + 8.1)
- Mean basal insulin within 10% of 15.96 units (14.0 × 1.14)
- Mean awakenings within 15% of 1.4 (0.8 + 0.6)
- Night sweats rate within 20% tolerance
- Palpitations rate within 25% tolerance
- Dizziness rate within 25% tolerance

### 6. Intervention Subgroup (2 checks)
- **Size**: Keyword-based detection in subjective text (linkId=10) for "cycle-aware", "adjusted my basal", etc.
  - Expected: 64 patients (tolerance: 10%)
- **Efficacy**: Intervention patients in luteal phase should show glucose increase of ~0.81 mg/dL (vs 8.1 baseline)
  - Tolerance: 30% (due to smaller sample size)

## Tolerance Strategy

The validator uses **relative tolerance** (percentage of expected value) except for:
- **Absolute bounds**: Age range (±1 year)
- **Low-probability events**: Symptom rates have higher tolerance (25-30%) due to binomial variance with small sample sizes
- **Intervention effects**: 30% tolerance due to smaller subgroup sample size (n=64)

The tolerance bands account for Monte Carlo sampling variability expected from stochastic generation with finite sample sizes.

## Notes

- **Phase calculation**: Automatically calculated from LMP date (linkId=4) and authored date
- **Intervention detection**: Currently detects keywords in linkId=10 text (requires Phase 2 implementation)
- **Random seed**: Use the same seed in generation to get reproducible validation results