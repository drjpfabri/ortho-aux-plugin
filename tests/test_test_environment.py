import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("mode", ["api", "scenarios_only"])
def test_synthetic_tests_ignore_inherited_runtime_configuration(tmp_path, mode):
    workspace = tmp_path / "isolated-project"
    workspace.mkdir()
    shutil.copytree(ROOT / "app", workspace / "app", ignore=shutil.ignore_patterns("__pycache__"))
    tests = workspace / "tests"
    tests.mkdir()
    for name in ("conftest.py", "test_plugin.py", "test_safety_scenarios.py"):
        shutil.copyfile(ROOT / "tests" / name, tests / name)

    sentinel = tmp_path / "inherited.sqlite3"
    with sqlite3.connect(sentinel) as connection:
        connection.execute("CREATE TABLE sentinel (message TEXT)")
        connection.execute("INSERT INTO sentinel VALUES ('synthetic sentinel')")
    sentinel_digest = hashlib.sha256(sentinel.read_bytes()).hexdigest()
    ignored_path = tmp_path / "inherited-fallback.sqlite3"
    report = tmp_path / "environment-report.json"
    # This plugin observes the collected application's engine, without importing it early.
    (workspace / "isolation_probe.py").write_text(
        """import json
import os
import sys
from pathlib import Path


def pytest_sessionfinish(session, exitstatus):
    module = sys.modules['app.main']
    Path(os.environ['TEST_ENVIRONMENT_REPORT']).write_text(json.dumps({
        'database_driver': module.engine.url.drivername,
        'database_path': module.engine.url.database,
        'environment': module.runtime_environment(),
        'allowed_classifications': sorted(module.allowed_data_classifications()),
        'inherited_variables_absent': all(name not in os.environ for name in (
            'DATABASE_URL', 'RENDER', 'ORTHO_API_KEY', 'ORTHO_GOVERNANCE_APPROVAL_REF',
            'ORTHO_UNRECOGNIZED_CONFIGURATION',
        )),
    }), encoding='utf-8')
""",
        encoding="utf-8",
    )
    environment = {
        **os.environ,
        "PYTHONPATH": str(workspace),
        "PYTEST_ADDOPTS": "",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "TEST_ENVIRONMENT_REPORT": str(report),
        "DATABASE_URL": f"sqlite:///{sentinel}",
        "RENDER": "true",
        "ORTHO_API_KEY": "synthetic-inherited-key",
        "ORTHO_AUX_DB": str(ignored_path),
        "ORTHO_ENV": "production",
        "ORTHO_ALLOWED_DATA_CLASSIFICATIONS": "synthetic,deidentified",
        "ORTHO_GOVERNANCE_PROFILE": "deidentified_validation",
        "ORTHO_GOVERNANCE_APPROVED": "true",
        "ORTHO_GOVERNANCE_APPROVAL_REF": "synthetic-unapproved-reference",
        "ORTHO_UNRECOGNIZED_CONFIGURATION": "synthetic-inherited-setting",
    }
    target = (
        ["tests/test_plugin.py::test_health_and_security_headers"]
        if mode == "api"
        else ["--collect-only", "tests/test_safety_scenarios.py"]
    )
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-p", "isolation_probe", *target],
        cwd=workspace,
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    state = json.loads(report.read_text(encoding="utf-8"))
    assert state["database_driver"] == "sqlite"
    assert state["environment"] == "test"
    assert state["allowed_classifications"] == ["synthetic"]
    assert state["inherited_variables_absent"] is True
    database_path = Path(state["database_path"])
    assert database_path != sentinel
    assert database_path != ignored_path
    assert not database_path.is_relative_to(workspace)
    assert not database_path.parent.exists(), "The test database directory must be cleaned up."
    assert not (workspace / "data").exists()
    assert not ignored_path.exists()
    assert hashlib.sha256(sentinel.read_bytes()).hexdigest() == sentinel_digest
