
def date_expenses(cur, sd_datetime, ed_datetime=None):
    if ed_datetime:
        cur.execute('''SELECT E.EXPENSES_ID, C.NAME, E.PRICE, E.DESCRIPTION, E.TRANSACTION_DATE, array_agg(T.NAME) as tags
                            FROM EXPENSES E
                            JOIN CATEGORY C ON C.ID = E.CATEGORY_ID
                            LEFT JOIN Expense_Tag ET ON E.EXPENSES_ID = ET.Expenses_id
                            LEFT JOIN Tag T ON ET.Tag_id = T.ID
                            WHERE E.TRANSACTION_DATE BETWEEN %s AND %s
                            GROUP BY E.EXPENSES_ID, C.NAME, E.PRICE, E.DESCRIPTION, E.TRANSACTION_DATE
                            ORDER BY E.TRANSACTION_DATE DESC''', (sd_datetime, ed_datetime))
    else:
        cur.execute('''SELECT E.EXPENSES_ID, C.NAME, E.PRICE, E.DESCRIPTION, E.TRANSACTION_DATE, array_agg(T.NAME) as tags
                            FROM EXPENSES E
                            JOIN CATEGORY C ON C.ID = E.CATEGORY_ID
                            LEFT JOIN Expense_Tag ET ON E.EXPENSES_ID = ET.Expenses_id
                            LEFT JOIN Tag T ON ET.Tag_id = T.ID
                            WHERE E.TRANSACTION_DATE = %s
                            GROUP BY E.EXPENSES_ID, C.NAME, E.PRICE, E.DESCRIPTION, E.TRANSACTION_DATE
                            ORDER BY E.TRANSACTION_DATE DESC''', (sd_datetime,))

    return cur.fetchall()

def price_query(cur, start_price, max_price=None):
    if max_price:
        cur.execute('''SELECT C.NAME,
                            E.PRICE,
                            E.DESCRIPTION,
                            E.TRANSACTION_DATE,
                            array_agg(T.Name) as tags
                        FROM CATEGORY C
                        JOIN EXPENSES E ON C.ID = E.CATEGORY_ID
                        LEFT JOIN Expense_Tag ET ON E.Expenses_id = ET.Expenses_id
                        LEFT JOIN Tag T ON ET.Tag_id = T.ID
                        WHERE E.PRICE BETWEEN %s AND %s
                        GROUP BY C.NAME, E.PRICE, E.DESCRIPTION, E.TRANSACTION_DATE, E.Expenses_id''',
                    (start_price, max_price))
    else:
        cur.execute('''SELECT C.NAME,
                            E.PRICE,
                            E.DESCRIPTION,
                            E.TRANSACTION_DATE,
                            array_agg(T.Name) as tags
                        FROM CATEGORY C
                        JOIN EXPENSES E ON C.ID = E.CATEGORY_ID
                        LEFT JOIN Expense_Tag ET ON E.Expenses_id = ET.Expenses_id
                        LEFT JOIN Tag T ON ET.Tag_id = T.ID
                        WHERE E.PRICE = %s
                        GROUP BY C.NAME, E.PRICE, E.DESCRIPTION, E.TRANSACTION_DATE, E.Expenses_id''', (start_price,))

    return cur.fetchall()

def category_expenses_query(cur, category_id):
    cur.execute('''
        SELECT
            E.PRICE,
            E.DESCRIPTION,
            E.TRANSACTION_DATE,
            ARRAY_AGG(T.NAME) AS tags
        FROM EXPENSES E
        LEFT JOIN Expense_Tag ET ON E.Expenses_id = ET.Expenses_id
        LEFT JOIN Tag T ON ET.Tag_id = T.ID
        WHERE E.CATEGORY_ID = %s
        GROUP BY E.Expenses_id
    ''', (category_id,))
    return cur.fetchall()

def generate_query(cur):
    cur.execute('''SELECT 
                         E.EXPENSES_ID,
                         C.NAME,
                         E.PRICE,
                         E.DESCRIPTION,
                         E.TRANSACTION_DATE,
                         array_agg(T.Name) as tags
                     FROM CATEGORY C
                     JOIN EXPENSES E ON C.ID = E.CATEGORY_ID
                     LEFT JOIN Expense_Tag ET ON E.Expenses_id = ET.Expenses_id
                     LEFT JOIN Tag T ON ET.Tag_id = T.ID
                     GROUP BY E.Expenses_id, C.Name, E.Price, E.Description, E.Transaction_date
                     ORDER BY E.Expenses_id DESC''')
    return cur.fetchall()

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

