from fastapi import Request

from exam_baseline.baseline.service import GenerationService


def get_service(request: Request) -> GenerationService:
    return request.app.state.service
