import psycopg2
from flask import request, render_template, flash, redirect, send_file
from money_control import app, db_conn, cur
from money_control.utils import (get_categories, load_json, check_expenses_id,
                                 category_id_name, suggested_tags, is_valid_custom_tag,
                                 check_category_name, generate_new_json)
from money_control.queries import (date_expenses, price_query, category_expenses_query, generate_query,
                                   generate_category_tag_chart_query, generate_category_chart_query)
from money_control.charts import generate_expense_chart,  generate_tag_expense_chart
from datetime import datetime
import base64
import os
import json
import matplotlib.pyplot as plt


@app.route('/', methods=['GET','POST'])
@app.route('/add_expenses', methods=['GET','POST'])
def add_expenses():
    if request.method == 'POST':
        if 'next_step' in request.form:
            price = request.form['price']
            description = request.form['description']
            date = request.form['date']
            category_id = request.form['category']
            tags = description.split()

            if not description:
                flash('You have to provide some description!', 'error')
                return render_template('index.html', price=price,
                                       description=description, date=date,
                                       category_id=category_id,categories= get_categories())

            return render_template('index.html', tags=tags, price=price,
                                   description=description, date=date, category_id=category_id)

        elif 'submit_expenses' in request.form:
            price = request.form['price']
            description = request.form['description']
            date = request.form['date']
            category_id = request.form['category']
            selected_tag = request.form.getlist('tag')
            expenses_id = check_expenses_id()

            date_time = None

            custom_tag = request.form.getlist('custom_tags')

            try:
                date_time = datetime.strptime(date, "%d.%m.%Y")
            except ValueError:
                flash('Invalid input. Please put the correct form (dd.mm.yyyy)', 'error')

            try:
                price = float(price)
                if price <= 0:
                    raise ValueError('Invalid input.', 'error')
            except ValueError:
                flash('Error. Input has to be number and greater than zero!','error')
                return redirect('/')

            if date_time is not None:
                cur.execute('INSERT INTO EXPENSES (EXPENSES_ID, CATEGORY_ID, PRICE, DESCRIPTION, TRANSACTION_DATE)'
                            ' VALUES (%s, %s, %s, %s, %s) RETURNING EXPENSES_ID',
                            (expenses_id, category_id, price, description, date_time))
                new_expenses_id = cur.fetchone()[0]
                if custom_tag:
                    added_tags = set()
                    for custom_tag_str in custom_tag:
                        custom_tag_names = custom_tag_str.split(',')
                        for custom_tag_name in custom_tag_names:
                            custom_tag_name = custom_tag_name.strip().lower()
                            if custom_tag_name:
                                if is_valid_custom_tag(custom_tag_name):
                                    if custom_tag_name not in added_tags:
                                        added_tags.add(custom_tag_name)
                                        cur.execute('SELECT ID FROM Tag WHERE NAME = %s', (custom_tag_name,))
                                        tag_row = cur.fetchone()
                                        if not tag_row:
                                            cur.execute('INSERT INTO TAG (NAME) VALUES(%s) RETURNING ID',
                                                        (custom_tag_name,))
                                            tag_id = cur.fetchone()[0]
                                        else:
                                            tag_id = tag_row[0]
                                        cur.execute('INSERT INTO EXPENSE_TAG (EXPENSES_ID, TAG_ID) VALUES (%s, %s)',
                                                    (new_expenses_id, tag_id))
                                else:
                                    flash(f'Invalid custom tag: {custom_tag_name}.',
                                          'error')
                if selected_tag:
                    for selected_t in selected_tag:
                        # Check if the tag already exists in the Tag table
                        cur.execute('SELECT ID FROM Tag WHERE NAME = %s', (selected_t,))
                        tag_row = cur.fetchone()
                        if not tag_row:
                            # If the tag does not exist, insert it into the Tag table
                            cur.execute('INSERT INTO Tag (NAME) VALUES (%s) RETURNING ID', (selected_t,))
                            tag_id = cur.fetchone()[0]
                        else:
                            # If the tag already exists, fetch its ID
                            tag_id = tag_row[0]
                        # Insert relation between expense and tag into Expense_Tag table
                        cur.execute('INSERT INTO Expense_Tag (EXPENSES_ID, TAG_ID) VALUES (%s, %s)',
                                    (new_expenses_id, tag_id))
                db_conn.commit()

                flash('Transaction successfully added to database!', 'success')
            return redirect('/')

    elif request.method == 'GET':
        return render_template('index.html', categories=get_categories())


