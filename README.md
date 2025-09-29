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

Generate synthetic questionnaire responses with multiple observations per patient:

```bash
# Activate virtual environment
source venv/bin/activate

# Small test (10 patients, 40 observations)
python -m src.main -p 10 -obs 4

# Full demo cohort (187 patients, 748 observations, 64 intervention)
python -m src.main -p 187 -obs 4 -i 64
```

**CLI Options:**
- `-p, --num-patients` - Number of unique patients (default: 10, target: 187)
- `-obs, --observations-per-patient` - Observations per patient (default: 4)
- `-i, --intervention-count` - Patients in intervention group (default: 34% of patients)
- `-o, --output-dir` - Output directory (default: output/)
- `--seed` - Random seed for reproducibility (default: 42)
- `--no-clean` - Don't delete existing output files

**Key Features:**
- **Longitudinal data**: Each patient has multiple survey responses at different cycle phases
- **Phase-aware generation**: Follicular vs luteal differences in glucose, insulin, symptoms
- **Intervention subgroup**: 64 patients with cycle-aware adjustments show improved outcomes
- **Stable characteristics**: Same patient maintains consistent demographics across observations

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