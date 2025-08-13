from datetime import datetime
class Category:
    def __init__(self,name:str):
        self.name = name
    def __str__(self):
        return f"Category: {self.name}"
class Expense:
    def __init__(self, amount: float, date: datetime, category: str, description: str = ""):
        self.amount = amount
        self.date = datetime.now() or date
        self.category = category
        self.description = description
    def __str__(self) -> str:
        return f"Expense: ${self.amount:.2f} on {self.date.strftime('%Y-%m-%d')} in category '{self.category}'" + \
           (f" — {self.description}" if self.description else "")
class ExpenseTracker:
    def __init__(self):
        self.categories = []
        self.expenses = []
    def add_category(self, name):
        if not name:
            return False
        else:
            category = Category(name)
            self.categories.append(category)
            return True
    def show_categories(self):
        if not self.categories:
            print("No categories available.")
        else:
            print("Categories:")
            for cat in self.categories:
                print(f"- {cat}")

    def add_expense(self, amount, date, category_name, description=""):
        if amount <= 0:
            raise ValueError("Amount should be greater than zero")

        # Optional: verify category exists
        if not any(cat.name == category_name for cat in self.categories):
            print(f'Category:{category_name} does not exist')
            return None
        else:
            expense = Expense(amount, date, category_name, description)
            self.expenses.append(expense)
            return True

    def get_expenses_by_category(self, category_name):
        filtered = [expense for expense in self.expenses if expense.category == category_name]
        return filtered
    def get_expenses_by_date(self,start_date, end_date):
        filtered = [expense for expense in self.expenses if start_date <= expense.date <= end_date]
        return filtered
    def total_expenses_by_category(self,categories):
        pass