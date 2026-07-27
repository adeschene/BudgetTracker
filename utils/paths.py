from pathlib import Path

# Project root, resolved from this file's location rather than the working
# directory, so the app can be launched from anywhere
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def project_path(*parts) -> Path:
    # Build an absolute path to a file inside the project
    return PROJECT_ROOT.joinpath(*parts)
