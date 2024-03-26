
def date_expenses(cur, sd_datetime=None, ed_datetime=None, offset=0, limit=2000):
    if sd_datetime and ed_datetime:
        cur.execute('''SELECT C.ID as category_id,
                            C.NAME,
                            E.TRANSACTION_DATE,
                            E.DESCRIPTION,
                            E.PRICE,
                            ARRAY_AGG(T.Name) as tags,
                            ARRAY_AGG(T.ID) as tag_ids
                        FROM CATEGORY C
                        JOIN EXPENSES E ON C.ID = E.CATEGORY_ID
                        LEFT JOIN Expense_Tag ET ON E.Expenses_id = ET.Expenses_id
                        LEFT JOIN Tag T ON ET.Tag_id = T.ID
                        WHERE E.TRANSACTION_DATE BETWEEN %s AND %s
                        GROUP BY C.ID, C.NAME, E.TRANSACTION_DATE, E.DESCRIPTION, E.PRICE, E.Expenses_id
                        ORDER BY E.TRANSACTION_DATE DESC
                        LIMIT %s OFFSET %s''',
                    (sd_datetime, ed_datetime, limit, offset))
    elif sd_datetime:
        cur.execute('''SELECT C.ID as category_id,
                            C.NAME,
                            E.TRANSACTION_DATE,
                            E.DESCRIPTION,
                            E.PRICE,
                            ARRAY_AGG(T.Name) as tags,
                            ARRAY_AGG(T.ID) as tag_ids
                        FROM CATEGORY C
                        JOIN EXPENSES E ON C.ID = E.CATEGORY_ID
                        LEFT JOIN Expense_Tag ET ON E.Expenses_id = ET.Expenses_id
                        LEFT JOIN Tag T ON ET.Tag_id = T.ID
                        WHERE E.TRANSACTION_DATE >= %s
                        GROUP BY C.ID, C.NAME, E.TRANSACTION_DATE, E.DESCRIPTION, E.PRICE, E.Expenses_id
                        ORDER BY E.TRANSACTION_DATE DESC
                        LIMIT %s OFFSET %s''',
                    (sd_datetime, limit, offset))
    else:
        cur.execute('''SELECT C.ID as category_id,
                            C.NAME,
                            E.TRANSACTION_DATE,
                            E.DESCRIPTION,
                            E.PRICE,
                            ARRAY_AGG(T.Name) as tags,
                            ARRAY_AGG(T.ID) as tag_ids
                        FROM CATEGORY C
                        JOIN EXPENSES E ON C.ID = E.CATEGORY_ID
                        LEFT JOIN Expense_Tag ET ON E.Expenses_id = ET.Expenses_id
                        LEFT JOIN Tag T ON ET.Tag_id = T.ID
                        WHERE E.TRANSACTION_DATE <= %s
                        GROUP BY C.ID, C.NAME, E.TRANSACTION_DATE, E.DESCRIPTION, E.PRICE, E.Expenses_id
                        ORDER BY E.TRANSACTION_DATE DESC
                        LIMIT %s OFFSET %s''',
                    (ed_datetime, limit, offset))

    return cur.fetchall()
def date_expenses_exact(cur, ex_datetime, offset=0, limit=2000):
    cur.execute('''SELECT C.ID as category_id,
                        C.NAME,
                        E.TRANSACTION_DATE,
                        E.DESCRIPTION,
                        E.PRICE,
                        ARRAY_AGG(T.Name) as tags,
                        ARRAY_AGG(T.ID) as tag_ids
                    FROM CATEGORY C
                    JOIN EXPENSES E ON C.ID = E.CATEGORY_ID
                    LEFT JOIN Expense_Tag ET ON E.Expenses_id = ET.Expenses_id
                    LEFT JOIN Tag T ON ET.Tag_id = T.ID
                    WHERE E.TRANSACTION_DATE = %s
                    GROUP BY C.ID, C.NAME, E.TRANSACTION_DATE, E.DESCRIPTION, E.PRICE, E.Expenses_id
                    ORDER BY E.TRANSACTION_DATE DESC
                    LIMIT %s OFFSET %s''',
                (ex_datetime, limit, offset))
    return cur.fetchall()
