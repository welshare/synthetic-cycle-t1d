# Cohort Validation

This document explains how to use the validation functions to verify that generated questionnaire responses meet the expected probabilistic boundary conditions.

## Overview

The validation system checks that synthetic data matches the population parameters defined in `CLAUDE.md`:

- **Demographics**: Cohort size (187), age distribution (18-45, mean ~31.5)
- **Insulin delivery**: Pump vs injection ratio (~65%/35%)
- **Cycle characteristics**: Regularity distribution, phase balance
- **Physiological patterns by phase**:
  - Follicular: Glucose ~118 mg/dL, basal insulin ~14.0 units
  - Luteal: Glucose ~126 mg/dL (+8.1), basal insulin ~16.0 units (+14%)
- **Sleep quality**: Awakenings by phase
- **Symptom rates**: Night sweats, palpitations, dizziness by phase
- **Intervention subgroup**: Size (64 patients), glucose improvement (~90% reduction)

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

### Demographics (4 checks)
- Total response count
- Age range (min/max)
- Mean age

### Insulin Delivery (1 check)
- Pump vs injection ratio

### Cycle Characteristics (4 checks)
- Very regular ratio
- Somewhat regular ratio
- Irregular ratio
- Follicular vs luteal phase balance

### Follicular Phase (5 checks)
- Mean glucose
- Mean basal insulin
- Mean sleep awakenings
- Night sweats rate
- Palpitations rate
- Dizziness rate

### Luteal Phase (5 checks)
- Mean glucose (expected increase)
- Mean basal insulin (expected increase)
- Mean sleep awakenings (expected increase)
- Night sweats rate (expected increase)
- Palpitations rate (expected increase)
- Dizziness rate (expected increase)

### Intervention Subgroup (2 checks)
- Intervention subgroup size
- Glucose improvement effect

## Notes

- **Phase calculation**: Automatically calculated from LMP date (linkId=4) and authored date
- **Intervention detection**: Currently detects keywords in linkId=10 text (requires Phase 2 implementation)
- **Random seed**: Use the same seed in generation to get reproducible validation results