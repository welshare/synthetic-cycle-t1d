# Synthetic Data Generation: T1D & Menstrual Cycle

Synthetic FHIR QuestionnaireResponse generator for the Welshare HPMP demo, simulating data from 187 women with Type 1 Diabetes to validate cycle-phase insulin variability.

## Setup

### Prerequisites
- Python 3.10+

### Installation

1. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Project Structure

```
src/
  generators/       # Data generation modules
  models/          # Population parameters and distributions
  validators/      # FHIR and statistical validation
  main.py          # CLI entry point
tests/             # Unit tests
output/            # Generated JSON responses
sample-questionnaire.json  # FHIR Questionnaire definition
```

## Usage

Generate synthetic questionnaire responses:

```bash
# Activate virtual environment
source venv/bin/activate

# RECOMMENDED: One response per patient (187 responses)
python -m src.main -p 187 -i 64 --one-per-patient

# Test with smaller cohort
python -m src.main -p 20 --one-per-patient

# Alternative: Longitudinal mode (748 responses, multiple per patient)
python -m src.main -p 187 -obs 4 -i 64
```

**CLI Options:**
- `-p, --num-patients` - Number of unique patients (default: 10, target: 187)
- `-obs, --observations-per-patient` - Observations per patient (default: 4, longitudinal mode)
- `-i, --intervention-count` - Patients in intervention group (default: 34% of patients)
- `--one-per-patient` - Generate 1 response per patient (cross-sectional design)
- `-o, --output-dir` - Output directory (default: output/)
- `--seed` - Random seed for reproducibility (default: 42)
- `--no-clean` - Don't delete existing output files

**Key Features:**
- **Cross-sectional mode** (`--one-per-patient`): 187 patients = 187 responses, each randomly in follicular or luteal phase
- **Longitudinal mode**: Each patient has multiple survey responses at different cycle phases
- **Phase-aware generation**: Follicular vs luteal differences in glucose, insulin, symptoms
- **Intervention subgroup**: 64 patients with cycle-aware adjustments show improved outcomes
- **Hypothesis demonstration**: Compare follicular vs luteal groups to validate cycle-phase insulin variability

## Development

Run tests:
```bash
pytest
```

Format code:
```bash
black src/ tests/
ruff check src/ tests/
```

## References

- See `CLAUDE.md` for project context
- See `instructions.md` for population parameters
- FHIR R4: https://hl7.org/fhir/R4/