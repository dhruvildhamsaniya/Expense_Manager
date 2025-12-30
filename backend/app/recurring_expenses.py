from fastapi import APIRouter, HTTPException, status, Depends, Request
from app.models.recurring_expense import (
    RecurringExpenseCreate, 
    RecurringExpenseUpdate, 
    RecurringExpenseResponse
)
from app.utils import get_current_user
from app.db import db
from typing import List
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/recurring-expenses", tags=["recurring-expenses"])

@router.get("", response_model=List[RecurringExpenseResponse])
async def get_recurring_expenses(
    current_user: dict = Depends(get_current_user)
):
    """Get all recurring expenses for current user."""
    try:
        user_id = int(current_user['sub'])
        
        expenses = await db.fetch_all(
            """
            SELECT id, user_id, category_id, amount, currency, description,
                   frequency, start_date, last_generated_date, is_active,
                   created_at, updated_at
            FROM recurring_expenses
            WHERE user_id = $1
            ORDER BY is_active DESC, start_date DESC
            """,
            user_id
        )
        
        return [dict(e) for e in expenses]
    
    except Exception as e:
        logger.error(f"Error fetching recurring expenses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch recurring expenses"
        )

@router.get("/upcoming")
async def get_upcoming_recurring(
    current_user: dict = Depends(get_current_user)
):
    """Get upcoming recurring expenses (active ones that will generate soon)."""
    try:
        user_id = int(current_user['sub'])
        
        expenses = await db.fetch_all(
            """
            SELECT re.id, re.amount, re.currency, re.description, re.frequency,
                   re.start_date, re.last_generated_date, c.name as category_name
            FROM recurring_expenses re
            LEFT JOIN categories c ON re.category_id = c.id
            WHERE re.user_id = $1 AND re.is_active = true
            ORDER BY re.frequency, re.start_date
            LIMIT 10
            """,
            user_id
        )
        
        return [dict(e) for e in expenses]
    
    except Exception as e:
        logger.error(f"Error fetching upcoming recurring: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch upcoming recurring expenses"
        )

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_recurring_expense(
    expense: RecurringExpenseCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new recurring expense."""
    try:
        user_id = int(current_user['sub'])
        
        result = await db.fetch_one(
            """
            INSERT INTO recurring_expenses 
            (user_id, category_id, amount, currency, description, frequency, start_date)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id, user_id, category_id, amount, currency, description,
                      frequency, start_date, last_generated_date, is_active,
                      created_at, updated_at
            """,
            user_id, expense.category_id, expense.amount, expense.currency,
            expense.description, expense.frequency, expense.start_date
        )
        
        logger.info(f"Recurring expense created: {result['id']} for user {user_id}")
        return dict(result)
    
    except Exception as e:
        logger.error(f"Error creating recurring expense: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create recurring expense"
        )

@router.put("/{expense_id}")
async def update_recurring_expense(
    expense_id: int,
    expense: RecurringExpenseUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a recurring expense."""
    try:
        user_id = int(current_user['sub'])
        
        result = await db.fetch_one(
            """
            UPDATE recurring_expenses
            SET category_id = $1, amount = $2, currency = $3, description = $4,
                frequency = $5, start_date = $6, is_active = COALESCE($7, is_active),
                updated_at = now()
            WHERE id = $8 AND user_id = $9
            RETURNING id, user_id, category_id, amount, currency, description,
                      frequency, start_date, last_generated_date, is_active,
                      created_at, updated_at
            """,
            expense.category_id, expense.amount, expense.currency, expense.description,
            expense.frequency, expense.start_date, expense.is_active,
            expense_id, user_id
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recurring expense not found"
            )
        
        logger.info(f"Recurring expense updated: {expense_id}")
        return dict(result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating recurring expense: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update recurring expense"
        )

@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recurring_expense(
    expense_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Delete (deactivate) a recurring expense."""
    try:
        user_id = int(current_user['sub'])
        
        # Soft delete - set is_active to false
        result = await db.execute(
            """
            UPDATE recurring_expenses
            SET is_active = false, updated_at = now()
            WHERE id = $1 AND user_id = $2
            """,
            expense_id, user_id
        )
        
        if result == "UPDATE 0":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recurring expense not found"
            )
        
        logger.info(f"Recurring expense deactivated: {expense_id}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting recurring expense: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete recurring expense"
        )