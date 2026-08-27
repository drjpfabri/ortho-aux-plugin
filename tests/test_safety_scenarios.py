from copy import deepcopy

import pytest

from app.main import SAFETY_KEYS, FinalizeRequest, run_gate


def empty_safety():
    return {key: False for key in SAFETY_KEYS}


def base_payload():
    return {
        "context": {
            "case_type": "extremity_trauma",
            "patient_group": "adult",
            "pediatric_specific_review_documented": False,
        },
        "neurovascular": {"baseline_documented": True},
        "safety": empty_safety(),
    }


def scenario(name, payload, can_finalize, alert=None, blocker=None):
    return {
        "name": name,
        "payload": payload,
        "can_finalize": can_finalize,
        "alert": alert,
        "blocker": blocker,
    }


SCENARIOS = []

# Every priority flag is tested both without and with a documented response.
for safety_key, label in SAFETY_KEYS.items():
    blocked = base_payload()
    blocked["safety"] = {**empty_safety(), safety_key: True}
    SCENARIOS.append(
        scenario(
            f"{safety_key}_without_response",
            blocked,
            False,
            alert=label,
            blocker="resposta documentada",
        )
    )

    released = deepcopy(blocked)
    released["safety_response"] = {"urgent_actions_documented": True}
    SCENARIOS.append(
        scenario(
            f"{safety_key}_with_response",
            released,
            True,
            alert=label,
        )
    )


