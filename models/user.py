from decouple import config
from db.interface import DatabaseInterface
from datetime import datetime, date
from tools.mathematix import tz_today
from enum import Enum
from tools.mathematix import tz_today

ADMIN_USERNAME = config('ADMIN_USERNAME')
ADMIN_PASSWORD = config('ADMIN_PASSWORD')

class UserStates(Enum):
    NONE = 0


class User:
    # states:

    _database = None
    Scheduler = None
    GarbageCollectionInterval = 60

    Instances = {}  # active Users will cache into this; so there's no need to access database everytime
    # causing a slight enhancement on performance
    @staticmethod
    def Database():
        if User._database == None:
            User._database = DatabaseInterface.Get()
        return User._database

    @staticmethod
    def GarbageCollect():
        now = tz_today()
        garbage = []
        for chat_id in User.Instances:
            if (now - User.Instances[chat_id].last_interaction).total_seconds() / 60 >= User.GarbageCollectionInterval / 2:
                garbage.append(chat_id)
        # because changing dict size in a loop on itself causes error,
        # we first collect redundant chat_id s and then delete them from the memory
        for g in garbage:
            del User.Instances[g]

    @staticmethod
    def ExtractQueryData(row: list, no_cache: bool = False):
        return User(row[0], bool(row[1]), bool(row[2]), row[3], no_cache=no_cache)
    
    @staticmethod
    def Get(chat_id, no_cache: bool = False):
        if chat_id in User.Instances:
            User.Instances[chat_id].last_interaction = tz_today()
            return User.Instances[chat_id]
        
        User.GarbageCollect()  # garbage collect other users
            
        row = User.Database().get(chat_id)
        if row:
            return User.ExtractQueryData(row, no_cache=no_cache)
        return User(chat_id=chat_id, no_cache=no_cache).save()
    
    @staticmethod
    def Everybody():
        return User.Database().get_all()

    @staticmethod
    def GetAll():
        return [User.ExtractQueryData(user_row) for user_row in User.Database().load_everybody()]
    
    def save(self):
        self.Database().update(self)
        self.previous_message_id = None
        return self

    def __init__(self, chat_id, is_intervaller: bool = False, is_changer: bool=False, language: str='fa', no_cache: bool = False) -> None:
        self.is_admin: bool = False
        self.chat_id: int = chat_id
        self.last_interaction: datetime = tz_today()
        self.state: UserStates = None
        self.state_data: any = None
        self.is_changer = is_changer
        self.is_intervaller = is_intervaller
        self.language: str = language
        self.previous_message_id = None
        if not no_cache:
            User.Instances[chat_id] = self

    def change_state(self, state: UserStates = UserStates.NONE, data: any = None):
        self.state = state
        self.state_data = data

    def __str__(self) -> str:
        return f'{self.chat_id}'

    def authorization(self, args):
        if self.is_admin:
            return True

        if args and len(args) >= 2:
            username = args[0]
            password = args[1]
            self.is_admin = password == ADMIN_PASSWORD and username == ADMIN_USERNAME
            return self.is_admin

        return False

    @staticmethod
    def Statistics():
        # first save all last interactions:
        for id in User.Instances:
            User.Instances[id].save()
        now = tz_today().date()
        today_actives, yesterday_actives, this_week_actives, this_month_actives = 0, 0, 0, 0

        last_interactions = User.Database().get_all(column=DatabaseInterface.User_LAST_INTERACTION)
        for interaction_date in last_interactions:
            if interaction_date and (isinstance(interaction_date, datetime) or isinstance(interaction_date, date)):
                if now.year == interaction_date.year:
                    if now.month == interaction_date.month:
                        this_month_actives += 1
                        if now.isocalendar()[1] == interaction_date.isocalendar()[1]:
                            this_week_actives += 1
                            if now.day == interaction_date.day:
                                today_actives += 1
                        if now.day == interaction_date.day + 1:
                            yesterday_actives += 1
                    elif now.month == interaction_date.month + 1:
                        delta = now - (interaction_date.date() if isinstance(interaction_date, datetime) else interaction_date)
                        if delta and delta.days == 1:
                            yesterday_actives += 1
                elif now.year == interaction_date.year + 1 and now.month == 1 and interaction_date.month == 12:
                        delta = now - (interaction_date.date() if isinstance(interaction_date, datetime) else interaction_date)
                        if delta and delta.days == 1:
                            yesterday_actives += 1
        return {'daily': today_actives, 'yesterday': yesterday_actives, 'weekly': this_week_actives, 'monthly': this_month_actives, 'all': len(last_interactions)}
