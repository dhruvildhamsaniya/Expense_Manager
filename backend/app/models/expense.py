from pydantic import BaseModel, validator
from typing import Optional
from datetime import date, datetime
from decimal import Decimal

class ExpenseCreate(BaseModel):
    amount: Decimal
    currency: str = "USD"
    expense_date: date
    category_id: Optional[int]
    description: Optional[str] = None
    
    @validator('amount')
    def amount_validator(cls, v):
        if v < 0:
            raise ValueError('Amount must be >= 0')
        return v

class ExpenseUpdate(ExpenseCreate):
    pass

class ExpenseResponse(BaseModel):
    id: int
    user_id: int
    category_id: Optional[int]
    amount: Decimal
    currency: str
    expense_date: date
    description: Optional[str]
    receipt_url: Optional[str]
    created_at: datetime
    updated_at: datetime
