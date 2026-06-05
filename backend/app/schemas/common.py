from pydantic import BaseModel


class TimestampedModel(BaseModel):
    id: str
    created_at: str
    updated_at: str

