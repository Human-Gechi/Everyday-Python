from datetime import datetime
import pandas as pd
import regex as re
class Category:
    def __init__(self,name:str):
        self.name = name
    def __str__(self):
        return f"Category: {self.name}"
class Expense:
    def __init__(self, amount: float, date: datetime = None, category: str = "", description: str = ""):
        self.amount = amount
        self.date = str(date) if date else datetime.now()
        self.category = category
        self.description = description

    def __str__(self) -> str:
        return f"Expense: ${self.amount:.2f} on {self.date.strftime('%Y-%m-%d')} in category '{self.category}'" + \
           (f" — {self.description}" if self.description else "")
    def __repr__(self): # to avoid looping throught the list of expenses when calling the func.
        return self.__str__()
#base expenses class
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

    def get_expenses_by_category(self, category_name, file_path=r"C:\Users\HP\OneDrive\Desktop\Pythonpractice\OOP practice\Report.csv"):
        try:
            if file_path:
                df = pd.read_csv(file_path, parse_dates=["Date"])
                filtered = df[df["Category"].str.contains(category_name,regex=True,na=False)]
                return filtered
            else:  # Use in-memory expenses list
                return [expense for expense in self.expenses if expense.category == category_name]

        except FileNotFoundError:
            print("File not found.")
            return []

    def get_expenses_by_date(self,date,file_path=r"C:\Users\HP\OneDrive\Desktop\Pythonpractice\OOP practice\Report.csv"):
        try:
            if file_path:  # If CSV file is provided
                df = pd.read_csv(file_path, parse_dates=["Date"])
                filtered = df[df["Date"].astype(str).str.contains(date, regex=True, na=False)]

                return filtered
            else:  # Use in-memory expenses list
                return [expense for expense in self.expenses if expense.category == date]

        except FileNotFoundError:
            print("File not found.")
            return []
    def total_expenses_by_category(self,category_name,file_path= r'C:\Users\HP\OneDrive\Desktop\Pythonpractice\OOP practice\Report.csv'):
       df = pd.read_csv(file_path, parse_dates=['Date'])
       total = df.loc[df['Category'] == category_name, 'Amount'].sum()
       return total

    def save_report(self, file_path):
        # Load old data if file exists
        try:
            old_df = pd.read_csv(file_path)
        except FileNotFoundError:
            old_df = pd.DataFrame(columns=["Date", "Category", "Amount", "Description"])

        #Convert current expenses to DataFrame
        new_data = []
        for expense in self.expenses:
            new_data.append({
                "Date": expense.date,
                "Category": expense.category,
                "Amount": expense.amount,
                "Description": expense.description
            })
        new_df = pd.DataFrame(new_data)

        #Merge old + new, drop duplicates
        combined_df = pd.concat([old_df, new_df]).drop_duplicates()

        combined_df.to_csv(file_path, index=False)
# quick demo
product = ExpenseTracker()
product.add_category('Groceries')
product.add_category('Drugs')
print(product.total_expenses_by_category('Drugs'))

