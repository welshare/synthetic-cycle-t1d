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

## Development Goals

### Phase 1: Data Generation Scripts
- Create synthetic QuestionnaireResponse generator
- Implement physiologically realistic variability
- Apply population-level statistical patterns from instructions.md
- Ensure FHIR R4 compliance and LOINC code accuracy

### Phase 2: Validation
- Verify aggregate statistics match expected patterns
- Ensure individual-level coherence (e.g., age-appropriate diagnosis duration)
- Validate cycle phase calculations from LMP dates

### Phase 3: Demo Integration
- Generate dataset suitable for HPMP demo visualization
- Support privacy-preserving aggregation (k-anonymity ≥15)
- Enable matching scenario between Flo + DiabetesDAO data sources