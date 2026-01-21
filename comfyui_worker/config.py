from pydantic import BaseModel, Field


class Settings(BaseModel):
    comfyui_base_url: str = Field(..., min_length=1)
