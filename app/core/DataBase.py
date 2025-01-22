# from datetime import datetime, timezone
import os
import sqlite3


class DataBase:
    def __init__(self, dict_result=None, db_name: str = 'ml_data.db'):
        """
        Инициализация базы данных.
        :param db_name: Имя файла базы данных.
        :param dict_result: Пример данных для создания структуры таблицы.
        """
        # Определение пути к базе данных в директории "database"
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', db_name)
        # Создание папки, если её нет
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.dict_result = dict_result

        # Подключение к базе данных
        self.conn = None  # Устанавливаем соединение в None для последующего открытия
        self.connect()  # Автоматически открываем соединение

        # Создание таблицы, если есть пример данных
        self.table_name = 'trading_data_ml'
        if self.dict_result:
            self.create_table_from_dict(self.dict_result)

    def connect(self):
        """Открывает соединение с базой данных, если оно закрыто."""
        if not self.conn:
            self.conn = sqlite3.connect(self.db_path)

    def close_connection(self):
        """Закрывает соединение с базой данных."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def is_connected(self):
        """Проверяет, открыто ли соединение."""
        return self.conn is not None

    def create_table_from_dict(self, sample_data):
        """
        Создает таблицу на основе структуры словаря.
        :param sample_data: Пример данных для определения структуры таблицы.
        """
        self.connect()  # Убедимся, что соединение открыто
        cursor = self.conn.cursor()

        # Определяем типы данных
        types_mapping = {
            bool: "BOOLEAN",
            int: "INTEGER",
            float: "REAL",
            str: "TEXT",
        }

        columns = []
        for key, value in sample_data.items():
            value_type = type(value)
            sql_type = types_mapping.get(value_type, "TEXT")  # По умолчанию TEXT
            columns.append(f"{key} {sql_type}")

        # Создание таблицы
        columns_sql = ", ".join(columns)
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {self.table_name} (id INTEGER PRIMARY KEY AUTOINCREMENT, {columns_sql})")
        self.conn.commit()

    def insert_data_from_dict(self, data):
        """
        Добавляет данные в таблицу.
        :param data: Словарь с данными для вставки.
        """
        self.connect()  # Убедимся, что соединение открыто
        cursor = self.conn.cursor()
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        sql = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        cursor.execute(sql, list(data.values()))
        self.conn.commit()

    def fetch_all_data(self):
        """
        Извлекает все данные из таблицы.
        :return: Все данные в виде списка словарей.
        """
        self.connect()  # Убедимся, что соединение открыто
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM {self.table_name}")
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]


# class DataBaseTarget:
#     def __init__(self, db_name: str = 'trading_labels.db'):
#         """
#         Инициализация базы данных.
#         :param db_name: Имя файла базы данных.
#         """
#         # Определение пути к базе данных в директории "database"
#         self.db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', db_name)
#         self.name_table = 'balanced_trades'
#
#     def get_one_new_trade(self):
#         """
#         Получить одну запись из таблицы trades со статусом 'new'.
#         Обновляет статус выбранной записи на 'done'.
#         :return: Словарь с данными записи или None, если записей нет.
#         """
#         conn = sqlite3.connect(self.db_path)
#         conn.row_factory = sqlite3.Row  # Позволяет возвращать данные в виде словаря
#         cursor = conn.cursor()
#
#         try:
#             # Получаем одну запись со статусом 'new'
#             cursor.execute(f"SELECT `id`, `pair`, `ts_start`, `result` FROM {self.name_table} WHERE status = 'new' LIMIT 1")
#             row = cursor.fetchone()
#
#             if not row:  # Если записи нет, возвращаем None
#                 return None
#             self.set_status(status='done', _id=row['id'])
#
#             return dict(row)  # Преобразуем запись в словарь и возвращаем
#         except sqlite3.Error as e:
#             print(f"Ошибка при выполнении SQL-запроса: {e}")
#             return None
#         finally:
#             conn.close()
#
#     def set_status(self, status, _id):
#         conn = sqlite3.connect(self.db_path)
#         cursor = conn.cursor()
#
#         try:
#             cursor.execute(f"UPDATE {self.name_table} SET status = ? WHERE id = ?", (status, _id))
#             conn.commit()
#         except sqlite3.Error as e:
#             print(f"Ошибка при выполнении SQL-запроса: {e}")
#             return None
#         finally:
#             conn.close()


class DataBaseTarget:
    def __init__(self, db_name: str = 'trading_labels.db'):
        """
        Инициализация базы данных.
        :param db_name: Имя файла базы данных.
        """
        # Определение пути к базе данных в директории "database"
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', db_name)
        self.name_table = 'balanced_trades'
        self.conn = None
        self.connect()

    def connect(self):
        """Подключается к базе данных, если соединение отсутствует."""
        try:
            if self.conn is None or not self.conn:
                self.conn = sqlite3.connect(self.db_path)
                self.conn.row_factory = sqlite3.Row  # Возвращает строки как словари
                print("Соединение с базой данных установлено.")
        except sqlite3.Error as e:
            print(f"Ошибка при подключении к базе данных: {e}")
            self.conn = None

    def close_connection(self):
        """Закрывает соединение с базой данных."""
        if self.conn:
            try:
                self.conn.close()
                print("Соединение с базой данных закрыто.")
            except sqlite3.Error as e:
                print(f"Ошибка при закрытии соединения: {e}")
            finally:
                self.conn = None

    def get_one_new_trade(self):
        """
        Получить одну запись из таблицы trades со статусом 'new'.
        Обновляет статус выбранной записи на 'done'.
        :return: Словарь с данными записи или None, если записей нет.
        """
        self.connect()
        cursor = self.conn.cursor()

        try:
            # Получаем одну запись со статусом 'new'
            cursor.execute(
                f"SELECT `id`, `pair`, `ts_start`, `result` FROM {self.name_table} WHERE status = 'new' LIMIT 1"
            )
            row = cursor.fetchone()

            if not row:  # Если записи нет, возвращаем None
                return None

            # Обновляем статус на 'done'
            self.set_status(status='done', _id=row['id'])

            return dict(row)  # Преобразуем запись в словарь и возвращаем
        except sqlite3.Error as e:
            print(f"Ошибка при выполнении SQL-запроса: {e}")
            return None

    def set_status(self, status, _id):
        """
        Обновляет статус записи в таблице.
        :param status: Новый статус.
        :param _id: Идентификатор записи.
        """
        self.connect()
        cursor = self.conn.cursor()

        try:
            cursor.execute(
                f"UPDATE {self.name_table} SET status = ? WHERE id = ?",
                (status, _id),
            )
            self.conn.commit()
            # print(f"Статус записи с id={_id} обновлен на {status}.")
        except sqlite3.Error as e:
            print(f"Ошибка при выполнении SQL-запроса: {e}")
