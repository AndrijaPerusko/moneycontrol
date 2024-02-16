from flask import Flask, request, flash, redirect, render_template, jsonify, send_file
from flask_wtf import FlaskForm
from wtforms import FloatField, StringField
from wtforms.validators import InputRequired
from datetime import datetime
import psycopg2
import json

app = Flask(__name__)

app.secret_key = 'some_random_string'
app.config['DATABASE_URL'] = 'postgresql://postgres:admin@localhost/money'
db_conn = psycopg2.connect(app.config['DATABASE_URL'])
cur = db_conn.cursor()

class ExpenseForm(FlaskForm):
    price = FloatField('Price', validators=[InputRequired()])
    description = StringField('Description', validators=[InputRequired()])
    date = StringField('Date (dd.mm.yyyy)', validators=[InputRequired()])


@app.route('/', methods=['GET','POST'])
@app.route('/add_expenses', methods=['GET','POST'])
def add_expenses():
    form = ExpenseForm()
    cur.execute('SELECT * FROM category')
    categories = cur.fetchall()
    if form.validate_on_submit() and request.method == 'POST':
        price = form.price.data
        description = form.description.data
        date = form.date.data
        category_id = request.form['category']

        date_time = None

        try:
            date_time = datetime.strptime(date,"%d.%m.%Y")
        except ValueError:
            flash('Invalid input. Please put the correct form (dd.mm.yyyy)')

        try:
            price = float(price)
            if price <=0:
                raise ValueError('Invalid input.')
        except ValueError:
            flash('Error. Input has to be number and greater than zero!')
            return redirect('/')

        if date_time is not None:
            cur.execute('INSERT INTO EXPENSES (CATEGORY_ID, PRICE, TAG, TRANSACTION_DATE) VALUES (%s, %s, %s, %s)',
                        (category_id, price, description, date_time))
            db_conn.commit()
            flash('Transaction successfully added to database!')
        return redirect('/')
    elif request.method == 'GET':
        return render_template('index.html', categories=categories, form=form)

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
        'transaction_date': i[3].strftime('%d.%m.%Y')} for i in query_res
    ]
    final_result = {'expenses': results}
    return jsonify(final_result)


@app.route('/category', methods=['GET', 'POST'])
def category():
    cur.execute('SELECT * FROM category')
    categories = cur.fetchall()
    if request.method == 'POST':
        category_id = request.form['category_id']
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

        return render_template('category.html', final_result=results)
    else:
        return render_template('category.html',categories=categories)


@app.route('/price_sort', methods=['GET','POST'])
def price_sort():
    if request.method == 'POST':
        min_price = request.form['min_price']
        max_price = request.form['max_price']
        sort_order = request.form['sort_order']

        if sort_order == 'asc':
            sql_order = 'ASC'
        else:
            sql_order = 'DESC'

        cur.execute(f'''SELECT C.NAME,
                            E.PRICE,
                            E.TAG,
                            E.TRANSACTION_DATE
                        FROM CATEGORY C
                        JOIN EXPENSES E ON C.ID = E.CATEGORY_ID
                        WHERE E.PRICE BETWEEN %s AND %s
                        ORDER BY E.PRICE {sql_order}''', (min_price, max_price))
        sql_query = cur.fetchall()
        results = [{
            'category': i[0],
            'price': float(i[1]),
            'tag': i[2],
            'date': i[3].strftime('%d.%m.%Y')} for i in sql_query]

        return render_template('price_filter.html', results=results)
    return render_template('price_filter.html')

@app.route('/date_filter', methods=['GET','POST'])
def date_fiter():
    if request.method == 'POST':
        start_date = request.form['start_date']
        end_date = request.form['end_date']


        if not start_date and not end_date:
            flash("Error. You didn't select dates!")
            return redirect('/date_filter')

        try:
            sd_datetime = datetime.strptime(start_date, '%d.%m.%Y')
            ed_datetime = datetime.strptime(end_date, '%d.%m.%Y')
        except ValueError:
            flash('Invalid input or you didnt select start or end date!')
            return redirect('/date_filter')

        if sd_datetime > ed_datetime:
            flash("Start date can't be greater that end date!")
            return redirect('/date_filter')


        cur.execute('''SELECT C.NAME,
                            E.PRICE,
                            E.TAG,
                            E.TRANSACTION_DATE
                        FROM CATEGORY C
                        JOIN EXPENSES E ON C.ID = E.CATEGORY_ID
                        WHERE E.TRANSACTION_DATE BETWEEN %s AND %s
                        ORDER BY E.TRANSACTION_DATE DESC''', (sd_datetime, ed_datetime))
        query_res = cur.fetchall()
        if not query_res:
            flash('No data for this date range!')
            return redirect('/date_filter')
        results = [{
            'category': i[0],
            'price': float(i[1]),
            'tag': i[2],
            'date': i[3].strftime('%d.%m.%Y')} for i in query_res]

        return render_template('date_filter.html', results=results)
    return render_template('date_filter.html')

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

@app.route('/extract_expenses', methods=['GET'])
def extract_expenses():
    json_data = load_json()
    filename = 'expenses.json'

    json_object = json.dumps(json_data, indent=2)

    with open(filename, 'w') as file:
        file.write(json_object)

    return send_file(
        filename,
        mimetype='application/json',
        as_attachment=True,
)


if __name__ == '__main__':
    app.run(debug=True)

