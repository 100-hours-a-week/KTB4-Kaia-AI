from fastapi import HTTPException

from inference import run_generation
from models import tests as test_model
from schemas import TestRequest


def result_row_to_dict(row: dict) -> dict:
    return {
        "config_index": row["config_index"],
        "config": {
            "temperature": row["temperature"],
            "top_k": row["top_k"],
            "repetition_penalty": row["repetition_penalty"],
            "max_new_tokens": row["max_new_tokens"],
        },
        "generated_text": row["generated_text"],
        "elapsed_time": row["elapsed_time"],
        "tokens_per_sec": row["tokens_per_sec"],
    }


def create_test(test: TestRequest) -> dict:
    test_id, created_at = test_model.insert_test(test.input_text)

    results = []
    for i, config in enumerate(test.configs):
        result = run_generation(test.input_text, config)
        test_model.insert_result(test_id, i, config, result)
        results.append({
            "config_index": i,
            "config": config.model_dump(),
            **result,
        })

    return {
        "id": test_id,
        "input_text": test.input_text,
        "created_at": created_at,
        "results": results,
    }


def list_tests() -> list[dict]:
    return test_model.get_all_tests()


def get_test(test_id: int) -> dict:
    test = test_model.get_test(test_id)
    if test is None:
        raise HTTPException(status_code=404, detail="Test not found")

    results = test_model.get_results(test_id)
    return {
        "id": test["id"],
        "input_text": test["input_text"],
        "created_at": test["created_at"],
        "results": [result_row_to_dict(row) for row in results],
    }


def delete_test(test_id: int) -> dict:
    if test_model.get_test(test_id) is None:
        raise HTTPException(status_code=404, detail="Test not found")
    test_model.delete_test(test_id)
    return {"message": f"Test {test_id} deleted"}
