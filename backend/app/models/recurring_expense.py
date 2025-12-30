from pydantic import BaseModel, validator
from typing import Optional
from datetime import date, datetime
from decimal import Decimal

class RecurringExpenseCreate(BaseModel):
    category_id: Optional[int]
    amount: Decimal
    currency: str = "INR"
    description: Optional[str] = None
    frequency: str  # 'weekly' or 'monthly'
    start_date: date
    
    @validator('amount')
    def amount_validator(cls, v):
        if v < 0:
            raise ValueError('Amount must be >= 0')
        return v
    
    @validator('frequency')
    def frequency_validator(cls, v):
        if v not in ['weekly', 'monthly']:
            raise ValueError('Frequency must be weekly or monthly')
        return v

class RecurringExpenseUpdate(RecurringExpenseCreate):
    is_active: Optional[bool] = None

class RecurringExpenseResponse(BaseModel):
    id: int
    user_id: int
    category_id: Optional[int]
    amount: Decimal
    currency: str
    description: Optional[str]
    frequency: str
    start_date: date
    last_generated_date: Optional[date]
    is_active: bool
    created_at: datetime
    updated_at: datetime