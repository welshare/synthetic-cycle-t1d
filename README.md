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

*Coming soon: CLI commands for generating synthetic responses*

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