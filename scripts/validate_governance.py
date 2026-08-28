import ast
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTER_PATH = ROOT / "governance" / "control-register.yaml"
REQUIRED_CONTROL_IDS = {f"GOV-{number:03d}" for number in range(1, 14)}
ALLOWED_STATUSES = {"implemented", "partial", "open", "accepted"}


def fail(message: str) -> None:
    raise SystemExit(f"Governance validation failed: {message}")


def python_constant(path: Path, name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
    fail(f"constant {name} not found in {path.relative_to(ROOT)}")


def render_env_value(document: dict, name: str):
    services = document.get("services", [])
    if len(services) != 1:
        fail("render.yaml must define exactly one web service")
    for item in services[0].get("envVars", []):
        if item.get("key") == name:
            return item.get("value")
    fail(f"{name} is missing from render.yaml")


def main() -> None:
    register = yaml.safe_load(REGISTER_PATH.read_text(encoding="utf-8"))
    controls = register.get("controls", [])
    control_ids = [item.get("id") for item in controls]
    if set(control_ids) != REQUIRED_CONTROL_IDS or len(control_ids) != len(set(control_ids)):
        fail("control IDs must be unique and cover GOV-001 through GOV-013")

    for control in controls:
        if control.get("status") not in ALLOWED_STATUSES:
            fail(f"invalid status for {control.get('id')}")
        evidence = control.get("evidence", [])
        if not evidence:
            fail(f"{control.get('id')} has no evidence")
        for relative_path in evidence:
            if not (ROOT / relative_path).exists():
                fail(f"evidence path does not exist: {relative_path}")

    policy_version = register.get("policy_version")
    if policy_version != python_constant(ROOT / "app" / "main.py", "GOVERNANCE_POLICY_VERSION"):
        fail("policy version differs between code and control register")

    as_of = date.fromisoformat(register["as_of"])
    review_due = date.fromisoformat(register["review_due"])
    if review_due < as_of:
        fail("review_due precedes as_of")

    current_release = register.get("current_release", {})
    if current_release.get("profile") != "synthetic_alpha":
        fail("current profile must remain synthetic_alpha")
    if current_release.get("allowed_data_classifications") != ["synthetic"]:
        fail("current release must allow synthetic data only")
    for field in (
        "clinical_use_authorized",
        "patient_derived_data_authorized",
        "frontend_integration_authorized",
        "rag_enabled",
    ):
        if current_release.get(field) is not False:
            fail(f"{field} must remain false")

    gates = register.get("release_gates", {})
    if gates.get("synthetic_alpha", {}).get("authorized") is not True:
        fail("synthetic_alpha gate must be authorized")
    for gate_name in ("external_alpha", "deidentified_validation", "clinical_use"):
        gate = gates.get(gate_name, {})
        if gate.get("authorized") is not False:
            fail(f"{gate_name} must remain blocked")
        unknown_blockers = set(gate.get("blockers", [])) - REQUIRED_CONTROL_IDS
        if unknown_blockers:
            fail(f"{gate_name} references unknown blockers: {sorted(unknown_blockers)}")

    render_config = yaml.safe_load((ROOT / "render.yaml").read_text(encoding="utf-8"))
    if render_config["services"][0].get("autoDeployTrigger") != "checksPass":
        fail("Render must wait for GitHub checks before deploying")
    if render_env_value(render_config, "ORTHO_GOVERNANCE_PROFILE") != "synthetic_alpha":
        fail("Render governance profile differs from the control register")
    if str(render_env_value(render_config, "ORTHO_GOVERNANCE_REVIEW_DUE")) != str(review_due):
        fail("Render review date differs from the control register")
    if render_env_value(render_config, "ORTHO_ALLOWED_DATA_CLASSIFICATIONS") != "synthetic":
        fail("Render must remain synthetic-only")

    print(
        f"Governance register valid: {len(controls)} controls, "
        f"policy {policy_version}, review due {review_due.isoformat()}."
    )


if __name__ == "__main__":
    main()
