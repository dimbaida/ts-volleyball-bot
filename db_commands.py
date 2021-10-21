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
        self.id: int = player_id
        self.name: str = name
        self.lastname: str = lastname
        self.telegram_id: int = telegram_id
        self.birthdate: datetime.datetime = birthdate
        self.email: str = email
        self.mobile: str = mobile
        self.active: bool = active
        self.admin: bool = admin

    def check_attendance(self, event_date: datetime.datetime) -> bool or None:
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
                                player_id = {self.id}
                            and 
                                event_id = (select id from events where date = '{event_date}')
                        """)
                decision = cursor.fetchall()

            if connection:
                connection.close()

            try:
                return decision[0][0]
            except IndexError:
                return None

        except psycopg2.Error as e:
            print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")

    def set_decision(self, event_date: datetime.datetime, decision: bool) -> None:
        """
        Adds the player's decision to the attendance table for the given date
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
                        insert into attendance(player_id, event_id, decision, timestamp)
                            values(
                                (select id from players where telegram_id = {self.telegram_id}),
                                (select id from events where date = '{event_date}'),
                                {decision},
                                CURRENT_TIMESTAMP
                            )
                        on conflict (player_id, event_id) do update
                            set decision = {decision}, timestamp = CURRENT_TIMESTAMP
                    """)
            print(f"[PostgreSQL INFO]: {self.name} {self.lastname} inserted values into 'attendance': {event_date}, {decision}")

            if connection:
                connection.close()

        except psycopg2.Error as e:
            print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")

    def write_cache(self, cache: str) -> None:
        """
        Writes cache to the players table
        :param cache: Cache
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
                       update players set cache = '{cache}'
                       where id = {self.id}
                    """)
            if connection:
                connection.close()
        except psycopg2.Error as e:
            print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")

    def read_cache(self) -> str:
        """
        Reads cache from the players table
        :return: Cache
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
                        select cache from players
                        where id = {self.id};
                    """)
                cache = cursor.fetchall()
            if connection:
                connection.close()
            return cache[0][0]

        except psycopg2.Error as e:
            print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")

    def purge_cache(self) -> None:
        """
        Purges cache from the players table
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
                        update players
                        set cache = null
                        where id = {self.id};
                    """)
            if connection:
                connection.close()

        except psycopg2.Error as e:
            print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")


class Guest:
    def __init__(self,
                 guest_id: int,
                 name: str,
                 event_id: int,
                 added_by: int):
        self.id: int = guest_id
        self.event_id: int = event_id
        self.name: str = name
        self.added_by = added_by

    def change_name(self, name: str):
        """
        Rename the guest
        :param name: New name
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
                       update guests set name = '{name}'
                       where id = {self.id}
                    """)
            if connection:
                connection.close()
        except psycopg2.Error as e:
            print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")

    def delete(self):
        """
        Deletes the guest
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
                        delete from guests * where id = {self.id};
                    """)

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
        self.id: int = event_id
        self.date: datetime.datetime = date
        self.date_formatted: str = date.strftime("%d.%m.%Y")
        self.type: str = event_type
        self.icon: str = ICONS[event_type]
        self.note: str = note

    def players(self) -> list:
        """
        Returns the list of players that made a decision on the event
        :return: players
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
                        select  players.id,
                                players.name, 
                                players.lastname,
                                players.telegram_id,
                                players.birthdate,
                                players.email,
                                players.mobile,
                                players.active,
                                players.admin,
                                players.cache
                        from attendance
                        join players on players.id = attendance.player_id
                        where attendance.event_id = (select id from events where date = '{self.date}')
                        order by attendance.timestamp asc
                    """)
                players_data = cursor.fetchall()
                players = []
                for player in players_data:
                    players.append(Player(player_id=player[0],
                                          name=player[1],
                                          lastname=player[2],
                                          telegram_id=player[3],
                                          birthdate=player[4],
                                          email=player[5],
                                          mobile=player[6],
                                          active=player[7],
                                          admin=player[8]))
            if connection:
                connection.close()
            return players
        except psycopg2.Error as e:
            print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")

    def players_formatted(self) -> str:
        """
        Returns a string with enumerated list of players
        :return:
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
                        select  p.name, p.lastname, a.decision from players p
                        left join attendance a on p.id = a.player_id 
                            and a.event_id = (select e.id from events e where e.date = '{self.date}')
                        where p.active
                        order by a.timestamp asc
                    """)
                players = cursor.fetchall()

                cursor.execute(
                    f"""
                        select name from guests
                        where event_id = {self.id}
                        order by timestamp asc
                    """)
                guests = cursor.fetchall()

                if connection:
                    connection.close()

                players_yes: str = ''
                guests_str: str = ''
                players_no: str = ''
                players_none: str = ''
                num_yes: int = 1
                num_guests: int = 1
                num_no: int = 1
                num_none: int = 1
                for player in players:
                    if player[2] == True:
                        players_yes += f'\n{num_yes}. {player[1]} {player[0]}'
                        num_yes += 1
                    elif player[2] == False:
                        players_no += f'\n{num_no}. {player[1]} {player[0]}'
                        num_no += 1
                    elif player[2] is None:
                        players_none += f'\n{num_none}. {player[1]} {player[0]}'
                        num_none += 1
                for guest in guests:
                    guests_str += f'\n{num_guests}. {guest[0]}'
                    num_guests += 1

            text = ''
            if players_yes:
                text += "Придут:"
                text += players_yes
                text += '\n\n'
            if guests:
                text += "Гости:"
                text += guests_str
                text += '\n\n'
            if players_no:
                text += 'Пропустят:'
                text += players_no
                text += '\n\n'
            if players_none:
                text += 'Не отметились:'
                text += players_none
                text += '\n\n'
            else:
                text += "Все игроки отмечены"
            return text

        except psycopg2.Error as e:
            print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")

    def delete(self):
        """
        Deletes the event
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
                        delete from attendance * where event_id = {self.id};
                        delete from guests * where event_id = {self.id};
                        delete from events * where date = '{self.date}';
                    """)

            if connection:
                connection.close()

        except psycopg2.Error as e:
            print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")

    def switch_type(self):
        """
        Switch the type of event, e.g. "game" -> "train" or "train" -> "game"
        """
        new_type = {'train': 'game', 'game': 'train'}[self.type]
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
                        update events
                        set type = '{new_type}'
                        where id = {self.id}
                    """)
            if connection:
                connection.close()
        except psycopg2.Error as e:
            print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")
        self.type = new_type
        self.icon = ICONS[self.type]

    def add_guest(self, guest_name: str, player: Player) -> None:  # TODO: return Guest
        """
        Adds name to the 'guests' table
        :param guest_name: guest name
        :param player: player who added the guest
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
                        insert into guests(event_id, name, added_by, timestamp)
                        values({self.id}, '{guest_name}', {player.id}, CURRENT_TIMESTAMP)
                    """)
            print(f"[PostgreSQL INFO]: Guest {guest_name} was added to {self.date} by {player.lastname} {player.name}")

            if connection:
                connection.close()

        except psycopg2.Error as e:
            print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")

    def guests(self) -> list:
        """
        Returns the list of guests for the event
        :return: guests
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
                        select id, name, event_id, added_by
                        from guests
                        where event_id = '{self.id}'
                        order by timestamp asc
                    """)
                guests_data = cursor.fetchall()
                guests = []
                for guest in guests_data:
                    guests.append(Guest(guest_id=guest[0], name=guest[1], event_id=guest[2], added_by=guest[3]))
            if connection:
                connection.close()
            return guests
        except psycopg2.Error as e:
            print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")

    def update_note(self, note: str, player: Player) -> None:
        """
        Updates the note for the event
        :param note: Text for the note
        :param player: Player who added the note
        :return:
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
                        update events
                        set note = '{note}'
                        where id = {self.id}
                    """)
            print(f"[PostgreSQL INFO]: Note was added to {self.date} by {player.name} {player.lastname}")

            if connection:
                connection.close()
            self.note = note

        except psycopg2.Error as e:
            print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")


