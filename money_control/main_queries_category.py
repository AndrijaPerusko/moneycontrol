def main_category_query(cur):
    cur.execute("""
        SELECT 
            c.ID AS CategoryID,
            c.Name AS CategoryName,
            COALESCE(COUNT(DISTINCT e.Expenses_id), 0) AS NumberOfExpenses,
            COALESCE(COUNT(et.Tag_id), 0) AS NumberOfTags,
            COALESCE(SUM(DISTINCT e.PRICE), 0) AS TotalExpenses
        FROM Category c
        LEFT JOIN Expenses e ON c.ID = e.CATEGORY_ID
        LEFT JOIN Expense_Tag et ON e.Expenses_id = et.Expenses_id
        GROUP BY c.ID, c.Name
        ORDER BY c.Name;
    """)
    return cur.fetchall()
def main_category_tag_count(cur,category_id):
    cur.execute("""
        SELECT COUNT(et.tag_id) AS tag_count
        FROM category c
        LEFT JOIN expenses e ON c.id = e.category_id
        LEFT JOIN expense_tag et ON e.expenses_id = et.expenses_id
        WHERE c.id = %s
        GROUP BY c.id
    """, (category_id,))
    tag_count_result = cur.fetchone()
    return tag_count_result[0] if tag_count_result else 0

def main_category_top_tags(cur, category_id):
    cur.execute("""
        SELECT t.name, t.id, COUNT(et.tag_id) AS tag_usage
        FROM tag t
        JOIN expense_tag et ON t.id = et.tag_id
        JOIN expenses e ON et.expenses_id = e.expenses_id
        WHERE e.category_id = %s
        GROUP BY t.id
        ORDER BY tag_usage DESC
        LIMIT 3
    """, (category_id,))
    top_tags = cur.fetchall()
    return top_tags

def main_category_recent_tags(cur, category_id):
    cur.execute("""
        SELECT t.id, t.name
        FROM tag t
        JOIN expense_tag et ON t.id = et.tag_id
        JOIN expenses e ON et.expenses_id = e.expenses_id
        WHERE e.category_id = %s 
            AND e.TRANSACTION_DATE >= CURRENT_DATE - INTERVAL '7 days'
            AND e.TRANSACTION_DATE <= CURRENT_DATE
        GROUP BY t.id
        ORDER BY MAX(e.transaction_date) ASC
        LIMIT 10
    """, (category_id,))
    recent_tags = cur.fetchall()
    return recent_tags

def main_category_top_expense(cur, category_id):
    cur.execute("""
        SELECT description
        FROM expenses
        WHERE category_id = %s
        GROUP BY description
        ORDER BY COUNT(*) DESC
        LIMIT 3
    """, (category_id,))
    top_expenses = cur.fetchall()
    return top_expenses

def main_category_expense_count(cur,category_id):
    cur.execute("""
        SELECT COUNT(*)
        FROM expenses
        WHERE category_id = %s
    """, (category_id,))
    expense_count_result = cur.fetchone()
    expense_count = expense_count_result[0] if expense_count_result else 0
    return expense_count

def main_category_expense_seven_days(cur, category_id):
    cur.execute("""
        SELECT DISTINCT description 
        FROM expenses e
        WHERE category_id = %s 
        AND e.TRANSACTION_DATE >= CURRENT_DATE - INTERVAL '7 days'
        AND e.TRANSACTION_DATE <= CURRENT_DATE
        LIMIT 5;
    """, (category_id,))
    latest_expenses = cur.fetchall()
    return latest_expenses

def main_category_sum(cur, category_id):
    cur.execute("""
        SELECT COALESCE(SUM(price), 0) AS total_expense
        FROM expenses
        WHERE category_id = %s
    """, (category_id,))
    total_expense_result = cur.fetchone()
    total_expense = total_expense_result[0]
    return total_expense

def main_category_average_sum(cur, category_id):
    cur.execute("""
         SELECT COALESCE(ROUND(AVG(e.price), 2), 0) AS average_price
         FROM expenses e
         WHERE e.category_id = %s;
     """, (category_id,))
    average_price_result = cur.fetchone()
    average_price = average_price_result[0]
    return average_price

def main_category_most_expensive(cur,category_id):
    cur.execute("""
        SELECT e.expenses_id, e.description, e.transaction_date, e.price, 
               string_agg(t.name, ', ') as tags, 
               string_agg(CAST(t.id AS TEXT), ', ') as tag_ids
        FROM expenses e
        LEFT JOIN (
            SELECT et.expenses_id, t.name, t.id
            FROM expense_tag et
            JOIN tag t ON et.tag_id = t.id
        ) t ON e.expenses_id = t.expenses_id
        WHERE e.category_id = %s
        GROUP BY e.expenses_id, e.description, e.transaction_date, e.price
        ORDER BY e.price DESC
        LIMIT 3;
    """, (category_id,))

    most_expensive_results = cur.fetchall()
    return most_expensive_results

def main_category_most_cheap(cur,category_id):
    cur.execute("""
        SELECT e.expenses_id, e.description, e.transaction_date, e.price, 
               string_agg(t.name, ', ') as tags, 
               string_agg(CAST(t.id AS TEXT), ', ') as tag_ids
        FROM expenses e
        LEFT JOIN (
            SELECT et.expenses_id, t.name, t.id
            FROM expense_tag et
            JOIN tag t ON et.tag_id = t.id
        ) t ON e.expenses_id = t.expenses_id
        WHERE e.category_id = %s
        GROUP BY e.expenses_id, e.description, e.transaction_date, e.price
        ORDER BY e.price ASC
        LIMIT 3;
    """, (category_id,))

    cheapest_expenses = cur.fetchall()
    return cheapest_expenses