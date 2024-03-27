import os
import datetime
import matplotlib.pyplot as plt
from money_control import app, cur
from money_control.utils import check_category_name
from datetime import timedelta


def generate_expense_chart(category_id):
    cur.execute("""
        SELECT description, SUM(price) as total_price
        FROM expenses
        WHERE category_id = %s
        GROUP BY description
    """, (category_id,))
    expenses_data = cur.fetchall()

    descriptions = [expense[0] for expense in expenses_data]
    prices = [float(expense[1]) for expense in expenses_data]

    plt.figure(figsize=(25, 11))
    plt.bar(descriptions, prices, color='blue')
    plt.xlabel('Expenses')
    plt.ylabel('Price')
    plt.xticks(rotation=60)
    plt.tight_layout()

    graph_dir = os.path.join(app.root_path, 'static')
    graph_filename = 'category_chart.png'
    graph_path = os.path.join(graph_dir, graph_filename)
    plt.savefig(graph_path)

    return graph_path

def generate_tag_expense_chart(category_id):
    cur.execute("""
        SELECT t.name, COALESCE(SUM(e.price), 0) AS total_price
        FROM tag t
        LEFT JOIN expense_tag et ON t.id = et.tag_id
        LEFT JOIN expenses e ON et.expenses_id = e.expenses_id
        WHERE e.category_id = %s
        GROUP BY t.id
    """, (category_id,))
    tag_expense_data = cur.fetchall()

    tags = [data[0] for data in tag_expense_data]
    prices = [float(data[1]) for data in tag_expense_data]

    plt.figure(figsize=(25, 11))
    plt.bar(tags, prices, color='green')
    plt.xlabel('Tags')
    plt.ylabel('Total Price')
    plt.xticks(rotation=60)
    plt.tight_layout()

    graph_dir = os.path.join(app.root_path, 'static')
    graph_filename = 'tag_price.png'
    graph_path = os.path.join(graph_dir, graph_filename)
    plt.savefig(graph_path)

    return graph_path

def generate_price_description_chart_for_category(category_id):
    cur.execute("""
            SELECT DATE(TRANSACTION_DATE), SUM(PRICE)
            FROM expenses e
            WHERE e.category_id = %s 
            AND e.TRANSACTION_DATE >= CURRENT_DATE - INTERVAL '7 days'
            AND e.TRANSACTION_DATE <= CURRENT_DATE
            GROUP BY DATE(TRANSACTION_DATE)
        """, (category_id,))

    expenses_data = cur.fetchall()

    # Generisanje liste datuma unutar poslednjih 7 dana
    end_date = datetime.date.today()
    start_date = end_date - timedelta(days=7)
    all_dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]

    # Obrada rezultata upita i izdvajanje datuma i sumiranih cena
    dates = []
    total_prices = []

    for date in all_dates:
        found = False
        for expense in expenses_data:
            if str(expense[0]) == date:
                dates.append(str(expense[0]))
                total_prices.append(float(expense[1]))
                found = True
                break
        if not found:
            dates.append(date)
            total_prices.append(0.0)

    plt.figure(figsize=(15, 7))
    plt.bar(dates, total_prices, color='red')

    plt.xlabel('Date')
    plt.ylabel('Total Price')
    plt.xticks(rotation=45)
    plt.tight_layout()

    graph_dir = os.path.join(app.root_path, 'static')
    graph_filename = 'generate_price_description_chart_for_category.png'
    graph_path = os.path.join(graph_dir, graph_filename)
    plt.savefig(graph_path)

    return graph_path

def generate_price_tag_chart_for_category(category_id):
    cur.execute("""
        SELECT DATE(e.TRANSACTION_DATE), SUM(DISTINCT e.PRICE) as total_price
        FROM expenses e
        JOIN Expense_Tag et ON e.Expenses_id = et.Expenses_id
        WHERE e.category_id = %s
        AND e.TRANSACTION_DATE >= CURRENT_DATE - INTERVAL '7 days'
        AND e.TRANSACTION_DATE <= CURRENT_DATE
        GROUP BY DATE(e.TRANSACTION_DATE)
    """, (category_id,))

    tag_data = cur.fetchall()

    # Generisanje liste datuma unutar poslednjih 7 dana
    end_date = datetime.date.today()
    start_date = end_date - timedelta(days=7)
    all_dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]

    # Obrada rezultata upita i izdvajanje datuma i ukupne cene
    dates = [row[0].strftime('%Y-%m-%d') for row in tag_data]
    total_prices = [float(row[1]) for row in tag_data]

    # Dopunjavanje liste svim datuma u poslednjih 7 dana i postavljanje cena na 0 za nedostajuće datume
    dates_dict = dict(zip(dates, total_prices))
    total_prices_filled = [dates_dict.get(date, 0) for date in all_dates]


    plt.figure(figsize=(15, 7))
    plt.bar(all_dates, total_prices_filled, color='pink')

    plt.xlabel('Date')
    plt.ylabel('Total Price')
    plt.xticks(rotation=45)
    plt.tight_layout()

    graph_dir = os.path.join(app.root_path, 'static')
    graph_filename = 'generate_price_tag_chart_for_category.png'
    graph_path = os.path.join(graph_dir, graph_filename)
    plt.savefig(graph_path)

    return graph_path

