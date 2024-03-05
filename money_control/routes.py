from flask import request, render_template, flash, redirect, jsonify, send_file
from money_control import app, db_conn, cur
from money_control.utils import get_categories, load_json, check_expenses_id, category_id_name, suggested_tags
from datetime import datetime
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
            return render_template('index.html', tags=tags, price=price,
                                   description=description, date=date, category_id=category_id)

        elif 'submit_expenses' in request.form:
            price = request.form['price']
            description = request.form['description']
            date = request.form['date']
            category_id = request.form['category']
            tag = request.form['tag']

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
                flash('Error. Input has to be number and greater than zero!','error')
                return redirect('/')
            if date_time is not None:
                cur.execute('INSERT INTO EXPENSES (CATEGORY_ID, PRICE, DESCRIPTION, TAG, TRANSACTION_DATE) VALUES (%s, %s, %s, %s, %s)',
                            (category_id, price, description, tag, date_time))
                db_conn.commit()
                flash('Transaction successfully added to database!', 'success')
            return redirect('/')

    elif request.method == 'GET':
        return render_template('index.html', categories=get_categories())


@app.route('/generate', methods=['GET', 'POST'])
def generate():
    cur.execute('''SELECT
                C.NAME,
                E.PRICE,
                E.TAG,
                E.TRANSACTION_DATE
            FROM CATEGORY C
            JOIN EXPENSES E ON C.ID = E.CATEGORY_ID ''')
    query_res = cur.fetchall()

    results = [{
        'category': i[0],
        'price': float(i[1]),
        'description': i[2],
        'date': i[3].strftime('%d.%m.%Y')} for i in query_res
    ]

    return render_template('generate.html', results=results)


@app.route('/category', methods=['GET', 'POST'])
def category():
    categories = get_categories()
    if request.method == 'POST':
        category_id = request.form['category_id']
        if not category_id:
            flash('Please select a category!')
            return redirect('/category')
        cur.execute('''
            SELECT
                PRICE,
                TAG,
                TRANSACTION_DATE
            FROM EXPENSES
            WHERE CATEGORY_ID = %s
        ''', (category_id,))
        query_res = cur.fetchall()

        results = [{
            'price': float(i[0]),
            'description': i[1],
            'transaction_date': i[2].strftime('%d.%m.%Y')} for i in query_res
        ]
        if not results:
            flash('No expenses found for selected category.')

        return render_template('category.html', categories=categories, final_result=results)
    return render_template('category.html', categories=categories)




@app.route('/price_sort', methods=['GET','POST'])
def price_sort():
    if request.method == 'POST':
        start_price = request.form['start_price']
        max_price = request.form['max_price']

        if not start_price:
            flash("You have to provide Start Price!")
            return redirect('/price_sort')
        if start_price and max_price:
            if float(start_price) > float(max_price):
                flash('Max price cant be lower then start price!')
                return redirect('/price_sort')


        if max_price:
            cur.execute(f'''SELECT C.NAME,
                                E.PRICE,
                                E.DESCRIPTION,
                                E.TRANSACTION_DATE
                            FROM CATEGORY C
                            JOIN EXPENSES E ON C.ID = E.CATEGORY_ID
                            WHERE E.PRICE BETWEEN %s AND %s''', (start_price, max_price))
        else:
            cur.execute(f'''SELECT C.NAME,
                                E.PRICE,
                                E.DESCRIPTION,
                                E.TRANSACTION_DATE
                            FROM CATEGORY C
                            JOIN EXPENSES E ON C.ID = E.CATEGORY_ID
                            WHERE E.PRICE = %s''', (start_price,))

        sql_query = cur.fetchall()
        results = [{
            'category': i[0],
            'price': float(i[1]),
            'description': i[2],
            'date': i[3].strftime('%d.%m.%Y')} for i in sql_query]

        if not results:
            flash('No results to display!')


        return render_template('price_filter.html', results=results)


    return render_template('price_filter.html')