def price_query(cur, start_price=None, max_price=None, offset=0, limit=2000):
    if start_price and max_price:
        cur.execute('''SELECT C.ID as category_id,
                            C.NAME,
                            E.PRICE,
                            E.DESCRIPTION,
                            E.TRANSACTION_DATE,
                            ARRAY_AGG(T.Name) as tags,
                            ARRAY_AGG(T.ID) as tag_ids
                        FROM CATEGORY C
                        JOIN EXPENSES E ON C.ID = E.CATEGORY_ID
                        LEFT JOIN Expense_Tag ET ON E.Expenses_id = ET.Expenses_id
                        LEFT JOIN Tag T ON ET.Tag_id = T.ID
                        WHERE E.PRICE BETWEEN %s AND %s
                        GROUP BY C.ID, C.NAME, E.PRICE, E.DESCRIPTION, E.TRANSACTION_DATE, E.Expenses_id
                        ORDER BY E.PRICE
                        LIMIT %s OFFSET %s''',
                    (start_price, max_price, limit, offset))
    elif max_price:
        cur.execute('''SELECT C.ID as category_id,
                            C.NAME,
                            E.PRICE,
                            E.DESCRIPTION,
                            E.TRANSACTION_DATE,
                            ARRAY_AGG(T.Name) as tags,
                            ARRAY_AGG(T.ID) as tag_ids
                        FROM CATEGORY C
                        JOIN EXPENSES E ON C.ID = E.CATEGORY_ID
                        LEFT JOIN Expense_Tag ET ON E.Expenses_id = ET.Expenses_id
                        LEFT JOIN Tag T ON ET.Tag_id = T.ID
                        WHERE E.PRICE <= %s
                        GROUP BY C.ID, C.NAME, E.PRICE, E.DESCRIPTION, E.TRANSACTION_DATE, E.Expenses_id
                        ORDER BY E.PRICE
                        LIMIT %s OFFSET %s
                        ''', (max_price, limit, offset))
    else:
        cur.execute('''SELECT C.ID as category_id,
                            C.NAME,
                            E.PRICE,
                            E.DESCRIPTION,
                            E.TRANSACTION_DATE,
                            ARRAY_AGG(T.Name) as tags,
                            ARRAY_AGG(T.ID) as tag_ids
                        FROM CATEGORY C
                        JOIN EXPENSES E ON C.ID = E.CATEGORY_ID
                        LEFT JOIN Expense_Tag ET ON E.Expenses_id = ET.Expenses_id
                        LEFT JOIN Tag T ON ET.Tag_id = T.ID
                        WHERE E.PRICE >= %s
                        GROUP BY C.ID, C.NAME, E.PRICE, E.DESCRIPTION, E.TRANSACTION_DATE, E.Expenses_id
                        ORDER BY E.PRICE
                        LIMIT %s OFFSET %s
                        ''', (start_price, limit, offset))

    return cur.fetchall()
def exact_price_query(cur, exact_price, offset=0, limit=2000):
    cur.execute('''SELECT C.ID as category_id,
                        C.NAME,
                        E.PRICE,
                        E.DESCRIPTION,
                        E.TRANSACTION_DATE,
                        ARRAY_AGG(T.Name) as tags,
                        ARRAY_AGG(T.ID) as tag_ids
                    FROM CATEGORY C
                    JOIN EXPENSES E ON C.ID = E.CATEGORY_ID
                    LEFT JOIN Expense_Tag ET ON E.Expenses_id = ET.Expenses_id
                    LEFT JOIN Tag T ON ET.Tag_id = T.ID
                    WHERE E.PRICE = %s
                    GROUP BY C.ID, C.NAME, E.PRICE, E.DESCRIPTION, E.TRANSACTION_DATE, E.Expenses_id
                    ORDER BY E.PRICE
                    LIMIT %s OFFSET %s
                ''', (exact_price, limit, offset))
    return cur.fetchall()
