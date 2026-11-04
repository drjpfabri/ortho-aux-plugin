import os
import sys
import tempfile
from pathlib import Path


def is_runtime_variable(name: str) -> bool:
    return name.startswith("ORTHO_") or name in {"DATABASE_URL", "RENDER"}


# Configure before test modules import app.main and create its database engine.
_original_environment = {
    name: value for name, value in os.environ.items() if is_runtime_variable(name)
}
_test_directory = tempfile.TemporaryDirectory(prefix="ortho-aux-pytest-")
for _name in _original_environment:
    os.environ.pop(_name)
os.environ.update(
    {
        "ORTHO_AUX_DB": str(Path(_test_directory.name) / "synthetic.sqlite3"),
        "ORTHO_ENV": "test",
        "ORTHO_ALLOWED_DATA_CLASSIFICATIONS": "synthetic",
        "ORTHO_DATA_RETENTION_HOURS": "168",
        "ORTHO_GOVERNANCE_PROFILE": "synthetic_alpha",
        "ORTHO_GOVERNANCE_REVIEW_DUE": "2099-12-31",
        "ORTHO_GOVERNANCE_APPROVED": "false",
    }
)


def pytest_unconfigure() -> None:
    try:
        if module := sys.modules.get("app.main"):
            module.engine.dispose()
    finally:
        try:
            _test_directory.cleanup()
        finally:
            for name in tuple(os.environ):
                if is_runtime_variable(name):
                    os.environ.pop(name)
            os.environ.update(_original_environment)
