import psycopg2
import datetime
from common_constants import ICONS
from config import host, user, password, database


class Player:
    def __init__(self,
                 player_id: int,
                 name: str,
                 lastname: str,
                 telegram_id: int,
                 birthdate: datetime.datetime,
                 email: str,
                 mobile: str,
                 active: bool,
                 admin: bool):
        self.id = player_id
        self.name = name
        self.lastname = lastname
        self.telegram_id = telegram_id
        self.birthdate = birthdate.strftime("%Y.%m.%d")
        self.email = email
        self.mobile = mobile
        self.active = active
        self.admin = admin

    def check_attendance(self, event_date: str) -> bool or None:
        """
            Checks if the player has already made a decision on going to the event
            :param event_date: date in string format yyyy-mm-dd
            :return: True, False or None
            """
        try:
            connection = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=database)
            connection.autocommit = True

            with connection.cursor() as cursor:
                cursor.execute(
                    f"""  
                            select decision from attendance 
                            where 
                                player_id = {self.id})
                            and 
                                event_id = (select id from events where date = '{event_date}')
                        """)
                decision = cursor.fetchall()

            if connection:
                connection.close()

            try:
                decision = decision[0][0]
                return True if decision == 'YES' else False
            except IndexError:
                return None

        except psycopg2.Error as e:
            print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")

    def add_decision(self, event_date: str, decision: str) -> None:
        """
        :param event_date: date in string format yyyy-mm-dd
        :param decision: 'YES' or 'NO'
        """
        try:
            connection = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=database)
            connection.autocommit = True

            with connection.cursor() as cursor:
                cursor.execute(
                    f"""  
                        insert into attendance(player_id, event_id, decision)
                            values(
                                (select id from players where telegram_id = {self.telegram_id}),
                                (select id from events where date = '{event_date}'),
                                '{decision}'
                            )
                        on conflict (player_id, event_id) do update
                            set decision = '{decision}'
                    """)
            print(f"[PostgreSQL INFO]: {self.name} {self.lastname} inserted values into 'attendance': {event_date}, {decision}")

            if connection:
                connection.close()

        except psycopg2.Error as e:
            print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")


