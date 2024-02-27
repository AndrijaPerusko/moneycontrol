import sys
from PyQt5.QtWidgets import (QApplication, QVBoxLayout, QLineEdit, QPushButton, QComboBox, QDateEdit, QLabel,
                             QMessageBox, QWizard, QWizardPage, QRadioButton)
from datetime import datetime
import psycopg2


class ExpenseWizard(QWizard):
    def __init__(self, parent=None):
        super(ExpenseWizard, self).__init__(parent)
        self.setWindowTitle('Expense Wizard')


        self.db_conn = psycopg2.connect("postgresql://postgres:admin@localhost/money")
        self.cur = self.db_conn.cursor()

        self.addPage(ExpensePage1(self))
        self.addPage(ExpensePage2(self))
        self.addPage(ExpensePage3(self))

        self.setMinimumSize(640, 480)

    def get_categories(self):
        try:
            self.cur.execute('SELECT * FROM category')
            return self.cur.fetchall()
        except psycopg2.Error as e:
            print("Error fetching categories:", e)
            return []

    def add_expense_to_database(self, price, description, date, category, tag):
        try:

            self.cur.execute(
                'INSERT INTO expenses (category_id, price, description, transaction_date, tag) VALUES (%s, %s, %s, %s, %s)',
                (category, price, description, date, tag))
            self.db_conn.commit()
            QMessageBox.information(self, "Success", "Expense added successfully!")
        except psycopg2.Error as e:
            QMessageBox.warning(self, "Error", "Failed to add expense to the database: {}".format(e))


class ExpensePage1(QWizardPage):
    def __init__(self, parent=None):
        super(ExpensePage1, self).__init__(parent)
        self.setTitle("Step 1")
        layout = QVBoxLayout()
        self.price_input = QLineEdit()
        layout.addWidget(QLabel("Price:"))
        layout.addWidget(self.price_input)
        self.description_input = QLineEdit()
        layout.addWidget(QLabel("Description:"))
        layout.addWidget(self.description_input)
        self.date_input = QDateEdit()
        self.date_input.setDisplayFormat("dd/MM/yyyy")
        layout.addWidget(QLabel("Date:"))
        layout.addWidget(self.date_input)
        self.category_input = QComboBox()
        layout.addWidget(QLabel("Category:"))
        layout.addWidget(self.category_input)
        self.setLayout(layout)


        categories = parent.get_categories()
        self.category_input.addItems([category[1] for category in categories])

    def validatePage(self):
        price = self.price_input.text()
        description = self.description_input.text()
        date = self.date_input.date().toString("yyyy-MM-dd")
        category = self.category_input.currentIndex() + 1

        if not price or not description:
            QMessageBox.warning(self, "Warning", "All fields must be filled!")
            return False


        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            QMessageBox.warning(self, "Warning", "Invalid date format! Please use yyyy-MM-dd")
            return False


        try:
            price = float(price)
            if price <= 0:
                raise ValueError('Invalid input.')
        except ValueError:
            QMessageBox.warning(self, "Warning", "Price must be a positive number!")
            return False


        self.wizard().price = price
        self.wizard().description = description
        self.wizard().date = date
        self.wizard().category = category

        return True


class ExpensePage2(QWizardPage):
    def __init__(self, parent=None):
        super(ExpensePage2, self).__init__(parent)
        self.setTitle("Step 2")
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.radio_group = []

    def initializePage(self):

        description = self.wizard().description
        tags = description.split()
        layout = self.layout()
        self.radio_group = []
        for tag in tags:
            radio_button = QRadioButton(tag)
            layout.addWidget(radio_button)
            self.radio_group.append(radio_button)

    def validatePage(self):
        checked_button = None
        for button in self.radio_group:
            if button.isChecked():
                checked_button = button
                break
        if checked_button is None:
            QMessageBox.warning(self, "Warning", "Please select a tag!")
            return False


        tag = checked_button.text()
        self.wizard().tag = tag

        return True


class ExpensePage3(QWizardPage):
    def __init__(self, parent=None):
        super(ExpensePage3, self).__init__(parent)
        self.setTitle("Step 3")
        layout = QVBoxLayout()
        self.setLayout(layout)

    def initializePage(self):
        price = self.wizard().price
        description = self.wizard().description
        date = self.wizard().date
        category = self.wizard().category
        tag = self.wizard().tag

        layout = self.layout()
        layout.addWidget(QLabel("Price: {}".format(price)))
        layout.addWidget(QLabel("Description: {}".format(description)))
        layout.addWidget(QLabel("Date: {}".format(date)))
        layout.addWidget(QLabel("Category: {}".format(category)))
        layout.addWidget(QLabel("Tag: {}".format(tag)))


        confirm_button = QPushButton("Confirm")
        confirm_button.clicked.connect(self.confirm_expense)
        layout.addWidget(confirm_button)

    def confirm_expense(self):
        wizard = self.wizard()
        wizard.add_expense_to_database(wizard.price, wizard.description, wizard.date, wizard.category, wizard.tag)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    wizard = ExpenseWizard()
    wizard.show()
    sys.exit(app.exec_())