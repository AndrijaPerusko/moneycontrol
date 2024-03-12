from flask import request, render_template, flash, redirect, send_file
from money_control import app, db_conn, cur
from money_control.utils import (get_categories, load_json, check_expenses_id,
                                 category_id_name, suggested_tags, is_valid_custom_tag, check_category_name)
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
                is_not_valid_custom_tag = False
                for custom_tag_str in custom_tag:
                    custom_tag_names = custom_tag_str.split(',')
                    for custom_tag_name in custom_tag_names:
                        custom_tag_name = custom_tag_name.strip().lower()
                        if custom_tag_name and not is_valid_custom_tag(custom_tag_name):
                            flash(f'Invalid custom tag: {custom_tag_names}', 'error')
                            is_not_valid_custom_tag = True
                            break
                if not is_not_valid_custom_tag:
                    cur.execute('INSERT INTO EXPENSES (EXPENSES_ID, CATEGORY_ID, PRICE, DESCRIPTION, TRANSACTION_DATE)'
                                ' VALUES (%s, %s, %s, %s, %s) RETURNING EXPENSES_ID',
                                (expenses_id, category_id, price, description, date_time))
                    new_expenses_id = cur.fetchone()[0]
                    print(f'ovo je exp_id: {new_expenses_id}')
                    if selected_tag:
                        for selected_t in selected_tag:
                            print(f'tag je:{selected_t}')
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
                    if custom_tag:
                        added_tags = set()  # Set za praćenje dodanih prilagođenih oznaka
                        for custom_tag_str in custom_tag:
                            custom_tag_names = custom_tag_str.split(',')
                            for custom_tag_name in custom_tag_names:
                                custom_tag_name = custom_tag_name.strip().lower()
                                if is_valid_custom_tag(custom_tag_name):
                                    # Provjeri je li prilagođena oznaka već dodana
                                    if custom_tag_name not in added_tags:
                                        cur.execute('SELECT ID FROM Tag WHERE NAME = %s', (custom_tag_name,))
                                        tag_row = cur.fetchone()
                                        if not tag_row:
                                            cur.execute('INSERT INTO TAG (NAME) VALUES(%s) RETURNING ID',
                                                        (custom_tag_name,))
                                            tag_id = cur.fetchone()[0]
                                        else:
                                            tag_id = tag_row[0]
                                        # Dodaj prilagođenu oznaku u bazu
                                        cur.execute('INSERT INTO EXPENSE_TAG (EXPENSES_ID, TAG_ID) VALUES (%s, %s)',
                                                    (new_expenses_id, tag_id))
                                        added_tags.add(custom_tag_name)

                db_conn.commit()
                if is_not_valid_custom_tag == True:
                    flash('Transaction unsuccessfull!', 'error')
                    return redirect('/')

                flash('Transaction successfully added to database!', 'success')
            return redirect('/')

    elif request.method == 'GET':
        return render_template('index.html', categories=get_categories())


@app.route('/generate', methods=['GET', 'POST'])
def generate():
    cur.execute('''SELECT 
                        C.NAME,
                        E.PRICE,
                        E.DESCRIPTION,
                        E.TRANSACTION_DATE,
                        array_agg(T.Name) as tags
                    FROM CATEGORY C
                    JOIN EXPENSES E ON C.ID = E.CATEGORY_ID
                    LEFT JOIN Expense_Tag ET ON E.Expenses_id = ET.Expenses_id
                    LEFT JOIN Tag T ON ET.Tag_id = T.ID
                    GROUP BY E.Expenses_id, C.Name, E.Price, E.Description, E.Transaction_date''')
    query_res = cur.fetchall()

    results = [{
        'category': row[0],
        'price': float(row[1]),
        'description': row[2],
        'date': row[3].strftime('%d.%m.%Y'),
        'tag': row[4] if row[4] else []
    } for row in query_res]

    return render_template('generate.html', results=results)


