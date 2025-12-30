# 💰 Expense Manager

A full-stack personal finance application for tracking expenses, managing categories, and analyzing spending patterns.

## Features

### Core Features

- ✅ User authentication (register/login/logout) with secure password hashing
- ✅ Add, edit, and delete expenses
- ✅ Category management with custom colors
- ✅ Date range and category filters
- ✅ Dashboard with monthly category breakdown
- ✅ Interactive charts using Chart.js
- ✅ REST API for all CRUD operations
- ✅ PostgreSQL stored procedure for efficient monthly totals
- ✅ Backend error logging to file
- ✅ Budget tracking and alerts
- ✅ Recurring expenses
- ✅ Multi-currency support with real-time conversion
- ✅ Email notifications

### Additional Features

- 📁 Receipt uploads (stored locally)
- 📊 Export expenses to CSV
- 🔍 Search and pagination
- 🎨 Responsive UI with clean design

## Tech Stack

### Backend

- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Relational database
- **asyncpg** - Async database driver
- **python-jose** - JWT token handling
- **passlib** - Password hashing with bcrypt

### Frontend

- **Jinja2** - Server-side template rendering
- **Chart.js** - Data visualization
- **Vanilla JavaScript** - Dynamic behavior
- **CSS** - Custom styling

## Quick Start

### Prerequisites

- Python 3.11+ and PostgreSQL 15+

---

## Local Development Setup

**When to use:** Development, debugging, or if Docker is not available.

### Step 1: Install System Dependencies

**Ubuntu/Debian:**

```bash
sudo apt-get update
sudo apt-get install -y \
    postgresql postgresql-contrib \
    tesseract-ocr tesseract-ocr-eng \
    libgl1-mesa-glx libglib2.0-0 \
    python3.11 python3.11-venv python3-pip
```

**macOS:**

```bash
brew install postgresql@15 tesseract python@3.11
brew services start postgresql@15
```

**Windows:**

1. Install PostgreSQL: https://www.postgresql.org/download/windows/
2. Install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
3. Install Python: https://www.python.org/downloads/

### Step 2: Setup PostgreSQL Database

```bash
# Start PostgreSQL (if not running)
sudo service postgresql start  # Linux
brew services start postgresql@15  # macOS

# Create database user
sudo -u postgres psql
```

Then in PostgreSQL prompt:

```sql
CREATE USER expense_user WITH PASSWORD 'expense_pass';
CREATE DATABASE expense_db OWNER expense_user;
GRANT ALL PRIVILEGES ON DATABASE expense_db TO expense_user;
\q
```

Verify connection:

```bash
psql -U expense_user -d expense_db -h localhost
```

### Step 3: Run Database Migrations

```bash
# Navigate to project
cd expense-manager/backend

# Run migrations in order
psql -U expense_user -d expense_db -h localhost -f migrations/init.sql
psql -U expense_user -d expense_db -h localhost -f migrations/002_add_enhanced_features.sql
psql -U expense_user -d expense_db -h localhost -f migrations/003_fix_multicurrency.sql

# Verify tables
psql -U expense_user -d expense_db -h localhost -c "\dt"
```

### Step 4: Setup Python Environment

```bash
# Create virtual environment
cd backend
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\activate  # Windows

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### Step 5: Configure Environment Variables

```bash
# Copy example file
cp .env.example .env

# Edit configuration
nano .env  # or use any text editor
```

**Required .env settings:**

```env
DATABASE_URL=postgresql://expense_user:expense_pass@localhost:5432/expense_db
SECRET_KEY=your-very-secret-key-change-this-to-random-32-plus-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
UPLOAD_FOLDER=uploads/receipts
MAX_UPLOAD_SIZE=5242880

# OCR Settings
TESSERACT_CMD=/usr/bin/tesseract  # Leave empty if in PATH
OCR_ENABLED=true

# Currency Settings
EXCHANGE_RATE_API_URL=https://api.exchangerate-api.com/v4/latest
CACHE_EXCHANGE_RATES_HOURS=24

# Email Settings (optional - for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
SMTP_FROM_EMAIL=your-email@gmail.com
EMAIL_ENABLED=false  # Set to true when configured

# Budget Thresholds
BUDGET_WARNING_THRESHOLD=80.0
BUDGET_ALERT_THRESHOLD=100.0
```

### Step 6: Create Required Directories

```bash
mkdir -p logs uploads/receipts app/static
```

### Step 7: Run Application

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run with uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or for production (no reload)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Step 8: Verify Application

```bash
# Test health endpoint
curl http://localhost:8000/

