import logging
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
                 is_active: bool,
                 is_admin: bool):
        self.id: int = player_id
        self.name: str = name
        self.lastname: str = lastname
        self.telegram_id: int = telegram_id
        self.birthdate: datetime.datetime = birthdate
        self.email: str = email
        self.mobile: str = mobile
        self.is_active: bool = is_active
        self.is_admin: bool = is_admin

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
                        SELECT decision FROM attendance
                        WHERE 
                            player = {self.id}
                        AND 
                            event = (SELECT id FROM events WHERE date = '{event_date}')
                    """)
                decision = cursor.fetchall()

            if connection:
                connection.close()

            try:
                return decision[0][0]
            except IndexError:
                return None

        except psycopg2.Error as e:
            logging.error(e)

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
                        INSERT INTO attendance(player, event, decision, timestamp)
                            VALUES(
                                (SELECT id FROM players WHERE telegram_id = {self.telegram_id}),
                                (SELECT id FROM events WHERE date = '{event_date}'),
                                {decision},
                                CURRENT_TIMESTAMP
                            )
                        ON CONFLICT (player, event) DO UPDATE
                            SET decision = {decision}, timestamp = CURRENT_TIMESTAMP
                    """)
            logging.info(f"[{self.id}]{self.lastname} {self.name} -> {event_date} - {decision}")

            if connection:
                connection.close()

        except psycopg2.Error as e:
            logging.error(e)

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
            logging.error(e)

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
                        SELECT cache FROM players
                        WHERE id = {self.id};
                    """)
                cache = cursor.fetchall()
            if connection:
                connection.close()
            return cache[0][0]

        except psycopg2.Error as e:
            logging.error(e)

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
                        UPDATE players
                        SET cache = null
                        WHERE id = {self.id};
                    """)
            if connection:
                connection.close()

        except psycopg2.Error as e:
            logging.error(e)


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
                       UPDATE guests SET name = '{name}'
                       WHERE id = {self.id}
                    """)
            if connection:
                connection.close()
        except psycopg2.Error as e:
            logging.error(e)

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
                        DELETE FROM guests * WHERE id = {self.id};
                    """)

            if connection:
                connection.close()

        except psycopg2.Error as e:
            logging.error(e)


