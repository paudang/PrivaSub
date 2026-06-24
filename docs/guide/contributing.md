# Contributing

We welcome contributions to PrivaSub! Since this is a privacy-first, offline application, maintaining code quality and robust testing is critical.

## Local Setup for Development

1. **Fork and Clone** the repository.
2. **Install Dev Dependencies:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   pip install pytest pytest-cov
   ```

## Development Guidelines

- **Architecture:** The application separates the UI layer (`src/ui`) from the core AI/audio logic (`src/core`). Keep business logic decoupled from `customtkinter` classes.
- **Git Hooks:** PrivaSub uses a `pre-push` hook located in `.githooks/pre-push` to enforce code quality. 
   To enable it locally:
   ```bash
   git config core.hooksPath .githooks
   ```
- All code contributions must be accompanied by relevant tests.
- The project maintains a strict **90% test coverage** requirement.
- Test suites are automatically executed on `git push` via a pre-push hook.
- We use `unittest` and `coverage.py`. To run tests locally:
  ```bash
  coverage run run_tests.py
  coverage report -m --fail-under=90
  ```

## Running Tests

We require a **minimum of 90% test coverage** for all new features before they can be merged. 

To run the test suite and check your coverage, use the included test runner:
```bash
python run_tests.py
```
This script will execute all unit tests in the `tests/` folder and print a coverage report to the terminal. If your coverage drops below 90%, the `pre-push` hook will block you from pushing to GitHub.

## Submitting a Pull Request
1. Ensure `python run_tests.py` passes 100% with >90% coverage.
2. Provide a clear description of the feature or bugfix.
3. Include screenshots if your changes affect the UI.
