import sqlite3
from datetime import datetime
from tools import manuwriter

class DatabaseInterfaceBase:
    _instance = None
    TABLE_USERS = "users"
    USER_ID = 'id'
    USER_LAST_INTERACTION = 'last_interaction'
    USER_ALL_FIELDS = f'({USER_ID}, {USER_LAST_INTERACTION})'
    DATE_FORMAT = '%Y-%m-%d'
    @staticmethod
    def Get():
        if not DatabaseInterfaceBase._instance:
            DatabaseInterfaceBase._instance = DatabaseInterfaceBase()
        return DatabaseInterfaceBase._instance

    def setup(self):
        connection = None
        try:
            connection = sqlite3.connect(self._name, detect_types=sqlite3.PARSE_DECLTYPES)
            cursor = connection.cursor()

            # check if the table users was created
            if not cursor.execute(f"SELECT name from sqlite_master WHERE name='{DatabaseInterfaceBase.TABLE_USERS}'").fetchone():
                query = f"CREATE TABLE {DatabaseInterfaceBase.TABLE_USERS} ({DatabaseInterfaceBase.USER_ID} INTEGER PRIMARY KEY," +\
                    f" {DatabaseInterfaceBase.USER_LAST_INTERACTION} DATE)"
                # create table user
                cursor.execute(query)
                manuwriter.log(f"{DatabaseInterfaceBase.TABLE_USERS} table created successfuly.", category_name='info')

            # else: # TEMP-*****
            #     cursor.execute(f'ALTER TABLE {DatabaseInterfaceBase.TABLE_USERS} ADD {DatabaseInterfaceBase.USER_LAST_INTERACTION} DATE')
            #     connection.commit()
            manuwriter.log("Database setup completed.", category_name='info')
            cursor.close()
            connection.close()
        except Exception as ex:
            if connection:
                connection.close()
            raise ex  # create custom exception for this


    def add(self, user, log_category_prefix=''):
        connection = None
        if not user:
            raise Exception("You must provide an user to save")
        try:
            query = f"INSERT INTO {DatabaseInterfaceBase.TABLE_USERS} {DatabaseInterfaceBase.USER_ALL_FIELDS} VALUES (?, ?)"
            connection = sqlite3.connect(self._name)
            cursor = connection.cursor()
            cursor.execute(query, (user.chat_id, user.last_interaction.strftime(DatabaseInterfaceBase.DATE_FORMAT)))
            manuwriter.log(f"New user: {user} saved into database successfully.", category_name=f'{log_category_prefix}info')
            cursor.close()
            connection.commit()
            connection.close()
        except Exception as ex:
            manuwriter.log(f"Cannot save this user:{user}", ex, category_name=f'{log_category_prefix}database')
            if connection:
                connection.close()
            raise ex  # custom ex needed here too

    def get(self, chat_id):
        connection = sqlite3.connect(self._name)
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM {DatabaseInterfaceBase.TABLE_USERS} WHERE {DatabaseInterfaceBase.USER_ID}=? LIMIT 1", (chat_id, ))
        row = cursor.fetchone()
        cursor.close()
        connection.close()
        return row

    def get_all(self, column: str=USER_ID) -> list:
        connection = sqlite3.connect(self._name)
        cursor = connection.cursor()
        cursor.execute(f"SELECT ({column}) FROM {DatabaseInterfaceBase.TABLE_USERS}")
        rows = cursor.fetchall()
        cursor.close()
        connection.close()
        if column == DatabaseInterfaceBase.USER_LAST_INTERACTION:
            return [datetime.strptime(row[0], DatabaseInterfaceBase.DATE_FORMAT) if row[0] else None for row in rows]
        return [row[0] for row in rows] # just return a list of ids

    def update(self, user, log_category_prefix=''):
        connection = sqlite3.connect(self._name)
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM {DatabaseInterfaceBase.TABLE_USERS} WHERE {DatabaseInterfaceBase.USER_ID}=? LIMIT 1", (user.chat_id, ))
        if cursor.fetchone(): # if user with his chat id has been saved before in the database
            FIELDS_TO_SET = f'{DatabaseInterfaceBase.USER_LAST_INTERACTION}=?'
            cursor.execute(f'UPDATE {DatabaseInterfaceBase.TABLE_USERS} SET {FIELDS_TO_SET} WHERE {DatabaseInterfaceBase.USER_ID}=?', \
                (user.last_interaction.strftime(DatabaseInterfaceBase.DATE_FORMAT) , user.chat_id))
        else:
            cursor.execute(f"INSERT INTO {DatabaseInterfaceBase.TABLE_USERS} {DatabaseInterfaceBase.USER_ALL_FIELDS} VALUES (?, ?)", \
                (user.chat_id, user.last_interaction.strftime(DatabaseInterfaceBase.DATE_FORMAT)))
            manuwriter.log("New user started using this bot with chat_id=: " + user.__str__(), category_name=f'{log_category_prefix}info')
        connection.commit()
        cursor.close()
        connection.close()

    def __init__(self, name="data.db"):
        print("CAlling with the name of ", name)
        self._name = name
        self.setup()
