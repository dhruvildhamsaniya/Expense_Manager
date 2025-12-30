from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
from decimal import Decimal

class BudgetCreate(BaseModel):
    category_id: int
    month: int
    year: int
    amount: Decimal
    
    @validator('month')
    def month_validator(cls, v):
        if not 1 <= v <= 12:
            raise ValueError('Month must be between 1 and 12')
        return v
    
    @validator('year')
    def year_validator(cls, v):
        if v < 2000:
            raise ValueError('Year must be >= 2000')
        return v
    
    @validator('amount')
    def amount_validator(cls, v):
        if v < 0:
            raise ValueError('Amount must be >= 0')
        return v

class BudgetUpdate(BudgetCreate):
    pass

class BudgetResponse(BaseModel):
    id: int
    user_id: int
    category_id: int
    month: int
    year: int
    amount: Decimal
    created_at: datetime
    updated_at: datetime

class BudgetVsActual(BaseModel):
    category_id: int
    category_name: str
    budget_amount: Decimal
    actual_amount: Decimal
    remaining: Decimal
    percentage: float