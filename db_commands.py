import logging
import psycopg2
import datetime
from common_constants import ICONS
from config import host, user, password, database

logging.basicConfig(level=logging.INFO, format='%(levelname)s >> %(message)s')


class Player:
    def __init__(self, **kwargs):
        self.id: int = kwargs['id']
        self.name: str = kwargs['name']
        self.lastname: str = kwargs['lastname']
        self.telegram_id: int = kwargs['telegram_id']
        self.birthdate: datetime.datetime = kwargs['birthdate']
        self.email: str = kwargs['email']
        self.mobile: str = kwargs['mobile']
        self.active: bool = kwargs['active']
        self.admin: bool = kwargs['admin']
        self.team: bool = kwargs['team']

    def check_attendance(self, event_id: int) -> bool | None:
        """
        Checks if the player has already made a decision on going to the event
        :param event_id: event id
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
                        WHERE player = {self.id} AND event = {event_id}; 
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

    def set_decision(self, event_id: int, decision: bool) -> None:
        """
        Adds the player's decision to the attendance table for the given date
        :param event_id: event id
        :param decision: 'YES' or 'NO'
        """
        event = get_event(event_id)
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
                            VALUES({self.id}, {event.id}, {decision}, CURRENT_TIMESTAMP)
                        ON CONFLICT (player, event) DO UPDATE
                            SET decision = {decision}, timestamp = CURRENT_TIMESTAMP;
                    """)
            logging.info(f"[{self.id}]{self.lastname} {self.name} -> [{event.id}]{event.date_formatted} - {decision}")

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
                       UPDATE players SET cache = '{cache}'
                       WHERE id = {self.id};
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
    def __init__(self, **kwargs):
        self.id: int = kwargs['id']
        self.event: int = kwargs['event']
        self.name: str = kwargs['name']
        self.added_by = kwargs['added_by']

    def change_name(self, name: str) -> None:
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
                       WHERE id = {self.id};
                    """)
            if connection:
                connection.close()
        except psycopg2.Error as e:
            logging.error(e)

    def delete(self) -> None:
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
                        DELETE FROM guests 
                        WHERE id = {self.id};
                    """)
            if connection:
                connection.close()

        except psycopg2.Error as e:
            logging.error(e)


class Event:
    def __init__(self, **kwargs):
        self.id: int = kwargs['id']
        self.date: datetime.datetime = kwargs['date']
        self.date_formatted: str = self.date.strftime("%d.%m.%Y")
        self.type: str = kwargs['type']
        self.created_by: int = kwargs['created_by']
        self.icon: str = ICONS[self.type]
        self.note: str = kwargs['note']

    def players(self) -> list[Player]:
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
                               players.team
                        FROM attendance
                        JOIN players ON players.id = attendance.player
                        WHERE attendance.event = {self.id})
                        ORDER BY attendance.timestamp ASC;
                    """)
                data = cursor.fetchall()
                players = []
                for player in data:
                    players.append(Player(id=player[0],
                                          name=player[1],
                                          lastname=player[2],
                                          telegram_id=player[3],
                                          birthdate=player[4],
                                          email=player[5],
                                          mobile=player[6],
                                          active=player[7],
                                          admin=player[8],
                                          team=player[9]))
            if connection:
                connection.close()
            return players
        except psycopg2.Error as e:
            logging.error(e)

    def guests(self) -> list[Guest]:
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
                        ORDER BY timestamp ASC;
                    """)
                data = cursor.fetchall()
                guests = []
                for guest in data:
                    guests.append(Guest(id=guest[0], name=guest[1], event=guest[2], added_by=guest[3]))
            if connection:
                connection.close()
            return guests
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
                        SELECT player FROM attendance
                        WHERE decision = true and event = {self.id}
                        ORDER BY timestamp ASC;
                    """)
                players_yes = [x[0] for x in cursor.fetchall()]

                cursor.execute(
                    f"""
                        SELECT player FROM attendance
                        WHERE decision = false and event = {self.id}
                        ORDER BY timestamp ASC;
                    """)
                players_no = [x[0] for x in cursor.fetchall()]

                cursor.execute(
                    f"""
                        SELECT name FROM guests
                        WHERE event = {self.id}
                        ORDER BY timestamp ASC;
                    """)
                guests = [x[0] for x in cursor.fetchall()]

                if connection:
                    connection.close()

                text = text_yes = text_guests = text_no = text_none = ''
                i = j = k = 1
                for player in get_active_players():
                    if player.id in players_yes:
                        text_yes += f'{i}. {player.lastname} {player.name}\n'
                        i += 1
                    elif player.id in players_no:
                        text_no += f'{j}. {player.lastname} {player.name}\n'
                        j += 1
                    elif self.type == 'train' or (self.type == 'game' and player.team):
                        text_none += f'{k}. {player.lastname} {player.name}\n'
                        k += 1
                for n, guest in enumerate(guests):
                    text_guests += f'{n+1}. {guest}\n'

                text = text + f'Прийдуть:\n{text_yes}' if text_yes else text
                text = text + f'\nГості:\n{text_guests}' if text_guests and self.type == 'train' else text
                text = text + f'\nПропустять:\n{text_no}' if text_no else text
                text = text + f'\nНе відмітились:\n{text_none}' if text_none else text

                return text

        except psycopg2.Error as e:
            logging.error(e)

    def delete(self) -> None:
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
                        DELETE FROM attendance WHERE event = {self.id};
                        DELETE FROM guests WHERE event = {self.id};
                        DELETE FROM events WHERE id = {self.id};
                    """)

            if connection:
                connection.close()

        except psycopg2.Error as e:
            logging.error(e)

    def switch_type(self) -> None:
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
                        WHERE id = {self.id};
                    """)
            if connection:
                connection.close()
        except psycopg2.Error as e:
            logging.error(e)
        self.type = new_type
        self.icon = ICONS[self.type]

    def add_guest(self, guest_name: str, player: Player) -> Guest:
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
                        VALUES({self.id}, '{guest_name}', {player.id}, CURRENT_TIMESTAMP);
                        
                        SELECT id, name, event, added_by FROM guests 
                        WHERE event = {self.id}, name = '{guest_name}', added_by = {player.id};
                    """)
                data = cursor.fetchall()[0]
                guest_kwargs = dict(id=data[0],
                                    name=data[1],
                                    event=data[2],
                                    added_by=data[3])
            logging.info(f"[{player.id}]{player.lastname} {player.name} added guest to [{self.id}]{self.date_formatted}: {guest_name}")

            if connection:
                connection.close()

            return Guest(**guest_kwargs)

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
                        WHERE id = {self.id};
                    """)
            logging.info(f'[{player.id}]{player.lastname} {player.name} added note to [{self.id}]{self.date_formatted}: "{note}"')

            if connection:
                connection.close()
            self.note = note

        except psycopg2.Error as e:
            logging.error(e)


def get_player(player_id: int) -> Player:
    """
    Get player by its id
    :param player_id: player id
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
                    SELECT id, name, lastname, telegram_id, birthdate, email, mobile, active, admin, team
                    FROM players WHERE id = '{player_id}';
                """)
            data = cursor.fetchall()[0]

        if connection:
            connection.close()

        return Player(id=data[0],
                      name=data[1],
                      lastname=data[2],
                      telegram_id=data[3],
                      birthdate=data[4],
                      email=data[5],
                      mobile=data[6],
                      active=data[7],
                      admin=data[8],
                      team=data[9])

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
                    SELECT true FROM players WHERE telegram_id = {telegram_id};
                """)
            player = cursor.fetchall()
        if connection:
            connection.close()

        return True if player else False

    except psycopg2.Error as e:
        logging.error(e)