SCENARIOS.extend(
    [
        scenario("baseline_documented", base_payload(), True),
        scenario(
            "baseline_missing",
            {
                "context": {"case_type": "extremity_trauma", "patient_group": "adult"},
                "neurovascular": {},
                "safety": empty_safety(),
            },
            False,
            blocker="neurovascular basal",
        ),
        scenario(
            "baseline_conflicting_states",
            {
                "context": {"case_type": "extremity_trauma", "patient_group": "adult"},
                "neurovascular": {"baseline_documented": True, "unable_to_assess": True},
                "safety": empty_safety(),
            },
            False,
            blocker="conflitantes",
        ),
        scenario(
            "extremity_not_applicable",
            {
                "context": {"case_type": "extremity_trauma", "patient_group": "adult"},
                "neurovascular": {"not_applicable": True},
                "safety": empty_safety(),
            },
            False,
            blocker="não aplicável",
        ),
        scenario(
            "axial_not_applicable",
            {
                "context": {"case_type": "axial_trauma", "patient_group": "adult"},
                "neurovascular": {"not_applicable": True},
                "safety": empty_safety(),
            },
            True,
        ),
        scenario(
            "nontraumatic_not_applicable",
            {
                "context": {"case_type": "non_traumatic", "patient_group": "adult"},
                "neurovascular": {"not_applicable": True},
                "safety": empty_safety(),
            },
            True,
        ),
        scenario(
            "education_not_applicable",
            {
                "context": {"case_type": "education_only", "patient_group": "adult"},
                "neurovascular": {"not_applicable": True},
                "safety": empty_safety(),
            },
            True,
        ),
        scenario(
            "unable_to_assess_is_explicit",
            {
                "context": {"case_type": "extremity_trauma", "patient_group": "adult"},
                "neurovascular": {"unable_to_assess": True},
                "safety": empty_safety(),
            },
            True,
            alert="AVALIAÇÃO LIMITADA",
        ),
        scenario(
            "post_intervention_missing",
            {
                **base_payload(),
                "intervention": {"performed": True, "may_change_nv": True},
            },
            False,
            blocker="pós-imobilização",
        ),
        scenario(
            "post_intervention_in_intervention",
            {
                **base_payload(),
                "intervention": {
                    "performed": True,
                    "may_change_nv": True,
                    "post_nv_documented": True,
                },
            },
            True,
        ),
        scenario(
            "post_intervention_in_nv_check",
            {
                **base_payload(),
                "intervention": {"performed": True, "may_change_nv": True},
                "neurovascular": {
                    "baseline_documented": True,
                    "post_intervention_documented": True,
                },
            },
            True,
        ),
        scenario(
            "deficit_without_response",
            {
                **base_payload(),
                "neurovascular": {
                    "baseline_documented": True,
                    "concern_for_deficit": True,
                },
            },
            False,
            alert="déficit neurovascular",
            blocker="resposta documentada",
        ),
        scenario(
            "deficit_with_response",
            {
                **base_payload(),
                "neurovascular": {
                    "baseline_documented": True,
                    "concern_for_deficit": True,
                },
                "safety_response": {"urgent_actions_documented": True},
            },
            True,
            alert="déficit neurovascular",
        ),
        scenario(
            "pediatric_review_missing",
            {
                "context": {"case_type": "extremity_trauma", "patient_group": "pediatric"},
                "neurovascular": {"baseline_documented": True},
                "safety": empty_safety(),
            },
            False,
            blocker="pediátrica específica",
        ),
        scenario(
            "pediatric_review_complete",
            {
                "context": {
                    "case_type": "extremity_trauma",
                    "patient_group": "pediatric",
                    "pediatric_specific_review_documented": True,
                },
                "neurovascular": {"baseline_documented": True},
                "safety": empty_safety(),
            },
            True,
        ),
        scenario(
            "possible_patient_mix",
            {**base_payload(), "identity": {"possible_patient_mix": True}},
            False,
            blocker="MISTURA DE PACIENTE",
        ),
        scenario(
            "laterality_conflict",
            {**base_payload(), "identity": {"laterality_conflict": True}},
            False,
            blocker="Lateralidade conflitante",
        ),
        scenario(
            "procedure_incomplete",
            {
                **base_payload(),
                "procedure": {"procedure_reported": True, "minimum_data_complete": False},
            },
            False,
            blocker="Procedimento sem dados mínimos",
        ),
        scenario(
            "critical_field_pending",
            {**base_payload(), "critical_field_pending": True},
            False,
            blocker="Campo crítico pendente",
        ),
        scenario(
            "unvalidated_ai_as_decision",
            {**base_payload(), "unvalidated_ai_suggestion_as_decision": True},
            False,
            blocker="Sugestão IA não validada",
        ),
        scenario(
            "compartment_with_pulse_without_response",
            {
                **base_payload(),
                "safety": {**empty_safety(), "sindrome_compartimental": True},
                "neurovascular": {
                    "baseline_documented": True,
                    "distal_pulse_present": True,
                },
            },
            False,
            alert="síndrome compartimental",
            blocker="resposta documentada",
        ),
        scenario(
            "compartment_with_pulse_and_response",
            {
                **base_payload(),
                "safety": {**empty_safety(), "sindrome_compartimental": True},
                "neurovascular": {
                    "baseline_documented": True,
                    "distal_pulse_present": True,
                },
                "safety_response": {"urgent_actions_documented": True},
            },
            True,
            alert="síndrome compartimental",
        ),
        scenario(
            "occult_vascular_risk_with_pulse_without_response",
            {
                **base_payload(),
                "safety": {**empty_safety(), "risco_lesao_vascular_oculta": True},
                "neurovascular": {
                    "baseline_documented": True,
                    "distal_pulse_present": True,
                },
            },
            False,
            alert="risco vascular oculto",
            blocker="resposta documentada",
        ),
        scenario(
            "occult_vascular_risk_with_pulse_and_response",
            {
                **base_payload(),
                "safety": {**empty_safety(), "risco_lesao_vascular_oculta": True},
                "neurovascular": {
                    "baseline_documented": True,
                    "distal_pulse_present": True,
                },
                "safety_response": {"urgent_actions_documented": True},
            },
            True,
            alert="risco vascular oculto",
        ),
        scenario(
            "combined_open_injury_and_bleeding_without_response",
            {
                **base_payload(),
                "safety": {
                    **empty_safety(),
                    "fratura_exposta": True,
                    "hemorragia": True,
                },
            },
            False,
            alert="fratura exposta",
            blocker="resposta documentada",
        ),
        scenario(
            "combined_open_injury_and_bleeding_with_response",
            {
                **base_payload(),
                "safety": {
                    **empty_safety(),
                    "fratura_exposta": True,
                    "hemorragia": True,
                },
                "safety_response": {"urgent_actions_documented": True},
            },
            True,
            alert="hemorragia",
        ),
    ]
)


def test_suite_contains_exactly_50_synthetic_scenarios():
    assert len(SCENARIOS) == 50
    assert len({item["name"] for item in SCENARIOS}) == 50


@pytest.mark.parametrize("item", SCENARIOS, ids=[item["name"] for item in SCENARIOS])
def test_synthetic_safety_scenario(item):
    request = FinalizeRequest.model_validate(item["payload"])
    alerts, blockers = run_gate(request)
    assert (len(blockers) == 0) is item["can_finalize"]
    if item["alert"]:
        assert any(item["alert"] in message for message in alerts)
    if item["blocker"]:
        assert any(item["blocker"] in message for message in blockers)