def check_player(telegram_id: int) -> bool:
    """
    Checks if telegram_id is in the list of players
    :param telegram_id: telegram id
    :return: True / False
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
                    select true from players where telegram_id={telegram_id};
                """)
            player = cursor.fetchall()
            player = player[0]
        if connection:
            connection.close()

        return True if player else False

    except psycopg2.Error as e:
        print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")


def get_event_by_date(date: str) -> Event:
    """
    Get event by its date
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
            event_note = event[0][3]

        if connection:
            connection.close()

        return Event(event_id, event_date, event_type, event_note)

    except psycopg2.Error as e:
        print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")


def get_event_by_id(event_id: int) -> Event:
    """
    Get event by its id
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
            event_note = event[0][3]

        if connection:
            connection.close()

        return Event(event_id, event_date, event_type, event_note)

    except psycopg2.Error as e:
        print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")


def get_guest_by_id(guest_id: int) -> Guest:
    """
        Get guest by id
        :param guest_id: guest id
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
                    select id, name, event_id, added_by from guests where id='{guest_id}'
                """)
            guest = cursor.fetchall()
            guest_id = guest[0][0]
            guest_name = guest[0][1]
            guest_event_id = guest[0][2]
            guest_added_by = guest[0][3]

        if connection:
            connection.close()

        return Guest(guest_id, guest_name, guest_event_id, guest_added_by)

    except psycopg2.Error as e:
        print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")


