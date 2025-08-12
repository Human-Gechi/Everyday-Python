import pandas as pd
import argparse
import json
import os

def find_files(directory, extensions=('.csv', '.xls', '.xlsx', '.json', '.txt')):
    """Walk through directory and yield file paths matching extensions."""
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(extensions):
                yield os.path.join(root, file)

def summarize_data(file_path):
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif file_path.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(file_path)
    elif file_path.endswith('.txt'):
        df = pd.read_csv(file_path, sep='\t')
    elif file_path.endswith('.json'):
        try:
            df = pd.read_json(file_path)
        except ValueError:

            with open(file_path) as f:
                data = json.load(f)
            df = pd.json_normalize(data)
    else:
        print("Unsupported file format.")
        return

    print(f"\n📊 Dataset Summary: {file_path}")
    print("-" * 50)
    print(f"Rows: {df.shape[0]}")
    print(f"Columns: {df.shape[1]}")

    pd.Series([df.shape[0]]).to_csv('row_count.csv', header=None, index=False)
    pd.Series([df.shape[1]]).to_csv('column_count.csv', header=None, index=False)

    print("\nNull values per column:")
    print(df.isnull().sum())
    df.isnull().sum().to_csv('null_count.csv', header=None)

    print("\n🔑 Unique values per column:")
    for col in df.columns:
        try:
            print(f"{col}: {df[col].nunique()}")
        except TypeError:
            print(f"{col}: ❌ Cannot locate unique values try again later")
    df.nunique().to_csv('unique_count.csv', header=None)

    print("\nData types:")
    print(df.dtypes)
    df.dtypes.to_csv('data_types.csv', header=None)

    print("\n📈 Descriptive Statistics:")
    print(df.describe(include='all'))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dataset Summary CLI Tool")
    parser.add_argument("filepath", help="Path to dataset/file/directory")
    args = parser.parse_args()

    if os.path.isdir(args.filepath):
        print(f"🔎 Searching for data files in: {args.filepath}")
        for file in find_files(args.filepath):
            summarize_data(file)

    elif os.path.isfile(args.filepath):
        summarize_data(args.filepath)

    else:
        print(f"⚠️ File or folder '{args.filepath}' cannot be found directly.Searching computer system...")

        exist = None
        for root, dirs, files in os.walk("C:\\"):
            for file in files:
                if file.lower() == args.filepath.lower():
                    exist = os.path.join(root, file)
                    break
            if exist:
                break

        if exist:
            print(f"✅ Found file: {exist}")
            summarize_data(exist)
        else:
            print("❌ File does not exist.")