# Работает. Кул

import psycopg2
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
import sys

class ContractsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Система управления договорами")
        self.root.geometry("1200x700")
        self.original_data = {}

        # Параметры подключения к БД
        self.db_params = {
            'host': 'localhost',
            'database': 'my_db',
            'user': 'postgres',
            'password': 'student',
            'port': 1234
        }
        
        self.connection = None
        self.connect_db()
        
        self.create_widgets()
        self.load_table_list()
        
    def connect_db(self):
        """Подключение к базе данных"""
        try:
            self.connection = psycopg2.connect(**self.db_params)
            # Автоматический коммит для избежания проблем с транзакциями
            self.connection.autocommit = True
            print("Успешное подключение к БД")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось подключиться к БД: {e}")
            sys.exit(1)
    
    
    def create_widgets(self):
        """Создание интерфейса"""
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Верхняя панель
        top_frame = ttk.Frame(main_frame)
        top_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(top_frame, text="Таблица:").grid(row=0, column=0, padx=(0, 5))
        self.table_var = tk.StringVar()
        self.table_combo = ttk.Combobox(top_frame, textvariable=self.table_var, state="readonly", width=20)
        self.table_combo.grid(row=0, column=1, padx=(0, 10))
        self.table_combo.bind('<<ComboboxSelected>>', self.on_table_select)
        
        # Кнопки управления
        ttk.Button(top_frame, text="Обновить", command=self.load_data).grid(row=0, column=2, padx=2)
        ttk.Button(top_frame, text="Добавить", command=self.add_record).grid(row=0, column=3, padx=2)
        ttk.Button(top_frame, text="Редактировать", command=self.edit_record).grid(row=0, column=4, padx=2)
        ttk.Button(top_frame, text="Удалить", command=self.delete_record).grid(row=0, column=5, padx=2)
        ttk.Button(top_frame, text="Отчеты", command=self.show_reports).grid(row=0, column=6, padx=2)
        
        # Панель поиска и фильтрации
        search_frame = ttk.Frame(main_frame)
        search_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(search_frame, text="Поиск:").grid(row=0, column=0, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        self.search_entry.grid(row=0, column=1, padx=(0, 10))
        self.search_entry.bind('<KeyRelease>', self.search_records)
        
        ttk.Label(search_frame, text="Поле:").grid(row=0, column=2, padx=(0, 5))
        self.search_field_var = tk.StringVar()
        self.search_field_combo = ttk.Combobox(search_frame, textvariable=self.search_field_var, width=15)
        self.search_field_combo.grid(row=0, column=3, padx=(0, 10))
        
        ttk.Button(search_frame, text="Сброс", command=self.reset_filters).grid(row=0, column=4, padx=5)
        
        # Контейнер для таблицы как в Excel
        table_container = ttk.Frame(main_frame)
        table_container.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Создаем фрейм для дерева и скроллбаров
        tree_frame = ttk.Frame(table_container)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
       # Создаем Treeview
        self.tree = ttk.Treeview(tree_frame, show='headings')

    # Добавляем обработчики событий
        #self.tree.bind('<Motion>', self.on_treeview_select)  # всплывающая подсказка при наведении
        self.tree.bind('<Double-1>', self.show_full_text_dialog)  # полный текст по двойному клику
        
        # Вертикальный скроллбар
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=v_scrollbar.set)
        
        # Горизонтальный скроллбар
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(xscrollcommand=h_scrollbar.set)
        
        # Размещаем элементы с помощью pack (более надежно для скроллбаров)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Настройка весов для растягивания
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
 
    def on_table_select(self, event=None):
        """Обработчик выбора таблицы"""
        self.load_data()
        self.update_search_fields()
        
    def update_search_fields(self):
        """Обновление полей для поиска"""
        table = self.table_var.get()
        if not table:
            return
            
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = %s ORDER BY ordinal_position", (table,))
                columns = [row[0] for row in cursor.fetchall()]
                self.search_field_combo['values'] = columns
                if columns:
                    self.search_field_var.set(columns[0])
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при загрузке полей: {e}")
    
    def load_data(self):
        """Загрузка данных из выбранной таблицы"""
        table = self.table_var.get()
        if not table:
            return
            
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {table} ORDER BY 1")
                
                # Очистка таблицы
                for item in self.tree.get_children():
                    self.tree.delete(item)
                    
                # Установка колонок
                columns = [desc[0] for desc in cursor.description]
                self.tree['columns'] = columns
                
                # Автоподбор ширины колонок на основе заголовков
                for col in columns:
                    self.tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(c, False))
                    # Начальная ширина колонки на основе длины заголовка
                    width = max(80, len(col) * 8)
                    self.tree.column(col, width=width, minwidth=50, stretch=True)
                
                # Заполнение данными
                for row in cursor.fetchall():
                    self.tree.insert('', 'end', values=row)
                    
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при загрузке данных: {e}")
    
    def search_records(self, event=None):
        """Поиск записей"""
        table = self.table_var.get()
        search_text = self.search_var.get()
        search_field = self.search_field_var.get()
        
        if not table or not search_text or not search_field:
            self.load_data()
            return
            
        try:
            with self.connection.cursor() as cursor:
                query = f"SELECT * FROM {table} WHERE {search_field}::text ILIKE %s ORDER BY 1"
                cursor.execute(query, (f'%{search_text}%',))
                
                # Очистка и обновление таблицы
                for item in self.tree.get_children():
                    self.tree.delete(item)
                    
                for row in cursor.fetchall():
                    self.tree.insert('', 'end', values=row)
                    
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при поиске: {e}")
    
    def sort_treeview(self, col, reverse):
        """Сортировка таблицы по колонке"""
        data = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
        data.sort(reverse=reverse)
        
        for index, (val, child) in enumerate(data):
            self.tree.move(child, '', index)
            
        self.tree.heading(col, command=lambda: self.sort_treeview(col, not reverse))
    
    def reset_filters(self):
        """Сброс фильтров"""
        self.search_var.set("")
        self.load_data()
    
    def add_record(self):
        """Добавление новой записи"""
        table = self.table_var.get()
        if not table:
            messagebox.showwarning("Предупреждение", "Выберите таблицу")
            return
            
        if table == "contracts":
            self.add_contract_with_stages()
        else:
            self.show_add_dialog(table)
    
    def edit_record(self):
        """Редактирование выбранной записи"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите запись для редактирования")
            return
            
        table = self.table_var.get()
        values = self.tree.item(selected[0])['values']
        self.show_edit_dialog(table, values)
    
    def delete_record(self):
        """Удаление выбранной записи"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите запись для удаления")
            return
            
        if messagebox.askyesno("Подтверждение", "Удалить выбранную запись?"):
            try:
                # Создаем новое соединение для операции удаления
                with psycopg2.connect(**self.db_params) as conn:
                    with conn.cursor() as cursor:
                        table = self.table_var.get()
                        record_id = self.tree.item(selected[0])['values'][0]
                        
                        cursor.execute(f"DELETE FROM {table} WHERE {self.tree['columns'][0]} = %s", (record_id,))
                        conn.commit()
                        
                    self.load_data()
                    messagebox.showinfo("Успех", "Запись удалена")
                    
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при удалении: {e}")

    def show_add_dialog(self, table):
        """Диалог добавления записи"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Добавление в {table}")
        dialog.geometry("500x600")
        dialog.transient(self.root)  # Делаем окно модальным
        dialog.grab_set()  # Захватываем фокус
        
        # Обработчик закрытия окна
        def on_closing():
            dialog.grab_release()  # Освобождаем фокус
            dialog.destroy()
        
        dialog.protocol("WM_DELETE_WINDOW", on_closing)
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(f"""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = %s 
                    ORDER BY ordinal_position
                """, (table,))
                
                columns = cursor.fetchall()
                entries = {}
                
                # Создаем скроллируемый фрейм
                canvas = tk.Canvas(dialog)
                scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
                scrollable_frame = ttk.Frame(canvas)
                
                scrollable_frame.bind(
                    "<Configure>",
                    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
                )
                
                canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
                canvas.configure(yscrollcommand=scrollbar.set)
                
                main_frame = ttk.Frame(scrollable_frame, padding="10")
                main_frame.pack(fill=tk.BOTH, expand=True)
                
                for i, (col_name, data_type, is_nullable) in enumerate(columns):
                    # Пропускаем auto-increment поля
                    if 'serial' in data_type or col_name.endswith('_id') and 'nextval' in data_type:
                        continue
                        
                    ttk.Label(main_frame, text=f"{col_name}:").grid(row=i, column=0, sticky=tk.W, pady=2)
                    
                    # Для внешних ключей создаем выпадающие списки
                    if col_name.endswith('_id') and not col_name.endswith('org_id'):
                        # Получаем данные для выпадающего списка
                        ref_table = col_name.replace('_id', 's')  # contract_type_id -> contract_types
                        if ref_table == "stages":
                            ref_table = "stages"
                        elif ref_table == "vat_rates":
                            ref_table = "vat_rates"
                        
                        try:
                            with self.connection.cursor() as cursor2:
                                if ref_table == "contract_types":
                                    cursor2.execute(f"SELECT type_id, type_name FROM {ref_table} ORDER BY type_name")
                                elif ref_table == "stages":
                                    cursor2.execute(f"SELECT stage_id, stage_name FROM {ref_table} ORDER BY stage_id")
                                elif ref_table == "vat_rates":
                                    cursor2.execute(f"SELECT vat_id, vat_percent FROM {ref_table} ORDER BY vat_id")
                                else:
                                    cursor2.execute(f"SELECT {ref_table[:-1]}_id, {ref_table[:-1]}_name FROM {ref_table} ORDER BY 1")
                                
                                ref_data = cursor2.fetchall()
                            
                            combo_var = tk.StringVar()
                            combo = ttk.Combobox(main_frame, textvariable=combo_var, width=27)
                            combo['values'] = [f"{row[0]} - {row[1]}" for row in ref_data]
                            combo.grid(row=i, column=1, pady=2, padx=(5, 0))
                            entries[col_name] = (combo, 'combo')
                            
                        except Exception as e:
                            # Если не получилось создать комбобокс, используем обычное поле
                            entry = ttk.Entry(main_frame, width=30)
                            entry.grid(row=i, column=1, pady=2, padx=(5, 0))
                            entries[col_name] = (entry, 'entry')
                    
                    elif 'date' in data_type:
                        entry = ttk.Entry(main_frame, width=30)
                        entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
                        entry.grid(row=i, column=1, pady=2, padx=(5, 0))
                        entries[col_name] = (entry, 'entry')
                    else:
                        entry = ttk.Entry(main_frame, width=30)
                        entry.grid(row=i, column=1, pady=2, padx=(5, 0))
                        entries[col_name] = (entry, 'entry')
                
                canvas.pack(side="left", fill="both", expand=True)
                scrollbar.pack(side="right", fill="y")
                
                def save_record():
                    try:
                        # Создаем новое соединение для операции добавления
                        with psycopg2.connect(**self.db_params) as conn:
                            with conn.cursor() as cursor:
                                # Формируем INSERT запрос
                                valid_columns = []
                                values = []
                                
                                for col_name, (widget, widget_type) in entries.items():
                                    if widget_type == 'combo':
                                        value = widget.get().split(' - ')[0] if widget.get() else None
                                    else:
                                        value = widget.get()
                                    
                                    if value:  # Only include non-empty values
                                        valid_columns.append(col_name)
                                        values.append(value)
                                
                                if not valid_columns:
                                    messagebox.showerror("Ошибка", "Заполните хотя бы одно поле")
                                    return
                                
                                columns_str = ', '.join(valid_columns)
                                values_str = ', '.join(['%s'] * len(valid_columns))
                                
                                query = f"INSERT INTO {table} ({columns_str}) VALUES ({values_str})"
                                cursor.execute(query, values)
                                conn.commit()
                            
                            messagebox.showinfo("Успех", "Запись добавлена")
                            on_closing()
                            self.load_data()
                            
                    except Exception as e:
                        messagebox.showerror("Ошибка", f"Ошибка при добавлении: {e}")
                                
                button_frame = ttk.Frame(dialog)
                button_frame.pack(fill=tk.X, pady=10)
                
                ttk.Button(button_frame, text="Сохранить", command=save_record).pack(side=tk.LEFT, padx=5)
                ttk.Button(button_frame, text="Отмена", command=on_closing).pack(side=tk.LEFT, padx=5)
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при загрузке структуры таблицы: {e}")

    def show_edit_dialog(self, table, values):
        """Диалог редактирования записи"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Редактирование {table}")
        dialog.geometry("500x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        def on_closing():
            dialog.grab_release()
            dialog.destroy()
        
        dialog.protocol("WM_DELETE_WINDOW", on_closing)
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {table} LIMIT 0")
                columns = [desc[0] for desc in cursor.description]
                
                entries = {}
                
                # Создаем скроллируемый фрейм
                canvas = tk.Canvas(dialog)
                scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
                scrollable_frame = ttk.Frame(canvas)
                
                scrollable_frame.bind(
                    "<Configure>",
                    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
                )
                
                canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
                canvas.configure(yscrollcommand=scrollbar.set)
                
                main_frame = ttk.Frame(scrollable_frame, padding="10")
                main_frame.pack(fill=tk.BOTH, expand=True)
                
                for i, (col_name, value) in enumerate(zip(columns, values)):
                    ttk.Label(main_frame, text=f"{col_name}:").grid(row=i, column=0, sticky=tk.W, pady=2)
                    
                    # Для первого поля (ID) делаем нередактируемым
                    if i == 0:
                        entry = ttk.Entry(main_frame, width=30, state='readonly')
                    else:
                        entry = ttk.Entry(main_frame, width=30)
                    
                    entry.insert(0, str(value) if value is not None else "")
                    entry.grid(row=i, column=1, pady=2, padx=(5, 0))
                    entries[col_name] = entry
                
                canvas.pack(side="left", fill="both", expand=True)
                scrollbar.pack(side="right", fill="y")
                
                
                def save_changes():
                    try:
                        # Создаем новое соединение для операции редактирования
                        with psycopg2.connect(**self.db_params) as conn:
                            with conn.cursor() as cursor:
                                # Формируем UPDATE запрос
                                set_clause = ', '.join([f"{col} = %s" for col in columns[1:]])  # Пропускаем ID
                                new_values = [entries[col].get() for col in columns[1:]]
                                primary_key = columns[0]  # первый столбец - первичный ключ
                                
                                query = f"UPDATE {table} SET {set_clause} WHERE {primary_key} = %s"
                                cursor.execute(query, new_values + [values[0]])
                                conn.commit()
                            
                            messagebox.showinfo("Успех", "Запись обновлена")
                            on_closing()
                            self.load_data()
                            
                    except Exception as e:
                        messagebox.showerror("Ошибка", f"Ошибка при обновлении: {e}")
                
                button_frame = ttk.Frame(dialog)
                button_frame.pack(fill=tk.X, pady=10)
                
                ttk.Button(button_frame, text="Сохранить", command=save_changes).pack(side=tk.LEFT, padx=5)
                ttk.Button(button_frame, text="Отмена", command=on_closing).pack(side=tk.LEFT, padx=5)
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при загрузке данных: {e}")



    def add_contract_with_stages(self):
        """Форма для ввода договора с этапами (отношение 1:М) - с именами полей как в БД"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавление договора с этапами")
        dialog.geometry("800x700")
        
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Договор и этапы (отношение 1:М)", font=('Arial', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # === ПОЛЯ ДОГОВОРА (ОСНОВНАЯ ТАБЛИЦА) ===
        contract_frame = ttk.LabelFrame(main_frame, text="Таблица: contracts", padding="5")
        contract_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Поля договора с именами как в БД
        fields = [
            ("contract_code*:", "contract_code"),
            ("contract_date*:", "contract_date"), 
            ("subject*:", "subject"),
            ("note:", "note"),
            ("exec_date:", "exec_date")
        ]
        
        entries = {}
        for i, (label, field_name) in enumerate(fields):
            ttk.Label(contract_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=2)
            entry = ttk.Entry(contract_frame, width=40)
            if field_name == "contract_date":
                entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
            entry.grid(row=i, column=1, pady=2, padx=(5, 0))
            entries[field_name] = entry
        
        # Выпадающие списки для внешних ключей
        foreign_keys = [
            ("type_id*:", "type_id", "contract_types", "type_name"),
            ("stage_id*:", "stage_id", "stages", "stage_name"),
            ("vat_id*:", "vat_id", "vat_rates", "vat_percent"),
            ("customer_org_id*:", "customer_org_id", "organizations", "name"),
            ("contractor_org_id*:", "contractor_org_id", "organizations", "name")
        ]
        
        combo_vars = {}
        combo_widgets = {}
        ref_data = {}
        
        for i, (label, field_name, ref_table, ref_column) in enumerate(foreign_keys, start=len(fields)):
            ttk.Label(contract_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=2)
            combo_var = tk.StringVar()
            combo = ttk.Combobox(contract_frame, textvariable=combo_var, width=37)
            combo.grid(row=i, column=1, pady=2, padx=(5, 0))
            combo_vars[field_name] = combo_var
            combo_widgets[field_name] = combo
        
        # Заполняем комбобоксы данными
        try:
            with self.connection.cursor() as cursor:
                # Организации
                cursor.execute("SELECT org_id, name FROM organizations ORDER BY name")
                organizations = cursor.fetchall()
                ref_data['customer_org_id'] = {name: org_id for org_id, name in organizations}
                ref_data['contractor_org_id'] = {name: org_id for org_id, name in organizations}
                combo_widgets['customer_org_id']['values'] = [name for _, name in organizations]
                combo_widgets['contractor_org_id']['values'] = [name for _, name in organizations]
                
                # Типы договоров
                cursor.execute("SELECT type_id, type_name FROM contract_types ORDER BY type_name")
                types = cursor.fetchall()
                ref_data['type_id'] = {name: type_id for type_id, name in types}
                combo_widgets['type_id']['values'] = [name for _, name in types]
                
                # Стадии
                cursor.execute("SELECT stage_id, stage_name FROM stages ORDER BY stage_id")
                stages = cursor.fetchall()
                ref_data['stage_id'] = {name: stage_id for stage_id, name in stages}
                combo_widgets['stage_id']['values'] = [name for _, name in stages]
                
                # Ставки НДС
                cursor.execute("SELECT vat_id, vat_percent FROM vat_rates ORDER BY vat_id")
                vats = cursor.fetchall()
                ref_data['vat_id'] = {f"{percent}%": vat_id for vat_id, percent in vats}
                combo_widgets['vat_id']['values'] = [f"{percent}%" for _, percent in vats]
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки справочников: {e}")
            return
        
        # === ЭТАПЫ ДОГОВОРА (СВЯЗАННАЯ ТАБЛИЦА) ===
        stages_frame = ttk.LabelFrame(main_frame, text="Таблица: contract_stages", padding="5")
        stages_frame.grid(row=9, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Таблица этапов с именами колонок как в БД
        columns = ('stage_no', 'planned_exec_date', 'topic', 'stage_sum', 'advance_sum')
        stages_tree = ttk.Treeview(stages_frame, columns=columns, show='headings', height=6)
        
        # Заголовки столбцов как в БД
        stages_tree.heading('stage_no', text='stage_no')
        stages_tree.heading('planned_exec_date', text='planned_exec_date')
        stages_tree.heading('topic', text='topic')
        stages_tree.heading('stage_sum', text='stage_sum')
        stages_tree.heading('advance_sum', text='advance_sum')
        
        # Ширина столбцов
        stages_tree.column('stage_no', width=80)
        stages_tree.column('planned_exec_date', width=120)
        stages_tree.column('topic', width=200)
        stages_tree.column('stage_sum', width=100)
        stages_tree.column('advance_sum', width=100)
        
        stages_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Кнопки управления этапами
        stages_buttons = ttk.Frame(stages_frame)
        stages_buttons.pack(fill=tk.X, pady=5)
        
        ttk.Button(stages_buttons, text="Добавить этап", 
                command=lambda: self.add_stage_dialog(stages_tree)).pack(side=tk.LEFT, padx=2)
        ttk.Button(stages_buttons, text="Удалить этап", 
                command=lambda: self.delete_stage(stages_tree)).pack(side=tk.LEFT, padx=2)
        ttk.Button(stages_buttons, text="Очистить все", 
                command=lambda: self.clear_all_stages(stages_tree)).pack(side=tk.LEFT, padx=2)
        
        # === КНОПКИ СОХРАНЕНИЯ ===
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=10, column=0, columnspan=2, pady=10)
        
        ttk.Button(buttons_frame, text="Сохранить договор с этапами", 
                command=lambda: self.save_contract_with_stages_db_names(
                    dialog, entries, combo_vars, stages_tree, ref_data
                )).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Настройка весов для растягивания
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(9, weight=1)

    def add_stage_dialog(self, stages_tree):
        """Диалог добавления этапа - с именами полей как в БД"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавление этапа в contract_stages")
        dialog.geometry("400x350")
        
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Поля с именами как в таблице contract_stages
        ttk.Label(main_frame, text="stage_no*:").grid(row=0, column=0, sticky=tk.W, pady=2)
        stage_no_entry = ttk.Entry(main_frame, width=30)
        stage_no_entry.grid(row=0, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(main_frame, text="planned_exec_date:").grid(row=1, column=0, sticky=tk.W, pady=2)
        planned_date_entry = ttk.Entry(main_frame, width=30)
        planned_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        planned_date_entry.grid(row=1, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(main_frame, text="topic*:").grid(row=2, column=0, sticky=tk.W, pady=2)
        topic_entry = ttk.Entry(main_frame, width=30)
        topic_entry.grid(row=2, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(main_frame, text="stage_sum*:").grid(row=3, column=0, sticky=tk.W, pady=2)
        sum_entry = ttk.Entry(main_frame, width=30)
        sum_entry.grid(row=3, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(main_frame, text="advance_sum:").grid(row=4, column=0, sticky=tk.W, pady=2)
        advance_entry = ttk.Entry(main_frame, width=30)
        advance_entry.insert(0, "0")
        advance_entry.grid(row=4, column=1, pady=2, padx=(5, 0))
        
        def save_stage():
            try:
                stage_no = int(stage_no_entry.get())
                planned_date = planned_date_entry.get()
                topic = topic_entry.get()
                stage_sum = float(sum_entry.get())
                advance = float(advance_entry.get() or 0)
                
                if not topic or stage_sum <= 0:
                    messagebox.showerror("Ошибка", "Заполните обязательные поля (topic и stage_sum)")
                    return
                    
                # Проверяем, что аванс не больше суммы
                if advance > stage_sum:
                    messagebox.showerror("Ошибка", "advance_sum не может быть больше stage_sum")
                    return
                    
                # Сохраняем как числа (не преобразуем в строки)
                stages_tree.insert('', 'end', values=(stage_no, planned_date, topic, stage_sum, advance))
                dialog.destroy()
                
            except ValueError:
                messagebox.showerror("Ошибка", "Проверьте правильность введенных чисел")
        
        ttk.Button(main_frame, text="Добавить этап", command=save_stage).grid(row=5, column=0, columnspan=2, pady=10)

    def delete_stage(self, stages_tree):
        """Удаление выбранного этапа"""
        selected = stages_tree.selection()
        if selected:
            stages_tree.delete(selected)
    
        
    def show_reports(self):
        """Отображение отчетов с улучшенным интерфейсом"""
        reports_window = tk.Toplevel(self.root)
        reports_window.title("Отчеты с фильтрами")
        reports_window.geometry("500x400")
        
        ttk.Label(reports_window, text="Выберите отчет с фильтрами", font=('Arial', 12, 'bold')).pack(pady=10)
        
        # Кнопки отчетов с фильтрами
        ttk.Button(reports_window, text="1. Сведения по договорам (с фильтрами)", 
                command=self.report_contract_details_with_filters, width=35).pack(pady=5)
        ttk.Button(reports_window, text="2. График оплаты по договорам (с фильтрами)", 
                command=self.report_payment_schedule_with_filters, width=35).pack(pady=5)
        ttk.Button(reports_window, text="3. График поступлений (с фильтрами)", 
                command=self.report_payment_actual_with_filters, width=35).pack(pady=5)
        ttk.Button(reports_window, text="4. Дебиторская задолженность (с фильтрами)", 
                command=self.report_debt_with_filters, width=35).pack(pady=5)
    
    def auto_resize_columns(self):
        """Автоподбор ширины столбцов по содержимому"""
        for col in self.tree['columns']:
            # Определяем максимальную длину содержимого в столбце
            max_len = len(col)  # начинаем с длины заголовка
            
            for item in self.tree.get_children():
                value = self.tree.set(item, col)
                if value:
                    max_len = max(max_len, len(str(value)))
            
            # Устанавливаем ширину с небольшим запасом
            new_width = max_len * 8 + 20
            self.tree.column(col, width=min(new_width, 500))  # ограничиваем максимальную ширину

    def show_full_text_dialog(self, event):
        """Показ полного текста ячейки в диалоговом окне по двойному клику"""
        item = self.tree.selection()[0] if self.tree.selection() else None
        column = self.tree.identify_column(event.x)
        
        if item and column:
            col_index = int(column.replace('#', '')) - 1
            if col_index < len(self.tree['columns']):
                col_name = self.tree['columns'][col_index]
                value = self.tree.set(item, col_name)
                
                # Показываем диалог с полным текстом
                dialog = tk.Toplevel(self.root)
                dialog.title(f"Полный текст: {col_name}")
                dialog.geometry("500x300")
                dialog.transient(self.root)
                
                # Текстовое поле с прокруткой
                text_frame = ttk.Frame(dialog, padding="10")
                text_frame.pack(fill=tk.BOTH, expand=True)
                
                text_widget = tk.Text(text_frame, wrap=tk.WORD, width=60, height=15)
                text_widget.insert(1.0, value)
                text_widget.config(state=tk.DISABLED)  # делаем read-only
                
                v_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
                text_widget.configure(yscrollcommand=v_scrollbar.set)
                
                text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                
                ttk.Button(dialog, text="Закрыть", command=dialog.destroy).pack(pady=10)
    
    def load_table_list(self):
        """Загрузка списка таблиц"""
        tables = [
            "organizations", "contracts", "contract_stages", "payments",
            "contract_types", "stages", "vat_rates", "payment_types"
        ]
        self.table_combo['values'] = tables

    
    def clear_all_stages(self, stages_tree):
        
        if stages_tree.get_children():
            if messagebox.askyesno("Подтверждение", "Удалить все этапы?"):
                for child in stages_tree.get_children():
                    stages_tree.delete(child)

    def save_contract_with_stages_db_names(self, dialog, entries, combo_vars, stages_tree, ref_data):
        """Сохранение договора с этапами - с именами полей как в БД"""
        try:
            # Проверяем обязательные поля договора
            contract_code = entries['contract_code'].get()
            contract_date = entries['contract_date'].get()
            subject = entries['subject'].get()
            
            # Получаем значения из комбобоксов
            customer_name = combo_vars['customer_org_id'].get()
            contractor_name = combo_vars['contractor_org_id'].get()
            type_name = combo_vars['type_id'].get()
            stage_name = combo_vars['stage_id'].get()
            vat_percent = combo_vars['vat_id'].get()
            
            if not all([contract_code, contract_date, subject, customer_name, contractor_name, 
                    type_name, stage_name, vat_percent]):
                messagebox.showerror("Ошибка", "Заполните все обязательные поля договора (помечены *)")
                return
            
            # Проверяем, что есть хотя бы один этап
            if not stages_tree.get_children():
                messagebox.showerror("Ошибка", "Добавьте хотя бы один этап договора")
                return
            
            # Получаем ID из справочников
            customer_id = ref_data['customer_org_id'].get(customer_name)
            contractor_id = ref_data['contractor_org_id'].get(contractor_name)
            type_id = ref_data['type_id'].get(type_name)
            stage_id = ref_data['stage_id'].get(stage_name)
            vat_id = ref_data['vat_id'].get(vat_percent)
            
            # Создаем новое соединение для операции
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cursor:
                    # 1. Сохраняем договор в таблицу contracts
                    cursor.execute("""
                        INSERT INTO contracts (contract_code, contract_date, customer_org_id, contractor_org_id, 
                                            type_id, stage_id, vat_id, subject, note, exec_date, total_sum)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0)
                        RETURNING contract_id
                    """, (contract_code, contract_date, customer_id, contractor_id, 
                        type_id, stage_id, vat_id, subject, 
                        entries['note'].get(), entries['exec_date'].get()))
                    
                    contract_id = cursor.fetchone()[0]
                    
                    # 2. Сохраняем этапы в таблицу contract_stages
                    total_sum = 0
                    for child in stages_tree.get_children():
                        stage_no, planned_exec_date, topic, stage_sum, advance_sum = stages_tree.item(child)['values']
                        
                        # Преобразуем строки в числа
                        stage_no = int(stage_no)
                        stage_sum = float(stage_sum)
                        advance_sum = float(advance_sum or 0)
                        
                        cursor.execute("""
                            INSERT INTO contract_stages (contract_id, stage_no, planned_exec_date, 
                                                    stage_id, stage_sum, advance_sum, topic)
                            VALUES (%s, %s, %s, 2, %s, %s, %s)
                        """, (contract_id, stage_no, planned_exec_date, stage_sum, advance_sum, topic))
                        total_sum += stage_sum
                    
                    # Обновляем общую сумму договора
                    cursor.execute("UPDATE contracts SET total_sum = %s WHERE contract_id = %s", 
                                (total_sum, contract_id))
                    conn.commit()
                
                messagebox.showinfo("Успех", "Данные успешно сохранены!\n\n"
                                        f"Договор (contracts): {contract_code}\n"
                                        f"Этапов (contract_stages): {len(stages_tree.get_children())}\n"
                                        f"Общая сумма: {total_sum:,.2f} руб.")
                dialog.destroy()
                self.load_data()
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при сохранении: {e}")
    
    

    def report_contract_details_with_filters(self):
        """Отчет: Сведения по договорам с фильтрами и сортировкой"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Параметры отчета: Сведения по договорам")
        dialog.geometry("500x600")
        
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="ФИЛЬТРЫ", font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Период
        ttk.Label(main_frame, text="Дата договора с:").grid(row=1, column=0, sticky=tk.W, pady=2)
        date_from_entry = ttk.Entry(main_frame, width=20)
        date_from_entry.grid(row=1, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(main_frame, text="Дата договора по:").grid(row=2, column=0, sticky=tk.W, pady=2)
        date_to_entry = ttk.Entry(main_frame, width=20)
        date_to_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        date_to_entry.grid(row=2, column=1, pady=2, padx=(5, 0))
        
        # Заказчики
        ttk.Label(main_frame, text="Заказчик:").grid(row=3, column=0, sticky=tk.W, pady=2)
        customer_var = tk.StringVar()
        customer_combo = ttk.Combobox(main_frame, textvariable=customer_var, width=20)
        customer_combo.grid(row=3, column=1, pady=2, padx=(5, 0))
        
        # Типы договоров
        ttk.Label(main_frame, text="Тип договора:").grid(row=4, column=0, sticky=tk.W, pady=2)
        type_var = tk.StringVar()
        type_combo = ttk.Combobox(main_frame, textvariable=type_var, width=20)
        type_combo.grid(row=4, column=1, pady=2, padx=(5, 0))
        
        # Статусы
        ttk.Label(main_frame, text="Статус договора:").grid(row=5, column=0, sticky=tk.W, pady=2)
        status_var = tk.StringVar()
        status_combo = ttk.Combobox(main_frame, textvariable=status_var, width=20)
        status_combo.grid(row=5, column=1, pady=2, padx=(5, 0))
        
        # СОРТИРОВКА
        ttk.Label(main_frame, text="СОРТИРОВКА", font=('Arial', 10, 'bold')).grid(row=6, column=0, columnspan=2, pady=(20, 10))
        
        ttk.Label(main_frame, text="Сортировать по:").grid(row=7, column=0, sticky=tk.W, pady=2)
        sort_field_var = tk.StringVar(value="none")
        sort_field_combo = ttk.Combobox(main_frame, textvariable=sort_field_var, width=20)
        sort_field_combo['values'] = ['none', 'contract_code', 'contract_date', 'customer_name', 'contractor_name', 'type_name', 'stage_name', 'total_sum', 'total_paid', 'total_sum - total_paid', 'count(stage_no)']
        sort_field_combo.grid(row=7, column=1, pady=2, padx=(5, 0))
        
        # Создаем виджеты направления сортировки, но сразу скрываем
        sort_direction_label = ttk.Label(main_frame, text="Направление:")
        sort_direction_label.grid(row=11, column=0, sticky=tk.W, pady=2)
        sort_direction_label.grid_remove()  # скрываем

        sort_order_var = tk.StringVar(value="DESC")
        asc_rb = ttk.Radiobutton(main_frame, text="По возрастанию", variable=sort_order_var, value="ASC")
        asc_rb.grid(row=11, column=1, sticky=tk.W, pady=2)
        asc_rb.grid_remove()  # скрываем

        desc_rb = ttk.Radiobutton(main_frame, text="По убыванию", variable=sort_order_var, value="DESC")
        desc_rb.grid(row=12, column=1, sticky=tk.W, pady=2)
        desc_rb.grid_remove()  # скрываем

        # Функция для показа/скрытия виджетов направления
        def toggle_sort_direction(event):
            if sort_field_var.get() == "none":
                sort_direction_label.grid_remove()
                asc_rb.grid_remove()
                desc_rb.grid_remove()
            else:
                sort_direction_label.grid()
                asc_rb.grid()
                desc_rb.grid()

        
        # Привязываем функцию к изменению выбора в комбобоксе
        sort_field_combo.bind('<<ComboboxSelected>>', toggle_sort_direction)


        # ttk.Label(main_frame, text="Направление:").grid(row=8, column=0, sticky=tk.W, pady=2)
        # sort_order_var = tk.StringVar(value="DESC")
        # ttk.Radiobutton(main_frame, text="По возрастанию", variable=sort_order_var, value="ASC").grid(row=8, column=1, sticky=tk.W, pady=2)
        # ttk.Radiobutton(main_frame, text="По убыванию", variable=sort_order_var, value="DESC").grid(row=9, column=1, sticky=tk.W, pady=2)
        
        # Заполняем комбобоксы
        try:
            with self.connection.cursor() as cursor:
                # Заказчики
                cursor.execute("SELECT name FROM organizations ORDER BY name")
                customers = [row[0] for row in cursor.fetchall()]
                customer_combo['values'] = customers
                
                # Типы договоров
                cursor.execute("SELECT type_name FROM contract_types ORDER BY type_name")
                types = [row[0] for row in cursor.fetchall()]
                type_combo['values'] = types
                
                # Статусы
                cursor.execute("SELECT stage_name FROM stages ORDER BY stage_name")
                statuses = [row[0] for row in cursor.fetchall()]
                status_combo['values'] = statuses
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки справочников: {e}")
        
        def generate_report():
            # Собираем условия WHERE
            where_conditions = []
            params = []
            
            date_from = date_from_entry.get()
            date_to = date_to_entry.get()
            customer = customer_var.get()
            contract_type = type_var.get()
            status = status_var.get()
            
            if date_from:
                where_conditions.append("c.contract_date >= %s")
                params.append(date_from)
            if date_to:
                where_conditions.append("c.contract_date <= %s")
                params.append(date_to)
            if customer:
                where_conditions.append("cust.name = %s")
                params.append(customer)
            if contract_type:
                where_conditions.append("ct.type_name = %s")
                params.append(contract_type)
            if status:
                where_conditions.append("s.stage_name = %s")
                params.append(status)
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            # Сортировка
            sort_field = sort_field_var.get()
            sort_order = sort_order_var.get()
            
            # Маппинг полей сортировки
            sort_mapping = {
                'contract_date': 'c.contract_date',
                'total_sum': 'c.total_sum',
                'total_paid': 'c.total_paid',
                'total_sum - total_paid': '(c.total_sum - c.total_paid)',
                'customer_name': 'cust.name',
                'contractor_name': 'cont.name',
                'contractor_code': 'c.contract_code',
                'type_name': 'ct.type_name',
                'stage_name': 'stage_name',
                'count(stage_no)': 'COUNT(cs.stage_no)'


            }
            
            #order_clause = f"ORDER BY {sort_field} {sort_order}"
            order_clause = f"ORDER BY {sort_mapping.get(sort_field, 'c.contract_date')} {sort_order}"
            print(order_clause)
            query = f"""
            SELECT 
                c.contract_code as "Номер договора",
                c.contract_date as "Дата договора",
                cust.name as "Заказчик",
                cont.name as "Исполнитель",
                ct.type_name as "Тип договора",
                s.stage_name as "Статус",
                c.total_sum as "Общая сумма",
                c.total_paid as "Оплачено",
                (c.total_sum - c.total_paid) as "Задолженность",
                COUNT(cs.stage_no) as "Кол-во этапов"
                
            FROM contracts c
            JOIN organizations cust ON c.customer_org_id = cust.org_id
            JOIN organizations cont ON c.contractor_org_id = cont.org_id
            JOIN contract_types ct ON c.type_id = ct.type_id
            JOIN stages s ON c.stage_id = s.stage_id
            LEFT JOIN contract_stages cs ON c.contract_id = cs.contract_id
            {where_clause}
            GROUP BY c.contract_id, cust.name, cont.name, ct.type_name, s.stage_name
            {order_clause}
            """
            
            dialog.destroy()
            self.display_report_with_params(query, "Сведения по договорам (с фильтрами)", params)
        
        self.tree.bind('<Double-1>', self.show_full_text_dialog)
        ttk.Button(main_frame, text="Сформировать отчет", command=generate_report).grid(row=13, column=0, columnspan=2, pady=20)

    def report_payment_schedule_with_filters(self):
        """Отчет: График оплаты по договорам с фильтрами"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Параметры отчета: График оплаты")
        dialog.geometry("500x500")
        
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="ФИЛЬТРЫ", font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Период
        ttk.Label(main_frame, text="Плановая дата с:").grid(row=1, column=0, sticky=tk.W, pady=2)
        date_from_entry = ttk.Entry(main_frame, width=20)
        date_from_entry.grid(row=1, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(main_frame, text="Плановая дата по:").grid(row=2, column=0, sticky=tk.W, pady=2)
        date_to_entry = ttk.Entry(main_frame, width=20)
        date_to_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        date_to_entry.grid(row=2, column=1, pady=2, padx=(5, 0))
        
        # Заказчики
        ttk.Label(main_frame, text="Заказчик:").grid(row=3, column=0, sticky=tk.W, pady=2)
        customer_var = tk.StringVar()
        customer_combo = ttk.Combobox(main_frame, textvariable=customer_var, width=20)
        customer_combo.grid(row=3, column=1, pady=2, padx=(5, 0))
        
        # СОРТИРОВКА
        ttk.Label(main_frame, text="СОРТИРОВКА", font=('Arial', 10, 'bold')).grid(row=4, column=0, columnspan=2, pady=(20, 10))
        
        ttk.Label(main_frame, text="Сортировать по:").grid(row=5, column=0, sticky=tk.W, pady=2)
        sort_field_var = tk.StringVar(value="none")
        sort_field_combo = ttk.Combobox(main_frame, textvariable=sort_field_var, width=20)
        sort_field_combo['values'] = ['none', 'contract_code', 'name', 'stage_no', 'planned_exec_date', 'stage_sum', 'advance_sum', 'stage_sum - advance_sum']
        sort_field_combo.grid(row=5, column=1, pady=2, padx=(5, 0))
        
        # ttk.Label(main_frame, text="Направление:").grid(row=6, column=0, sticky=tk.W, pady=2)
        # sort_order_var = tk.StringVar(value="ASC")
        # ttk.Radiobutton(main_frame, text="По возрастанию", variable=sort_order_var, value="ASC").grid(row=6, column=1, sticky=tk.W, pady=2)
        # ttk.Radiobutton(main_frame, text="По убыванию", variable=sort_order_var, value="DESC").grid(row=7, column=1, sticky=tk.W, pady=2)
        
        # Создаем виджеты направления сортировки, но сразу скрываем
        sort_direction_label = ttk.Label(main_frame, text="Направление:")
        sort_direction_label.grid(row=11, column=0, sticky=tk.W, pady=2)
        sort_direction_label.grid_remove()  # скрываем

        sort_order_var = tk.StringVar(value="DESC")
        asc_rb = ttk.Radiobutton(main_frame, text="По возрастанию", variable=sort_order_var, value="ASC")
        asc_rb.grid(row=11, column=1, sticky=tk.W, pady=2)
        asc_rb.grid_remove()  # скрываем

        desc_rb = ttk.Radiobutton(main_frame, text="По убыванию", variable=sort_order_var, value="DESC")
        desc_rb.grid(row=12, column=1, sticky=tk.W, pady=2)
        desc_rb.grid_remove()  # скрываем

        # Функция для показа/скрытия виджетов направления
        def toggle_sort_direction(event):
            if sort_field_var.get() == "none":
                sort_direction_label.grid_remove()
                asc_rb.grid_remove()
                desc_rb.grid_remove()
            else:
                sort_direction_label.grid()
                asc_rb.grid()
                desc_rb.grid()

        
        # Привязываем функцию к изменению выбора в комбобоксе
        sort_field_combo.bind('<<ComboboxSelected>>', toggle_sort_direction)


        # Заполняем комбобоксы
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT name FROM organizations ORDER BY name")
                customers = [row[0] for row in cursor.fetchall()]
                customer_combo['values'] = customers
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки справочников: {e}")
        
        def generate_report():
            # Собираем условия WHERE
            where_conditions = []
            params = []
            
            date_from = date_from_entry.get()
            date_to = date_to_entry.get()
            customer = customer_var.get()
            
            if date_from:
                where_conditions.append("cs.planned_exec_date >= %s")
                params.append(date_from)
            if date_to:
                where_conditions.append("cs.planned_exec_date <= %s")
                params.append(date_to)
            if customer:
                where_conditions.append("cust.name = %s")
                params.append(customer)
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            # Сортировка
            sort_field = sort_field_var.get()
            sort_order = sort_order_var.get()
            if sort_field == 'none': order_clause=''
            else: order_clause = f"ORDER BY {sort_field} {sort_order}"
            
            query = f"""
            SELECT 
                c.contract_code as "Номер договора",
                cust.name as "Заказчик",
                cs.stage_no as "№ этапа",
                cs.topic as "Тема этапа",
                cs.planned_exec_date as "Плановая дата",
                cs.stage_sum as "Сумма этапа",
                cs.advance_sum as "Аванс",
                (cs.stage_sum - cs.advance_sum) as "Остаток к оплате"
            FROM contracts c
            JOIN organizations cust ON c.customer_org_id = cust.org_id
            JOIN contract_stages cs ON c.contract_id = cs.contract_id
            {where_clause}
            {order_clause}
            """
            
            dialog.destroy()
            self.display_report_with_params(query, "График оплаты по договорам (с фильтрами)", params)
        
        ttk.Button(main_frame, text="Сформировать отчет", command=generate_report).grid(row=13, column=0, columnspan=2, pady=20)

    def report_payment_actual_with_filters(self):
        """Отчет: Фактические поступления с фильтрами"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Параметры отчета: Фактические поступления")
        dialog.geometry("500x600")
        
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="ФИЛЬТРЫ", font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Период
        ttk.Label(main_frame, text="Дата оплаты с:").grid(row=1, column=0, sticky=tk.W, pady=2)
        date_from_entry = ttk.Entry(main_frame, width=20)
        date_from_entry.grid(row=1, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(main_frame, text="Дата оплаты по:").grid(row=2, column=0, sticky=tk.W, pady=2)
        date_to_entry = ttk.Entry(main_frame, width=20)
        date_to_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        date_to_entry.grid(row=2, column=1, pady=2, padx=(5, 0))
        
        # Заказчики
        ttk.Label(main_frame, text="Заказчик:").grid(row=3, column=0, sticky=tk.W, pady=2)
        customer_var = tk.StringVar()
        customer_combo = ttk.Combobox(main_frame, textvariable=customer_var, width=20)
        customer_combo.grid(row=3, column=1, pady=2, padx=(5, 0))
        
        # Виды оплат
        ttk.Label(main_frame, text="Вид оплаты:").grid(row=4, column=0, sticky=tk.W, pady=2)
        payment_type_var = tk.StringVar()
        payment_type_combo = ttk.Combobox(main_frame, textvariable=payment_type_var, width=20)
        payment_type_combo.grid(row=4, column=1, pady=2, padx=(5, 0))
        
        # Группировка
        ttk.Label(main_frame, text="Группировка:", font=('Arial', 10, 'bold')).grid(row=5, column=0, columnspan=2, pady=(20, 10))
        
        group_by_var = tk.StringVar(value="none")
        def update_sort_fields(*args):
            group_var = group_by_var.get()
            if group_var == "none":
                sort_field_combo['values'] = ['none', 'contract_code','name','payment_date', 'payment_sum', 'payment_type_name', 'payment_doc_no']
                sort_field_var.set = 'none'
            elif group_var == 'month':
                sort_field_combo['values'] = ['payment_date', 'payment_id', 'payment_sum']

        ttk.Radiobutton(main_frame, text="Без группировки", variable=group_by_var, value="none", command=update_sort_fields).grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=2)
        ttk.Radiobutton(main_frame, text="По месяцам", variable=group_by_var, value="month", command=update_sort_fields).grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=2)
        ttk.Radiobutton(main_frame, text="По заказчикам", variable=group_by_var, value="customer").grid(row=8, column=0, columnspan=2, sticky=tk.W, pady=2)
        
       # СОРТИРОВКА
        ttk.Label(main_frame, text="СОРТИРОВКА", font=('Arial', 10, 'bold')).grid(row=9, column=0, columnspan=2, pady=(20, 10))

        ttk.Label(main_frame, text="Сортировать по:").grid(row=10, column=0, sticky=tk.W, pady=2)
        sort_field_var = tk.StringVar(value="none")
        sort_field_combo = ttk.Combobox(main_frame, textvariable=sort_field_var, width=20)
        sort_field_combo['values'] = ['none', 'contract_code','name','payment_date', 'payment_sum', 'payment_type_name', 'payment_doc_no']
        #sort_field_combo['values'] = ['none', 'payment_date', 'payment_sum', 'contract_code']
        sort_field_combo.grid(row=10, column=1, pady=2, padx=(5, 0))

        # Создаем виджеты направления сортировки, но сразу скрываем
        sort_direction_label = ttk.Label(main_frame, text="Направление:")
        sort_direction_label.grid(row=11, column=0, sticky=tk.W, pady=2)
        sort_direction_label.grid_remove()  # скрываем

        sort_order_var = tk.StringVar(value="DESC")
        asc_rb = ttk.Radiobutton(main_frame, text="По возрастанию", variable=sort_order_var, value="ASC")
        asc_rb.grid(row=11, column=1, sticky=tk.W, pady=2)
        asc_rb.grid_remove()  # скрываем

        desc_rb = ttk.Radiobutton(main_frame, text="По убыванию", variable=sort_order_var, value="DESC")
        desc_rb.grid(row=12, column=1, sticky=tk.W, pady=2)
        desc_rb.grid_remove()  # скрываем

        # Функция для показа/скрытия виджетов направления
        def toggle_sort_direction(event):
            if sort_field_var.get() == "none":
                sort_direction_label.grid_remove()
                asc_rb.grid_remove()
                desc_rb.grid_remove()
            else:
                sort_direction_label.grid()
                asc_rb.grid()
                desc_rb.grid()

        
        # Привязываем функцию к изменению выбора в комбобоксе
        sort_field_combo.bind('<<ComboboxSelected>>', toggle_sort_direction)

        # Заполняем комбобоксы
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT name FROM organizations ORDER BY name")
                customers = [row[0] for row in cursor.fetchall()]
                customer_combo['values'] = customers
                
                cursor.execute("SELECT payment_type_name FROM payment_types ORDER BY payment_type_name")
                payment_types = [row[0] for row in cursor.fetchall()]
                payment_type_combo['values'] = payment_types
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки справочников: {e}")
        
        def generate_report():
            # Собираем условия WHERE
            where_conditions = []
            params = []
            
            date_from = date_from_entry.get()
            date_to = date_to_entry.get()
            customer = customer_var.get()
            payment_type = payment_type_var.get()
            
            if date_from:
                where_conditions.append("p.payment_date >= %s")
                params.append(date_from)
            if date_to:
                where_conditions.append("p.payment_date <= %s")
                params.append(date_to)
            if customer:
                where_conditions.append("cust.name = %s")
                params.append(customer)
            if payment_type:
                where_conditions.append("pt.payment_type_name = %s")
                params.append(payment_type)
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            # Группировка
            group_by = group_by_var.get()
            group_clause = ""
            select_fields = """
                c.contract_code as "Номер договора",
                cust.name as "Заказчик",
                p.payment_date as "Дата оплаты",
                p.payment_sum as "Сумма оплаты",
                pt.payment_type_name as "Вид оплаты",
                p.payment_doc_no as "№ документа"
            """
            
            if group_by == "month":
                select_fields = """
                    TO_CHAR(p.payment_date, 'YYYY-MM') as "Месяц",
                    COUNT(p.payment_id) as "Кол-во платежей",
                    SUM(p.payment_sum) as "Сумма за месяц"
                """
                group_clause = "GROUP BY TO_CHAR(p.payment_date, 'YYYY-MM')"
                
            elif group_by == "customer":
                select_fields = """
                    cust.name as "Заказчик",
                    COUNT(p.payment_id) as "Кол-во платежей",
                    SUM(p.payment_sum) as "Общая сумма",
                    AVG(p.payment_sum) as "Средний платеж"
                """
                group_clause = "GROUP BY cust.name"
            
            # Сортировка
            sort_field = sort_field_var.get()
            sort_order = sort_order_var.get()
            if sort_field == "none":
                order_clause = ""
            elif group_by == 'month':
                if sort_field == 'payment_date': order_clause = f"ORDER BY MIN({sort_field}) {sort_order}"
                if sort_field == 'payment_id': order_clause = f"ORDER BY COUNT({sort_field}) {sort_order}"
                if sort_field == 'payment_sum': order_clause = f"ORDER BY SUM({sort_field}) {sort_order}"
                #order_clause = "ORDER BY MIN(p.payment_date) ASC"
            else: order_clause = f"ORDER BY {sort_field} {sort_order}"
            
            #if len(group_clause) > 2 and sort_field != 'none' and group_clause.split()[2] != sort_field:
            #    group_clause += ', ' + sort_field
            query = f"""
            SELECT 
                {select_fields}
            FROM payments p
            JOIN contracts c ON p.contract_id = c.contract_id
            JOIN organizations cust ON c.customer_org_id = cust.org_id
            JOIN payment_types pt ON p.payment_type_id = pt.payment_type_id
            {where_clause}
            {group_clause}
            {order_clause}
            """
            print(query)
            dialog.destroy()
            self.display_report_with_params(query, "Фактические поступления (с фильтрами)", params)
        
        ttk.Button(main_frame, text="Сформировать отчет", command=generate_report).grid(row=13, column=0, columnspan=2, pady=20)

    def report_debt_with_filters(self):
        """Отчет: Дебиторская задолженность с фильтрами"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Параметры отчета: Дебиторская задолженность")
        dialog.geometry("500x400")
        
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="ФИЛЬТРЫ", font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Заказчики
        ttk.Label(main_frame, text="Заказчик:").grid(row=1, column=0, sticky=tk.W, pady=2)
        customer_var = tk.StringVar()
        customer_combo = ttk.Combobox(main_frame, textvariable=customer_var, width=20)
        customer_combo.grid(row=1, column=1, pady=2, padx=(5, 0))
        
        # Минимальная задолженность
        ttk.Label(main_frame, text="Мин. сумма задолженности:").grid(row=2, column=0, sticky=tk.W, pady=2)
        min_debt_var = tk.StringVar()
        min_debt_entry = ttk.Entry(main_frame, textvariable=min_debt_var, width=20)
        min_debt_entry.grid(row=2, column=1, pady=2, padx=(5, 0))
        
        # СОРТИРОВКА
        ttk.Label(main_frame, text="СОРТИРОВКА", font=('Arial', 10, 'bold')).grid(row=3, column=0, columnspan=2, pady=(20, 10))
        
        ttk.Label(main_frame, text="Сортировать по:").grid(row=5, column=0, sticky=tk.W, pady=2)
        sort_field_var = tk.StringVar(value="none")
        sort_field_combo = ttk.Combobox(main_frame, textvariable=sort_field_var, width=20)
        sort_field_combo['values'] = ['none', 'contract_code', 'contract_date', 'customer_name', 'contractor_name', 'total_sum', 'total_paid', 'sum - paid']
        sort_field_combo.grid(row=5, column=1, pady=2, padx=(5, 0))
        
        # ttk.Label(main_frame, text="Направление:").grid(row=6, column=0, sticky=tk.W, pady=2)
        # sort_order_var = tk.StringVar(value="ASC")
        # ttk.Radiobutton(main_frame, text="По возрастанию", variable=sort_order_var, value="ASC").grid(row=6, column=1, sticky=tk.W, pady=2)
        # ttk.Radiobutton(main_frame, text="По убыванию", variable=sort_order_var, value="DESC").grid(row=7, column=1, sticky=tk.W, pady=2)
        
        # Создаем виджеты направления сортировки, но сразу скрываем
        sort_direction_label = ttk.Label(main_frame, text="Направление:")
        sort_direction_label.grid(row=11, column=0, sticky=tk.W, pady=2)
        sort_direction_label.grid_remove()  # скрываем

        sort_order_var = tk.StringVar(value="DESC")
        asc_rb = ttk.Radiobutton(main_frame, text="По возрастанию", variable=sort_order_var, value="ASC")
        asc_rb.grid(row=11, column=1, sticky=tk.W, pady=2)
        asc_rb.grid_remove()  # скрываем

        desc_rb = ttk.Radiobutton(main_frame, text="По убыванию", variable=sort_order_var, value="DESC")
        desc_rb.grid(row=12, column=1, sticky=tk.W, pady=2)
        desc_rb.grid_remove()  # скрываем

        # Функция для показа/скрытия виджетов направления
        def toggle_sort_direction(event):
            if sort_field_var.get() == "none":
                sort_direction_label.grid_remove()
                asc_rb.grid_remove()
                desc_rb.grid_remove()
            else:
                sort_direction_label.grid()
                asc_rb.grid()
                desc_rb.grid()

        
        # Привязываем функцию к изменению выбора в комбобоксе
        sort_field_combo.bind('<<ComboboxSelected>>', toggle_sort_direction)

        # ttk.Label(main_frame, text="Сортировать по:").grid(row=4, column=0, sticky=tk.W, pady=2)
        # sort_field_var = tk.StringVar(value="contract_date")
        # sort_field_combo = ttk.Combobox(main_frame, textvariable=sort_field_var, width=20)
        # sort_field_combo['values'] = ['contract_date', 'total_sum', 'customer_name']
        # sort_field_combo.grid(row=4, column=1, pady=2, padx=(5, 0))
        
        # ttk.Label(main_frame, text="Направление:").grid(row=5, column=0, sticky=tk.W, pady=2)
        # sort_order_var = tk.StringVar(value="DESC")
        # ttk.Radiobutton(main_frame, text="По возрастанию", variable=sort_order_var, value="ASC").grid(row=5, column=1, sticky=tk.W, pady=2)
        # ttk.Radiobutton(main_frame, text="По убыванию", variable=sort_order_var, value="DESC").grid(row=6, column=1, sticky=tk.W, pady=2)
        
        # Заполняем комбобоксы
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT name FROM organizations ORDER BY name")
                customers = [row[0] for row in cursor.fetchall()]
                customer_combo['values'] = customers
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки справочников: {e}")
        
        def generate_report():
            # Собираем условия WHERE
            where_conditions = ["(c.total_sum - c.total_paid) > 0"]
            params = []
            
            customer = customer_var.get()
            min_debt = min_debt_var.get()
            
            if customer:
                where_conditions.append("cust.name = %s")
                params.append(customer)
            if min_debt:
                where_conditions.append("(c.total_sum - c.total_paid) >= %s")
                params.append(float(min_debt))
            
            where_clause = "WHERE " + " AND ".join(where_conditions)
            
            # Сортировка
            sort_field = sort_field_var.get()
            sort_order = sort_order_var.get()
            
            # Маппинг полей сортировки
            sort_mapping = {
                'contract_code': 'c.contract_code',
                'total_sum': 'c.total_sum',
                'total_paid': 'c.total_paid',
                'sum - paid': '(c.total_sum - c.total_paid)',
                'customer_name': 'cust.name',
                'contractor_name': 'cont.name'
            }
            
            #order_clause = f"ORDER BY {sort_field} {sort_order}"
            order_clause = f"ORDER BY {sort_mapping.get(sort_field, 'c.contract_date')} {sort_order}"


            #order_clause = f"ORDER BY {sort_field} {sort_order}"
            
            query = f"""
            SELECT
                c.contract_code as "Номер договора",
                c.contract_date as "Дата договора",
                cust.name as "Заказчик",
                cont.name as "Исполнитель",
                c.total_sum as "Общая сумма",
                c.total_paid as "Оплачено",
                (c.total_sum - c.total_paid) as "Задолженность"
            FROM contracts c
            JOIN organizations cust ON c.customer_org_id = cust.org_id
            JOIN organizations cont ON c.contractor_org_id = cont.org_id
            {where_clause}
            {order_clause}
            """
            
            dialog.destroy()
            self.display_report_with_params(query, "Дебиторская задолженность (с фильтрами)", params)
        
        ttk.Button(main_frame, text="Сформировать отчет", command=generate_report).grid(row=13, column=0, columnspan=2, pady=20)

    def display_report_with_params(self, query, title, params=None):
        """Отображение отчета с параметрами"""
        try:
            with self.connection.cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                    
                report_window = tk.Toplevel(self.root)
                report_window.title(title)
                report_window.geometry("1200x600")
                
                # Контейнер для таблицы
                report_container = ttk.Frame(report_window)
                report_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                
                # Создание таблицы для отчета
                tree = ttk.Treeview(report_container, show='headings')
                
                # Вертикальный скроллбар
                v_scrollbar = ttk.Scrollbar(report_container, orient="vertical", command=tree.yview)
                tree.configure(yscrollcommand=v_scrollbar.set)
                
                # Горизонтальный скроллбар
                h_scrollbar = ttk.Scrollbar(report_container, orient="horizontal", command=tree.xview)
                tree.configure(xscrollcommand=h_scrollbar.set)
                
                # Размещаем элементы
                tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
                
                # Настройка колонок
                columns = [desc[0] for desc in cursor.description]
                tree['columns'] = columns
                
                for col in columns:
                    tree.heading(col, text=col)
                    width = max(100, len(col) * 8)
                    tree.column(col, width=width, minwidth=60, stretch=True)
                
                # Заполнение данными
                for row in cursor.fetchall():
                    tree.insert('', 'end', values=row)
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при формировании отчета: {e}")


def main():
    root = tk.Tk()
    app = ContractsApp(root)
    root.mainloop()


if __name__ == "__main__":
    
    main()