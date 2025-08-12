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
    def add_expense(self,amount,date,category_name,description):