class Event:
    def __init__(self,
                 event_id: int,
                 date: datetime.datetime,
                 event_type: str,
                 note: str):
        self.id = event_id
        self.date = date.strftime("%Y.%m.%d")
        self.date_formatted = date.strftime("%d.%m.%Y")
        self.type = event_type
        self.icon = ICONS[event_type]
        self.note = note

    def players(self) -> dict:
        """
        :return: {'YES': players, 'NO': players, 'undecided': players}}
        """
        try:
            connection = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=database)
            connection.autocommit = True

            with connection.cursor() as cursor:

                players = {}

                cursor.execute(
                    f"""  
                        select players.* 
                        from attendance
                        join players on players.id = attendance.player_id
                        where attendance.event_id = (select id from events where date = '{self.date}')
                        and attendance.decision = 'YES'
                        order by id asc
                    """)
                players_data = cursor.fetchall()
                players_yes = []
                for player in players_data:
                    players_yes.append(Player(player[0], player[1], player[2], player[3], player[4], player[5], player[6], player[7], player[8]))
                players['YES'] = players_yes

                cursor.execute(
                    f"""  
                        select players.* 
                        from attendance
                        join players on players.id = attendance.player_id
                        where attendance.event_id = (select id from events where date = '{self.date}')
                        and attendance.decision = 'NO'
                        order by id asc
                    """)
                players_data = cursor.fetchall()
                players_no = []
                for player in players_data:
                    players_no.append(Player(player[0], player[1], player[2], player[3], player[4], player[5], player[6], player[7], player[8]))
                players['NO'] = players_yes

            if connection:
                connection.close()

            return players

        except psycopg2.Error as e:
            print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")

    def players_attendance_list(self) -> str:
        try:
            connection = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=database)
            connection.autocommit = True

            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    select players.name, players.lastname, attendance.decision
                    from attendance
                    join players on players.id = attendance.player_id
                    where attendance.event_id = (select id from events where date = '{self.date}')
                    """)
                players = cursor.fetchall()
                players_yes: str = ''
                players_no: str = ''
                num_yes: int = 1
                num_no: int = 1
                for player in players:
                    if player[2] == 'YES':
                        players_yes += f'\n{str(num_yes)}. {player[0]} {player[1]}'
                        num_yes += 1
                    elif player[2] == 'NO':
                        players_no += f'\n{str(num_no)}. {player[0]} {player[1]}'
                        num_no += 1

            if connection:
                connection.close()

            return f'Придут:{players_yes}\n\nПропустят:{players_no}'

        except psycopg2.Error as e:
            print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")

    def delete(self):
        try:
            connection = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=database)
            connection.autocommit = True

            with connection.cursor() as cursor:
                cursor.execute(
                    f"""  
                        delete from events * where date = '{self.date}'
                    """)

            if connection:
                connection.close()

        except psycopg2.Error as e:
            print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")

    def is_upcoming(self) -> bool:
        return datetime.datetime.today() <= datetime.datetime.strptime(self.date, "%Y-%m-%d")


def get_event_by_date(date: str) -> Event:
    """
    :param date: date in string format yyyy-mm-dd
    :return: Event
    """
    try:
        connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=database)
        connection.autocommit = True

        with connection.cursor() as cursor:
            cursor.execute(
                f"""  
                    select * from events where date='{date}'
                """)
            event = cursor.fetchall()
            event_id = event[0][0]
            event_date = event[0][1]
            event_type = event[0][2]
            event_note = event[0][2]

        if connection:
            connection.close()

        return Event(event_id, event_date, event_type, event_note)

    except psycopg2.Error as e:
        print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")


def get_event_by_id(event_id: int) -> Event:
    """
    :param event_id: event id
    :return: Event
    """
    try:
        connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=database)
        connection.autocommit = True

        with connection.cursor() as cursor:
            cursor.execute(
                f"""  
                    select * from events where id='{event_id}'
                """)
            event = cursor.fetchall()
            event_id = event[0][0]
            event_date = event[0][1]
            event_type = event[0][2]
            event_note = event[0][2]

        if connection:
            connection.close()

        return Event(event_id, event_date, event_type, event_note)

    except psycopg2.Error as e:
        print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")


def upcoming_events() -> list:
    """
    :return: list of Events which will take place after today
    """
    try:
        connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=database)
        connection.autocommit = True

        with connection.cursor() as cursor:
            cursor.execute(
                f"""  
                    select * from events where date >= current_date order by date ASC
                """)

            events_raw = cursor.fetchall()

        if connection:
            connection.close()

        events = [Event(event[0], event[1], event[2], event[3]) for event in events_raw]

        return events

    except psycopg2.Error as e:
        print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")


def get_player_by_telegram_id(telegram_id: int) -> Player:
    """
    :param telegram_id: telegram id
    :return: Player
    """
    try:
        connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=database)
        connection.autocommit = True

        with connection.cursor() as cursor:
            cursor.execute(
                f"""  
                    select * from players where telegram_id={telegram_id}
                """)
            player = cursor.fetchall()
            player = player[0]
        if connection:
            connection.close()
        return Player(player[0], player[1], player[2], player[3], player[4], player[5], player[6], player[7], player[8])

    except psycopg2.Error as e:
        print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")


def get_active_players() -> list:
    """
   :return: list of Players
   """
    try:
        connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=database)
        connection.autocommit = True

        with connection.cursor() as cursor:
            cursor.execute(
                f"""  
                   select * from players where active=true
               """)
            players_data = cursor.fetchall()
            players = []
            for player in players_data:
                players.append(Player(player[0], player[1], player[2], player[3],
                                      player[4], player[5], player[6], player[7], player[8]))
        if connection:
            connection.close()
        return players

    except psycopg2.Error as e:
        print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")


def create_event(event_date: str, event_type: str) -> Event:
    """
    :param event_date: date in string format yyyy-mm-dd
    :param event_type: 'train' or 'game'
    """
    try:
        connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=database)
        connection.autocommit = True

        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                    insert into events(date, type)
                    values('{event_date}', '{event_type}')
                    on conflict (date) do update
                        set type = '{event_type}';

                    select * from events 
                    where date = '{event_date}';
                """)
            event = cursor.fetchall()
            event_id = event[0][0]
            event_date = event[0][1]
            event_type = event[0][2]
            event_note = event[0][2]

        if connection:
            connection.close()

        return Event(event_id, event_date, event_type, event_note)

    except psycopg2.Error as e:
        print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")


