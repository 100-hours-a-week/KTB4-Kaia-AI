from fastapi import APIRouter

from controllers import tests as test_controller
from schemas import TestRequest

router = APIRouter()


@router.post("/tests")
def create_test(test: TestRequest):
    return test_controller.create_test(test)


@router.get("/tests")
def list_tests():
    return test_controller.list_tests()


@router.get("/tests/{test_id}")
def get_test(test_id: int):
    return test_controller.get_test(test_id)


@router.delete("/tests/{test_id}")
def delete_test(test_id: int):
    return test_controller.delete_test(test_id)
