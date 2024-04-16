from db.interface_base import DatabaseInterfaceBase

class DatabaseInterface(DatabaseInterfaceBase):
    '''Sample database interface. write as you please'''
    _instance = None

    @staticmethod
    def Get():
        if not DatabaseInterface._instance:
            DatabaseInterface._instance = DatabaseInterface()
        return DatabaseInterface._instance

    def setup(self):
        '''Write the overriding version'''
    # continue