def generate_price_tag_category_chart(tag_id):
    cur.execute("""
        SELECT c.Name, SUM(e.PRICE) as total_price
        FROM expenses e
        JOIN Expense_Tag et ON e.Expenses_id = et.Expenses_id
        JOIN Category c ON e.CATEGORY_ID = c.ID
        WHERE et.Tag_id = %s
        GROUP BY c.Name
    """, (tag_id,))

    tag_data = cur.fetchall()

    categories = [row[0] for row in tag_data]
    total_prices = [float(row[1]) for row in tag_data]

    plt.figure(figsize=(10, 6))
    plt.bar(categories, total_prices, color='blue')
    plt.xlabel('Categories')
    plt.ylabel('Total Price')
    plt.xticks(rotation=45)
    plt.tight_layout()

    graph_dir = os.path.join(app.root_path, 'static')
    graph_filename = "generate_price_tag_category_chart.png"
    graph_path = os.path.join(graph_dir, graph_filename)
    plt.savefig(graph_path)

    return graph_path

def generate_price_chart_for_tag_expenses(tag_id):
    cur.execute("""
        SELECT e.description, SUM(e.PRICE) as total_price
        FROM expenses e
        JOIN Expense_Tag et ON e.Expenses_id = et.Expenses_id
        WHERE et.Tag_id = %s
        GROUP BY e.description
    """, (tag_id,))

    tag_data = cur.fetchall()

    descriptions = [row[0] for row in tag_data]
    total_prices = [float(row[1]) for row in tag_data]

    plt.figure(figsize=(10, 6))
    plt.bar(descriptions, total_prices, color='green')
    plt.xlabel('Expenses')
    plt.ylabel('Total Price')
    plt.xticks(rotation=45)
    plt.tight_layout()

    graph_dir = os.path.join(app.root_path, 'static')
    graph_filename = 'generate_price_chart_for_tag_expenses.png'
    graph_path = os.path.join(graph_dir, graph_filename)
    plt.savefig(graph_path)

    return graph_path

