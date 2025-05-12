from tkinter import *
from tkinter import ttk, messagebox
import sqlite3


class InventoryManagementApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Система управления запасами")
        self.root.geometry("1000x600")

        # Главное меню
        menu = Menu(self.root)
        self.root.config(menu=menu)

        # Добавление пунктов меню
        menu.add_command(label="Товары", command=self.show_products)
        menu.add_command(label="Категории", command=self.show_categories)
        menu.add_command(label="Остатки", command=self.show_inventory)
        menu.add_command(label="Поставки", command=self.show_supplies)
        menu.add_command(label="Отчеты", command=self.show_reports)

        # Основное содержимое
        self.main_frame = Frame(self.root)
        self.main_frame.pack(fill=BOTH, expand=True)

        # Вкладка по умолчанию
        self.show_products()

    def clear_main_frame(self):
        """Очистка основного содержимого окна."""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    # === Управление товарами ===
    def show_products(self):
        """Отображение окна управления товарами."""
        self.clear_main_frame()
        Label(self.main_frame, text="Управление товарами", font=("Arial", 20)).pack(pady=10)

        # Фильтры для поиска
        filter_frame = Frame(self.main_frame)
        filter_frame.pack(pady=10, fill=X)
        Label(filter_frame, text="Фильтр по названию:").pack(side=LEFT, padx=5)
        self.filter_name = Entry(filter_frame, width=20)
        self.filter_name.pack(side=LEFT, padx=5)
        Label(filter_frame, text="Фильтр по категории:").pack(side=LEFT, padx=5)
        self.filter_category = Entry(filter_frame, width=20)
        self.filter_category.pack(side=LEFT, padx=5)
        Button(filter_frame, text="Применить фильтр", command=self.load_products).pack(side=LEFT, padx=5)

        # Кнопки действий
        button_frame = Frame(self.main_frame)
        button_frame.pack(pady=10)
        Button(button_frame, text="Добавить товар", command=self.add_product).pack(side=LEFT, padx=5)
        Button(button_frame, text="Редактировать товар", command=self.edit_product).pack(side=LEFT, padx=5)
        Button(button_frame, text="Удалить товар", command=self.delete_product).pack(side=LEFT, padx=5)

        # Таблица товаров
        self.product_tree = ttk.Treeview(
            self.main_frame,
            columns=("ID", "Название", "Категория", "Артикул", "Остаток", "Закупочная цена", "Розничная цена"),
            show="headings",
            height=15
        )
        for col in self.product_tree["columns"]:
            self.product_tree.heading(col, text=col, command=lambda c=col: self.sort_products(c))
            self.product_tree.column(col, anchor="center", width=120)
        self.product_tree.pack(fill=BOTH, expand=True)

        # Загрузка данных
        self.load_products()

    def load_products(self):
        """Загрузка списка товаров из базы данных с учетом фильтров."""
        try:
            conn = sqlite3.connect("inventory_system.db")
            cursor = conn.cursor()

            # Очистка таблицы
            for row in self.product_tree.get_children():
                self.product_tree.delete(row)

            # Подготовка фильтров
            name_filter = self.filter_name.get().strip()
            category_filter = self.filter_category.get().strip()
            query = '''
                SELECT p.id, p.name, c.name AS category, p.sku, i.quantity, p.purchase_price, p.retail_price
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                LEFT JOIN inventory i ON p.id = i.product_id
                WHERE 1=1
            '''
            params = []
            if name_filter:
                query += " AND p.name LIKE ?"
                params.append(f"%{name_filter}%")
            if category_filter:
                query += " AND c.name LIKE ?"
                params.append(f"%{category_filter}%")

            # Выполнение запроса
            cursor.execute(query, params)
            for row in cursor.fetchall():
                self.product_tree.insert("", "end", values=row)

            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка", f"Ошибка базы данных: {e}")

    def sort_products(self, column):
        """Сортировка таблицы товаров по указанной колонке."""
        data = [(self.product_tree.set(k, column), k) for k in self.product_tree.get_children("")]
        data.sort(key=lambda t: t[0])
        for index, (val, k) in enumerate(data):
            self.product_tree.move(k, "", index)

    def add_product(self):
        """Окно добавления нового товара."""
        def save_new_product():
            name = name_entry.get().strip()
            sku = sku_entry.get().strip()
            category = category_var.get()
            purchase_price = purchase_price_entry.get().strip()
            retail_price = retail_price_entry.get().strip()
            min_stock = min_stock_entry.get().strip()

            if not all([name, sku, category, purchase_price, retail_price, min_stock]):
                messagebox.showerror("Ошибка", "Все поля обязательны для заполнения.")
                return

            try:
                conn = sqlite3.connect("inventory_system.db")
                cursor = conn.cursor()

                # Получение ID категории
                cursor.execute("SELECT id FROM categories WHERE name = ?", (category,))
                category_id = cursor.fetchone()
                if category_id is None:
                    messagebox.showerror("Ошибка", "Указанная категория не существует.")
                    return

                # Вставка данных
                cursor.execute('''
                    INSERT INTO products (name, sku, category_id, purchase_price, retail_price, min_stock)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, sku, category_id[0], float(purchase_price), float(retail_price), int(min_stock)))
                conn.commit()
                conn.close()

                messagebox.showinfo("Успех", "Товар успешно добавлен.")
                self.load_products()
                add_window.destroy()
            except sqlite3.Error as e:
                messagebox.showerror("Ошибка", f"Ошибка базы данных: {e}")

        # Создание окна
        add_window = Toplevel(self.root)
        add_window.title("Добавить товар")
        Label(add_window, text="Название:").grid(row=0, column=0, padx=10, pady=5)
        name_entry = Entry(add_window, width=30)
        name_entry.grid(row=0, column=1, padx=10, pady=5)

        Label(add_window, text="Артикул:").grid(row=1, column=0, padx=10, pady=5)
        sku_entry = Entry(add_window, width=30)
        sku_entry.grid(row=1, column=1, padx=10, pady=5)

        Label(add_window, text="Категория:").grid(row=2, column=0, padx=10, pady=5)
        category_var = StringVar()
        category_dropdown = ttk.Combobox(add_window, textvariable=category_var, state="readonly")
        category_dropdown.grid(row=2, column=1, padx=10, pady=5)

        # Загрузка категорий
        try:
            conn = sqlite3.connect("inventory_system.db")
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM categories")
            categories = [row[0] for row in cursor.fetchall()]
            conn.close()
            category_dropdown["values"] = categories
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка", f"Ошибка базы данных: {e}")

        Label(add_window, text="Закупочная цена:").grid(row=3, column=0, padx=10, pady=5)
        purchase_price_entry = Entry(add_window, width=30)
        purchase_price_entry.grid(row=3, column=1, padx=10, pady=5)

        Label(add_window, text="Розничная цена:").grid(row=4, column=0, padx=10, pady=5)
        retail_price_entry = Entry(add_window, width=30)
        retail_price_entry.grid(row=4, column=1, padx=10, pady=5)

        Label(add_window, text="Минимальный остаток:").grid(row=5, column=0, padx=10, pady=5)
        min_stock_entry = Entry(add_window, width=30)
        min_stock_entry.grid(row=5, column=1, padx=10, pady=5)

        Button(add_window, text="Сохранить", command=save_new_product).grid(row=6, column=0, columnspan=2, pady=10)

    def edit_product(self):
        """Окно редактирования товара."""
        selected_item = self.product_tree.selection()
        if not selected_item:
            messagebox.showerror("Ошибка", "Выберите товар для редактирования.")
            return

        # Получение данных выбранного товара
        item = self.product_tree.item(selected_item)
        product_id = item["values"][0]

        def save_edited_product():
            name = name_entry.get().strip()
            sku = sku_entry.get().strip()
            category = category_var.get()
            purchase_price = purchase_price_entry.get().strip()
            retail_price = retail_price_entry.get().strip()
            min_stock = min_stock_entry.get().strip()

            if not all([name, sku, category, purchase_price, retail_price, min_stock]):
                messagebox.showerror("Ошибка", "Все поля обязательны для заполнения.")
                return

            try:
                conn = sqlite3.connect("inventory_system.db")
                cursor = conn.cursor()

                # Получение ID категории
                cursor.execute("SELECT id FROM categories WHERE name = ?", (category,))
                category_id = cursor.fetchone()
                if category_id is None:
                    messagebox.showerror("Ошибка", "Указанная категория не существует.")
                    return

                # Обновление данных
                cursor.execute('''
                    UPDATE products
                    SET name = ?, sku = ?, category_id = ?, purchase_price = ?, retail_price = ?, min_stock = ?
                    WHERE id = ?
                ''', (name, sku, category_id[0], float(purchase_price), float(retail_price), int(min_stock), product_id))
                conn.commit()
                conn.close()

                messagebox.showinfo("Успех", "Товар успешно обновлен.")
                self.load_products()
                edit_window.destroy()
            except sqlite3.Error as e:
                messagebox.showerror("Ошибка", f"Ошибка базы данных: {e}")

        # Создание окна
        edit_window = Toplevel(self.root)
        edit_window.title("Редактировать товар")
        Label(edit_window, text="Название:").grid(row=0, column=0, padx=10, pady=5)
        name_entry = Entry(edit_window, width=30)
        name_entry.insert(0, item["values"][1])
        name_entry.grid(row=0, column=1, padx=10, pady=5)

        Label(edit_window, text="Артикул:").grid(row=1, column=0, padx=10, pady=5)
        sku_entry = Entry(edit_window, width=30)
        sku_entry.insert(0, item["values"][3])
        sku_entry.grid(row=1, column=1, padx=10, pady=5)

        Label(edit_window, text="Категория:").grid(row=2, column=0, padx=10, pady=5)
        category_var = StringVar()
        category_dropdown = ttk.Combobox(edit_window, textvariable=category_var, state="readonly")
        category_dropdown.grid(row=2, column=1, padx=10, pady=5)

        # Загрузка категорий
        try:
            conn = sqlite3.connect("inventory_system.db")
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM categories")
            categories = [row[0] for row in cursor.fetchall()]
            conn.close()
            category_dropdown["values"] = categories
            category_dropdown.set(item["values"][2])
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка", f"Ошибка базы данных: {e}")

        Label(edit_window, text="Закупочная цена:").grid(row=3, column=0, padx=10, pady=5)
        purchase_price_entry = Entry(edit_window, width=30)
        purchase_price_entry.insert(0, item["values"][5])
        purchase_price_entry.grid(row=3, column=1, padx=10, pady=5)

        Label(edit_window, text="Розничная цена:").grid(row=4, column=0, padx=10, pady=5)
        retail_price_entry = Entry(edit_window, width=30)
        retail_price_entry.insert(0, item["values"][6])
        retail_price_entry.grid(row=4, column=1, padx=10, pady=5)

        Label(edit_window, text="Минимальный остаток:").grid(row=5, column=0, padx=10, pady=5)
        min_stock_entry = Entry(edit_window, width=30)
        min_stock_entry.insert(0, 1)  # Текущий минимальный остаток
        min_stock_entry.grid(row=5, column=1, padx=10, pady=5)

        Button(edit_window, text="Сохранить", command=save_edited_product).grid(row=6, column=0, columnspan=2, pady=10)

    def delete_product(self):
        """Удаление товара."""
        selected_item = self.product_tree.selection()
        if not selected_item:
            messagebox.showerror("Ошибка", "Выберите товар для удаления.")
            return

        # Получение ID выбранного товара
        item = self.product_tree.item(selected_item)
        product_id = item["values"][0]

        confirm = messagebox.askyesno("Подтверждение", f"Вы уверены, что хотите удалить товар '{item['values'][1]}'?")
        if not confirm:
            return

        try:
            conn = sqlite3.connect("inventory_system.db")
            cursor = conn.cursor()

            # Удаление товара
            cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()
            conn.close()

            messagebox.showinfo("Успех", "Товар успешно удален.")
            self.load_products()
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка", f"Ошибка базы данных: {e}")

    # === Управление категориями ===
    def show_categories(self):
        """Отображение окна управления категориями."""
        self.clear_main_frame()
        Label(self.main_frame, text="Управление категориями", font=("Arial", 20)).pack(pady=10)

        # Кнопки действий
        button_frame = Frame(self.main_frame)
        button_frame.pack(pady=10)
        Button(button_frame, text="Добавить категорию", command=self.add_category).pack(side=LEFT, padx=5)
        Button(button_frame, text="Редактировать категорию", command=self.edit_category).pack(side=LEFT, padx=5)
        Button(button_frame, text="Удалить категорию", command=self.delete_category).pack(side=LEFT, padx=5)

        # Таблица категорий
        self.category_tree = ttk.Treeview(
            self.main_frame,
            columns=("ID", "Название", "Описание"),
            show="headings",
            height=15
        )
        for col in self.category_tree["columns"]:
            self.category_tree.heading(col, text=col, command=lambda c=col: self.sort_categories(c))
            self.category_tree.column(col, anchor="center", width=200)
        self.category_tree.pack(fill=BOTH, expand=True)

        # Загрузка данных
        self.load_categories()

    def load_categories(self):
        """Загрузка списка категорий из базы данных."""
        try:
            conn = sqlite3.connect("inventory_system.db")
            cursor = conn.cursor()

            # Очистка таблицы
            for row in self.category_tree.get_children():
                self.category_tree.delete(row)

            # Загрузка данных
            cursor.execute("SELECT id, name, description FROM categories")
            for row in cursor.fetchall():
                self.category_tree.insert("", "end", values=row)

            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка", f"Ошибка базы данных: {e}")

    def sort_categories(self, column):
        """Сортировка таблицы категорий по указанной колонке."""
        data = [(self.category_tree.set(k, column), k) for k in self.category_tree.get_children("")]
        data.sort(key=lambda t: t[0])
        for index, (val, k) in enumerate(data):
            self.category_tree.move(k, "", index)

    def add_category(self):
        """Окно добавления новой категории."""
        def save_new_category():
            name = name_entry.get().strip()
            description = description_entry.get().strip()

            if not name:
                messagebox.showerror("Ошибка", "Название категории обязательно для заполнения.")
                return

            try:
                conn = sqlite3.connect("inventory_system.db")
                cursor = conn.cursor()

                # Вставка данных
                cursor.execute('''
                    INSERT INTO categories (name, description)
                    VALUES (?, ?)
                ''', (name, description))
                conn.commit()
                conn.close()

                messagebox.showinfo("Успех", "Категория успешно добавлена.")
                self.load_categories()
                add_window.destroy()
            except sqlite3.Error as e:
                messagebox.showerror("Ошибка", f"Ошибка базы данных: {e}")

        # Создание окна
        add_window = Toplevel(self.root)
        add_window.title("Добавить категорию")
        Label(add_window, text="Название:").grid(row=0, column=0, padx=10, pady=5)
        name_entry = Entry(add_window, width=30)
        name_entry.grid(row=0, column=1, padx=10, pady=5)

        Label(add_window, text="Описание:").grid(row=1, column=0, padx=10, pady=5)
        description_entry = Entry(add_window, width=30)
        description_entry.grid(row=1, column=1, padx=10, pady=5)

        Button(add_window, text="Сохранить", command=save_new_category).grid(row=2, column=0, columnspan=2, pady=10)

    def edit_category(self):
        """Окно редактирования категории."""
        selected_item = self.category_tree.selection()
        if not selected_item:
            messagebox.showerror("Ошибка", "Выберите категорию для редактирования.")
            return

        # Получение данных выбранной категории
        item = self.category_tree.item(selected_item)
        category_id = item["values"][0]

        def save_edited_category():
            name = name_entry.get().strip()
            description = description_entry.get().strip()

            if not name:
                messagebox.showerror("Ошибка", "Название категории обязательно для заполнения.")
                return

            try:
                conn = sqlite3.connect("inventory_system.db")
                cursor = conn.cursor()

                # Обновление данных
                cursor.execute('''
                    UPDATE categories
                    SET name = ?, description = ?
                    WHERE id = ?
                ''', (name, description, category_id))
                conn.commit()
                conn.close()

                messagebox.showinfo("Успех", "Категория успешно обновлена.")
                self.load_categories()
                edit_window.destroy()
            except sqlite3.Error as e:
                messagebox.showerror("Ошибка", f"Ошибка базы данных: {e}")

        # Создание окна
        edit_window = Toplevel(self.root)
        edit_window.title("Редактировать категорию")
        Label(edit_window, text="Название:").grid(row=0, column=0, padx=10, pady=5)
        name_entry = Entry(edit_window, width=30)
        name_entry.insert(0, item["values"][1])
        name_entry.grid(row=0, column=1, padx=10, pady=5)

        Label(edit_window, text="Описание:").grid(row=1, column=0, padx=10, pady=5)
        description_entry = Entry(edit_window, width=30)
        description_entry.insert(0, item["values"][2])
        description_entry.grid(row=1, column=1, padx=10, pady=5)

        Button(edit_window, text="Сохранить", command=save_edited_category).grid(row=2, column=0, columnspan=2, pady=10)

    def delete_category(self):
        """Удаление категории."""
        selected_item = self.category_tree.selection()
        if not selected_item:
            messagebox.showerror("Ошибка", "Выберите категорию для удаления.")
            return

        # Получение ID выбранной категории
        item = self.category_tree.item(selected_item)
        category_id = item["values"][0]

        confirm = messagebox.askyesno("Подтверждение", f"Вы уверены, что хотите удалить категорию '{item['values'][1]}'?")
        if not confirm:
            return

        try:
            conn = sqlite3.connect("inventory_system.db")
            cursor = conn.cursor()

            # Удаление категории
            cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
            conn.commit()
            conn.close()

            messagebox.showinfo("Успех", "Категория успешно удалена.")
            self.load_categories()
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка", f"Ошибка базы данных: {e}")

    # === Управление остатками ===
    def show_inventory(self):
        """Отображение окна управления остатками."""
        self.clear_main_frame()
        Label(self.main_frame, text="Управление остатками", font=("Arial", 20)).pack(pady=10)

        # Кнопки действий
        button_frame = Frame(self.main_frame)
        button_frame.pack(pady=10)
        Button(button_frame, text="Корректировать остаток", command=self.adjust_stock).pack(side=LEFT, padx=5)
        Button(button_frame, text="Просмотреть историю", command=self.view_stock_history).pack(side=LEFT, padx=5)

        # Таблица остатков
        self.inventory_tree = ttk.Treeview(
            self.main_frame,
            columns=("ID", "Название", "Артикул", "Остаток", "Минимальный остаток"),
            show="headings",
            height=15
        )
        for col in self.inventory_tree["columns"]:
            self.inventory_tree.heading(col, text=col, command=lambda c=col: self.sort_inventory(c))
            self.inventory_tree.column(col, anchor="center", width=150)
        self.inventory_tree.pack(fill=BOTH, expand=True)

        # Загрузка данных
        self.load_inventory()

    def load_inventory(self):
        """Загрузка текущих остатков из базы данных."""
        try:
            conn = sqlite3.connect("inventory_system.db")
            cursor = conn.cursor()

            # Очистка таблицы
            for row in self.inventory_tree.get_children():
                self.inventory_tree.delete(row)

            # Загрузка данных
            cursor.execute('''
                SELECT p.id, p.name, p.sku, i.quantity, p.min_stock
                FROM products p
                LEFT JOIN inventory i ON p.id = i.product_id
            ''')
            for row in cursor.fetchall():
                self.inventory_tree.insert("", "end", values=row)

            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка", f"Ошибка базы данных: {e}")

    def sort_inventory(self, column):
        """Сортировка таблицы остатков по указанной колонке."""
        data = [(self.inventory_tree.set(k, column), k) for k in self.inventory_tree.get_children("")]
        data.sort(key=lambda t: t[0])
        for index, (val, k) in enumerate(data):
            self.inventory_tree.move(k, "", index)

    def adjust_stock(self):
        """Окно корректировки остатка."""
        selected_item = self.inventory_tree.selection()
        if not selected_item:
            messagebox.showerror("Ошибка", "Выберите товар для корректировки.")
            return

        # Получение данных выбранного товара
        item = self.inventory_tree.item(selected_item)
        product_id = item["values"][0]
        current_quantity = item["values"][3]

        def save_stock_adjustment():
            new_quantity = new_quantity_entry.get().strip()
            change_reason = reason_entry.get().strip()

            if not new_quantity or not change_reason:
                messagebox.showerror("Ошибка", "Все поля обязательны для заполнения.")
                return

            try:
                conn = sqlite3.connect("inventory_system.db")
                cursor = conn.cursor()

                # Обновление остатков
                cursor.execute('''
                    UPDATE inventory
                    SET quantity = ?, last_updated = datetime('now')
                    WHERE product_id = ?
                ''', (int(new_quantity), product_id))

                # Запись в историю изменений
                cursor.execute('''
                    INSERT INTO stock_history (product_id, change_reason, quantity_change, date)
                    VALUES (?, ?, ?, datetime('now'))
                ''', (product_id, change_reason, int(new_quantity) - current_quantity))
                conn.commit()
                conn.close()

                messagebox.showinfo("Успех", "Остаток успешно обновлен.")
                self.load_inventory()
                adjust_window.destroy()
            except sqlite3.Error as e:
                messagebox.showerror("Ошибка", f"Ошибка базы данных: {e}")

        # Создание окна
        adjust_window = Toplevel(self.root)
        adjust_window.title("Корректировка остатка")
        Label(adjust_window, text="Название:").grid(row=0, column=0, padx=10, pady=5)
        Label(adjust_window, text=item["values"][1]).grid(row=0, column=1, padx=10, pady=5)

        Label(adjust_window, text="Текущий остаток:").grid(row=1, column=0, padx=10, pady=5)
        Label(adjust_window, text=current_quantity).grid(row=1, column=1, padx=10, pady=5)

        Label(adjust_window, text="Новый остаток:").grid(row=2, column=0, padx=10, pady=5)
        new_quantity_entry = Entry(adjust_window, width=30)
        new_quantity_entry.grid(row=2, column=1, padx=10, pady=5)

        Label(adjust_window, text="Причина изменения:").grid(row=3, column=0, padx=10, pady=5)
        reason_entry = Entry(adjust_window, width=30)
        reason_entry.grid(row=3, column=1, padx=10, pady=5)

        Button(adjust_window, text="Сохранить", command=save_stock_adjustment).grid(row=4, column=0, columnspan=2, pady=10)

    def view_stock_history(self):
        """Окно просмотра истории изменений остатков."""
        def load_history():
            """Загрузка истории изменений."""
            try:
                conn = sqlite3.connect("inventory_system.db")
                cursor = conn.cursor()

                # Очистка таблицы
                for row in history_tree.get_children():
                    history_tree.delete(row)

                # Загрузка данных
                cursor.execute('''
                    SELECT sh.date, p.name, sh.quantity_change, sh.change_reason
                    FROM stock_history sh
                    JOIN products p ON sh.product_id = p.id
                    ORDER BY sh.date DESC
                ''')
                for row in cursor.fetchall():
                    history_tree.insert("", "end", values=row)

                conn.close()
            except sqlite3.Error as e:
                messagebox.showerror("Ошибка", f"Ошибка базы данных: {e}")

        # Создание окна
        history_window = Toplevel(self.root)
        history_window.title("История изменений остатков")

        # Таблица истории
        history_tree = ttk.Treeview(
            history_window,
            columns=("Дата", "Название", "Изменение", "Причина"),
            show="headings",
            height=15
        )
        for col in history_tree["columns"]:
            history_tree.heading(col, text=col)
            history_tree.column(col, anchor="center", width=200)
        history_tree.pack(fill=BOTH, expand=True)

        # Загрузка данных
        load_history()

    # === Управление поставками ===
    def show_supplies(self):
        """Отображение окна управления поставками."""
        self.clear_main_frame()
        Label(self.main_frame, text="Управление поставками", font=("Arial", 20)).pack(pady=10)

        # Кнопки действий
        button_frame = Frame(self.main_frame)
        button_frame.pack(pady=10)
        Button(button_frame, text="Добавить поставку", command=self.add_supply).pack(side=LEFT, padx=5)
        Button(button_frame, text="Просмотреть детали", command=self.view_supply_details).pack(side=LEFT, padx=5)
        Button(button_frame, text="Завершить поставку", command=self.complete_supply).pack(side=LEFT, padx=5)

        # Таблица поставок
        self.supply_tree = ttk.Treeview(
            self.main_frame,
            columns=("ID", "Поставщик", "Дата", "Статус"),
            show="headings",
            height=15
        )
        for col in self.supply_tree["columns"]:
            self.supply_tree.heading(col, text=col, command=lambda c=col: self.sort_supplies(c))
            self.supply_tree.column(col, anchor="center", width=150)
        self.supply_tree.pack(fill=BOTH, expand=True)

        # Загрузка данных
        self.load_supplies()

    def load_supplies(self):
        """Загрузка списка поставок из базы данных."""
        try:
            conn = sqlite3.connect("inventory_system.db")
            cursor = conn.cursor()

            # Очистка таблицы
            for row in self.supply_tree.get_children():
                self.supply_tree.delete(row)

            # Загрузка данных
            cursor.execute('''
                SELECT s.id, sp.name, s.date, s.status
                FROM supplies s
                LEFT JOIN suppliers sp ON s.supplier_id = sp.id
            ''')
            for row in cursor.fetchall():
                self.supply_tree.insert("", "end", values=row)

            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка", f"Ошибка базы данных: {e}")

    def sort_supplies(self, column):
        """Сортировка таблицы поставок по указанной колонке."""
        data = [(self.supply_tree.set(k, column), k) for k in self.supply_tree.get_children("")]
        data.sort(key=lambda t: t[0])
        for index, (val, k) in enumerate(data):
            self.supply_tree.move(k, "", index)

    def add_supply(self):
        """Окно добавления новой поставки."""
        def save_new_supply():
            supplier = supplier_var.get()
            date = date_entry.get().strip()
            status = status_var.get()

            if not all([supplier, date, status]):
                messagebox.showerror("Ошибка", "Все поля обязательны для заполнения.")
                return

            try:
                conn = sqlite3.connect("inventory_system.db")
                cursor = conn.cursor()

                # Получение ID поставщика
                cursor.execute("SELECT id FROM suppliers WHERE name = ?", (supplier,))
                supplier_id = cursor.fetchone()
                if supplier_id is None:
                    messagebox.showerror("Ошибка", "Указанный поставщик не существует.")
                    return

                # Вставка данных
                cursor.execute('''
                    INSERT INTO supplies (supplier_id, date, status)
                    VALUES (?, ?, ?)
                ''', (supplier_id[0], date, status))
                conn.commit()
                conn.close()

                messagebox.showinfo("Успех", "Поставка успешно добавлена.")
                self.load_supplies()
                add_window.destroy()
            except sqlite3.Error as e:
                messagebox.showerror("Ошибка", f"Ошибка базы данных: {e}")

        # Создание окна
        add_window = Toplevel(self.root)
        add_window.title("Добавить поставку")
        Label(add_window, text="Поставщик:").grid(row=0, column=0, padx=10, pady=5)
        supplier_var = StringVar()
        supplier_dropdown = ttk.Combobox(add_window, textvariable=supplier_var, state="readonly")
        supplier_dropdown.grid(row=0, column=1, padx=10, pady=5)

        # Загрузка поставщиков
        try:
            conn = sqlite3.connect("inventory_system.db")
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM suppliers")
            suppliers = [row[0] for row in cursor.fetchall()]
            conn.close()
            supplier_dropdown["values"] = suppliers
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка", f"Ошибка базы данных: {e}")

        Label(add_window, text="Дата (YYYY-MM-DD):").grid(row=1, column=0, padx=10, pady=5)
        date_entry = Entry(add_window, width=30)
        date_entry.grid(row=1, column=1, padx=10, pady=5)

        Label(add_window, text="Статус:").grid(row=2, column=0, padx=10, pady=5)
        status_var = StringVar()
        status_dropdown = ttk.Combobox(add_window, textvariable=status_var, state="readonly")
        status_dropdown["values"] = ["Ожидается", "В пути", "Доставлено", "Отменено"]
        status_dropdown.grid(row=2, column=1, padx=10, pady=5)

        Button(add_window, text="Сохранить", command=save_new_supply).grid(row=3, column=0, columnspan=2, pady=10)

    def view_supply_details(self):
        """Окно просмотра деталей поставки."""
        selected_item = self.supply_tree.selection()
        if not selected_item:
            messagebox.showerror("Ошибка", "Выберите поставку для просмотра.")
            return

        # Получение данных выбранной поставки
        item = self.supply_tree.item(selected_item)
        supply_id = item["values"][0]

        def load_supply_items():
            """Загрузка товаров из выбранной поставки."""
            try:
                conn = sqlite3.connect("inventory_system.db")
                cursor = conn.cursor()

                # Очистка таблицы
                for row in item_tree.get_children():
                    item_tree.delete(row)

                # Загрузка данных
                cursor.execute('''
                    SELECT p.name, i.quantity
                    FROM supply_items i
                    JOIN products p ON i.product_id = p.id
                    WHERE i.supply_id = ?
                ''', (supply_id,))
                for row in cursor.fetchall():
                    item_tree.insert("", "end", values=row)

                conn.close()
            except sqlite3.Error as e:
                messagebox.showerror("Ошибка", f"Ошибка базы данных: {e}")

        # Создание окна
        details_window = Toplevel(self.root)
        details_window.title("Детали поставки")

        # Таблица товаров
        item_tree = ttk.Treeview(
            details_window,
            columns=("Название", "Количество"),
            show="headings",
            height=15
        )
        for col in item_tree["columns"]:
            item_tree.heading(col, text=col)
            item_tree.column(col, anchor="center", width=200)
        item_tree.pack(fill=BOTH, expand=True)

        # Загрузка данных
        load_supply_items()

    def add_items_to_supply(self):
        """Окно добавления товаров в поставку."""
        selected_item = self.supply_tree.selection()
        if not selected_item:
            messagebox.showerror("Ошибка", "Выберите поставку для добавления товаров.")
            return

        # Получение данных выбранной поставки
        item = self.supply_tree.item(selected_item)
        supply_id = item["values"][0]

        def save_item_to_supply():
            product = product_var.get()
            quantity = quantity_entry.get().strip()

            if not all([product, quantity]):
                messagebox.showerror("Ошибка", "Все поля обязательны для заполнения.")
                return

            try:
                conn = sqlite3.connect("inventory_system.db")
                cursor = conn.cursor()

                # Получение ID товара
                cursor.execute("SELECT id FROM products WHERE name = ?", (product,))
                product_id = cursor.fetchone()
                if product_id is None:
                    messagebox.showerror("Ошибка", "Указанный товар не существует.")
                    return

                # Вставка данных
                cursor.execute('''
                    INSERT INTO supply_items (supply_id, product_id, quantity)
                    VALUES (?, ?, ?)
                ''', (supply_id, product_id[0], int(quantity)))
                conn.commit()
                conn.close()

                messagebox.showinfo("Успех", "Товар успешно добавлен в поставку.")
                load_supply_items()
            except sqlite3.Error as e:
                messagebox.showerror("Ошибка", f"Ошибка базы данных: {e}")

        def load_supply_items():
            """Загрузка товаров из выбранной поставки."""
            try:
                conn = sqlite3.connect("inventory_system.db")
                cursor = conn.cursor()

                # Очистка таблицы
                for row in items_tree.get_children():
                    items_tree.delete(row)

                # Загрузка данных
                cursor.execute('''
                    SELECT p.name, i.quantity
                    FROM supply_items i
                    JOIN products p ON i.product_id = p.id
                    WHERE i.supply_id = ?
                ''', (supply_id,))
                for row in cursor.fetchall():
                    items_tree.insert("", "end", values=row)

                conn.close()
            except sqlite3.Error as e:
                messagebox.showerror("Ошибка", f"Ошибка базы данных: {e}")

        # Создание окна
        items_window = Toplevel(self.root)
        items_window.title("Добавление товаров в поставку")

        # Поля для добавления товаров
        Label(items_window, text="Товар:").grid(row=0, column=0, padx=10, pady=5)
        product_var = StringVar()
        product_dropdown = ttk.Combobox(items_window, textvariable=product_var, state="readonly")
        product_dropdown.grid(row=0, column=1, padx=10, pady=5)

        # Загрузка товаров
        try:
            conn = sqlite3.connect("inventory_system.db")
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM products")
            products = [row[0] for row in cursor.fetchall()]
            conn.close()
            product_dropdown["values"] = products
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка", f"Ошибка базы данных: {e}")

        Label(items_window, text="Количество:").grid(row=1, column=0, padx=10, pady=5)
        quantity_entry = Entry(items_window, width=30)
        quantity_entry.grid(row=1, column=1, padx=10, pady=5)

        Button(items_window, text="Добавить", command=save_item_to_supply).grid(row=2, column=0, columnspan=2, pady=10)

        # Таблица товаров в поставке
        items_tree = ttk.Treeview(
            items_window,
            columns=("Название", "Количество"),
            show="headings",
            height=15
        )
        for col in items_tree["columns"]:
            items_tree.heading(col, text=col)
            items_tree.column(col, anchor="center", width=200)
        items_tree.grid(row=3, column=0, columnspan=2, pady=10)

        # Загрузка товаров
        load_supply_items()

    def complete_supply(self):
        """Функция завершения поставки."""
        selected_item = self.supply_tree.selection()
        if not selected_item:
            messagebox.showerror("Ошибка", "Выберите поставку для завершения.")
            return

        # Получение данных выбранной поставки
        item = self.supply_tree.item(selected_item)
        supply_id = item["values"][0]
        supply_status = item["values"][3]

        # Проверка текущего статуса поставки
        if supply_status == "Доставлено":
            messagebox.showinfo("Информация", "Эта поставка уже завершена.")
            return

        confirm = messagebox.askyesno("Подтверждение", "Вы уверены, что хотите завершить эту поставку?")
        if not confirm:
            return

        try:
            conn = sqlite3.connect("inventory_system.db")
            cursor = conn.cursor()

            # Обновление остатков товаров
            cursor.execute('''
                SELECT product_id, quantity
                FROM supply_items
                WHERE supply_id = ?
            ''', (supply_id,))
            items = cursor.fetchall()
            for product_id, quantity in items:
                cursor.execute('''
                    UPDATE inventory
                    SET quantity = quantity + ?
                    WHERE product_id = ?
                ''', (quantity, product_id))

            # Обновление статуса поставки
            cursor.execute('''
                UPDATE supplies
                SET status = "Доставлено"
                WHERE id = ?
            ''', (supply_id,))
            conn.commit()
            conn.close()

            messagebox.showinfo("Успех", "Поставка успешно завершена. Остатки обновлены.")
            self.load_supplies()
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка", f"Ошибка базы данных: {e}")

    # === Формирование отчетов ===
    def show_reports(self):
        """Отображение окна формирования отчетов."""
        self.clear_main_frame()
        Label(self.main_frame, text="Формирование отчетов", font=("Arial", 20)).pack(pady=10)

        # Выбор типа отчета
        report_frame = Frame(self.main_frame)
        report_frame.pack(pady=10)
        Button(report_frame, text="Отчет по остаткам", command=self.generate_stock_report).pack(side=LEFT, padx=5)
        Button(report_frame, text="Отчет по поставкам", command=self.generate_supply_report).pack(side=LEFT, padx=5)
        Button(report_frame, text="Отчет по движению товаров", command=self.generate_stock_movement_report).pack(side=LEFT, padx=5)

        # Поле для вывода отчета
        self.report_text = Text(self.main_frame, wrap=WORD, width=100, height=30)
        self.report_text.pack(pady=10, fill=BOTH, expand=True)

    def display_report(self, content):
        """Вывод отчета в текстовом поле."""
        self.report_text.delete(1.0, END)
        self.report_text.insert(END, content)

    def generate_stock_report(self):
        """Генерация отчета по остаткам."""
        try:
            conn = sqlite3.connect("inventory_system.db")
            cursor = conn.cursor()

            # Получение данных об остатках
            cursor.execute('''
                SELECT p.name, p.sku, i.quantity, p.min_stock
                FROM products p
                LEFT JOIN inventory i ON p.id = i.product_id
            ''')
            rows = cursor.fetchall()
            conn.close()

            # Формирование отчета
            report = "Отчет по остаткам товаров\n"
            report += "-" * 50 + "\n"
            report += f"{'Название':<20} {'Артикул':<10} {'Остаток':<10} {'Мин. остаток':<10}\n"
            report += "-" * 50 + "\n"
            for row in rows:
                name, sku, quantity, min_stock = row
                quantity = quantity if quantity is not None else 0
                warning = " ⚠️" if quantity < min_stock else ""
                report += f"{name:<20} {sku:<10} {quantity:<10} {min_stock:<10}{warning}\n"
            report += "-" * 50 + "\n"

            self.display_report(report)
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка", f"Ошибка базы данных: {e}")

    def generate_supply_report(self):
        """Генерация отчета по поставкам."""
        try:
            conn = sqlite3.connect("inventory_system.db")
            cursor = conn.cursor()

            # Получение данных о поставках
            cursor.execute('''
                SELECT s.id, sp.name AS supplier, s.date, s.status
                FROM supplies s
                LEFT JOIN suppliers sp ON s.supplier_id = sp.id
                ORDER BY s.date DESC
            ''')
            supplies = cursor.fetchall()

            # Формирование отчета
            report = "Отчет по поставкам\n"
            report += "-" * 50 + "\n"
            report += f"{'ID':<5} {'Поставщик':<20} {'Дата':<15} {'Статус':<10}\n"
            report += "-" * 50 + "\n"
            for supply in supplies:
                supply_id, supplier, date, status = supply
                report += f"{supply_id:<5} {supplier:<20} {date:<15} {status:<10}\n"

                # Получение товаров в поставке
                cursor.execute('''
                    SELECT p.name, i.quantity
                    FROM supply_items i
                    JOIN products p ON i.product_id = p.id
                    WHERE i.supply_id = ?
                ''', (supply_id,))
                items = cursor.fetchall()
                for item in items:
                    product_name, quantity = item
                    report += f"    - {product_name} (Количество: {quantity})\n"

            report += "-" * 50 + "\n"
            conn.close()

            self.display_report(report)
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка", f"Ошибка базы данных: {e}")

    def generate_stock_movement_report(self):
        """Генерация отчета по движению товаров."""
        try:
            conn = sqlite3.connect("inventory_system.db")
            cursor = conn.cursor()

            # Получение данных о движении товаров
            cursor.execute('''
                SELECT sh.date, p.name, sh.quantity_change, sh.change_reason
                FROM stock_history sh
                JOIN products p ON sh.product_id = p.id
                ORDER BY sh.date DESC
            ''')
            movements = cursor.fetchall()
            conn.close()

            # Формирование отчета
            report = "Отчет по движению товаров\n"
            report += "-" * 50 + "\n"
            report += f"{'Дата':<20} {'Название':<20} {'Изменение':<10} {'Причина':<15}\n"
            report += "-" * 50 + "\n"
            for movement in movements:
                date, product_name, quantity_change, reason = movement
                report += f"{date:<20} {product_name:<20} {quantity_change:<10} {reason:<15}\n"
            report += "-" * 50 + "\n"

            self.display_report(report)
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка", f"Ошибка базы данных: {e}")




# Запуск приложения
if __name__ == "__main__":
    root = Tk()
    app = InventoryManagementApp(root)
    root.mainloop()