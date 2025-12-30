from fastapi import APIRouter, HTTPException, status, Depends, Request, File, UploadFile, Form
from app.models.expense import ExpenseCreate, ExpenseUpdate, ExpenseResponse
from app.utils import get_current_user, save_upload_file
from app.db import db
from typing import List, Optional
from datetime import date
from decimal import Decimal
import logging
import csv
import io
from fastapi.responses import StreamingResponse
from app.services.ocr_service import ocr_service
from app.services.currency_service import currency_service
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/expenses", tags=["expenses"])

@router.get("", response_model=dict)
async def get_expenses(
    request: Request,
    page: int = 1,
    per_page: int = 10,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category_id: Optional[int] = None,
    q: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = int(current_user['sub'])
        offset = (page - 1) * per_page
        
        # Build query
        where_clauses = ["e.user_id = $1"]
        params = [user_id]
        param_count = 1
        
        if start_date:
            param_count += 1
            where_clauses.append(f"e.expense_date >= ${param_count}")
            params.append(start_date)
        
        if end_date:
            param_count += 1
            where_clauses.append(f"e.expense_date <= ${param_count}")
            params.append(end_date)
        
        if category_id:
            param_count += 1
            where_clauses.append(f"e.category_id = ${param_count}")
            params.append(category_id)
        
        if q:
            param_count += 1
            where_clauses.append(f"e.description ILIKE ${param_count}")
            params.append(f"%{q}%")
        
        where_clause = " AND ".join(where_clauses)
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM expenses e WHERE {where_clause}"
        total = await db.fetch_one(count_query, *params)
        
        # Get expenses
        # FIX: Select both original_currency/amount AND converted_amount
        query = f"""
            SELECT e.id, e.user_id, e.category_id, 
                   e.amount, e.currency, 
                   e.original_currency, e.converted_amount, e.conversion_rate,
                   e.expense_date, e.description, e.receipt_url, 
                   e.created_at, e.updated_at, c.name as category_name
            FROM expenses e
            LEFT JOIN categories c ON e.category_id = c.id
            WHERE {where_clause}
            ORDER BY e.expense_date DESC, e.created_at DESC
            LIMIT ${param_count + 1} OFFSET ${param_count + 2}
        """
        params.extend([per_page, offset])
        
        expenses = await db.fetch_all(query, *params)
        
        return {
            "items": [dict(exp) for exp in expenses],
            "total": total['count'],
            "page": page,
            "per_page": per_page,
            "pages": (total['count'] + per_page - 1) // per_page
        }
    
    except Exception as e:
        logger.error(f"Error fetching expenses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch expenses"
        )

@router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    expense_id: int,
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = int(current_user['sub'])
        
        expense = await db.fetch_one(
            """
            SELECT id, user_id, category_id, amount, currency, expense_date,
                   description, receipt_url, created_at, updated_at
            FROM expenses
            WHERE id = $1 AND user_id = $2
            """,
            expense_id, user_id
        )
        
        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found"
            )
        
        return dict(expense)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching expense: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch expense"
        )

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_expense(
    amount: Decimal = Form(...),
    currency: str = Form("INR"),
    expense_date: date = Form(...),
    category_id: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    receipt: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = int(current_user['sub'])
        
        # Validate amount
        if amount < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Amount must be >= 0"
            )
        
        # Handle file upload and OCR
        receipt_url = None
        ocr_data = None
        
        if receipt:
            receipt_url = save_upload_file(receipt, user_id)
            
            # Run OCR if enabled
            if settings.OCR_ENABLED:
                try:
                    ocr_data = ocr_service.extract_receipt_data(receipt_url)
                    logger.info(f"OCR extraction: {ocr_data}")
                except Exception as e:
                    logger.error(f"OCR failed: {e}")
        
        # Get user's base currency for conversion
        user_data = await db.fetch_one(
            "SELECT base_currency FROM users WHERE id = $1",
            user_id
        )
        base_currency = user_data['base_currency'] if user_data else 'INR'
        
        # Convert amount to base currency
        conversion = await currency_service.convert_amount(
            float(amount), 
            currency, 
            base_currency
        )
        
        result = await db.fetch_one(
            """
            INSERT INTO expenses (user_id, category_id, amount, currency, 
                                  expense_date, description, receipt_url,
                                  original_currency, converted_amount, conversion_rate)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id, user_id, category_id, amount, currency, expense_date,
                      description, receipt_url, original_currency, converted_amount,
                      conversion_rate, created_at, updated_at
            """,
            user_id, category_id, amount, currency, expense_date, description, receipt_url,
            currency, conversion['converted_amount'], conversion['rate']
        )
        
        logger.info(f"Expense created: {result['id']} by user {user_id}")
        
        response_data = dict(result)
        if ocr_data:
            response_data['ocr_data'] = ocr_data
        
        return response_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating expense: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create expense"
        )

