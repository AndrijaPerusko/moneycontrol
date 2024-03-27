def main_expense_tag_count(cur, description):
    cur.execute("""
    SELECT COUNT(DISTINCT et.Tag_id)
        FROM Expenses e
        JOIN Expense_Tag et ON e.Expenses_id = et.Expenses_id
        WHERE e.DESCRIPTION = %s;
        """, (description,))

    tag_count = cur.fetchone()[0]
    return tag_count

def main_expense_top_tags(cur, description):
    cur.execute("""
        SELECT COUNT(et.Tag_id) as tag_count, t.Name, t.ID as tag_id
        FROM Expenses e
        JOIN Expense_Tag et ON e.Expenses_id = et.Expenses_id
        JOIN Tag t ON et.Tag_id = t.ID
        WHERE e.DESCRIPTION = %s
        GROUP BY t.Name, t.ID
        ORDER BY tag_count DESC
        LIMIT 10;
        """, (description,))

    top_tags = cur.fetchall()
    return top_tags

def main_expense_tag_seven_days(cur, description):
    cur.execute("""
        SELECT DISTINCT ON (et.Tag_id) et.Tag_id, t.Name
        FROM Expenses e
        JOIN Expense_Tag et ON e.Expenses_id = et.Expenses_id
        JOIN Tag t ON et.Tag_id = t.ID
        WHERE e.DESCRIPTION = %s
        AND e.TRANSACTION_DATE >= CURRENT_DATE - INTERVAL '7 days'
        AND e.TRANSACTION_DATE <= CURRENT_DATE
        ORDER BY et.Tag_id, e.TRANSACTION_DATE DESC
        LIMIT 10;
    """, (description,))

    past_7_days_tag = cur.fetchall()
    return past_7_days_tag

def main_expense_category_count(cur, description):
    cur.execute("""
        SELECT COUNT(DISTINCT c.ID)
        FROM Expenses e
        JOIN Category c ON e.CATEGORY_ID = c.ID
        WHERE e.DESCRIPTION = %s;
    """, (description,))

    category_count = cur.fetchone()[0]
    return category_count

def main_expense_category_top(cur, description):
    cur.execute("""
        SELECT c.ID, c.Name, COUNT(*) as count
        FROM Expenses e
        JOIN Category c ON e.CATEGORY_ID = c.ID
        WHERE e.DESCRIPTION = %s
        GROUP BY c.ID, c.Name
        ORDER BY count DESC
        LIMIT 4;
    """, (description,))

    popular_categories = cur.fetchall()
    return popular_categories

def main_expense_category_seven_days(cur, description):
    cur.execute("""
        SELECT c.ID, c.Name
        FROM Expenses e
        JOIN Category c ON e.CATEGORY_ID = c.ID
        WHERE e.DESCRIPTION = %s
        AND e.TRANSACTION_DATE >= CURRENT_DATE - INTERVAL '7 days'
        AND e.TRANSACTION_DATE <= CURRENT_DATE
        GROUP BY c.ID, c.Name;
    """, (description,))

    recent_categories = cur.fetchall()
    return recent_categories

def main_expense_total_price(cur, description):
    cur.execute("""
        SELECT COALESCE(SUM(e.PRICE), 0) as total_price
        FROM Expenses e
        WHERE e.DESCRIPTION = %s;
    """, (description,))

    total_price = cur.fetchone()[0]
    return total_price

def main_expense_average_price(cur, description):
    cur.execute("""
        SELECT ROUND(AVG(e.PRICE), 2) as avg_price
        FROM Expenses e
        WHERE e.DESCRIPTION = %s;
    """, (description,))

    avg_price = cur.fetchone()[0]
    return avg_price

def main_expense_same_description(cur, description):
    cur.execute("""
        SELECT COUNT(e.Expenses_id) as total_expenses
        FROM Expenses e
        WHERE e.DESCRIPTION = %s;
    """, (description,))

    same_desc = cur.fetchone()[0]
    return same_desc

def main_expense_table_top(cur, description):
    cur.execute("""
        SELECT c.ID, c.Name as Category, e.PRICE, e.TRANSACTION_DATE,
               string_agg(t.Name, ', ') as Tags,
               string_agg(CAST(t.ID AS TEXT), ', ') as Tag_IDs
        FROM Expenses e
        JOIN Category c ON e.CATEGORY_ID = c.ID
        JOIN Expense_Tag et ON e.Expenses_id = et.Expenses_id
        JOIN Tag t ON et.Tag_id = t.ID
        WHERE e.DESCRIPTION = %s
        GROUP BY c.ID, c.Name, e.PRICE, e.TRANSACTION_DATE
        ORDER BY e.PRICE DESC
        LIMIT 3;
    """, (description,))

    top_price_expenses = cur.fetchall()
    return top_price_expenses

def main_expense_table_cheapest(cur, description):
    cur.execute("""
        SELECT c.ID, c.Name as Category, e.PRICE, e.TRANSACTION_DATE,
               string_agg(t.Name, ', ') as Tags,
               string_agg(CAST(t.ID AS TEXT), ', ') as Tag_IDs
        FROM Expenses e
        JOIN Category c ON e.CATEGORY_ID = c.ID
        JOIN Expense_Tag et ON e.Expenses_id = et.Expenses_id
        JOIN Tag t ON et.Tag_id = t.ID
        WHERE e.DESCRIPTION = %s
        GROUP BY c.ID, c.Name, e.PRICE, e.TRANSACTION_DATE
        ORDER BY e.PRICE ASC
        LIMIT 3;
    """, (description,))

    cheapest_price = cur.fetchall()
    return cheapest_price
