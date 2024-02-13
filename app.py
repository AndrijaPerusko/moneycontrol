from flask import Flask, request, flash, redirect, render_template
from flask_wtf import FlaskForm
from wtforms import FloatField, StringField
from wtforms.validators import InputRequired
from datetime import datetime
import psycopg2

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

if __name__ == '__main__':
    app.run(debug=True)