def category_expenses_query(cur, category_id, offset=0, limit=2000):
    cur.execute('''
        SELECT
            E.DESCRIPTION,
            E.PRICE,
            E.TRANSACTION_DATE,
            ARRAY_AGG(T.NAME) AS tags,
            ARRAY_AGG(T.ID) AS tag_ids
        FROM EXPENSES E
        LEFT JOIN Expense_Tag ET ON E.Expenses_id = ET.Expenses_id
        LEFT JOIN Tag T ON ET.Tag_id = T.ID
        WHERE E.CATEGORY_ID = %s
        GROUP BY E.Expenses_id
        ORDER BY E.TRANSACTION_DATE DESC
        LIMIT %s OFFSET %s
    ''', (category_id, limit, offset))
    return cur.fetchall()

def generate_query(cur,page,per_page):
    offset = (page - 1) * per_page
    cur.execute(f'''SELECT 
                         E.EXPENSES_ID,
                         E.DESCRIPTION,
                         E.PRICE,       
                         C.NAME,
                         C.ID as category_id,
                         E.TRANSACTION_DATE,
                         array_agg(T.Name) as tags,
                         array_agg(T.ID) as tag_ids
                     FROM CATEGORY C
                     JOIN EXPENSES E ON C.ID = E.CATEGORY_ID
                     LEFT JOIN Expense_Tag ET ON E.Expenses_id = ET.Expenses_id
                     LEFT JOIN Tag T ON ET.Tag_id = T.ID
                     GROUP BY E.Expenses_id, C.Name, C.ID, E.Price, E.Description, E.Transaction_date
                     ORDER BY E.Expenses_id DESC
                     LIMIT %s OFFSET %s''', (per_page, offset))
    results = cur.fetchall()
    return results

def generate_category_tag_chart_query(cur, selected_tag):
    cur.execute("""SELECT C.NAME, COUNT(ET.EXPENSES_ID)
                    FROM CATEGORY C
                    LEFT JOIN EXPENSES E ON C.ID = E.CATEGORY_ID
                    LEFT JOIN EXPENSE_TAG ET ON E.EXPENSES_ID = ET.EXPENSES_ID
                    LEFT JOIN TAG T ON ET.TAG_ID = T.ID
                    WHERE T.NAME = %s
                    GROUP BY C.NAME;""", (selected_tag,))
    return cur.fetchall()

def generate_category_chart_query(cur):
    cur.execute("""SELECT C.NAME,
                        SUM(E.PRICE)
                FROM CATEGORY C
                JOIN EXPENSES E ON C.ID = E.CATEGORY_ID
                GROUP BY C.NAME;""")
    return cur.fetchall()

def calculate_pagination(cur, per_page=20):
    cur.execute("""
       SELECT COUNT(*) FROM (
           SELECT t.ID
           FROM 
               Tag t
           LEFT JOIN 
               Expense_Tag et ON t.ID = et.Tag_id
           LEFT JOIN 
               Expenses e ON et.Expenses_id = e.Expenses_id
           LEFT JOIN 
               Category c ON e.CATEGORY_ID = c.ID
           GROUP BY 
               t.ID
       ) as count_query;
       """)
    total_count = cur.fetchone()[0]
    total_pages = (total_count // per_page) + (1 if total_count % per_page > 0 else 0)

    return total_pages

def get_tag_by_name(cur, tag_id):
    cur.execute("""
            SELECT Name FROM Tag WHERE ID = %s;
        """, (tag_id,))
    tag_name = cur.fetchone()[0]
    return tag_name

def count_tag_usage(cur, tag_id):
    cur.execute('SELECT COUNT(*) FROM Expense_Tag WHERE Tag_id = %s', (tag_id,))
    return cur.fetchone()[0]

def get_total_count_expenses(cur):
    cur.execute("""
       SELECT COUNT(DISTINCT E.EXPENSES_ID)
       FROM 
           Expenses E
       LEFT JOIN 
           Expense_Tag ET ON E.Expenses_id = ET.Expenses_id
       LEFT JOIN 
           Category C ON E.CATEGORY_ID = C.ID
       """)
    total_count = cur.fetchone()[0]
    return total_count