class Event:
    def __init__(self,
                 event_id: int,
                 date: datetime.datetime,
                 event_type: str,
                 note: str):
        self.id: int = event_id
        self.date: datetime.datetime = date
        self.date_formatted: str = self.date.strftime("%d.%m.%Y")
        self.type: str = event_type
        self.icon: str = ICONS[self.type]
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
                        SELECT players.id,
                               players.name, 
                               players.lastname,
                               players.telegram_id,
                               players.birthdate,
                               players.email,
                               players.mobile,
                               players.active,
                               players.admin,
                               players.cache
                        FROM attendance
                        JOIN players ON players.id = attendance.player
                        WHERE attendance.event = (SELECT id FROM events WHERE date = '{self.date}')
                        ORDER BY attendance.timestamp ASC
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
                                          is_active=player[7],
                                          is_admin=player[8]))
            if connection:
                connection.close()
            return players
        except psycopg2.Error as e:
            logging.error(e)

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
                        SELECT p.name, p.lastname, a.decision FROM players p
                        LEFT JOIN attendance a ON p.id = a.player 
                            AND a.event = (SELECT e.id FROM events e WHERE e.date = '{self.date}')
                        WHERE p.active
                        ORDER BY a.timestamp ASC
                    """)
                players = cursor.fetchall()

                cursor.execute(
                    f"""
                        SELECT name FROM guests
                        WHERE event = {self.id}
                        ORDER BY timestamp ASC
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
                    if player[2] is True:
                        players_yes += f'\n{num_yes}. {player[1]} {player[0]}'
                        num_yes += 1
                    elif player[2] is False:
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
                text += "Прийдуть:"
                text += players_yes
                text += '\n\n'
            if guests:
                text += "Гості:"
                text += guests_str
                text += '\n\n'
            if players_no:
                text += 'Пропустять:'
                text += players_no
                text += '\n\n'
            if players_none:
                text += 'Не відмітились:'
                text += players_none
                text += '\n\n'
            else:
                text += "Всі гравці відмічені"
            return text

        except psycopg2.Error as e:
            logging.error(e)

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
                        DELETE FROM attendance * WHERE event = {self.id};
                        DELETE FROM guests * WHERE event = {self.id};
                        DELETE FROM events * WHERE id = {self.id};
                    """)

            if connection:
                connection.close()

        except psycopg2.Error as e:
            logging.error(e)

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
                        UPDATE events
                        SET type = '{new_type}'
                        WHERE id = {self.id}
                    """)
            if connection:
                connection.close()
        except psycopg2.Error as e:
            logging.error(e)
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
                        INSERT INTO guests(event, name, added_by, timestamp)
                        VALUES({self.id}, '{guest_name}', {player.id}, CURRENT_TIMESTAMP)
                    """)
            logging.info(f"[{player.id}]{player.lastname} {player.name} added guest {guest_name} to [{self.id}]{self.date_formatted}")

            if connection:
                connection.close()

        except psycopg2.Error as e:
            logging.error(e)

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
                        SELECT id, name, event, added_by
                        FROM guests
                        WHERE event = '{self.id}'
                        ORDER BY timestamp ASC
                    """)
                guests_data = cursor.fetchall()
                guests = []
                for guest in guests_data:
                    guests.append(Guest(guest_id=guest[0], name=guest[1], event_id=guest[2], added_by=guest[3]))
            if connection:
                connection.close()
            return guests
        except psycopg2.Error as e:
            logging.error(e)

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
                        UPDATE events
                        SET note = '{note}'
                        WHERE id = {self.id}
                    """)
            logging.info(f'[{player.id}]{player.lastname} {player.name} added note to [{self.id}]{self.date_formatted}: "{note}"')

            if connection:
                connection.close()
            self.note = note

        except psycopg2.Error as e:
            logging.error(e)


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
                    SELECT true FROM players WHERE telegram_id={telegram_id};
                """)
            player = cursor.fetchall()
        if connection:
            connection.close()

        return True if player else False

    except psycopg2.Error as e:
        logging.error(e)


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
                    SELECT * FROM events WHERE date='{date}'
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
        logging.error(e)


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
                    SELECT * FROM events WHERE id='{event_id}'
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
        logging.error(e)


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
                    SELECT id, name, event, added_by FROM guests WHERE id='{guest_id}'
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
        logging.error(e)


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
                    SELECT * FROM events WHERE date >= current_date ORDER BY date ASC
                """)

            events_raw = cursor.fetchall()

        if connection:
            connection.close()

        events = [Event(event[0], event[1], event[2], event[3]) for event in events_raw]

        return events

    except psycopg2.Error as e:
        logging.error(e)


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
                    SELECT  players.id,
                            players.name, 
                            players.lastname,
                            players.telegram_id,
                            players.birthdate,
                            players.email,
                            players.mobile,
                            players.active,
                            players.admin
                    FROM players WHERE telegram_id={telegram_id}
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
                      is_active=player[7],
                      is_admin=player[8])

    except psycopg2.Error as e:
        logging.error(e)


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
                SELECT  players.id,
                        players.name, 
                        players.lastname,
                        players.telegram_id,
                        players.birthdate,
                        players.email,
                        players.mobile,
                        players.active,
                        players.admin
                FROM players WHERE active=true
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
                                      is_active=player[7],
                                      is_admin=player[8]))
        if connection:
            connection.close()
        return players

    except psycopg2.Error as e:
        logging.error(e)


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
                SELECT  players.id,
                        players.name, 
                        players.lastname,
                        players.telegram_id,
                        players.birthdate,
                        players.email,
                        players.mobile,
                        players.active,
                        players.admin
                FROM players
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
                                      is_active=player[7],
                                      is_admin=player[8]))
        if connection:
            connection.close()
        return players

    except psycopg2.Error as e:
        logging.error(e)


def create_event(event_date: str, event_type: str, created_by: int) -> Event:
    """
    Creates a new event
    :param event_date: date in string format yyyy-mm-dd
    :param event_type: 'train' or 'game'
    :param created_by: the player, who created the event
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
                    INSERT INTO events(date, type, created_by, timestamp)
                    VALUES('{event_date}', '{event_type}', {created_by}, CURRENT_TIMESTAMP)
                    ON CONFLICT (date) DO UPDATE
                        SET type = '{event_type}';

                    SELECT id, date, type, note FROM events 
                    WHERE date = '{event_date}';
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
        logging.error(e)