def upcoming_events() -> list:
    """
    Get the list of upcoming events
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
    Get the player by his/her telegram id
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
                    select  players.id,
                            players.name, 
                            players.lastname,
                            players.telegram_id,
                            players.birthdate,
                            players.email,
                            players.mobile,
                            players.active,
                            players.admin
                    from players where telegram_id={telegram_id}
                """)
            player = cursor.fetchall()
            player = player[0]
        if connection:
            connection.close()
        return Player(player_id=player[0],
                      name=player[1],
                      lastname=player[2],
                      telegram_id=player[3],
                      birthdate=player[4],
                      email=player[5],
                      mobile=player[6],
                      active=player[7],
                      admin=player[8])

    except psycopg2.Error as e:
        print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")


def get_active_players() -> list:
    """
    Get the list of all active players
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
                select  players.id,
                        players.name, 
                        players.lastname,
                        players.telegram_id,
                        players.birthdate,
                        players.email,
                        players.mobile,
                        players.active,
                        players.admin
                from players where active=true
                """)
            players_data = cursor.fetchall()
            players = []
            for player in players_data:
                players.append(Player(player_id=player[0],
                                      name=player[1],
                                      lastname=player[2],
                                      telegram_id=player[3],
                                      birthdate=player[4],
                                      email=player[5],
                                      mobile=player[6],
                                      active=player[7],
                                      admin=player[8]))
        if connection:
            connection.close()
        return players

    except psycopg2.Error as e:
        print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")


def get_all_players() -> list:
    """
    Get the list of all players
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
                select  players.id,
                        players.name, 
                        players.lastname,
                        players.telegram_id,
                        players.birthdate,
                        players.email,
                        players.mobile,
                        players.active,
                        players.admin
                from players
                """)
            players_data = cursor.fetchall()
            players = []
            for player in players_data:
                players.append(Player(player_id=player[0],
                                      name=player[1],
                                      lastname=player[2],
                                      telegram_id=player[3],
                                      birthdate=player[4],
                                      email=player[5],
                                      mobile=player[6],
                                      active=player[7],
                                      admin=player[8]))
        if connection:
            connection.close()
        return players

    except psycopg2.Error as e:
        print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")


def create_event(event_date: str, event_type: str) -> Event:
    """
    Creates a new event
    :param event_date: date in string format yyyy-mm-dd
    :param event_type: 'train' or 'game'
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
                    insert into events(date, type)
                    values('{event_date}', '{event_type}')
                    on conflict (date) do update
                        set type = '{event_type}';

                    select id, date, type, note from events 
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


