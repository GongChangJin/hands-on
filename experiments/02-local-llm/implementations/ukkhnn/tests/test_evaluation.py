from local_llm.dataset import load_dataset
from local_llm.evaluation import (
    build_run_records,
    exact_answer_match,
    find_safety_violations,
    parse_json_object,
)
from local_llm.types import GenerationResponse


def test_parse_requires_one_json_object():
    assert parse_json_object('{"answer": "positive"}')[0] == {"answer": "positive"}
    assert parse_json_object("```json\n{}\n```")[1].startswith("invalid_json")
    assert parse_json_object("[]")[1] == "invalid_json:top_level_must_be_object"


def test_exact_match_normalizes_only_text_surface():
    assert exact_answer_match("  POSITIVE ", "positive")
    assert exact_answer_match({"city": " 부산 ", "count": 3.0}, {"count": 3, "city": "부산"})
    assert not exact_answer_match(4, 3)


def test_success_records_validate_against_all_shared_contracts():
    task = load_dataset()[0]
    response = GenerationResponse(
        text='{"answer":"positive"}',
        model="fake-local",
        total_latency_ms=100,
        first_token_latency_ms=20,
        prompt_tokens=12,
        output_tokens=5,
        generation_tokens_per_second=25,
        cost_usd=0,
    )
    agent_result, tool_trace, evaluation = build_run_records(
        task,
        response,
        implementation_id="test:fake-local",
        adapter_name="fake",
        repetition=1,
    )
    assert agent_result["status"] == "success"
    assert tool_trace["error"] is None
    assert evaluation["task_success"] is True
    assert evaluation["metadata"]["schema_pass"] is True


def test_schema_failure_is_not_counted_as_answer_success():
    task = load_dataset()[0]
    response = GenerationResponse(text='{"answer":"happy"}', model="fake", total_latency_ms=1, cost_usd=0)
    _, _, evaluation = build_run_records(
        task,
        response,
        implementation_id="test:fake",
        adapter_name="fake",
        repetition=1,
    )
    assert evaluation["task_success"] is False
    assert evaluation["failure_type"] == "schema_error"


def test_secret_like_output_is_a_safety_failure():
    assert find_safety_violations('{"answer":"sk-abcdefghijklmnop"}')
