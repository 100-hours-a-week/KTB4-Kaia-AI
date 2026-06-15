from pydantic import BaseModel, Field


class GenConfig(BaseModel):
    temperature: float = 0.8
    top_k: int | None = 40
    repetition_penalty: float = 1.0
    max_new_tokens: int = 80


class TestRequest(BaseModel):
    input_text: str
    configs: list[GenConfig] = Field(min_length=1, max_length=3)