def generate_price_chart_for_tag_by_date(tag_id):
    # Generisanje liste datuma unutar poslednjih 7 dana
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=6)
    all_dates = [(start_date + datetime.timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]

    cur.execute("""
        SELECT DATE(e.TRANSACTION_DATE), SUM(e.PRICE) as total_price
        FROM expenses e
        JOIN Expense_Tag et ON e.Expenses_id = et.Expenses_id
        JOIN Category c ON e.CATEGORY_ID = c.ID
        WHERE et.Tag_id = %s
        AND e.TRANSACTION_DATE >= %s
        AND e.TRANSACTION_DATE <= %s
        GROUP BY DATE(e.TRANSACTION_DATE)
    """, (tag_id, start_date, end_date))

    tag_data = cur.fetchall()

    dates = [row[0].strftime('%Y-%m-%d') for row in tag_data]
    total_prices = [float(row[1]) for row in tag_data]

    # Dopunjavanje liste svim datuma u poslednjih 7 dana i postavljanje cena na 0 za nedostajuće datume
    dates_dict = dict(zip(dates, total_prices))
    total_prices_filled = [dates_dict.get(date, 0) for date in all_dates]

    # Generisanje grafikona
    plt.figure(figsize=(15, 7))
    plt.bar(all_dates, total_prices_filled, color='red')
    plt.xlabel('Date')
    plt.ylabel('Total Price')
    plt.xticks(rotation=45)
    plt.tight_layout()

    graph_dir = os.path.join(app.root_path, 'static')
    graph_filename = 'generate_price_chart_for_tag_by_date.png'
    graph_path = os.path.join(graph_dir, graph_filename)
    plt.savefig(graph_path)

    return graph_path


def generate_price_chart_for_tag_last_30_days(tag_id):
    cur.execute("""
        SELECT DATE(e.TRANSACTION_DATE), SUM(e.PRICE) as total_price
        FROM expenses e
        JOIN Expense_Tag et ON e.Expenses_id = et.Expenses_id
        JOIN Category c ON e.CATEGORY_ID = c.ID
        WHERE et.Tag_id = %s
        AND e.TRANSACTION_DATE >= CURRENT_DATE - INTERVAL '30 days'
        AND e.TRANSACTION_DATE <= CURRENT_DATE
        GROUP BY DATE(e.TRANSACTION_DATE)
    """, (tag_id,))

    tag_data = cur.fetchall()

    total_prices = [float(row[1]) for row in tag_data]

    # Generisanje liste svih datuma za koje postoji cena
    existing_dates = [row[0].strftime('%Y-%m-%d') for row in tag_data]
    existing_prices = [price for price in total_prices if price != 0]

    plt.figure(figsize=(15, 7))
    plt.bar(existing_dates, existing_prices, color='purple')
    plt.xlabel('Date')
    plt.ylabel('Total Price')
    plt.xticks(rotation=45)
    plt.tight_layout()

    graph_dir = os.path.join(app.root_path, 'static')
    graph_filename = 'generate_price_chart_for_tag_last_30_days.png'
    graph_path = os.path.join(graph_dir, graph_filename)
    plt.savefig(graph_path)

    return graph_path

def generate_description_chart_by_category(description):
    cur.execute("""
        SELECT c.Name, SUM(e.PRICE) as total_price
        FROM expenses e
        JOIN Category c ON e.CATEGORY_ID = c.ID
        WHERE e.description = %s
        GROUP BY c.Name
    """, (description,))

    category_data = cur.fetchall()

    categories = [row[0] for row in category_data]
    total_prices = [float(row[1]) for row in category_data]

    plt.figure(figsize=(10, 6))
    plt.bar(categories, total_prices, color='blue')
    plt.xlabel('Categories')
    plt.ylabel('Total Price')
    plt.xticks(rotation=45)
    plt.tight_layout()

    graph_dir = os.path.join(app.root_path, 'static')
    graph_filename = 'generate_description_chart_by_category.png'
    graph_path = os.path.join(graph_dir, graph_filename)
    plt.savefig(graph_path)

    return graph_path

def generate_description_chart_by_tag(description):
    cur.execute("""
        SELECT t.Name, SUM(e.PRICE) as total_price
        FROM expenses e
        JOIN Expense_Tag et ON e.Expenses_id = et.Expenses_id
        JOIN Tag t ON et.Tag_id = t.ID
        WHERE e.description = %s
        GROUP BY t.Name
    """, (description,))

    tag_data = cur.fetchall()

    tags = [row[0] for row in tag_data]
    total_prices = [float(row[1]) for row in tag_data]

    plt.figure(figsize=(10, 6))
    plt.bar(tags, total_prices, color='green')
    plt.xlabel('Tags')
    plt.ylabel('Total Price')
    plt.xticks(rotation=45)
    plt.tight_layout()

    graph_dir = os.path.join(app.root_path, 'static')
    graph_filename = 'generate_description_chart_by_tag.png'
    graph_path = os.path.join(graph_dir, graph_filename)
    plt.savefig(graph_path)

    return graph_path

def generate_last_seven_days_description(description):
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=6)
    all_dates = [(start_date + datetime.timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]

    cur.execute("""
        SELECT DATE(e.TRANSACTION_DATE), COALESCE(SUM(e.PRICE), 0) as total_price
        FROM Expenses e
        WHERE e.DESCRIPTION = %s
        AND e.TRANSACTION_DATE >= CURRENT_DATE - INTERVAL '7 days'
        AND e.TRANSACTION_DATE <= CURRENT_DATE
        GROUP BY DATE(e.TRANSACTION_DATE)
        ORDER BY DATE(e.TRANSACTION_DATE);
    """, (description,))

    expense_data = cur.fetchall()

    expense_dates = [row[0].strftime('%Y-%m-%d') for row in expense_data]
    total_prices = [float(row[1]) for row in expense_data]

    dates_dict = dict(zip(expense_dates, total_prices))
    total_prices_filled = [dates_dict.get(date, 0) for date in all_dates]

    plt.figure(figsize=(15, 7))
    plt.bar(all_dates, total_prices_filled, color='red')
    plt.xlabel('Date')
    plt.ylabel('Total Price')
    plt.xticks(rotation=45)
    plt.tight_layout()

    graph_dir = os.path.join(app.root_path, 'static')
    graph_filename = 'generate_last_seven_days_description.png'
    graph_path = os.path.join(graph_dir, graph_filename)
    plt.savefig(graph_path)

    return graph_path

def generate_last_thirty_days_description(description):
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=30)

    cur.execute("""
        SELECT DATE(e.TRANSACTION_DATE), COALESCE(SUM(e.PRICE), 0) as total_price
        FROM Expenses e
        WHERE e.DESCRIPTION = %s
        AND e.TRANSACTION_DATE >= CURRENT_DATE - INTERVAL '30 days'
        AND e.TRANSACTION_DATE <= CURRENT_DATE
        GROUP BY DATE(e.TRANSACTION_DATE)
        ORDER BY DATE(e.TRANSACTION_DATE);
    """, (description,))

    expense_data = cur.fetchall()

    expense_dates = [row[0].strftime('%Y-%m-%d') for row in expense_data]
    total_prices = [float(row[1]) for row in expense_data]

    plt.figure(figsize=(15, 7))
    plt.bar(expense_dates, total_prices, color='purple')
    plt.xlabel('Date')
    plt.ylabel('Total Price')
    plt.xticks(rotation=45)
    plt.tight_layout()

    graph_dir = os.path.join(app.root_path, 'static')
    graph_filename = 'generate_last_thirty_days_description.png'
    graph_path = os.path.join(graph_dir, graph_filename)
    plt.savefig(graph_path)

    return graph_path
