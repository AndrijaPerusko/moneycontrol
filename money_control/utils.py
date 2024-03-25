from money_control import cur
import string
import re

def get_categories():
    cur.execute('SELECT * FROM category')
    return cur.fetchall()

def load_json():
    cur.execute('''
        SELECT
            E.Expenses_id,
            E.TRANSACTION_DATE,
            E.DESCRIPTION,
            E.PRICE,
            C.Name AS Category,
            array_agg(T.Name) AS Tags
        FROM
            Expenses E
        LEFT JOIN
            Category C ON E.CATEGORY_ID = C.ID
        LEFT JOIN
            Expense_Tag ET ON E.Expenses_id = ET.Expenses_id
        LEFT JOIN
            Tag T ON ET.Tag_id = T.ID
        GROUP BY
            E.Expenses_id, E.TRANSACTION_DATE, E.DESCRIPTION, E.PRICE, C.Name
        ORDER BY
            E.expenses_id
    ''')
    exp_data = cur.fetchall()

    results = [{
        'category': i[4],
        'transaction #': i[0],
        'date': i[1].strftime('%d.%m.%Y'),
        'description': i[2],
        'price': float(i[3]),
        'tags': i[5] if i[5] else []
    } for i in exp_data]

    return results
def check_expenses_id():
    cur.execute('''SELECT MAX(EXPENSES_ID) FROM EXPENSES''')
    last_expenses_id = cur.fetchone()[0]
    return last_expenses_id + 1 if last_expenses_id is not None else 1

def category_id_name(category_name):
    cur.execute("SELECT ID FROM CATEGORY WHERE name = %s", (category_name,))
    category_id = cur.fetchone()
    if category_id:
        return category_id[0]
    else:
        return None

def check_category_name(category_id):
    cur.execute("SELECT NAME FROM CATEGORY WHERE ID = %s", (category_id,))
    result = cur.fetchone()
    if result:
        return result[0]
    else:
        return None

def suggested_tags(description):
    stop_words = {'and', 'on', 'at', 'or', 'but', 'if', 'then', 'else', 'when', 'a'}

    if isinstance(description, str):
        words = description.split()
    else:
        words = description

    unique_tags = set()
    for word in words:
        word = word.strip(string.punctuation)
        if word and word.lower() not in stop_words:
            unique_tags.add(word.lower())

    return list(unique_tags)


def validate_custom_tags(custom_tags):
    pattern = re.compile(r'^[a-zA-Z0-9,\s]+$')
    for tag in custom_tags:
        if not pattern.match(tag):
            return False
    return True

def is_valid_custom_tag(tag):
    pattern = r'^[a-zA-Z0-9,\s]+$'
    return bool(re.match(pattern, tag))

def generate_new_json(user_input):
    data = []
    for i in range(int(user_input)):
        obj = {
            "category_id": "",
            "description": "",
            "price": "",
            "date": "",
            "expenses_id": ""
        }
        data.append(obj)
        print(user_input)
    return data

