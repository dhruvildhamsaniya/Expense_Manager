from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime

class CategoryCreate(BaseModel):
    name: str
    color: Optional[str] = None
    
    @validator('color')
    def color_validator(cls, v):
        if v and not v.startswith('#'):
            raise ValueError('Color must be a hex value starting with #')
        return v

class CategoryResponse(BaseModel):
    id: int
    user_id: int
    name: str
    color: Optional[str]
    created_at: datetime