@app.route('/date_filter', methods=['GET','POST'])
def date_fiter():
    if request.method == 'POST':
        start_date = request.form['start_date']
        end_date = request.form['end_date']


        if not start_date:
            flash("Error. You didn't select a start date!")
            return redirect('/date_filter')

        try:
            sd_datetime = datetime.strptime(start_date, '%d.%m.%Y')
            if end_date:
                ed_datetime = datetime.strptime(end_date, '%d.%m.%Y')
        except ValueError:
            flash('Invalid input or you didnt select start or end date!')
            return redirect('/date_filter')

        if end_date and sd_datetime > ed_datetime:
            flash("Start date can't be greater that end date!")
            return redirect('/date_filter')

        if end_date:
            cur.execute('''SELECT C.NAME,
                                E.PRICE,
                                E.DESCRIPTION,
                                E.TRANSACTION_DATE
                            FROM CATEGORY C
                            JOIN EXPENSES E ON C.ID = E.CATEGORY_ID
                            WHERE E.TRANSACTION_DATE BETWEEN %s AND %s
                            ORDER BY E.TRANSACTION_DATE DESC''', (sd_datetime, ed_datetime))
        else:
            cur.execute('''SELECT C.NAME,
                                E.PRICE,
                                E.DESCRIPTION,
                                E.TRANSACTION_DATE
                            FROM CATEGORY C
                            JOIN EXPENSES E ON C.ID = E.CATEGORY_ID
                            WHERE E.TRANSACTION_DATE = %s
                            ORDER BY E.TRANSACTION_DATE DESC''', (sd_datetime,))

        query_res = cur.fetchall()
        if not query_res:
            flash('No data for this date range or exact date!')
            return redirect('/date_filter')
        results = [{
            'category': i[0],
            'price': float(i[1]),
            'description': i[2],
            'date': i[3].strftime('%d.%m.%Y')} for i in query_res]

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


@app.route('/import_json', methods = ['GET', 'POST'])
def import_json():
    if request.method == 'POST':
        file = request.files['file']

        if file.filename.endswith('.json'):
            json_data = json.load(file)
            all_data = []

            try:
                max_expenses_id = None
                for item in json_data:
                    category_name = item['category']
                    if category_name:
                        category_id = category_id_name(category_name)
                        if category_id is not None:
                            price = float(item['price'])
                            date = item['date']
                            description = item['description']
                            expenses_id = item['expenses_id']

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
                            flash('There is no category with that name.')
                            return redirect('import_json.html')
                    else:
                        flash('Category name not provided!')
                        return redirect('import_json.html')
            except ValueError as e:
                flash(f"Error importing data {e}")
            return render_template('submit_json.html', all_data=all_data)
        else:
            flash('Invalid file format. Please import JSON file!')
        return redirect('/')
    else:
        return render_template('import_json.html')


@app.route('/submit_json', methods=['POST'])
def submit_json():
    if request.method == 'POST':
        for all_data in request.form.getlist('transaction_data'):
            data = json.loads(all_data)
            price = data['price']
            description = data['description']
            date = data['date']
            category_id = data['category_id']
            expenses_id = data['expenses_id']


            date_time = None

            selected_tag = request.form.get(f'tag_{expenses_id}')


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
                return redirect('/import_json')
            if date_time is not None:
                cur.execute('INSERT INTO EXPENSES (EXPENSES_ID, CATEGORY_ID, PRICE, DESCRIPTION, TAG, TRANSACTION_DATE) VALUES (%s, %s, %s, %s, %s, %s)',
                            (expenses_id, category_id, price, description, selected_tag, date_time))
                db_conn.commit()
            flash('Transaction successfully added to database!', 'success')
        return redirect('/import_json')


@app.route('/generate_chart', methods=['GET', 'POST'])
def generate_chart():
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

        plt.figure(figsize=(6,4))
        plt.bar(categories, prices, color=['blue'])
        plt.xlabel('Category')
        plt.ylabel('Price')
        plt.title('Expenses by category')
        # plt.xticks(rotation=25, fontsize=8, ha='right')
        plt.xticks(rotation=25, fontsize=8)
        plt.tight_layout()

        graph = os.path.join(app.root_path, 'static', 'chart.jpg')
        plt.savefig(graph)

        return render_template('generate_chart.html', graph='static/chart.jpg')
    return render_template('generate_chart.html')
