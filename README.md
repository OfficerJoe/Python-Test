# Python-Test

A basic Python project template with code scanning enabled.

## Project Structure

```
├── src/                  # Source code
│   └── calculator.py     # Sample module
├── tests/                # Test suite
│   └── test_calculator.py
├── pyproject.toml        # Project metadata and build config
└── .github/workflows/
    └── codeql.yml        # CodeQL code scanning on push to main
```

## Getting Started

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

## Code Scanning

CodeQL analysis runs automatically on every push and pull request targeting `main`.