from fastapi import APIRouter, HTTPException, status, Response, Depends, Request
from fastapi.responses import RedirectResponse
from app.models.user import UserRegister, UserLogin, UserResponse
from app.utils import hash_password, verify_password, create_access_token, get_current_user
from app.db import db
from app.config import settings
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserRegister):
    try:
        # Check if user exists
        existing_user = await db.fetch_one(
            "SELECT id FROM users WHERE username = $1 OR email = $2",
            user.username, user.email
        )
        
        if existing_user:
            logger.warning(f"Registration attempt with existing username/email: {user.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already exists"
            )
        
        # Hash password and create user
        hashed_pw = hash_password(user.password)
        result = await db.fetch_one(
            """
            INSERT INTO users (username, email, password_hash)
            VALUES ($1, $2, $3)
            RETURNING id, username, email, created_at
            """,
            user.username, user.email, hashed_pw
        )
        
        logger.info(f"New user registered: {user.username}")
        return {
            "message": "User created successfully",
            "user": dict(result)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login")
async def login(user: UserLogin, response: Response):
    try:
        # Find user by username or email
        db_user = await db.fetch_one(
            """
            SELECT id, username, email, password_hash
            FROM users
            WHERE username = $1 OR email = $1
            """,
            user.username_or_email
        )
        
        if not db_user or not verify_password(user.password, db_user['password_hash']):
            logger.warning(f"Failed login attempt for: {user.username_or_email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Create access token
        access_token = create_access_token(
            data={"sub": str(db_user['id']), "username": db_user['username']},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            samesite="lax"
        )
        
        logger.info(f"User logged in: {db_user['username']}")
        return {
            "message": "Login successful",
            "user": {
                "id": db_user['id'],
                "username": db_user['username'],
                "email": db_user['email']
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}