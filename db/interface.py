import sqlite3
from datetime import datetime
from tools import manuwriter


class DatabaseInterface:
    _instance = None
    TABLE_USERS = "users"
    USER_ID = 'id'
    USER_LAST_INTERACTION = 'last_interaction'
    USER_IS_INTERVALLER = 'intervaller'
    USER_IS_CHANGER = 'changer'
    USER_LANGUAGE = 'language'
    USER_ALL_FIELDS = f'({USER_ID}, {USER_LAST_INTERACTION}, {USER_IS_INTERVALLER}, {USER_IS_CHANGER}, {USER_LANGUAGE})'
    DATE_FORMAT = '%Y-%m-%d'
    @staticmethod
    def Get():
        if not DatabaseInterface._instance:
            DatabaseInterface._instance = DatabaseInterface()
        return DatabaseInterface._instance

    def setup(self):
        connection = None
        try:
            connection = sqlite3.connect(self._name, detect_types=sqlite3.PARSE_DECLTYPES)
            cursor = connection.cursor()

            # check if the table users was created
            if not cursor.execute(f"SELECT name from sqlite_master WHERE name='{DatabaseInterface.TABLE_USERS}'").fetchone():
                query = f"CREATE TABLE {DatabaseInterface.TABLE_USERS} ({DatabaseInterface.USER_ID} INTEGER PRIMARY KEY," +\
                    f"{DatabaseInterface.USER_IS_INTERVALLER} TINYINT, {DatabaseInterface.USER_IS_CHANGER} TINYINT, {DatabaseInterface.USER_LANGUAGE} TEXT, {DatabaseInterface.USER_LAST_INTERACTION} DATE)"
                # create table user
                cursor.execute(query)
                manuwriter.log(f"{DatabaseInterface.TABLE_USERS} table created successfuly.", category_name='info')
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
            query = f"INSERT INTO {DatabaseInterface.TABLE_USERS} {DatabaseInterface.USER_ALL_FIELDS} VALUES (?, ?, ?, ?, ?)"
            self.execute(False, query, user.chat_id, user.last_interaction.strftime(DatabaseInterface.DATE_FORMAT), user.is_intervaller, user.is_changer, user.language)

        except Exception as ex:
            manuwriter.log(f"Cannot save this user:{user}", ex, category_name=f'{log_category_prefix}database')
            if connection:
                connection.close()
            raise ex  # custom ex needed here too

    def get(self, chat_id):
        rows = self.execute(True, f"SELECT * FROM {DatabaseInterface.TABLE_USERS} WHERE {DatabaseInterface.USER_ID}=? LIMIT 1", chat_id)
        return rows[0] if rows else None

    def load_everybody(self) -> list:
        return self.execute(True, f"SELECT * FROM {DatabaseInterface.TABLE_USERS}")

    def get_all(self, column: str=USER_ID) -> list:
        rows = self.execute(True, f"SELECT ({column}) FROM {DatabaseInterface.TABLE_USERS}")
        if column == DatabaseInterface.USER_LAST_INTERACTION:
            return [datetime.strptime(row[0], DatabaseInterface.DATE_FORMAT) if row[0] else None for row in rows]
        return [row[0] for row in rows] # just return a list of ids

    def update(self, user, log_category_prefix=''):
        connection = sqlite3.connect(self._name)
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM {DatabaseInterface.TABLE_USERS} WHERE {DatabaseInterface.USER_ID}=? LIMIT 1", (user.chat_id, ))
        if cursor.fetchone(): # if user with his chat id has been saved before in the database
            FIELDS_TO_SET = ','.join(
                f'{column}=?' for column in (DatabaseInterface.USER_IS_INTERVALLER, DatabaseInterface.USER_IS_CHANGER, DatabaseInterface.USER_LANGUAGE, DatabaseInterface.USER_LAST_INTERACTION)
            )
            cursor.execute(f'UPDATE {DatabaseInterface.TABLE_USERS} SET {FIELDS_TO_SET} WHERE {DatabaseInterface.USER_ID}=?', \
                (user.is_intervaller, user.is_changer, user.language, user.last_interaction.strftime(DatabaseInterface.DATE_FORMAT) , user.chat_id))
        else:
            cursor.execute(f"INSERT INTO {DatabaseInterface.TABLE_USERS} {DatabaseInterface.USER_ALL_FIELDS} VALUES (?, ?, ?, ?, ?)", \
                (user.chat_id, user.last_interaction.strftime(DatabaseInterface.DATE_FORMAT), user.is_intervaller, user.is_changer, user.language))
            manuwriter.log("New user started using this bot with chat_id=: " + user.__str__(), category_name=f'{log_category_prefix}info')
        connection.commit()
        cursor.close()
        connection.close()

    def execute(self, is_fetch_query: bool, query: str, *params):
        '''Execute queries that doesnt return result such as insert or delete'''
        rows = None
        connection = sqlite3.connect(self._name)
        cursor = connection.cursor()
        cursor.execute(query, (*params, ))
        if is_fetch_query:
            rows = cursor.fetchall()
        else:  # its a change and needs to be saved
            connection.commit()
        cursor.close()
        connection.close()
        return rows
    
    def __init__(self, name="data.db"):
        self._name = name
        self.setup()
