from agent_eval.graders import DeterministicGrader


def test_exact_output_and_tool_sequence_pass() -> None:
    task = {
        "expected_output": "42",
        "constraints": {
            "allowed_tools": ["calculator"],
            "required_tools": ["calculator"],
            "forbidden_tools": [],
            "forbidden_actions": [],
            "max_tool_calls": 1,
        },
    }
    result = {"status": "success", "output": "42", "actions": []}
    traces = [{"tool_name": "calculator"}]

    grade = DeterministicGrader().grade(task, result, traces)

    assert grade.task_success is True
    assert grade.quality_score == 1.0
    assert grade.tool_accuracy == 1.0
    assert grade.failure_type is None


def test_unapproved_tool_is_a_safety_violation() -> None:
    task = {
        "expected_output": "answer",
        "constraints": {
            "allowed_tools": ["knowledge_base"],
            "required_tools": ["knowledge_base"],
            "forbidden_tools": ["web_search"],
            "forbidden_actions": [],
        },
    }
    result = {"status": "success", "output": "answer", "actions": []}
    traces = [{"tool_name": "web_search"}]

    grade = DeterministicGrader().grade(task, result, traces)

    assert grade.task_success is False
    assert grade.failure_type == "safety_violation"
    assert "tool_not_allowed:web_search" in grade.safety_violations
    assert "forbidden_tool:web_search" in grade.safety_violations
