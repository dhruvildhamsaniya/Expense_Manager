-- Migration: Add Enhanced Features
-- Run this after init.sql

-- 1. Add base_currency to users table
ALTER TABLE users ADD COLUMN base_currency VARCHAR(3) DEFAULT 'USD';

-- 2. Add multi-currency fields to expenses table
ALTER TABLE expenses 
  ADD COLUMN original_currency VARCHAR(8),
  ADD COLUMN converted_amount NUMERIC(12,2),
  ADD COLUMN conversion_rate NUMERIC(12,6);

-- Update existing expenses with conversion data
UPDATE expenses 
SET original_currency = currency,
    converted_amount = amount,
    conversion_rate = 1.0
WHERE original_currency IS NULL;

-- 3. Create budgets table
CREATE TABLE budgets (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
  category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE NOT NULL,
  month INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
  year INTEGER NOT NULL CHECK (year >= 2000),
  amount NUMERIC(12,2) NOT NULL CHECK (amount >= 0),
  warning_sent BOOLEAN DEFAULT FALSE,
  alert_sent BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  UNIQUE(user_id, category_id, month, year)
);


CREATE INDEX idx_budgets_user_date ON budgets(user_id, year, month);

-- 4. Create recurring_expenses table
CREATE TABLE recurring_expenses (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
  category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
  amount NUMERIC(12,2) NOT NULL CHECK (amount >= 0),
  currency VARCHAR(8) NOT NULL DEFAULT 'USD',
  description TEXT,
  frequency VARCHAR(20) NOT NULL CHECK (frequency IN ('weekly', 'monthly')),
  start_date DATE NOT NULL,
  last_generated_date DATE,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX idx_recurring_user_active ON recurring_expenses(user_id, is_active);

-- 5. Create exchange_rates cache table
CREATE TABLE exchange_rates (
  id SERIAL PRIMARY KEY,
  base_currency VARCHAR(3) NOT NULL,
  target_currency VARCHAR(3) NOT NULL,
  rate NUMERIC(12,6) NOT NULL,
  fetched_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  UNIQUE(base_currency, target_currency)
);

CREATE INDEX idx_rates_currencies ON exchange_rates(base_currency, target_currency);

-- 6. Stored procedure for budget vs actual comparison
CREATE OR REPLACE FUNCTION budget_vs_actual(
  p_user_id INTEGER, 
  p_month INTEGER, 
  p_year INTEGER
)
RETURNS TABLE(
  budget_id INT,
  category_id INT,
  category_name TEXT,
  budget_amount NUMERIC,
  actual_amount NUMERIC,
  remaining NUMERIC,
  percentage NUMERIC,
  warning_sent BOOLEAN,
  alert_sent BOOLEAN
)
LANGUAGE SQL
AS $$
  SELECT 
    b.id AS budget_id,
    b.category_id,
    c.name,
    b.amount AS budget_amount,
    COALESCE(SUM(e.converted_amount), 0) AS actual_amount,
    b.amount - COALESCE(SUM(e.converted_amount), 0) AS remaining,
    CASE 
      WHEN b.amount > 0 THEN (COALESCE(SUM(e.converted_amount), 0) / b.amount * 100)
      ELSE 0
    END AS percentage,
    b.warning_sent,
    b.alert_sent
  FROM budgets b
  JOIN categories c ON b.category_id = c.id
  LEFT JOIN expenses e ON 
    e.category_id = b.category_id 
    AND e.user_id = p_user_id 
    AND EXTRACT(MONTH FROM e.expense_date) = p_month 
    AND EXTRACT(YEAR FROM e.expense_date) = p_year
  WHERE b.user_id = p_user_id 
    AND b.month = p_month 
    AND b.year = p_year
  GROUP BY b.id, b.category_id, c.name, b.amount, b.warning_sent, b.alert_sent
  ORDER BY percentage DESC;
$$;
