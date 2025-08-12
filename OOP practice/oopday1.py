import pandas as pd
import os
import regex as re
class Book():
    def __init__(self, author, title):
        self.__author = author
        self.__title = title

    @property
    def author(self):
        return self.__author

    @author.setter
    def author(self, value):
        self.__author = value

    @property
    def title(self):
        return self.__title

    @title.setter
    def title(self, value):
        self.__title = value

class PhysicalBook(Book):
    def __init__(self, author, title, stock):
        super().__init__(author, title)
        self.__stock = stock

    @property
    def stock(self):
        return self.__stock

    @stock.setter
    def stock(self, value):
        if value <= 0:
            raise ValueError('Stock must be positive')
        self.__stock = value

class Ebook(Book):
    def __init__(self, author, title, copies):
        super().__init__(author, title)
        self.__copies = copies

    @property
    def copies(self):
        return self.__copies

    @copies.setter
    def copies(self, value):
        if value <= 0:
            raise ValueError('Copies must be positive')
        self.__copies = value

def require_role(required_role):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            if getattr(self, 'role', None) == required_role:
                return func(self, *args, **kwargs)
            else:
                raise PermissionError("Unauthorized access")
        return wrapper
    return decorator

class LibraryManager:
    def __init__(self, role):
        self.role = role
        self.books = []
        self.load_books_from_csv()

    def books_to_dicts(self):
        book_list = []
        for book in self.books:
            if isinstance(book, PhysicalBook):
                book_list.append({
                    "Type": "Physical",
                    "Author": book.author,
                    "Title": book.title,
                    "Quantity": book.stock
                })
            elif isinstance(book, Ebook):
                book_list.append({
                    "Type": "Ebook",
                    "Author": book.author,
                    "Title": book.title,
                    "Quantity": book.copies
                })
        return book_list

    def save_books_to_csv(self):
        book_dicts = self.books_to_dicts()
        df = pd.DataFrame(book_dicts)
        print(f"Saving {len(book_dicts)} books to CSV...")
        print(df)
        file_path = r'C:\Users\HP\OneDrive\Desktop\Pythonpractice\OOP practice\books.csv'
        df.to_csv(file_path, index=False)

    def load_books_from_csv(self):
        if not os.path.exists('Books.csv'):
            return pd.DataFrame()
        df = pd.read_csv('Books.csv')
        for _, row in df.iterrows():
            book_type = row['Type'].lower()
            author = row['Author']
            title = row['Title']
            quantity = row['Quantity']
            if book_type == 'physical':
                self.books.append(PhysicalBook(author, title, quantity))
            elif book_type == 'ebook':
                self.books.append(Ebook(author, title, quantity))

    @require_role("admin")
    def add_book(self, book_type, author, title, quantity):
        book_type = book_type.lower()
        if book_type == "physical":
            new_book = PhysicalBook(author, title, quantity)
        elif book_type == "ebook":
            new_book = Ebook(author, title, quantity)
        else:
            raise ValueError("Invalid book type. Choose 'physical' or 'ebook'.")
        self.books.append(new_book)
        self.save_books_to_csv()
        return f"{book_type.capitalize()} book '{title}' added successfully."
    def viewbooks(self):
        title = input('What book are you looking for? ').strip().lower()
        if not os.path.exists(r'C:\Users\HP\OneDrive\Desktop\Pythonpractice\OOP practice\books.csv'):
            print("No books found in the library.")
            return
        df = pd.read_csv(r'C:\Users\HP\OneDrive\Desktop\Pythonpractice\OOP practice\books.csv')
        matches = df[df['Title'].str.contains(title, case=False, regex=True, na=False)]
        if matches.empty:
            print(f"No book found with the title '{title}'.")
        else:
            print("Found book(s):")
            print(matches.to_string(index=False))
admin = LibraryManager(role=input("Enter your role (admin/user): ").strip().lower())
while True:
    action = input("Enter action (add/view/exit): ").strip().lower()
    if action == "add":
        book_type = input("Enter book type (physical/ebook): ").strip().lower()
        author = input("Enter author name: ").strip()
        title = input("Enter book title: ").strip()
        quantity = int(input("Enter quantity: ").strip())
        print(admin.add_book(book_type, author, title, quantity))
    elif action == "view":
        admin.viewbooks()
    elif action == "exit":
        break
    else:
        print("Invalid action. Please choose 'add', 'view', or 'exit'.")
