# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository is a synthetic data generation project for the Welshare Health Profile Matching Platform (HPMP) demo. The project validates the hypothesis that women with Type 1 Diabetes (T1D) experience measurable changes in glucose and insulin needs during the luteal phase of their menstrual cycle, and that cycle-aware dosing can improve glucose stability.

### Core Objective

Create a suite of scripts that synthesize realistic FHIR QuestionnaireResponse resources matching the structure defined in `sample-questionnaire.json`. The synthetic data will simulate responses from a cohort of 187 women with T1D, demonstrating the integration of cycle tracking data (Flo App) with diabetes management data (DiabetesDAO) through Welshare's HPMP platform.

### Research Hypothesis (HYP-MC-01)

Women with T1D show measurable rise in glucose and insulin needs during the luteal phase. Without cycle-aware dosing, this produces periods of hyperglycemia and occasional overnight crashes from over-correction. Cycle-aware recommendations improve stability.

## Data Structure

The project centers around a FHIR Questionnaire resource (`sample-questionnaire.json`) that captures:
- Patient demographics (age 18-45, years since T1D diagnosis)
- Insulin management details (delivery method: 65% pump, 35% injections; basal doses)
- Menstrual cycle characteristics (regularity, last menstrual period, phase)
- Nighttime glucose patterns (CGM data 00:00-06:00)
- Sleep quality (awakenings, symptoms)
- Subjective experiences of glucose stability across menstrual phases

The questionnaire uses standardized LOINC codes for medical terminology and follows FHIR R4 specifications for healthcare data interoperability.

## Synthetic Population Parameters

### Cohort Demographics
- **Total profiles:** 187 matched users
- **Age range:** 18-45 years (reproductive age)
- **Insulin delivery:**
  - 120 pump users (~65%)
  - 67 injection users (~35%)
- **Cycle tracking:** At least 2 complete cycles logged per user
- **Data points:** ~350 follicular + ~350 luteal phase observations

### Expected Physiological Patterns

**Follicular Phase (Baseline):**
- Mean nighttime glucose: ~118 mg/dL
- Time in Range (TIR 70-180): ~75%
- Average basal insulin: 14.0 units/night
- Sleep awakenings: 0.8 per night
- Symptom rates: Night sweats 12%, Palpitations 5%, Dizziness 4%

**Luteal Phase (Elevated Insulin Resistance):**
- Mean nighttime glucose: ~126 mg/dL (+8.1 mg/dL)
- Time in Range: ~68% (-6.4 percentage points)
- Average basal insulin: 16.0 units/night (+14% increase)
- Glucose variability (CV): +3.2 percentage points
- Sleep awakenings: 1.4 per night
- Symptom rates: Night sweats 22%, Palpitations 11%, Dizziness 9%

**Intervention Subgroup (64 users):**
- Applied cycle-aware basal adjustment (-10-20% on flagged nights)
- Results: TIR ↑ +7.8%, Mean glucose ↓ -7.3 mg/dL, Hypo rate unchanged

## Implementation Status

### Phase 1: Basic Data Generation ✓ COMPLETE

**Architecture:**
- `src/models/cohort_params.py` - Population parameters and statistical distributions
- `src/models/cycle_utils.py` - Menstrual cycle phase calculations
- `src/generators/patient_generator.py` - Demographics and physiological data generation
- `src/generators/response_builder.py` - FHIR QuestionnaireResponse assembly
- `src/main.py` - CLI entry point

**Current Capabilities:**
- ✅ Generates FHIR R4-compliant QuestionnaireResponse resources
- ✅ **Multiple observations per patient** simulating longitudinal survey data
- ✅ **Cycle phase-aware generation** - follicular vs luteal patterns
- ✅ **Intervention subgroup** (64 patients with cycle-aware basal adjustment)
- ✅ **Per-patient stable characteristics** (age, diagnosis, delivery method persist)
- ✅ **Phase-specific LMP dates** that correctly calculate to target phase
- ✅ **Physiological differences by phase:**
  - Luteal: +8.1 mg/dL glucose, +14% insulin, +symptom rates
  - Intervention: -90% of luteal glucose increase, -10-20% basal dose
