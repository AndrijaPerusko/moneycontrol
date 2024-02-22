from flask import Flask
import psycopg2

app = Flask(__name__)

app.secret_key = 'some_random_string'
app.config['DATABASE_URL'] = 'postgresql://postgres:admin@localhost/money'
db_conn = psycopg2.connect(app.config['DATABASE_URL'])
cur = db_conn.cursor()

from money_control import routes
