from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from app.db import db
from app import auth, categories, expenses, dashboard
from app.middleware import SecurityHeadersMiddleware
from app import recurring_expenses, budgets
from app.scheduler import start_scheduler, shutdown_scheduler
from app.utils import get_current_user
from contextlib import asynccontextmanager
import logging
from logging.handlers import RotatingFileHandler
import os


# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/app.log', maxBytes=10485760, backupCount=5),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await db.connect()
    start_scheduler()  # NEW: Start background scheduler
    logger.info("Application started with scheduler")
    yield
    # Shutdown
    shutdown_scheduler()  # NEW: Shutdown scheduler
    await db.disconnect()
    logger.info("Application shutdown")

app = FastAPI(title="Expense Manager", lifespan=lifespan)

app.add_middleware(SecurityHeadersMiddleware)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(expenses.router)
app.include_router(dashboard.router)
app.include_router(budgets.router)  # NEW
app.include_router(recurring_expenses.router)  # NEW

# Frontend routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    try:
        user = await get_current_user(request)
        return RedirectResponse(url="/dashboard")
    except:
        return templates.TemplateResponse("index.html", {"request": request})

@app.get("/auth/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/auth/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    try:
        user = await get_current_user(request)
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "user": user
        })
    except:
        return RedirectResponse(url="/auth/login")

@app.get("/expenses", response_class=HTMLResponse)
async def expenses_page(request: Request):
    try:
        user = await get_current_user(request)
        return templates.TemplateResponse("expenses.html", {
            "request": request,
            "user": user
        })
    except:
        return RedirectResponse(url="/auth/login")

@app.get("/categories", response_class=HTMLResponse)
async def categories_page(request: Request):
    try:
        user = await get_current_user(request)
        return templates.TemplateResponse("categories.html", {
            "request": request,
            "user": user
        })
    except:
        return RedirectResponse(url="/auth/login")

# NEW: Budgets page
@app.get("/budgets", response_class=HTMLResponse)
async def budgets_page(request: Request):
    try:
        user = await get_current_user(request)
        return templates.TemplateResponse("budgets.html", {
            "request": request,
            "user": user
        })
    except:
        return RedirectResponse(url="/auth/login")

# NEW: Recurring expenses page
@app.get("/recurring", response_class=HTMLResponse)
async def recurring_page(request: Request):
    try:
        user = await get_current_user(request)
        return templates.TemplateResponse("recurring.html", {
            "request": request,
            "user": user
        })
    except:
        return RedirectResponse(url="/auth/login")

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("access_token")
    return response

# Error handlers
@app.exception_handler(404)
async def not_found(request: Request, exc):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

@app.exception_handler(500)
async def server_error(request: Request, exc):
    logger.error(f"Internal server error: {exc}")
    return templates.TemplateResponse("500.html", {"request": request}, status_code=500)