- ✅ Reproducible generation via random seed (default: 42)
- ✅ Automatic output directory management

**Usage:**
```bash
source venv/bin/activate

# ONE-PER-PATIENT MODE (Cross-sectional, RECOMMENDED)
# 187 patients = 187 responses, each in random phase
python -m src.main -p 187 -i 64 --one-per-patient

# Test with smaller cohort
python -m src.main -p 20 --one-per-patient

# LONGITUDINAL MODE (Multiple observations per patient)
# 187 patients × 4 observations = 748 responses
python -m src.main -p 187 -obs 4 -i 64

# Options:
#   -p, --num-patients           Number of unique patients (default: 10)
#   -obs, --observations-per-patient  Observations per patient (default: 4)
#   -i, --intervention-count     Patients in intervention group (default: 34% of patients)
#   --one-per-patient            Generate 1 response per patient (cross-sectional)
#   -o, --output-dir             Output directory (default: output/)
#   --seed                       Random seed (default: 42)
#   --no-clean                   Don't delete existing output files
```

**Outputs:**

**One-per-patient mode (cross-sectional):**
- Files: `output/response-patient-NNNN.json`
- 187 unique patients = **187 total responses**
- Balanced: ~93 follicular + ~94 luteal phase observations
- Each patient appears once, randomly assigned to a cycle phase
- Hypothesis tested via between-patient comparison (follicular group vs luteal group)

**Longitudinal mode:**
- Files: `output/response-patient-NNNN-obs-NNNN.json`
- 187 unique patients × 4 observations = **748 total responses**
- Balanced: ~374 follicular + ~374 luteal phase observations
- Same patient appears in multiple files with consistent demographics
- Hypothesis tested via within-patient comparison (repeated measures)

**All outputs:**
- FHIR R4-compliant with proper resourceType, status, authored timestamp
- All 10 questionnaire items populated with realistic values
- LMP dates correctly calculate to assigned cycle phase
- 64 patients (34%) in intervention subgroup showing improved luteal outcomes
- Basal insulin and glucose vary by cycle phase and intervention status

### Phase 2: Advanced Features (UPCOMING)

**Subjective Text Generation:**
- Replace placeholder text in linkId=10 with realistic patient narratives
- Vary descriptions based on cycle regularity and symptom patterns
- Include intervention-aware language for subgroup patients

### Phase 3: Validation & Analytics ✓ COMPLETE

**Statistical Validation:**
- ✅ Aggregate statistics verification script (`src/validate.py`)
- ✅ 22 validation checks against expected population parameters
- ✅ Detailed reporting with pass/fail status and deviations

**Adaptive Generation System:**
- ✅ Two-pass generation: 60% free sampling, 40% adaptive correction
- ✅ Real-time cohort tracking with `CohortTracker` class
- ✅ Automatic correction factor calculation for deviations
- ✅ 77.3% validation pass rate (17/22 checks) with seed 777
- ✅ Deterministic and reproducible with seed control

**FHIR Compliance:**
- ✅ Generated resources validate against FHIR R4 specification
- ✅ LOINC codes properly structured
- ✅ All required fields populated

**Demo Integration:**
- ✅ Intervention subgroup marked in subjective text for matching
- Privacy-preserving aggregation (k-anonymity ≥15) - Future
- Visualization data preparation (charts, graphs) - Future

## Key Learnings: Adaptive Synthetic Data Generation

### Challenge: Aggregate Boundary Constraints
**Problem:** Independent random sampling from distributions rarely meets aggregate statistical boundaries. With n=187, natural sampling variance caused 0% validation pass rates - cohorts never satisfied all tolerance bands simultaneously.

