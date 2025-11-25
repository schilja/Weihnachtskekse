import tkinter as tk
from tkinter import ttk, messagebox
from constants import UNITS
import database as db
from logic import aggregate
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from tkinter import filedialog

class AutocompleteEntry(ttk.Entry):
    def __init__(self, suggestions, *a, **k):
        super().__init__(*a, **k)
        self.suggestions = suggestions
        self.var = tk.StringVar()
        self.config(textvariable=self.var)
        self.listbox = None
        self.var.trace_add("write", self.changed)

    def changed(self, *_):
        val = self.var.get()
        if not val:
            self.hide()
            return
        words = [w for w in self.suggestions() if w.lower().startswith(val.lower())]
        if words:
            if not self.listbox:
                self.listbox = tk.Listbox()
                self.listbox.bind("<<ListboxSelect>>", self.on_select)
                self.listbox.place(in_=self, relx=0, rely=1, relwidth=1)
            self.listbox.delete(0, tk.END)
            for w in words:
                self.listbox.insert(tk.END, w)
        else:
            self.hide()

    def on_select(self, *_):
        if self.listbox:
            self.var.set(self.listbox.get(self.listbox.curselection()))
            self.hide()

    def hide(self):
        if self.listbox:
            self.listbox.destroy()
            self.listbox = None


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Keks-Rezepte")
        self.geometry("900x550")
        db.create_tables()
        self.selected_recipe_id = None
        self.build_ui()
        self.refresh_recipes()

    def build_ui(self):
        main = ttk.Frame(self, padding=10)
        main.pack(fill="both", expand=True)

        # left: recipes
        left = ttk.Frame(main)
        left.pack(side="left", fill="y", padx=(0, 10))

        ttk.Label(left, text="Rezepte").pack()
        self.recipe_list = tk.Listbox(left, width=30, height=20)
        self.recipe_list.pack()
        self.recipe_list.bind("<<ListboxSelect>>", self.on_select_recipe)

        ttk.Button(left, text="+ Neu", command=self.new_recipe).pack(fill="x", pady=2)
        ttk.Button(left, text="Umbenennen", command=self.rename_recipe).pack(fill="x", pady=2)
        ttk.Button(left, text="Löschen", command=self.delete_recipe).pack(fill="x", pady=2)

        # center: ingredients editor
        center = ttk.Frame(main)
        center.pack(side="left", fill="both", expand=True)

        ttk.Label(center, text="Zutaten").pack()

        cols = ("Name", "Menge", "Einheit")
        self.ing_tree = ttk.Treeview(center, columns=cols, show="headings")
        for c in cols:
            self.ing_tree.heading(c, text=c)
            self.ing_tree.column(c, width=120)
        self.ing_tree.pack(fill="both", expand=True)

        form = ttk.Frame(center)
        form.pack(fill="x")

        ttk.Label(form, text="Name").grid(row=0, column=0)
        self.ing_name = AutocompleteEntry(db.get_all_ingredient_names, form, width=25)
        self.ing_name.grid(row=1, column=0, padx=2)

        ttk.Label(form, text="Menge").grid(row=0, column=1)
        self.ing_amount = ttk.Entry(form, width=10)
        self.ing_amount.grid(row=1, column=1, padx=2)

        ttk.Label(form, text="Einheit").grid(row=0, column=2)
        self.ing_unit = ttk.Combobox(form, values=UNITS, width=18)
        self.ing_unit.current(0)
        self.ing_unit.grid(row=1, column=2, padx=2)

        ttk.Button(form, text="Hinzufügen", command=self.add_ingredient).grid(row=1, column=3, padx=5)
        ttk.Button(form, text="Entfernen", command=self.remove_ingredient).grid(row=1, column=4, padx=5)

        # right: bake selection & summary
        right = ttk.Frame(main)
        right.pack(side="right", fill="both", expand=True, padx=(10, 0))

        ttk.Label(right, text="Back-Auswahl (Anzahl)").pack()
        self.bake_tree = ttk.Treeview(right, columns=("Rezept", "Anzahl"), show="headings", height=10)
        self.bake_tree.heading("Rezept", text="Rezept")
        self.bake_tree.heading("Anzahl", text="Anzahl")
        self.bake_tree.column("Anzahl", width=80)
        self.bake_tree.pack(fill="x")
        self.bake_tree.bind("<Button-1>", self.show_amount_dropdown)
        ttk.Button(right, text="Zusammenfassen", command=self.make_summary).pack(pady=5)

        ttk.Label(right, text="Einkaufsliste").pack()
        self.summary = tk.Text(right, height=15)
        self.summary.pack(fill="both", expand=True)

        ttk.Button(right, text="Als PDF speichern", command=self.export_pdf).pack(pady=5)


    # --- Recipe actions ---
    def refresh_recipes(self):
        self.recipe_list.delete(0, tk.END)
        self.bake_tree.delete(*self.bake_tree.get_children())
        for rid, name in db.get_all_recipes():
            self.recipe_list.insert(tk.END, f"{rid}: {name}")
            self.bake_tree.insert("", tk.END, values=(name, 1))

    def on_select_recipe(self, _):
        sel = self.recipe_list.curselection()
        if not sel: return
        rid = int(self.recipe_list.get(sel).split(":")[0])
        self.selected_recipe_id = rid
        self.refresh_ingredients()

    def new_recipe(self):
        name = simple_input(self, "Neues Rezept", "Rezeptname:")
        if name:
            db.add_recipe(name)
            self.refresh_recipes()

    def rename_recipe(self):
        if not self.selected_recipe_id: return
        name = simple_input(self, "Umbenennen", "Neuer Name:")
        if name:
            db.update_recipe(self.selected_recipe_id, name)
            self.refresh_recipes()

    def delete_recipe(self):
        if not self.selected_recipe_id: return
        if messagebox.askyesno("Löschen", "Rezept wirklich löschen?"):
            db.delete_recipe(self.selected_recipe_id)
            self.selected_recipe_id = None
            self.ing_tree.delete(*self.ing_tree.get_children())
            self.refresh_recipes()

    # --- Ingredient actions ---
    def refresh_ingredients(self):
        self.ing_tree.delete(*self.ing_tree.get_children())
        for iid, name, unit, amount in db.get_ingredients_for_recipe(self.selected_recipe_id):
            self.ing_tree.insert("", tk.END, iid=iid, values=(name, amount, unit))

    def add_ingredient(self):
        if not self.selected_recipe_id: return
        try:
            name = self.ing_name.get().strip()
            amount = float(self.ing_amount.get())
            unit = self.ing_unit.get()
            if not name: return
            iid = db.get_or_create_ingredient(name, unit)
            db.add_ingredient_to_recipe(self.selected_recipe_id, iid, amount)
            self.ing_name.delete(0, tk.END)
            self.ing_amount.delete(0, tk.END)
            self.refresh_ingredients()
        except ValueError:
            messagebox.showerror("Fehler", "Menge muss eine Zahl sein")

    def remove_ingredient(self):
        if not self.selected_recipe_id: return
        sel = self.ing_tree.selection()
        if not sel: return
        iid = self.ing_tree.item(sel[0])["iid"]
        db.remove_ingredient_from_recipe(self.selected_recipe_id, iid)
        self.refresh_ingredients()

    def show_amount_dropdown(self, event):
        item = self.bake_tree.identify_row(event.y)
        column = self.bake_tree.identify_column(event.x)

        # Nur in Spalte "Anzahl" (Spalte 2)
        if column != "#2" or not item:
            return

        x, y, w, h = self.bake_tree.bbox(item, column)

        values = ["1", "2", "3", "4", "5"]
        current = self.bake_tree.item(item, "values")[1]

        combo = ttk.Combobox(
            self.bake_tree,
            values=values,
            state="readonly"
        )
        combo.place(x=x, y=y, width=w, height=h)
        combo.set(str(current))

        def save(_):
            vals = list(self.bake_tree.item(item, "values"))
            vals[1] = combo.get()
            self.bake_tree.item(item, values=vals)
            combo.destroy()

        combo.bind("<<ComboboxSelected>>", save)
        combo.bind("<FocusOut>", lambda e: combo.destroy())

    # --- Summary ---
    def make_summary(self):
        selected = []
        # Map recipe name -> id
        name_to_id = {name: rid for rid, name in db.get_all_recipes()}
        for row in self.bake_tree.get_children():
            name, factor = self.bake_tree.item(row)["values"]
            rid = name_to_id.get(name)
            if not rid: continue
            items = [(n, u, a) for (_, n, u, a) in db.get_ingredients_for_recipe(rid)]
            try:
                f = float(factor)
            except:
                f = 1
            selected.append((items, f))

        result = aggregate(selected)
        self.summary.delete("1.0", tk.END)
        for name, amount, unit in result:
            self.summary.insert(tk.END, f"- {amount} {unit} {name}\n")

        # Save as PDF
    def export_pdf(self):
        if not self.summary.get("1.0", tk.END).strip():
            return  # Nichts zu exportieren

        file = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Datei", "*.pdf")],
            title="Speichern unter"
        )
        if not file:
            return

        text = self.summary.get("1.0", tk.END).strip().split("\n")
        c = canvas.Canvas(file, pagesize=A4)
        width, height = A4
        margin = 50
        y = height - margin

        c.setFont("Helvetica", 12)
        c.drawString(margin, y, "Einkaufsliste")
        y -= 30

        for line in text:
            c.drawString(margin, y, line)
            y -= 20
            if y < 50:  # Neue Seite
                c.showPage()
                c.setFont("Helvetica", 12)
                y = height - margin

        c.save()
        messagebox.showinfo("PDF gespeichert", f"Einkaufsliste gespeichert unter:\n{file}")


def simple_input(root, title, text):
    top = tk.Toplevel(root)
    top.title(title)
    ttk.Label(top, text=text).pack(padx=10, pady=5)
    val = tk.StringVar()
    entry = ttk.Entry(top, textvariable=val)
    entry.pack(padx=10, pady=5)
    entry.focus()

    result = {"v": None}
    def submit():
        result["v"] = val.get()
        top.destroy()

    ttk.Button(top, text="OK", command=submit).pack(pady=5)
    root.wait_window(top)
    return result["v"]


