import sqlite3
from pathlib import Path

DB_PATH = Path("recipes.db")

def connect():
    return sqlite3.connect(DB_PATH)

def create_tables():
    with connect() as con:
        cur = con.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS recipes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS ingredients(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            unit TEXT NOT NULL,
            UNIQUE(name, unit)
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS recipe_ingredients(
            recipe_id INTEGER,
            ingredient_id INTEGER,
            amount REAL NOT NULL,
            FOREIGN KEY(recipe_id) REFERENCES recipes(id),
            FOREIGN KEY(ingredient_id) REFERENCES ingredients(id),
            PRIMARY KEY(recipe_id, ingredient_id)
        )""")

def add_recipe(name):
    with connect() as con:
        cur = con.cursor()
        cur.execute("INSERT OR IGNORE INTO recipes(name) VALUES (?)", (name,))
        con.commit()

def update_recipe(recipe_id, new_name):
    with connect() as con:
        con.execute("UPDATE recipes SET name=? WHERE id=?", (new_name, recipe_id))

def delete_recipe(recipe_id):
    with connect() as con:
        con.execute("DELETE FROM recipe_ingredients WHERE recipe_id=?", (recipe_id,))
        con.execute("DELETE FROM recipes WHERE id=?", (recipe_id,))

def get_all_recipes():
    with connect() as con:
        return con.execute("SELECT id, name FROM recipes ORDER BY name").fetchall()

def get_or_create_ingredient(name, unit):
    with connect() as con:
        cur = con.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO ingredients(name, unit) VALUES(?, ?)",
            (name.strip(), unit)
        )
        row = cur.execute(
            "SELECT id FROM ingredients WHERE name=? AND unit=?",
            (name.strip(), unit)
        ).fetchone()
        return row[0]

def add_ingredient_to_recipe(recipe_id, ingredient_id, amount):
    with connect() as con:
        con.execute("""
        INSERT OR REPLACE INTO recipe_ingredients(recipe_id, ingredient_id, amount)
        VALUES (?, ?, ?)
        """, (recipe_id, ingredient_id, float(amount)))

def remove_ingredient_from_recipe(recipe_id, ingredient_id):
    with connect() as con:
        con.execute("""
        DELETE FROM recipe_ingredients
        WHERE recipe_id=? AND ingredient_id=?
        """, (recipe_id, ingredient_id))

def get_ingredients_for_recipe(recipe_id):
    with connect() as con:
        return con.execute("""
        SELECT i.id, i.name, i.unit, ri.amount
        FROM recipe_ingredients ri
        JOIN ingredients i ON i.id = ri.ingredient_id
        WHERE ri.recipe_id=?
        ORDER BY i.name
        """, (recipe_id,)).fetchall()

def get_all_ingredient_names():
    with connect() as con:
        rows = con.execute("SELECT DISTINCT name FROM ingredients ORDER BY name").fetchall()
        return [r[0] for r in rows]
