# Contributing to PrivaSub

First off, thank you for considering contributing to PrivaSub! It's people like you that make it an amazing offline utility tool.

## Code of Conduct
By participating in this project, you agree to abide by our Code of Conduct. Please read `CODE_OF_CONDUCT.md` before contributing.

## How Can I Contribute?

### Reporting Bugs
*   Ensure the bug was not already reported by searching on GitHub under Issues.
*   If you can't find an open issue addressing the problem, open a new one using the **Bug Report** template.
*   Be sure to include:
    *   Your Operating System version (e.g. Windows 11 23H2).
    *   Python version (`python --version`).
    *   Clear, step-by-step instructions on how to reproduce the issue.
    *   Terminal errors/tracebacks or screenshots.

### Suggesting Enhancements
*   Check if the feature has already been requested under Issues.
*   Open a new issue using the **Feature Request** template to discuss the scope, design, and feasibility.

### Pull Requests
1.  Fork the repository and create your branch from `main`.
2.  Set up your virtual environment and install development dependencies.
3.  Write clean, readable Python code matching our style.
4.  Ensure that manual test scripts (`test_audio.py`, `test_ai.py`) execute successfully.
5.  Document your changes in the Pull Request template.

## Development Setup

1.  Clone your fork and navigate to the project directory:
    ```bash
    git clone https://github.com/paudang/PrivaSub.git
    cd PrivaSub
    ```
2.  Set up the local environment:
    ```bash
    python -m venv .venv
    # Windows:
    .venv\Scripts\Activate.ps1
    # macOS/Linux:
    source .venv/bin/activate
    
    pip install -r requirements.txt
    ```
3.  Test your modifications:
    - Run audio loopback test: `python test_audio.py`
    - Run transcription test: `python test_ai.py`
    - Run the main app: `python src/main.py`

## Style Guidelines
*   Follow [PEP 8](https://peps.python.org/pep-0008/) style guidelines for Python code.
*   Keep functions focused, concise, and document classes or methods with descriptive docstrings.
*   Keep dependencies lightweight; avoid importing heavy libraries (like PyTorch or full NumPy libraries where not needed) to maintain small build sizes.