def get_event(event_id: int) -> Event:
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
                    SELECT id, date, type, created_by, note 
                    FROM events WHERE id = '{event_id}';
                """)
            data = cursor.fetchall()[0]
            event_kwargs = dict(id=data[0],
                                date=data[1],
                                type=data[2],
                                created_by=data[3],
                                note=data[4])

        if connection:
            connection.close()

        return Event(**event_kwargs)

    except psycopg2.Error as e:
        logging.error(e)


def get_guest(guest_id: int) -> Guest:
    """
        Get guest by id
        :param guest_id: guest id
        :return: Guest
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
                    FROM guests WHERE id = '{guest_id}';
                """)
            data = cursor.fetchall()[0]
            guest_kwargs = dict(id=data[0],
                                name=data[1],
                                event=data[2],
                                added_by=data[3])

        if connection:
            connection.close()

        return Guest(**guest_kwargs)

    except psycopg2.Error as e:
        logging.error(e)


def upcoming_events() -> list[Event]:
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
                    SELECT id, date, type, created_by, note 
                    FROM events 
                    WHERE date >= CURRENT_DATE ORDER BY date ASC;
                """)

            events_raw = cursor.fetchall()

        if connection:
            connection.close()

        events = [Event(id=event[0], date=event[1], type=event[2], created_by=event[3], note=event[4]) for event in events_raw]

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
                            players.admin,
                            players.team
                    FROM players WHERE telegram_id = {telegram_id};
                """)
            data = cursor.fetchall()[0]
        if connection:
            connection.close()
        return Player(id=data[0],
                      name=data[1],
                      lastname=data[2],
                      telegram_id=data[3],
                      birthdate=data[4],
                      email=data[5],
                      mobile=data[6],
                      active=data[7],
                      admin=data[8],
                      team=data[9])

    except psycopg2.Error as e:
        logging.error(e)


def get_active_players() -> list[Player]:
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
                            players.admin,
                            players.team
                    FROM players WHERE active = true;
                """)
            data = cursor.fetchall()
            players = []
            for player in data:
                players.append(Player(id=player[0],
                                      name=player[1],
                                      lastname=player[2],
                                      telegram_id=player[3],
                                      birthdate=player[4],
                                      email=player[5],
                                      mobile=player[6],
                                      active=player[7],
                                      admin=player[8],
                                      team=player[9]))
        if connection:
            connection.close()
        return players

    except psycopg2.Error as e:
        logging.error(e)


def get_all_players() -> list[Player]:
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
                            players.admin,
                            players.team
                    FROM players;
                """)
            data = cursor.fetchall()
            players = []
            for player in data:
                players.append(Player(id=player[0],
                                      name=player[1],
                                      lastname=player[2],
                                      telegram_id=player[3],
                                      birthdate=player[4],
                                      email=player[5],
                                      mobile=player[6],
                                      active=player[7],
                                      admin=player[8],
                                      team=player[9]))
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

                    SELECT id, date, type, created_by, note FROM events 
                    WHERE date = '{event_date}';
                """)
            data = cursor.fetchall()[0]
            event_kwargs = dict(id=data[0],
                                date=data[1],
                                type=data[2],
                                created_by=data[3],
                                note=data[4])

        if connection:
            connection.close()

        return Event(**event_kwargs)

    except psycopg2.Error as e:
        logging.error(e)
