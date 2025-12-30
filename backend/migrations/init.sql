-- Create Users Table
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(80) UNIQUE NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create Categories Table
CREATE TABLE categories (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(100) NOT NULL,
  color VARCHAR(7),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  UNIQUE(user_id, name)
);

-- Create Expenses Table
CREATE TABLE expenses (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
  category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
  amount NUMERIC(12,2) NOT NULL CHECK (amount >= 0),
  currency VARCHAR(8) NOT NULL DEFAULT 'USD',
  expense_date DATE NOT NULL,
  description TEXT,
  receipt_url TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create Indexes
CREATE INDEX idx_expenses_user_date ON expenses(user_id, expense_date);
CREATE INDEX idx_expenses_category ON expenses(category_id);

-- Create Stored Procedure for Monthly Category Totals
CREATE OR REPLACE FUNCTION monthly_category_totals(
  p_user_id INTEGER, 
  p_start_date DATE, 
  p_end_date DATE
)
RETURNS TABLE(category_id INT, category_name TEXT, total NUMERIC)
LANGUAGE SQL
AS $func$
  SELECT c.id, c.name, COALESCE(SUM(e.amount),0) as total
  FROM categories c
  LEFT JOIN expenses e
    ON e.category_id = c.id 
    AND e.user_id = p_user_id 
    AND e.expense_date BETWEEN p_start_date AND p_end_date
  WHERE c.user_id = p_user_id
  GROUP BY c.id, c.name
  ORDER BY total DESC;
$func$;