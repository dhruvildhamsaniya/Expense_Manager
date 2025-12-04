from fastapi import APIRouter, HTTPException, status, Depends, Request
from app.models.category import CategoryCreate, CategoryResponse
from app.utils import get_current_user
from app.db import db
from typing import List
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/categories", tags=["categories"])

@router.get("", response_model=List[CategoryResponse])
async def get_categories(request: Request, current_user: dict = Depends(get_current_user)):
    try:
        user_id = int(current_user['sub'])
        categories = await db.fetch_all(
            """
            SELECT id, user_id, name, color, created_at
            FROM categories
            WHERE user_id = $1
            ORDER BY name
            """,
            user_id
        )
        return [dict(cat) for cat in categories]
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch categories"
        )

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_category(
    category: CategoryCreate,
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = int(current_user['sub'])
        
        result = await db.fetch_one(
            """
            INSERT INTO categories (user_id, name, color)
            VALUES ($1, $2, $3)
            RETURNING id, user_id, name, color, created_at
            """,
            user_id, category.name, category.color
        )
        
        logger.info(f"Category created: {category.name} by user {user_id}")
        return dict(result)
    
    except Exception as e:
        logger.error(f"Error creating category: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create category"
        )

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = int(current_user['sub'])
        
        result = await db.execute(
            "DELETE FROM categories WHERE id = $1 AND user_id = $2",
            category_id, user_id
        )
        
        if result == "DELETE 0":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        logger.info(f"Category deleted: {category_id} by user {user_id}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting category: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete category"
        )