@app.route('/category', methods=['GET', 'POST'])
def category():
    categories = get_categories()
    if request.method == 'POST':
        category_id = request.form['category_id']
        if not category_id:
            flash('Please select a category!', 'error')
            return redirect('/category')
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
        query_res = cur.fetchall()

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

        if max_price:
            cur.execute(f'''SELECT C.NAME,
                                E.PRICE,
                                E.DESCRIPTION,
                                E.TRANSACTION_DATE,
                                array_agg(T.Name) as tags
                            FROM CATEGORY C
                            JOIN EXPENSES E ON C.ID = E.CATEGORY_ID
                            LEFT JOIN Expense_Tag ET ON E.Expenses_id = ET.Expenses_id
                            LEFT JOIN Tag T ON ET.Tag_id = T.ID
                            WHERE E.PRICE BETWEEN %s AND %s
                            GROUP BY C.NAME, E.PRICE, E.DESCRIPTION, E.TRANSACTION_DATE, E.Expenses_id''', (start_price, max_price))
        else:
            cur.execute(f'''SELECT C.NAME,
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

        sql_query = cur.fetchall()
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
            if end_date:
                ed_datetime = datetime.strptime(end_date, '%d.%m.%Y')
        except ValueError:
            flash('Invalid input or you didnt select start or end date!','error')
            return redirect('/date_filter')

        if end_date and sd_datetime > ed_datetime:
            flash("Start date can't be greater that end date!",'error')
            return redirect('/date_filter')

        if end_date:
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

        query_res = cur.fetchall()
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
    # Ova funkcija će biti dostupna u svim šablonima kao 'check_category_name'
    return dict(check_category_name=check_category_name)

@app.route('/import_json', methods = ['GET', 'POST'])
def import_json():
    if request.method == 'POST':

        if 'file' not in request.files:
            flash('You have to insert JSON file!', 'error')
            return redirect('/import_json')

        file = request.files['file']

        if file and file.filename.endswith('.json'):
            try:
                json_data = json.load(file)
            except json.JSONDecodeError:
                flash('Invalid Json format', 'error')
                return redirect('/import_json')
            all_data = []

            try:
                max_expenses_id = None
                for index, item in enumerate(json_data, start=1): #check if it doesn't crash submit_json route
                    required_keys = ['category', 'description', 'price', 'date', 'expenses_id']
                    if not all(key in item for key in required_keys):
                        flash(f'One or more required keys are missing in transaction {index}', 'error')
                        return redirect('/import_json')
                    description = item['description']
                    category_name = item['category']
                    price = float(item['price'])
                    try:
                        price = float(price)
                    except ValueError:
                        flash(f'Invalid price value in transaction {index}. Price must be a number.', 'error')
                        return redirect('/import_json')
                    if category_name:
                        category_id = category_id_name(category_name)
                        if category_id is not None:
                            if description:
                                date = item['date']
                                expenses_id = item.get('expenses_id')

                                if not expenses_id:
                                    if max_expenses_id is None:
                                        max_expenses_id = check_expenses_id()

                                    expenses_id = max_expenses_id
                                    max_expenses_id +=1

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
        return redirect('/')
    return render_template('import_json.html')


@app.route('/submit_json', methods=['POST'])
def submit_json():
    if request.method == 'POST':
        inserted_transactions = False
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
                flash(f'Invalid input for transaction:{index}. Please put the correct form (dd.mm.yyyy)', 'error')

            try:
                price = float(price)
                if price <= 0:
                    raise ValueError('Invalid input.')
            except ValueError:
                flash(f'Error for transaction:{index}. Input has to be number and greater than zero!', 'error')
                return redirect('/import_json')


            if date_time is not None:
                is_not_valid_custom_tag = False
                for custom_tag_str in custom_tag:
                    custom_tag_names = custom_tag_str.split(',')
                    for custom_tag_name in custom_tag_names:
                        custom_tag_name = custom_tag_name.strip().lower()
                        if custom_tag_name and not is_valid_custom_tag(custom_tag_name):
                            flash(f'Invalid custom tag: {custom_tag_names} for transaction {index}.', 'error')
                            is_not_valid_custom_tag = True
                            break
                if not is_not_valid_custom_tag:
                    cur.execute('INSERT INTO EXPENSES (EXPENSES_ID, CATEGORY_ID, PRICE, DESCRIPTION, TRANSACTION_DATE)'
                                ' VALUES (%s, %s, %s, %s, %s) RETURNING EXPENSES_ID',
                                (expenses_id, category_id, price, description, date_time))
                    new_expenses_id = cur.fetchone()[0]
                    print(f'ovo je exp_id: {new_expenses_id}')
                    if selected_tag:
                        for selected_t in selected_tag:
                            print(f'tag je:{selected_t}')
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
                            cur.execute('INSERT INTO Expense_Tag (EXPENSES_ID, TAG_ID) VALUES (%s, %s)', (new_expenses_id, tag_id))
                    if custom_tag:
                        added_tags = set()  # Set za praćenje dodanih prilagođenih oznaka
                        for custom_tag_str in custom_tag:
                            custom_tag_names = custom_tag_str.split(',')
                            for custom_tag_name in custom_tag_names:
                                custom_tag_name = custom_tag_name.strip().lower()
                                if is_valid_custom_tag(custom_tag_name):
                                    # Provjeri je li prilagođena oznaka već dodana
                                    if custom_tag_name not in added_tags:
                                        cur.execute('SELECT ID FROM Tag WHERE NAME = %s', (custom_tag_name,))
                                        tag_row = cur.fetchone()
                                        if not tag_row:
                                            cur.execute('INSERT INTO TAG (NAME) VALUES(%s) RETURNING ID',
                                                        (custom_tag_name,))
                                            tag_id = cur.fetchone()[0]
                                        else:
                                            tag_id = tag_row[0]
                                        # Dodaj prilagođenu oznaku u bazu
                                        cur.execute('INSERT INTO EXPENSE_TAG (EXPENSES_ID, TAG_ID) VALUES (%s, %s)',
                                                    (new_expenses_id, tag_id))
                                        added_tags.add(custom_tag_name)
                inserted_transactions = True
                db_conn.commit()
        if inserted_transactions:
            if is_not_valid_custom_tag:
                flash('Not all transactions were added due to invalid custom tags!', 'error')
            else:
                flash('Transaction successfully added to database!', 'success')
        return redirect('/import_json')

@app.route('/generate_chart')
def generate_chart():
    return render_template('generate_chart.html')

@app.route('/generate_category_chart', methods=['GET', 'POST'])
def generate_category_chart():
    if request.method == 'POST':
        query = ("""SELECT C.NAME,
                            SUM(E.PRICE)
                    FROM CATEGORY C
                    JOIN EXPENSES E ON C.ID = E.CATEGORY_ID
                    GROUP BY C.NAME;""")
        cur.execute(query)
        query_result = cur.fetchall()

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

        plt.figure(figsize=(14, 6))
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