@app.route('/generate', methods=['GET', 'POST'])
def generate():
    if request.method == 'POST':
        if 'delete_expense' in request.form:
            expenses_id = request.form.get('expenses_id')

            try:
                with db_conn:
                    # Delete connection between expense and tags from expense_tag
                    cur.execute('DELETE FROM Expense_Tag WHERE Expenses_id = %s', (expenses_id,))

                    # DEL this expense from expenses table
                    cur.execute('DELETE FROM Expenses WHERE Expenses_id = %s', (expenses_id,))

            except psycopg2.Error as e:
                db_conn.rollback()
                print('Error deleting expense:', e)
            else:
                db_conn.commit()
                flash('Expense successfully deleted', 'success')
    query_res = generate_query(cur)

    results = [{
        'expenses_id': row[0],
        'category': row[1],
        'price': float(row[2]),
        'description': row[3],
        'date': row[4].strftime('%d.%m.%Y'),
        'tag': row[5] if row[5] else None
    } for row in query_res]

    return render_template('generate.html', results=results)


@app.route('/update_transaction/<int:expenses_id>', methods=['GET', 'POST'])
def update_transaction(expenses_id):
    if request.method == 'POST':
        category_id = request.form.get('category')
        price = request.form.get('price')
        description = request.form.get('description')
        date = request.form.get('date')
        tags = request.form.getlist('tag')
        custom_tag = request.form.get('custom_tag')
        date_time = None

        try:
            date_time = datetime.strptime(date, "%d.%m.%Y")
        except ValueError:
            flash('Invalid input. Please put the correct form (dd.mm.yyyy)', 'error')

        try:
            price = float(price)
            if price <= 0:
                raise ValueError('Invalid input.')
        except ValueError:
            flash('Error. Input has to be number and greater than zero!', 'error')

        if not description:
            flash('You have to provide some description!', 'error')

        if date_time is not None and description:
            try:
                with db_conn:
                    # Updating expense in tale Expenses
                    cur.execute(
                        'UPDATE Expenses SET CATEGORY_ID = %s, PRICE = %s, DESCRIPTION = %s, TRANSACTION_DATE = %s WHERE Expenses_id = %s',
                        (category_id, price, description, date_time, expenses_id))

                    # Delete existing links with unchecked tags
                    cur.execute('DELETE FROM Expense_Tag WHERE Expenses_id = %s', (expenses_id,))

                    # Adding new links with tags
                    if tags:
                        for tag in tags:
                            cur.execute('SELECT ID FROM Tag WHERE Name = %s', (tag,))
                            tag_id = cur.fetchone()[0]
                            cur.execute('INSERT INTO Expense_Tag (Expenses_id, Tag_id) VALUES (%s, %s)',
                                        (expenses_id, tag_id))

                    if custom_tag:
                        added_tags = set()
                        custom_tag_names = custom_tag.split(',')
                        for custom_tag_name in custom_tag_names:
                            custom_tag_name = custom_tag_name.strip().lower()
                            if custom_tag_name and is_valid_custom_tag(custom_tag_name):
                                if custom_tag_name not in added_tags:
                                    added_tags.add(custom_tag_name)
                                    cur.execute('SELECT ID FROM Tag WHERE NAME = %s', (custom_tag_name,))
                                    tag_row = cur.fetchone()
                                    if not tag_row:
                                        cur.execute('INSERT INTO TAG (NAME) VALUES(%s) RETURNING ID',
                                                    (custom_tag_name,))
                                        tag_id = cur.fetchone()[0]
                                    else:
                                        tag_id = tag_row[0]
                                    cur.execute('INSERT INTO EXPENSE_TAG (EXPENSES_ID, TAG_ID) VALUES (%s, %s)',
                                                (expenses_id, tag_id))
            except psycopg2.Error as e:
                db_conn.rollback()
                print('Error updating expense:', e)
                flash('Error updating expense', 'error')
            else:
                db_conn.commit()
                flash('Expense successfully updated','success')
                return redirect('/generate')


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
                    WHERE E.EXPENSES_ID = %s
                    GROUP BY E.EXPENSES_ID, C.NAME, E.PRICE, E.DESCRIPTION, E.TRANSACTION_DATE''', (expenses_id,))
    expense_data = []
    for row in cur.fetchall():
        tags = [tag for tag in row[5] if tag is not None] if row[5] else []
        expense_data.append({
            'expenses_id': row[0],
            'category': row[1],
            'price': row[2],
            'description': row[3],
            'date': row[4].strftime('%d.%m.%Y'),
            'tag': tags
        })
    categories = get_categories()
    return render_template('update_transaction.html', expense_data=expense_data, categories=categories)

@app.route('/main_category', methods=['GET', 'POST'])
def main_category():
    cur.execute("""
        SELECT c.id AS category_id,
               c.name AS category,               
               COALESCE(COUNT(e.expenses_id), 0) AS expense_count,
               COALESCE(COUNT(et.tag_id), 0) AS tag_count,
               COALESCE(SUM(e.price), 0) AS total_price
        FROM category c
        LEFT JOIN expenses e ON c.id = e.category_id
        LEFT JOIN expense_tag et ON e.expenses_id = et.expenses_id
        GROUP BY c.id, c.name
        ORDER BY c.name
    """)
    results = cur.fetchall()
    return render_template('main_category.html', results=results)
@app.route('/main_category_id/<int:category_id>', methods=['GET'])
def main_category_id(category_id):
    category_name = check_category_name(category_id)
    cur.execute("""
        SELECT COUNT(et.tag_id) AS tag_count
        FROM category c
        LEFT JOIN expenses e ON c.id = e.category_id
        LEFT JOIN expense_tag et ON e.expenses_id = et.expenses_id
        WHERE c.id = %s
        GROUP BY c.id
    """, (category_id,))
    tag_count_result = cur.fetchone()
    tag_count = tag_count_result[0] if tag_count_result else 0

    cur.execute("""
        SELECT t.name, COUNT(et.tag_id) AS tag_usage
        FROM tag t
        JOIN expense_tag et ON t.id = et.tag_id
        JOIN expenses e ON et.expenses_id = e.expenses_id
        WHERE e.category_id = %s
        GROUP BY t.id
        ORDER BY tag_usage DESC
        LIMIT 3
    """, (category_id,))
    top_tags = cur.fetchall()

    cur.execute("""
        SELECT t.name
        FROM tag t
        JOIN expense_tag et ON t.id = et.tag_id
        JOIN expenses e ON et.expenses_id = e.expenses_id
        WHERE e.category_id = %s 
        AND e.transaction_date >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY t.id
        ORDER BY MAX(e.transaction_date) ASC
        LIMIT 10
    """, (category_id,))
    recent_tags = cur.fetchall()

    cur.execute("""
        SELECT COUNT(*)
        FROM expenses
        WHERE category_id = %s
    """, (category_id,))
    expense_count_result = cur.fetchone()
    expense_count = expense_count_result[0] if expense_count_result else 0

    cur.execute("""
        SELECT description
        FROM expenses
        WHERE category_id = %s
        GROUP BY description
        ORDER BY COUNT(*) DESC
        LIMIT 3
    """, (category_id,))
    top_expenses = cur.fetchall()

    cur.execute("""
        SELECT DISTINCT description 
        FROM expenses 
        WHERE category_id = %s 
        AND transaction_date >= CURRENT_DATE - INTERVAL '7 days' 
        LIMIT 4;
    """, (category_id,))
    latest_expenses = cur.fetchall()

    cur.execute("""
        SELECT COALESCE(SUM(price), 0) AS total_expense
        FROM expenses
        WHERE category_id = %s
    """, (category_id,))
    total_expense_result = cur.fetchone()
    total_expense = total_expense_result[0]

    cur.execute("""
        SELECT COALESCE(ROUND(AVG(e.price), 2), 0) AS average_price
        FROM expenses e
        WHERE e.category_id = %s;
    """, (category_id,))
    average_price_result = cur.fetchone()
    average_price = average_price_result[0]

    cur.execute("""
        SELECT description, transaction_date, price
        FROM expenses
        WHERE category_id = %s
        ORDER BY price DESC
        LIMIT 3;
    """, (category_id,))
    most_expensive_results = cur.fetchall()

    cur.execute("""
        SELECT description, transaction_date, price
        FROM expenses
        WHERE category_id = %s
        ORDER BY price ASC
        LIMIT 3;
    """, (category_id,))
    cheapest_expenses = cur.fetchall()
    graph_path = generate_expense_chart(category_id)
    path_graph = generate_tag_expense_chart(category_id)

    return render_template('main_category_id.html',category_name=category_name, tag_count=tag_count,
                           top_tags=top_tags, recent_tags=recent_tags, expense_count=expense_count,
                           top_expenses=top_expenses, latest_expenses=latest_expenses, total_expense=total_expense,
                           average_price=average_price, most_expensive_results=most_expensive_results,
                           cheapest_expenses=cheapest_expenses, graph_path=graph_path, path_graph=path_graph)
@app.route('/category', methods=['GET', 'POST'])
def category():
    categories = get_categories()
    if request.method == 'POST':
        category_id = request.form['category_id']
        if not category_id:
            flash('Please select a category!', 'error')
            return redirect('/category')

        query_res = category_expenses_query(cur, category_id)
        results = [{
            'price': float(i[0]),
            'description': i[1],
            'transaction_date': i[2].strftime('%d.%m.%Y'),
            'tag': i[3] if i[3] else []} for i in query_res
        ]
        if not results:
            flash('No expenses found for selected category.', 'error')

        return render_template('category.html', categories=categories, final_result=results)
    return render_template('category.html', categories=categories)


@app.route('/price_sort', methods=['GET','POST'])
def price_sort():
    if request.method == 'POST':
        start_price = request.form['start_price']
        max_price = request.form['max_price']

        if not start_price:
            flash("You have to provide Start Price!", 'error')
            return redirect('/price_sort')
        if start_price and max_price:
            if float(start_price) > float(max_price):
                flash('Max price cant be lower then start price!','error')
                return redirect('/price_sort')

        sql_query = price_query(cur, start_price, max_price)
        results = [{
            'category': i[0],
            'price': float(i[1]),
            'description': i[2],
            'date': i[3].strftime('%d.%m.%Y'),
            'tags': i[4]} for i in sql_query]

        if not results:
            flash('No results to display!','neutral')

        return render_template('price_filter.html', results=results)
    return render_template('price_filter.html')


@app.route('/date_filter', methods=['GET','POST'])
def date_fiter():
    if request.method == 'POST':
        start_date = request.form['start_date']
        end_date = request.form['end_date']

        if not start_date:
            flash("Error. You didn't select a start date!",'error')
            return redirect('/date_filter')

        try:
            sd_datetime = datetime.strptime(start_date, '%d.%m.%Y')
            ed_datetime = None
            if end_date:
                ed_datetime = datetime.strptime(end_date, '%d.%m.%Y')
        except ValueError:
            flash('Invalid input or you didnt select start or end date!','error')
            return redirect('/date_filter')

        if end_date and sd_datetime > ed_datetime:
            flash("Start date can't be greater that end date!",'error')
            return redirect('/date_filter')

        query_res = date_expenses(cur, sd_datetime, ed_datetime)
        if not query_res:
            flash('No data for this date range or exact date!', 'neutral')
            return redirect('/date_filter')

        results = [{
            'expense_id': i[0],
            'category': i[1],
            'price': float(i[2]),
            'description': i[3],
            'date': i[4].strftime('%d.%m.%Y'),
            'tags': i[5] if i[5] else []} for i in query_res]

        return render_template('date_filter.html', results=results)
    return render_template('date_filter.html')

@app.route('/extract_expenses', methods=['GET'])
def extract_expenses():
    json_data = load_json()
    filename = os.path.join(os.path.dirname(__file__), 'expenses.json')

    json_object = json.dumps(json_data, indent=2)

    with open(filename, 'w') as file:
        file.write(json_object)

    return send_file(
        filename,
        mimetype='application/json',
        as_attachment=True,
)

@app.context_processor
def utility_processor():
    # This app.context_processor will be available in every jinja as check_category_name
    return dict(check_category_name=check_category_name)

@app.route('/import_json', methods = ['GET', 'POST'])
def import_json():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('You have to insert JSON file!', 'error')
            return redirect('/import_json')

        file = request.files['file']
        if not file or file.filename.strip() == '':
            flash('You have to insert Json file!', 'error')
            return redirect('/import_json')

        if file and file.filename.endswith('.json'):
            try:
                json_data = json.load(file)
            except json.JSONDecodeError:
                flash('Invalid Json format', 'error')
                return redirect('/import_json')
            all_data = []

            try:
                max_expenses_id = None
                for index, item in enumerate(json_data, start=1):
                    required_keys = ['category', 'description', 'price', 'date', 'expenses_id']
                    if not all(key in item for key in required_keys):
                        flash(f'One or more required keys are missing in transaction {index}', 'error')
                        return redirect('/import_json')
                    description = item['description']
                    category_name = item['category']
                    price = item['price']
                    date = item['date']
                    try:
                        datetime.strptime(date, '%d.%m.%Y')
                    except ValueError:
                        flash(f'Invalid date format in transaction {index}. Date must be in format day.month.year',
                              'error')
                        return redirect('/import_json')
                    try:
                        price = float(price)
                    except ValueError:
                        flash(f'Invalid price value in transaction {index}. Price must be a number.', 'error')
                        return redirect('/import_json')
                    if category_name:
                        category_id = category_id_name(category_name)
                        if category_id is not None:
                            if description:
                                expenses_id = item.get('expenses_id')

                                if not expenses_id:
                                    if max_expenses_id is None:
                                        max_expenses_id = check_expenses_id()

                                    expenses_id = max_expenses_id
                                    max_expenses_id +=1
                                else:
                                    flash(f'expenses_id has to be empty field. Error in transaction: {index}', 'error')
                                    return redirect('/import_json')

                                tags = suggested_tags(description)

                                all_data.append({
                                    'tags': tags,
                                    'price': price,
                                    'date': date,
                                    'description': description,
                                    'category_id': category_id,
                                    'expenses_id': expenses_id
                                })
                            else:
                                flash('You need to provide some description!','error')
                                return render_template('import_json.html')
                        else:
                            flash(f'There is no category with that name. Transaction:{index}','error')
                            return render_template('import_json.html')
                    else:
                        flash('Category name not provided!','error')
                        return redirect('import_json.html')
            except ValueError:
                flash(f"Error importing data for transaction {index}", 'error')
                return redirect('/import_json')
            return render_template('submit_json.html', all_data=all_data, transaction_index=index)
    return render_template('import_json.html')

@app.route('/submit_json', methods=['POST'])
def submit_json():
    if request.method == 'POST':
        for index, all_data in enumerate(request.form.getlist('transaction_data'), start=1):
            data = json.loads(all_data)
            price = data['price']
            description = data['description']
            date = data['date']
            category_id = data['category_id']
            expenses_id = data['expenses_id']

            date_time = None

            selected_tag = request.form.getlist(f'selected_tag_{expenses_id}')
            custom_tag = request.form.getlist(f'custom_tag_{expenses_id}')

            try:
                date_time = datetime.strptime(date, "%d.%m.%Y")
            except ValueError:
                flash(f'Invalid input for transaction:{index}. Please put the correct form (dd.mm.yyyy)',
                      'error')

            try:
                price = float(price)
                if price <= 0:
                    raise ValueError('Invalid input.')
            except ValueError:
                flash(f'Error for transaction:{index}. Input has to be number and greater than zero!',
                      'error')
                return redirect('/import_json')


            if date_time is not None:
                cur.execute('INSERT INTO EXPENSES (EXPENSES_ID, CATEGORY_ID, PRICE, DESCRIPTION, TRANSACTION_DATE)'
                            ' VALUES (%s, %s, %s, %s, %s) RETURNING EXPENSES_ID',
                            (expenses_id, category_id, price, description, date_time))
                new_expenses_id = cur.fetchone()[0]
                if custom_tag:
                    added_tags = set()
                    for custom_tag_str in custom_tag:
                        custom_tag_names = custom_tag_str.split(',')
                        for custom_tag_name in custom_tag_names:
                            custom_tag_name = custom_tag_name.strip().lower()
                            if custom_tag_name:
                                if is_valid_custom_tag(custom_tag_name):
                                    if custom_tag_name not in added_tags:
                                        added_tags.add(custom_tag_name)
                                        cur.execute('SELECT ID FROM Tag WHERE NAME = %s', (custom_tag_name,))
                                        tag_row = cur.fetchone()
                                        if not tag_row:
                                            cur.execute('INSERT INTO TAG (NAME) VALUES(%s) RETURNING ID',
                                                        (custom_tag_name,))
                                            tag_id = cur.fetchone()[0]
                                        else:
                                            tag_id = tag_row[0]
                                        cur.execute('INSERT INTO EXPENSE_TAG (EXPENSES_ID, TAG_ID) VALUES (%s, %s)',
                                                    (new_expenses_id, tag_id))
                                else:
                                    flash(f'Invalid custom tag: {custom_tag_name} for transaction {index}.',
                                          'error')
                if selected_tag:
                    for selected_t in selected_tag:
                        # Check if the tag already exists in the Tag table
                        cur.execute('SELECT ID FROM Tag WHERE NAME = %s', (selected_t,))
                        tag_row = cur.fetchone()
                        if not tag_row:
                            # If the tag does not exist, insert it into the Tag table
                            cur.execute('INSERT INTO Tag (NAME) VALUES (%s) RETURNING ID', (selected_t,))
                            tag_id = cur.fetchone()[0]
                        else:
                            # If the tag already exists, fetch its ID
                            tag_id = tag_row[0]
                        # Insert relation between expense and tag into Expense_Tag table
                        cur.execute('INSERT INTO Expense_Tag (EXPENSES_ID, TAG_ID) VALUES (%s, %s)',
                                    (new_expenses_id, tag_id))
                db_conn.commit()
        flash('Transaction successfully added to database!', 'success')
        return redirect('/import_json')

@app.route('/generate_chart')
def generate_chart():
    return render_template('generate_chart.html')

@app.route('/generate_category_chart', methods=['GET', 'POST'])
def generate_category_chart():
    if request.method == 'POST':
        query_result = generate_category_chart_query(cur)

        categories = [i[0] for i in query_result]
        prices = [float(i[1]) for i in query_result]

        plt.figure(figsize=(14,8))
        plt.bar(categories, prices, color=['blue'])
        plt.xlabel('Category')
        plt.ylabel('Price')
        plt.title('Expenses by category')
        # plt.xticks(rotation=25, fontsize=8, ha='right')
        plt.xticks(rotation=25, fontsize=8)
        plt.tight_layout()

        graph = os.path.join(app.root_path, 'static', 'chart.jpg')
        plt.savefig(graph)

        return render_template('generate_category_chart.html', graph='static/chart.jpg')
    return render_template('generate_category_chart.html')

@app.route('/generate_tag_chart', methods=['GET', 'POST'])
def generate_tag_chart():
    chart_img = None
    selected_category_name = None

    if request.method == 'POST':
        selected_category = request.form.get('category')

        cur.execute('SELECT NAME FROM CATEGORY WHERE ID = %s', (selected_category,))
        selected_category_name = cur.fetchone()[0]

        cur.execute("""SELECT T.NAME, COUNT(ET.EXPENSES_ID)
                        FROM TAG T
                        LEFT JOIN EXPENSE_TAG ET ON T.ID = ET.TAG_ID
                        LEFT JOIN EXPENSES E ON ET.EXPENSES_ID = E.EXPENSES_ID
                        WHERE E.CATEGORY_ID = %s
                        GROUP BY T.NAME;""", (selected_category,))
        tag_data = cur.fetchall()

        if not tag_data:
            flash(f"No expenses found for category: {selected_category_name}", 'error')
            return redirect(request.url)

        tags = [row[0] for row in tag_data]
        expenses_counts = [row[1] for row in tag_data]

        plt.figure(figsize=(14, 6), facecolor='#ccd8e5')
        plt.bar(tags, expenses_counts, color='skyblue')
        plt.xlabel('Tag')
        plt.ylabel('Number of Expenses')
        plt.title(f'Expenses by Tag in Category: {selected_category_name}')
        plt.xticks(rotation=45)
        plt.yticks(range(1, max(expenses_counts) + 2))
        plt.tight_layout()

        graph_path = os.path.join(app.root_path, 'static', 'tag_chart.jpg')
        plt.savefig(graph_path)

        # loading chart jpg in base64
        with open(graph_path, "rb") as img_file:
            chart_img = base64.b64encode(img_file.read()).decode('utf-8')

    cur.execute("SELECT ID, Name FROM Category;")
    categories = cur.fetchall()

    return render_template('generate_tag_chart.html', categories=categories, chart_img=chart_img,
                           selected_category_name=selected_category_name)

@app.route('/generate_category_tag_chart', methods=['GET','POST'])
def generate_category_tag_chart():
    selected_tag = request.form.get('tag')
    data = generate_category_tag_chart_query(cur, selected_tag)
    if not data:
        flash(f'Selected tag: {selected_tag} is not mentioned in any category', 'error')

    categories = [row[0] for row in data]
    tag_count = [row[1] for row in data]

    plt.figure(figsize=(14, 6), facecolor='#ccd8e5')
    plt.bar(categories, tag_count, color='skyblue')
    plt.xlabel('Category')
    plt.ylabel(f'Number of appearances for tag: {selected_tag}')
    plt.xticks(rotation=45)
    plt.yticks(range(1, max(tag_count) + 2))
    plt.tight_layout()

    graph_path = os.path.join(app.root_path, 'static', 'tag_chart.jpg')
    plt.savefig(graph_path)

    with open(graph_path, "rb") as img_file:
        chart_img = base64.b64encode(img_file.read()).decode('utf-8')

    return render_template('generate_category_tag_chart.html', chart_img=chart_img, selected_tag=selected_tag)

@app.route('/download_custom')
def download_custom():
    return render_template('download_custom.html')

@app.route('/download_generated_json', methods=['POST'])
def download_generated_json():
    num_obj = request.form.get('num_obj')

    if not num_obj or int(num_obj) <=0:
        flash("You can't generate json file without object", 'error')
        return redirect('/download_custom')

    data = generate_new_json(num_obj)
    file_path = os.path.join(os.path.dirname(__file__), 'generate.json')
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

    return send_file(file_path, as_attachment=True)
