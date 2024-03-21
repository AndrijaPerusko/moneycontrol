import os
import matplotlib.pyplot as plt
from money_control import app, cur
from money_control.utils import check_category_name


def generate_expense_chart(category_id):
    # Ovde dodaj SQL upit koji izvlači sve expenses za dati category_id sa njihovim cenama
    category_name = check_category_name(category_id)
    cur.execute("""
        SELECT description, price
        FROM expenses
        WHERE category_id = %s
    """, (category_id,))
    expenses_data = cur.fetchall()

    # Obrada rezultata upita i izdvajanje expenses i cena
    descriptions = [expense[0] for expense in expenses_data]
    prices = [float(expense[1]) for expense in expenses_data]

    # Generisanje grafikona
    plt.figure(figsize=(10, 5))
    plt.bar(descriptions, prices, color='blue')
    plt.xlabel('Expenses')
    plt.ylabel('Price')
    # plt.title('Expenses for Category: {}'.format(category_name))
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Čuvanje grafikona kao slike (opciono)
    graph_dir = os.path.join(app.root_path, 'static')
    graph_filename = 'category_chart.png'
    graph_path = os.path.join(graph_dir, graph_filename)
    plt.savefig(graph_path)

    return graph_path

def generate_tag_expense_chart(category_id):
    # Izvlačenje podataka iz baze za tagove i cene
    cur.execute("""
        SELECT t.name, COALESCE(SUM(e.price), 0) AS total_price
        FROM tag t
        LEFT JOIN expense_tag et ON t.id = et.tag_id
        LEFT JOIN expenses e ON et.expenses_id = e.expenses_id
        WHERE e.category_id = %s
        GROUP BY t.id
    """, (category_id,))
    tag_expense_data = cur.fetchall()

    # Razdvajanje tagova i cena
    tags = [data[0] for data in tag_expense_data]
    prices = [float(data[1]) for data in tag_expense_data]

    # Generisanje grafikona
    plt.figure(figsize=(10, 6))
    plt.bar(tags, prices, color='green')
    plt.xlabel('Tags')
    plt.ylabel('Total Price')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Čuvanje grafikona kao slike
    graph_dir = os.path.join(app.root_path, 'static')
    graph_filename = 'tag_price.png'
    graph_path = os.path.join(graph_dir, graph_filename)
    plt.savefig(graph_path)

    return graph_path