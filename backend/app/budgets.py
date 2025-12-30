from fastapi import APIRouter, HTTPException, status, Depends, Request
from app.models.budget import BudgetCreate, BudgetUpdate, BudgetResponse, BudgetVsActual
from app.utils import get_current_user
from app.db import db
from app.services.email_service import email_service
from app.config import settings
from typing import List
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/budgets", tags=["budgets"])

@router.get("", response_model=List[BudgetResponse])
async def get_budgets(
    month: int,
    year: int,
    current_user: dict = Depends(get_current_user)
):
    """Get all budgets for a specific month and year."""
    try:
        user_id = int(current_user['sub'])
        
        budgets = await db.fetch_all(
            """
            SELECT id, user_id, category_id, month, year, amount, created_at, updated_at
            FROM budgets
            WHERE user_id = $1 AND month = $2 AND year = $3
            ORDER BY amount DESC
            """,
            user_id, month, year
        )
        
        return [dict(b) for b in budgets]
    
    except Exception as e:
        logger.error(f"Error fetching budgets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch budgets"
        )

@router.get("/vs-actual", response_model=List[BudgetVsActual])
async def get_budget_vs_actual(
    month: int,
    year: int,
    current_user: dict = Depends(get_current_user)
):
    """Get budget vs actual spending comparison."""
    try:
        user_id = int(current_user['sub'])
        
        # Fetch budget vs actual data
        result = await db.fetch_all(
            "SELECT * FROM budget_vs_actual($1, $2, $3)",
            user_id, month, year
        )
        data = [dict(row) for row in result]
        
        # Fetch user email from DB
        user = await db.fetch_one("SELECT email FROM users WHERE id = $1", user_id)
        user_email = user['email'] if user else None
        
        # Check for budget alerts and send emails if needed
        await check_budget_alerts(user_id, data, user_email)
        
        return data
    
    except Exception as e:
        logger.error(f"Error fetching budget vs actual: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch budget comparison"
        )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_budget(
    budget: BudgetCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new budget or update existing one."""
    try:
        user_id = int(current_user['sub'])
        
        # Check if budget already exists for this category/month/year
        existing = await db.fetch_one(
            """
            SELECT id FROM budgets
            WHERE user_id = $1 AND category_id = $2 AND month = $3 AND year = $4
            """,
            user_id, budget.category_id, budget.month, budget.year
        )
        
        if existing:
            # Update existing budget
            result = await db.fetch_one(
                """
                UPDATE budgets
                SET amount = $1, updated_at = now()
                WHERE id = $2
                RETURNING id, user_id, category_id, month, year, amount, created_at, updated_at
                """,
                budget.amount, existing['id']
            )
        else:
            # Create new budget
            result = await db.fetch_one(
                """
                INSERT INTO budgets (user_id, category_id, month, year, amount)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id, user_id, category_id, month, year, amount, created_at, updated_at
                """,
                user_id, budget.category_id, budget.month, budget.year, budget.amount
            )
        
        logger.info(f"Budget created/updated for user {user_id}, category {budget.category_id}")
        return dict(result)
    
    except Exception as e:
        logger.error(f"Error creating budget: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create budget"
        )

@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(
    budget_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Delete a budget."""
    try:
        user_id = int(current_user['sub'])
        
        result = await db.execute(
            "DELETE FROM budgets WHERE id = $1 AND user_id = $2",
            budget_id, user_id
        )
        
        if result == "DELETE 0":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Budget not found"
            )
        
        logger.info(f"Budget deleted: {budget_id}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting budget: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete budget"
        )

async def check_budget_alerts(user_id: int, budget_data: List[dict], user_email: str):
    if not user_email:
        return

    for item in budget_data:
        percentage = float(item['percentage'])
        budget_id = item['budget_id']
        budget_amount = float(item['budget_amount'])
        actual_amount = float(item['actual_amount'])

        # ALERT (100%+)
        if (
            percentage >= settings.BUDGET_ALERT_THRESHOLD
            and not item['alert_sent']
        ):
            await email_service.send_budget_exceeded(
                user_email,
                item['category_name'],
                percentage,
                budget_amount,
                actual_amount
            )
            print(item['alert_sent'])

            await db.execute(
                "UPDATE budgets SET alert_sent = TRUE WHERE id = $1",
                budget_id
            )

        # WARNING (80%+)
        elif (
            percentage >= settings.BUDGET_WARNING_THRESHOLD
            and not item['warning_sent']
        ):
            await email_service.send_budget_warning(
                user_email,
                item['category_name'],
                percentage,
                budget_amount,
                actual_amount
            )
            print(item['warning_sent'])

            await db.execute(
                "UPDATE budgets SET warning_sent = TRUE WHERE id = $1",
                budget_id
            )