# Check logs
tail -f logs/app.log

# Open in browser
open http://localhost:8000  # macOS
xdg-open http://localhost:8000  # Linux
```

---

## Project Structure

```
expense-manager/
├── backend/
│   ├── app/
│   │   ├── main.py 
│   │   ├── middleware.py
│   │   ├── auth.py 
│   │   ├── expenses.py 
│   │   ├── categories.py
│   │   ├── dashboard.py
│   │   ├── budgets.py
│   │   ├── recurring_expenses.py
│   │   ├── scheduler.py
│   │   ├── db.py
│   │   ├── config.py 
│   │   ├── utils.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── category.py
│   │   │   ├── expense.py
│   │   │   ├── budget.py 
│   │   │   └── recurring_expense.py 
│   │   ├── services/ 
│   │   │   ├── ocr_service.py 
│   │   │   ├── currency_service.py 
│   │   │   └── email_service.py 
│   │   └── templates/
│   │       ├── base.html 
│   │       ├── index.html
│   │       ├── register.html
│   │       ├── login.html
│   │       ├── dashboard.html 
│   │       ├── expenses.html 
│   │       ├── categories.html
│   │       ├── budgets.html 
│   │       └── recurring.html 
│   ├── migrations/
│   │   ├── init.sql
│   │   ├── 002_add_enhanced_features.sql
│   │   └── 003_fix_multicurrency.sql 
│   ├── requirements.txt 
│   └── .env.example 
├── Dockerfile 
├── docker-compose.yml
└── README.md 
```

## API Documentation

Once the app is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Usage Guide

### First Time Setup

**1. Register Account**

- Go to http://localhost:8000
- Click "Get Started" or "Register"
- Fill in username, email, password
- Select base currency (e.g., USD, EUR, INR)
- Submit

**2. Create Categories**

- Navigate to "Categories" page
- Click "+ Add Category"
- Enter category name (e.g., "Food", "Transport", "Entertainment")
- Choose a color
- Save

**3. Add First Expense**

- Go to "Expenses" page
- Click "+ Add Expense"
- Fill in amount, date, select category
- Optionally upload receipt
- If OCR is enabled, extracted data will auto-fill
- Save

### Budget Management

**1. Set Monthly Budget**

- Go to "Budgets" page
- Select month and year
- Click "+ Add Budget"
- Choose category
- Enter budget amount
- Save

**2. Monitor Progress**

- View dashboard for visual progress bars
- Green: < 80% spent
- Yellow: 80-99% spent
- Red: >= 100% (over budget)
- Receive email alerts at thresholds

### Recurring Expenses

**1. Create Recurring**

- Go to "Recurring" page
- Click "+ Add Recurring Expense"
- Fill in details:
  - Amount and currency
  - Category
  - Description (e.g., "Netflix Subscription")
  - Frequency (monthly/weekly)
  - Start date
- Save

**2. Auto-Generation**

- System runs daily at 00:01 AM
- Generates expenses when due
- Marks as "[Recurring]" in description
- View upcoming recurring on dashboard

### Receipt OCR

**1. Upload Receipt**

- Create or edit expense
- Click "Choose File" for receipt
- Upload image (JPG, PNG)
- System processes with OCR
- Review extracted data:
  - Amount (highlighted in yellow)
  - Date (highlighted in yellow)
  - Currency
- Edit if needed
- Save

**2. Tips for Better OCR**

- Use clear, well-lit images
- Ensure receipt is flat (not crumpled)
- Capture the full receipt
- Avoid shadows and glare
- Minimum 800x600 resolution

### Multi-Currency

**1. Set Base Currency**

- During registration OR
- In user settings (if implemented)
- All dashboard totals show in base currency

**2. Add Expense in Different Currency**

- Create expense
- Select currency (USD, EUR, GBP, INR, etc.)
- Enter amount in that currency
- System automatically converts to base currency
- Both amounts are stored
- View original currency in expense list

### Filtering & Search

**1. Filter by Date**

- Select start date and end date
- Click "Apply Filters"
- View expenses in range

**2. Filter by Category**

- Select category from dropdown
- Click "Apply Filters"

**3. Search Description**

- Type keywords in search box
- Searches expense descriptions
- Click "Apply Filters"

**4. Export to CSV**

- Apply desired filters
- Click "Export CSV"
- Opens/downloads CSV file

### Dashboard Analytics

**1. Monthly View**

- Select date range (default: current month)
- Click "Apply"
- View:
  - Total expenses
  - Transaction count
  - Top category
  - Pie chart of category distribution
  - Budget vs actual (if budgets set)
  - Upcoming recurring expenses

**2. Charts**

- Hover over pie chart for details
- Click legend to hide/show categories
- Responsive on mobile

---

## API Endpoints

### Authentication

- `POST /api/auth/register` - Register user
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout

### Expenses

- `GET /api/expenses` - List expenses (paginated, filtered)
- `POST /api/expenses` - Create expense
- `GET /api/expenses/{id}` - Get expense
- `PUT /api/expenses/{id}` - Update expense
- `DELETE /api/expenses/{id}` - Delete expense
- `GET /api/expenses/export/csv` - Export CSV
- `POST /api/expenses/ocr-preview` - Preview OCR extraction

### Categories

- `GET /api/categories` - List categories
- `POST /api/categories` - Create category
- `DELETE /api/categories/{id}` - Delete category

### Budgets

- `GET /api/budgets` - List budgets for month/year
- `GET /api/budgets/vs-actual` - Budget vs actual comparison
- `POST /api/budgets` - Create/update budget
- `DELETE /api/budgets/{id}` - Delete budget

### Recurring Expenses

- `GET /api/recurring-expenses` - List recurring
- `GET /api/recurring-expenses/upcoming` - Upcoming recurring
- `POST /api/recurring-expenses` - Create recurring
- `PUT /api/recurring-expenses/{id}` - Update recurring
- `DELETE /api/recurring-expenses/{id}` - Deactivate recurring

### Dashboard

- `GET /api/dashboard/monthly` - Monthly breakdown

---

## Security Features

- ✅ Password hashing with bcrypt
- ✅ JWT token-based authentication
- ✅ HttpOnly cookies
- ✅ Parameterized SQL queries (SQL injection prevention)
- ✅ Input validation with Pydantic
- ✅ File upload restrictions
- ✅ CORS protection

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Support

For issues and questions:

- Review application logs in `logs/app.log`
- Check pgAdmin for database issues

  ---

## 📸 Screenshots

<p align="center">
  <img src="https://github.com/user-attachments/assets/ba5be164-a311-4096-862b-f1169c7b284b" alt="Dashboard Overview" width="900">
</p>

---

<p align="center">
  <img src="https://github.com/user-attachments/assets/32373115-32ad-40f3-a255-294df44f1361" alt="Expense List" width="900">
</p>

---

<p align="center">
  <img src="https://github.com/user-attachments/assets/765f492a-9a6a-45b6-a47d-565308185e9b" alt="Add Expense" width="900">
</p>

---

### Budget Management

Set monthly budgets per category and track your spending with visual progress indicators.

<p align="center">
  <img src="https://github.com/user-attachments/assets/022336cf-399f-4819-9dc1-a7b839c8f81d" alt="Budget Management" width="900">
</p>

---

<p align="center">
  <img src="https://github.com/user-attachments/assets/9adcea60-59cf-4b6d-905b-12342f79dc4c" alt="Budget Analysis" width="900">
</p>

---

<p align="center">
  <img src="https://github.com/user-attachments/assets/aefdf036-c00a-4a00-b7de-5e330a46152b" alt="Recurring Expenses" width="900">
</p>

---

<p align="center">
  <img src="https://github.com/user-attachments/assets/2a5c5dc0-37f0-4e1d-b1bf-305139b5cd8a" alt="Add Recurring" width="900">
</p>

---

<p align="center">
  <img src="https://github.com/user-attachments/assets/92692fff-39ee-4bc4-8934-8113c0f5a612" alt="Category Management" width="900">
</p>

---

<p align="center">
  <img src="https://github.com/user-attachments/assets/62e8f4a4-65ee-48f7-b44b-2a73efea7653" alt="Add Category" width="900">
</p>

---

<p align="center">
  <img src="https://github.com/user-attachments/assets/1b187f02-fa73-4426-a445-161602f06c62" alt="User Registration" width="900">
</p>

---

<p align="center">
  <img src="https://github.com/user-attachments/assets/150f029d-158b-486b-af62-b1740f8c5657" alt="Email Notification" width="700">
</p>

---


## Future Enhancements

- [ ] Mobile app (React Native)
- [ ] Data visualization improvements
- [ ] Expense sharing between users
- [ ] Advanced reporting (PDF)
- [ ] API rate limiting
- [ ] Two-factor authentication

---

Built with ❤️ using FastAPI, PostgreSQL, and Chart.js

