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

### DevOps
- **Docker & Docker Compose** - Containerization
- **pgAdmin** - Database management GUI

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- OR Python 3.11+ and PostgreSQL 15+

### Option 1: Docker (Recommended)

1. **Clone or create the project structure**
   ```bash
   mkdir expense-manager
   cd expense-manager
   # Copy all files from the artifact into this directory
   ```

2. **Start all services**
   ```bash
   docker-compose up --build
   ```

3. **Access the application**
   - App: http://localhost:8000
     - Email: dhruvildhamsaniya123@gmail.com
     - Password: dhruvil

4. **Setup pgAdmin (first time)**
   - Login to pgAdmin
   - Add New Server:
     - Name: expense_manager
     - Host: localhost
     - Port: 5432
     - Username: 
     - Password: 
     - Database: 

### Option 2: Local Development

1. **Setup PostgreSQL**
   ```bash
   # Create database
   createdb expense_db
   
   # Run migrations
   psql expense_db < backend/migrations/init.sql
   ```

2. **Setup Python environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

4. **Run the application**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access the application**
   - Open http://localhost:8000

## Project Structure

```
expense-manager/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app & routes
│   │   ├── auth.py              # Authentication endpoints
│   │   ├── expenses.py          # Expense CRUD endpoints
│   │   ├── categories.py        # Category endpoints
│   │   ├── dashboard.py         # Dashboard analytics
│   │   ├── db.py                # Database connection
│   │   ├── config.py            # Configuration
│   │   ├── utils.py             # Utility functions
│   │   ├── models/              # Pydantic models
│   │   │   ├── user.py
│   │   │   ├── category.py
│   │   │   └── expense.py
│   │   ├── templates/           # Jinja2 HTML templates
│   │   │   ├── base.html
│   │   │   ├── index.html
│   │   │   ├── register.html
│   │   │   ├── login.html
│   │   │   ├── dashboard.html
│   │   │   ├── expenses.html
│   │   │   └── categories.html
│   │   └── static/              # Static files (CSS, JS)
│   ├── logs/                    # Application logs
│   ├── migrations/
│   │   └── init.sql             # Database schema
│   ├── requirements.txt
│   └── .env.example
├── uploads/                     # Receipt uploads
├── docker-compose.yml
├── Dockerfile
├── .gitignore
└── README.md
```

## API Documentation

Once the app is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout

#### Expenses
- `GET /api/expenses` - List expenses (with filters)
- `POST /api/expenses` - Create expense
- `GET /api/expenses/{id}` - Get expense
- `PUT /api/expenses/{id}` - Update expense
- `DELETE /api/expenses/{id}` - Delete expense
- `GET /api/expenses/export/csv` - Export to CSV

#### Categories
- `GET /api/categories` - List categories
- `POST /api/categories` - Create category
- `DELETE /api/categories/{id}` - Delete category

#### Dashboard
- `GET /api/dashboard/monthly` - Monthly breakdown (uses stored procedure)

## Database Schema

### Users Table
```sql
- id (SERIAL PRIMARY KEY)
- username (VARCHAR UNIQUE)
- email (VARCHAR UNIQUE)
- password_hash (VARCHAR)
- created_at, updated_at (TIMESTAMP)
```

### Categories Table
```sql
- id (SERIAL PRIMARY KEY)
- user_id (FOREIGN KEY)
- name (VARCHAR)
- color (VARCHAR - hex color)
- created_at (TIMESTAMP)
```

### Expenses Table
```sql
- id (SERIAL PRIMARY KEY)
- user_id (FOREIGN KEY)
- category_id (FOREIGN KEY, nullable)
- amount (NUMERIC)
- currency (VARCHAR)
- expense_date (DATE)
- description (TEXT)
- receipt_url (TEXT)
- created_at, updated_at (TIMESTAMP)
```

### Stored Procedure
`monthly_category_totals(user_id, start_date, end_date)` - Returns category totals for a date range

## Security Features

- ✅ Password hashing with bcrypt
- ✅ JWT token-based authentication
- ✅ HttpOnly cookies
- ✅ Parameterized SQL queries (SQL injection prevention)
- ✅ Input validation with Pydantic
- ✅ File upload restrictions
- ✅ CORS protection

## Usage Guide

### 1. Register an Account
- Navigate to http://localhost:8000
- Click "Get Started" or "Register"
- Fill in username, email, and password
- Submit the form

### 2. Add Categories
- Go to "Categories" page
- Click "+ Add Category"
- Enter category name and choose a color
- Save

### 3. Add Expenses
- Go to "Expenses" page
- Click "+ Add Expense"
- Fill in:
  - Amount
  - Currency
  - Date
  - Category (optional)
  - Description (optional)
  - Receipt image (optional)
- Save

### 4. View Dashboard
- Go to "Dashboard" page
- Select date range
- View:
  - Total expenses
  - Number of transactions
  - Top spending category
  - Interactive pie chart
  - Category breakdown table

### 5. Filter and Search
- On Expenses page:
  - Filter by date range
  - Filter by category
  - Search by description
  - Export filtered results to CSV

## Logging

Application logs are stored in `logs/app.log` with:
- INFO: Normal operations
- WARNING: Suspicious activity
- ERROR: Exceptions with stack traces

Log rotation: 10MB max file size, 5 backup files

## Testing

Run the application and test:
1. User registration and login
2. Adding expenses with required fields
3. Category CRUD operations
4. Dashboard monthly totals (verify against database)
5. CSV export functionality
6. Error handling (missing required fields)

## Troubleshooting

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker-compose ps

# View logs
docker-compose logs postgres

# Recreate database
docker-compose down -v
docker-compose up
```

### Permission Issues
```bash
# Fix upload directory permissions
chmod 755 uploads/
```

### Port Already in Use
```bash
# Change ports in docker-compose.yml
ports:
  - "8001:8000"  # Change 8000 to 8001
```

## Environment Variables

Create `.env` file in backend directory:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/databasename
SECRET_KEY=your-very-secret-key-minimum-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
UPLOAD_FOLDER=uploads/receipts
MAX_UPLOAD_SIZE=5242880
```

## Production Deployment

1. **Change SECRET_KEY** in `.env`
2. **Use strong database password**
3. **Enable HTTPS**
4. **Set up proper firewall rules**
5. **Configure reverse proxy (Nginx)**
6. **Set up automated backups**
7. **Use environment-specific configs**

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request


## Support

For issues and questions:
- Check the troubleshooting section
- Review application logs in `logs/app.log`
- Check pgAdmin for database issues

## Future Enhancements

- [ ] Budget tracking and alerts
- [ ] Recurring expenses
- [ ] Multi-currency support with real-time conversion
- [ ] Email notifications
- [ ] Mobile app (React Native)
- [ ] Data visualization improvements
- [ ] Expense sharing between users
- [ ] Advanced reporting (PDF)
- [ ] API rate limiting
- [ ] Two-factor authentication

---

Built with ❤️ using FastAPI, PostgreSQL, and Chart.js
