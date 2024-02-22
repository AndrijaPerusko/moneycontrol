from money_control import cur
import string

def get_categories():
    cur.execute('SELECT * FROM category')
    return cur.fetchall()

def load_json():
    cur.execute('''SELECT
                C.NAME,
                E.EXPENSES_ID,
                E.TAG,
                E.PRICE,
                E.TRANSACTION_DATE
                FROM CATEGORY C
                JOIN EXPENSES E ON C.ID = E.CATEGORY_ID
                ORDER BY C.NAME''')
    exp_data = cur.fetchall()

    results = [{
        'category': i[0],
        'transaction #': i[1],
        'description': i[2],
        'price': float(i[3]),
        'date': i[4].strftime('%d.%m.%Y')} for i in exp_data]

    return results

def check_expenses_id():
    cur.execute('''SELECT COUNT(EXPENSES_ID) FROM EXPENSES''')
    res = cur.fetchall()[0]
    return res[0] + 1 if res else 1

def category_id_name(category_name):
    cur.execute("SELECT ID FROM CATEGORY WHERE name = %s", (category_name,))
    category_id = cur.fetchone()
    if category_id:
        return category_id[0]
    else:
        return None

def suggested_tags(description):
    stop_words = {'and', 'on', 'at', 'or', 'but', 'if', 'then', 'else', 'when', 'a'}

    if isinstance(description, str):
        words = description.split()
    else:
        words = description
    # words = description.split() if isinstance(description, str) else description

    filtered_words = []
    for word in words:
        word = word.strip(string.punctuation)
        if word and word.lower() not in stop_words:
            filtered_words.append(word)

    # filtered_words = [word.strip(string.punctuation).lower() for word in words
    #                   if word.strip(string.punctuation).lower() not in stop_words
    #                   and word.strip(string.punctuation) ]

    return filtered_words