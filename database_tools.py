import sqlite3
import pandas as pd
import os

# File paths
DB_PATH = "bike_catalog.db"
EXCEL_PATH = "catalog-bike.xlsx"

def init_database():
    """
    Load data from catalog-bike.xlsx and create a SQLite database.
    """
    if not os.path.exists(EXCEL_PATH):
        return f"Excel file not found at {EXCEL_PATH}"
    
    df = pd.read_excel(EXCEL_PATH)

    conn = sqlite3.connect(DB_PATH)
    df.to_sql("catalog", conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()
    return "Database initialized successfully!"

def text_to_sql(query: str) -> str:
    """
    Execute a SQL query on the catalog database and return result in markdown.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(query, conn)
        if df.empty:
            return "No results found."
        return df.to_markdown(index=False)
    except Exception as e:
        return f"SQL Error: {e}"
    finally:
        conn.close()

def get_database_info() -> str:
    """
    Return table schema and sample rows from catalog table.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(catalog);")
        schema = cursor.fetchall()
        headers = ["cid", "name", "type", "notnull", "default_value", "pk"]
        schema_df = pd.DataFrame(schema, columns=headers)

        sample_df = pd.read_sql_query("SELECT * FROM catalog LIMIT 3", conn)

        return (
            f"Schema for table `catalog`:\n\n{schema_df.to_markdown(index=False)}\n\n"
            f"Sample data:\n\n{sample_df.to_markdown(index=False)}"
        )
    except Exception as e:
        return f"Error retrieving schema: {e}"
    finally:
        conn.close()
