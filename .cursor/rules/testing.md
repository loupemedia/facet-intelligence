# Testing Rules

Reference: `docs/ENGINEERING_PRINCIPLES.md` → Testing Philosophy

## Mandatory Test Creation

When creating or modifying any Python function that handles:

- Scoring or ranking algorithms
- Data transformation where the output feeds another stage
- Feature engineering calculations
- Price modelling or regression logic
- Date/timezone logic
- Deduplication, hashing, or validation logic

A corresponding unit test **MUST** be created or updated.

## Test Location & Naming

```
tests/
├── __init__.py
├── unit/                  # Pure business logic — no DB, no S3, no network
│   ├── __init__.py
│   ├── conftest.py        # Shared fixtures
│   └── test_{module}_{script}.py
├── integration/           # Database/API tests (future)
│   └── ...
└── fixtures/              # Shared sample data files
    └── ...
```

Naming: `test_{module_folder}_{script_name}.py`

## Test Methodology

- **Framework**: `pytest`. Use `assert`, not `self.assertEqual()`.
- **Class grouping**: Group related tests in a class.
- **Shared fixtures**: Use `tests/unit/conftest.py` for reusable sample data.
- **No external dependencies**: Unit tests must not require database, S3, or network.
- **Descriptive names**: `test_face_up_score_penalises_deep_cut` not `test_score`.
- **Edge cases**: Always include tests for empty/missing input, zero values, boundary conditions.
- **Approx for floats**: Use `pytest.approx()` for floating-point comparisons.

## Running Tests

- Locally: `pytest tests/unit/ -v`
- CI: `.github/workflows/ci.yml`
