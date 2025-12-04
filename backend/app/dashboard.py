from fastapi import APIRouter, HTTPException, status, Depends, Request
from app.utils import get_current_user
from app.db import db
from typing import Optional
from datetime import date
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/monthly")
async def get_monthly_breakdown(
    start_date: date,
    end_date: date,
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = int(current_user['sub'])
        
        # Call stored procedure
        result = await db.fetch_all(
            "SELECT * FROM monthly_category_totals($1, $2, $3)",
            user_id, start_date, end_date
        )
        
        totals = [dict(row) for row in result]
        grand_total = sum(float(row['total']) for row in totals)
        
        logger.info(f"Monthly breakdown fetched for user {user_id}")
        
        return {
            "totals": totals,
            "grand_total": grand_total,
            "start_date": start_date,
            "end_date": end_date
        }
    
    except Exception as e:
        logger.error(f"Error fetching monthly breakdown: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch monthly breakdown"
        )