**Root Cause:**
- Sampling variance scales with √n
- 22 independent checks compound failure probability
- Integer-rounded metrics (awakenings) have high relative variance
- Low-probability events (<10%) have high binomial variance

### Solution: Two-Pass Cohort-Aware Generation

**Architecture Pattern:**
```
60% Free Sampling → Checkpoint → Calculate Deviations → 40% Corrective Sampling
```

**Key Components:**
1. **CohortTracker** (`src/generators/cohort_tracker.py`)
   - Tracks 20+ running statistics during generation
   - Calculates correction factors when deviations exceed thresholds
   - Returns dict of adjustments: shifts, multipliers, biases

2. **Enhanced Generators** (`src/generators/patient_generator.py`)
   - All methods accept optional correction parameters
   - Continuous metrics: additive shifts (e.g., `mean + shift`)
   - Discrete metrics: probability multipliers (e.g., `prob * 3.5`)
   - Categorical: preference biases (e.g., `prefer_pump=True`)

3. **Checkpoint Reporting** (`src/main.py`)
   - At 60% mark: print current stats vs targets
   - Show active corrections being applied
   - Store in memory to avoid I/O during generation

**Correction Strengths:**
- Phase balance: 2.5-3.0× probability bias (critical for 50/50 split)
- Symptom rates: 3.5-4.0× probability multipliers (overcome binomial variance)
- Continuous metrics: 0.7-2.0× gap closure (depends on remaining samples)
- Integer metrics: 2.0× shifts (account for rounding effects)

### Results & Insights

**Validation Performance:**
- **Before:** 0% pass rate (0/22 checks)
- **After:** 77.3% pass rate (17/22 checks) with seed 777
- **Typical:** 68-77% across random seeds

**Metrics Successfully Controlled:**
- ✅ Phase balance (50/50 follicular/luteal)
- ✅ Continuous means (glucose, insulin, age)
- ✅ Probability distributions (delivery method, cycle regularity)
- ✅ Medium-probability symptoms (12-22%)

**Inherently Difficult Metrics:**
- ⚠️ Integer-rounded low means (awakenings: 0.8, 1.4)
  - Relative tolerance: 15% = ±0.12 absolute
  - Correction headroom too small with n=187
- ⚠️ Low-probability symptoms (<10%)
  - n=87 luteal patients × 9% = expected 8 events
  - Binomial SD = 2.6 events = 30% relative variance
  - Exceeds 25% tolerance naturally

**Practical Recommendations:**
1. Use seed search (5-10 seeds) for critical metric requirements
2. Relax tolerances for low-mean integer metrics (15%→25%)
3. Relax tolerances for low-probability events (<10%): 25%→35%
4. With these adjustments: **95%+ pass rates achievable**

### Implementation Patterns for Future Reference

**When to use adaptive generation:**
- Sample size < 500 and multiple aggregate constraints
- Tight tolerance bands (10-20% relative)
- Mix of continuous and discrete metrics
- Integer-rounded metrics with low means

**Key design decisions:**
- **60/40 split** - Balances natural variation with correction power
- **Memory buffering** - Avoid I/O overhead during generation
- **Phase-specific corrections** - Track follicular/luteal separately
- **Threshold-based activation** - Only correct when deviation > threshold
- **Multiplier strength** - Higher for low-probability events (3.5-4.0×)

**Alternative considered (rejected):**
- Post-generation iterative refinement - Slower, requires file I/O, harder to reason about
- Acceptance sampling - Too many rejections with tight multi-dimensional constraints
- Constraint satisfaction - Over-constrains, loses natural variance

### Command Reference

```bash
# Generate with best seed
python -m src.main -p 187 -i 64 --one-per-patient --seed 777

# Validate with verbose output
python -m src.validate -i 64 -v

# Expected: 17/22 checks passing (77.3%)
```