@router.post("/ocr-preview")
async def ocr_preview(
    receipt: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Process receipt with OCR without saving the expense.
    Returns extracted data for preview.
    """
    try:
        user_id = int(current_user['sub'])
        
        if not settings.OCR_ENABLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OCR is not enabled"
            )
        
        # Save file temporarily
        receipt_url = save_upload_file(receipt, user_id)
        
        # Run OCR
        ocr_data = ocr_service.extract_receipt_data(receipt_url)
        
        return {
            "success": True,
            "data": ocr_data,
            "receipt_url": receipt_url
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCR preview error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OCR processing failed"
        )

@router.put("/{expense_id}")
async def update_expense(
    expense_id: int,
    amount: Decimal = Form(...),
    currency: str = Form("INR"),
    expense_date: date = Form(...),
    category_id: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    receipt: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = int(current_user['sub'])
        
        # Validate amount
        if amount < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Amount must be >= 0"
            )
        
        # Handle file upload
        receipt_url = None
        if receipt:
            receipt_url = save_upload_file(receipt, user_id)
        
        # Update query
        if receipt_url:
            query = """
                UPDATE expenses
                SET category_id = $1, amount = $2, currency = $3,
                    expense_date = $4, description = $5, receipt_url = $6,
                    updated_at = now()
                WHERE id = $7 AND user_id = $8
                RETURNING id, user_id, category_id, amount, currency, expense_date,
                          description, receipt_url, created_at, updated_at
            """
            result = await db.fetch_one(
                query, category_id, amount, currency, expense_date, 
                description, receipt_url, expense_id, user_id
            )
        else:
            query = """
                UPDATE expenses
                SET category_id = $1, amount = $2, currency = $3,
                    expense_date = $4, description = $5, updated_at = now()
                WHERE id = $6 AND user_id = $7
                RETURNING id, user_id, category_id, amount, currency, expense_date,
                          description, receipt_url, created_at, updated_at
            """
            result = await db.fetch_one(
                query, category_id, amount, currency, expense_date, 
                description, expense_id, user_id
            )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found"
            )
        
        logger.info(f"Expense updated: {expense_id} by user {user_id}")
        return dict(result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating expense: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update expense"
        )

@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: int,
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = int(current_user['sub'])
        
        result = await db.execute(
            "DELETE FROM expenses WHERE id = $1 AND user_id = $2",
            expense_id, user_id
        )
        
        if result == "DELETE 0":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found"
            )
        
        logger.info(f"Expense deleted: {expense_id} by user {user_id}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting expense: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete expense"
        )

@router.get("/export/csv")
async def export_csv(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = int(current_user['sub'])
        
        # Build query
        where_clauses = ["e.user_id = $1"]
        params = [user_id]
        param_count = 1
        
        if start_date:
            param_count += 1
            where_clauses.append(f"e.expense_date >= ${param_count}")
            params.append(start_date)
        
        if end_date:
            param_count += 1
            where_clauses.append(f"e.expense_date <= ${param_count}")
            params.append(end_date)
        
        where_clause = " AND ".join(where_clauses)
        
        query = f"""
            SELECT e.expense_date, c.name as category, e.amount, e.currency, e.description
            FROM expenses e
            LEFT JOIN categories c ON e.category_id = c.id
            WHERE {where_clause}
            ORDER BY e.expense_date DESC
        """
        
        expenses = await db.fetch_all(query, *params)
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Date', 'Category', 'Amount', 'Currency', 'Description'])
        
        for exp in expenses:
            writer.writerow([
                exp['expense_date'],
                exp['category'] or 'Uncategorized',
                exp['amount'],
                exp['currency'],
                exp['description'] or ''
            ])
        
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=expenses.csv"}
        )
    
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export CSV"
        )