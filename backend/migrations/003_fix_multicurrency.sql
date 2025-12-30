-- Fix stored procedure to use converted_amount instead of amount

DROP FUNCTION IF EXISTS monthly_category_totals(INTEGER, DATE, DATE);

CREATE OR REPLACE FUNCTION monthly_category_totals(
  p_user_id INTEGER, 
  p_start_date DATE, 
  p_end_date DATE
)
RETURNS TABLE(category_id INT, category_name TEXT, total NUMERIC)
LANGUAGE SQL
AS $$
  SELECT 
    c.id, 
    c.name, 
    -- FIX: Use converted_amount for proper multi-currency support
    COALESCE(SUM(e.converted_amount), 0) as total
  FROM categories c
  LEFT JOIN expenses e
    ON e.category_id = c.id 
    AND e.user_id = p_user_id 
    AND e.expense_date BETWEEN p_start_date AND p_end_date
  WHERE c.user_id = p_user_id
  GROUP BY c.id, c.name
  ORDER BY total DESC;
$$;
