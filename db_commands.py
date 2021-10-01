import psycopg2
from config import host, user, password, database


def player_by_telegram_id(telegram_id: int) -> tuple:
    """
    :param telegram_id: telegram id (int or string)
    :return: tuple (player_name, player_lastname) from "players" table
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
                    select name, lastname from players where telegram_id={telegram_id}
                """)
            player = cursor.fetchall()

        if connection:
            connection.close()

        return player[0]

    except psycopg2.Error as e:
        print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")


def event_type_by_date(date) -> str:
    """
    :param date: date in string format yyyy-mm-dd
    :return: event type: 'train' or 'game'
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
                    select type from events where date='{date}'
                """)
            event_type = cursor.fetchall()

        if connection:
            connection.close()

        return event_type[0][0]

    except psycopg2.Error as e:
        print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")


def upcoming_events() -> list:
    """
    :return: list of the events which will take place after today in format date
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
                    select date, type from events where date >= current_date order by date ASC
                """)

            events = cursor.fetchall()

        if connection:
            connection.close()

        return events

    except psycopg2.Error as e:
        print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")


def event_players(event_date: str) -> str:
    """
    :param event_date: date in string format yyyy-mm-dd
    :return: enumerated list of players' names
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
                select players.name, players.lastname, attendance.decision
                from attendance
                join players on players.id = attendance.player_id
                where attendance.event_id = (select id from events where date = '{event_date}')
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
                if player[2] == 'NO':
                    players_no += f'\n{str(num_no)}. {player[0]} {player[1]}'
                    num_no += 1

        if connection:
            connection.close()

        return f'Придут:{players_yes}\n\nПропустят:{players_no}'

    except psycopg2.Error as e:
        print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")


def active_telegram_ids() -> list:
    """
    :return: list of telegram ids of players that are marked as 'active'
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
                    select telegram_id from players where active = true
                """)
            players_raw = cursor.fetchall()
            players = []
            for player in players_raw:
                if player[0]:
                    players.append(player[0])

        if connection:
            connection.close()

        return players

    except psycopg2.Error as e:
        print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")


def check_attendance(telegram_id: int, event_date: str) -> str:
    """
    Checks if the player has already made a decision on going to the event
    :param telegram_id: telegram id
    :param event_date: date in string format yyyy-mm-dd
    :return: 'YES', 'NO' or '' (empty string)
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
                        player_id = (select id from players where telegram_id = {telegram_id})
                    and 
                        event_id = (select id from events where date = '{event_date}')
                """)
            decision = cursor.fetchall()

        if connection:
            connection.close()

        try:
            decision = decision[0][0]
            return decision
        except IndexError:
            return ''

    except psycopg2.Error as e:
        print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")


def check_admin(telegram_id: int) -> bool:
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
                    select admin from players where telegram_id = {telegram_id};
                """)
            result = cursor.fetchall()
        if connection:
            connection.close()
        return result[0][0]

    except psycopg2.Error as e:
        print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")


def add_decision(telegram_id: int, event_date: str, decision: str):
    """
    :param telegram_id: telegram id (int or string)
    :param event_date: date in string format yyyy-mm-dd
    :param decision: 'YES' or 'NO'
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
                    insert into attendance(player_id, event_id, decision)
                        values(
                            (select id from players where telegram_id = {telegram_id}),
                            (select id from events where date = '{event_date}'),
                            '{decision}'
                        )
                    on conflict (player_id, event_id) do update
                        set decision = '{decision}'
                """)
        print(f"[PostreSQL INFO]: user {telegram_id} inserted values into 'attendance': {event_date}, {decision}")

        if connection:
            connection.close()

    except psycopg2.Error as e:
        print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")


def create_event(event_date: str, event_type: str, telegram_id: int = None):
    """
    :param event_date: date in string format yyyy-mm-dd
    :param event_type: 'train' or 'game'
    :param telegram_id: 'None' or int
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
                        set type = '{event_type}'
                """)
        if telegram_id:
            print(f"[PostreSQL INFO]: user {telegram_id} created an event: {event_date}, {event_type}")

        if connection:
            connection.close()

    except psycopg2.Error as e:
        print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")


def delete_event(event_date: str, telegram_id: int = None):
    """
    :param event_date: date in string format yyyy-mm-dd
    :param telegram_id: 'None' or int
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
                    delete from events * where date = '{event_date}'
                """)
        if telegram_id:
            print(f"[PostreSQL INFO]: user {telegram_id} deleted event: {event_date}")

        if connection:
            connection.close()

    except psycopg2.Error as e:
        print(f"[PostgreSQL ERROR: {e.pgcode}]: {e}")


