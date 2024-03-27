def main_tag_with_pagination(cur, per_page, offset):
    cur.execute("""
           SELECT t.ID AS Tag_ID,
                   t.Name AS Tag_Name,
                   COUNT(DISTINCT c.ID) AS NumberOfCategories,
                   COUNT(DISTINCT e.Expenses_id) AS NumberOfExpenses,
                   COALESCE(SUM(e.price), 0) AS total_price
               FROM 
                   Tag t
               LEFT JOIN 
                   Expense_Tag et ON t.ID = et.Tag_id
               LEFT JOIN 
                   Expenses e ON et.Expenses_id = e.Expenses_id
               LEFT JOIN 
                   Category c ON e.CATEGORY_ID = c.ID
               GROUP BY 
                   t.ID, t.Name
               ORDER BY 
                   t.Name ASC
               LIMIT %s OFFSET %s;
           """, (per_page, offset))
    results = cur.fetchall()
    return results

def main_tag_category_count(cur,tag_id):
    cur.execute("""
        SELECT COALESCE(COUNT(DISTINCT c.ID), 0)
        FROM Category c
        JOIN Expenses e ON c.ID = e.CATEGORY_ID
        JOIN Expense_Tag et ON e.Expenses_id = et.Expenses_id
        WHERE et.Tag_id = %s;
    """, (tag_id,))

    category_count = cur.fetchone()[0]
    return category_count

def main_tag_top_categories(cur,tag_id):
    cur.execute("""
        SELECT c.ID, c.Name, COALESCE(COUNT(DISTINCT e.Expenses_id), 0) as tag_count
        FROM Category c
        LEFT JOIN Expenses e ON c.ID = e.CATEGORY_ID
        LEFT JOIN Expense_Tag et ON e.Expenses_id = et.Expenses_id
        WHERE et.Tag_id = %s
        GROUP BY c.ID, c.Name
        ORDER BY tag_count DESC
        LIMIT 3;
    """, (tag_id,))

    top_categories = cur.fetchall()
    return top_categories

def main_tag_categories_seven_days(cur,tag_id):
    cur.execute("""
        SELECT c.ID, c.Name
        FROM Category c
        JOIN Expenses e ON c.ID = e.CATEGORY_ID
        JOIN Expense_Tag et ON e.Expenses_id = et.Expenses_id
        WHERE et.Tag_id = %s
          AND e.TRANSACTION_DATE >= CURRENT_DATE - INTERVAL '7 days'
          AND e.TRANSACTION_DATE <= CURRENT_DATE
        GROUP BY c.ID, c.Name
        ORDER BY MAX(e.TRANSACTION_DATE) DESC
        LIMIT 5;
    """, (tag_id,))

    last_seven_days = cur.fetchall()
    return last_seven_days

def main_tag_expense_count(cur,tag_id):
    cur.execute("""
        SELECT COALESCE(COUNT(DISTINCT e.Expenses_id), 0)
        FROM Expenses e
        JOIN Expense_Tag et ON e.Expenses_id = et.Expenses_id
        WHERE et.Tag_id = %s;
    """, (tag_id,))

    expenses_count = cur.fetchone()[0]
    return expenses_count

def main_tag_top_expenses(cur,tag_id):
    cur.execute("""
        SELECT e.DESCRIPTION, COUNT(*) as frequency
        FROM Expenses e
        JOIN Expense_Tag et ON e.Expenses_id = et.Expenses_id
        WHERE et.Tag_id = %s
        GROUP BY e.DESCRIPTION
        ORDER BY frequency DESC
        LIMIT 3;
    """, (tag_id,))

    top_expenses = cur.fetchall()
    return top_expenses

def main_tag_expenses_seven_days(cur,tag_id):
    cur.execute("""
         SELECT DISTINCT subquery.DESCRIPTION
         FROM (
             SELECT e.DESCRIPTION
             FROM Expenses e
             JOIN Expense_Tag et ON e.Expenses_id = et.Expenses_id
             WHERE et.Tag_id = %s
             AND e.TRANSACTION_DATE >= CURRENT_DATE - INTERVAL '7 days'
             AND e.TRANSACTION_DATE <= CURRENT_DATE
             ORDER BY e.TRANSACTION_DATE ASC
             LIMIT 5
         ) AS subquery
         ORDER BY subquery.DESCRIPTION ASC;
     """, (tag_id,))
    seven_days_expenses = cur.fetchall()
    return seven_days_expenses

def main_tag_cost(cur, tag_id):
    cur.execute("""
        SELECT COALESCE(SUM(e.PRICE), 0) as TotalAmount
        FROM Expenses e
        JOIN Expense_Tag et ON e.Expenses_id = et.Expenses_id
        WHERE et.Tag_id = %s;
    """, (tag_id,))

    total_cost = cur.fetchone()[0]
    return total_cost

def main_tag_average(cur, tag_id):
    cur.execute("""
        SELECT COALESCE(ROUND(AVG(e.PRICE), 2), 0) as AveragePrice
        FROM Expenses e
        JOIN Expense_Tag et ON e.Expenses_id = et.Expenses_id
        WHERE et.Tag_id = %s;
    """, (tag_id,))

    average_price = cur.fetchone()[0]
    return average_price

def main_tag_top_prices(cur, tag_id):
    cur.execute("""
        SELECT e.DESCRIPTION,c.ID, c.Name as Category, e.TRANSACTION_DATE, e.PRICE
        FROM Expenses e
        JOIN Category c ON e.CATEGORY_ID = c.ID
        JOIN Expense_Tag et ON e.Expenses_id = et.Expenses_id
        WHERE et.Tag_id = %s
        ORDER BY e.PRICE DESC
        LIMIT 3;
    """, (tag_id,))

    top_expensive_expenses = cur.fetchall()
    return top_expensive_expenses

def main_tag_low_prices(cur, tag_id):
    cur.execute("""
        SELECT e.DESCRIPTION,c.ID, c.Name as Category, e.TRANSACTION_DATE, e.PRICE
        FROM Expenses e
        JOIN Category c ON e.CATEGORY_ID = c.ID
        JOIN Expense_Tag et ON e.Expenses_id = et.Expenses_id
        WHERE et.Tag_id = %s
        ORDER BY e.PRICE ASC
        LIMIT 3;
    """, (tag_id,))

    top_cheap_expenses = cur.fetchall()
    return top_cheap_expenses
