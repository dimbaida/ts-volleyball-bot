import os

host = os.getenv('DB_HOST')
user = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
database = os.getenv('DB')
port = os.getenv('DB_PORT')
bot_token = os.getenv('BOT_TOKEN')
ts_bot_group_id = os.getenv('TS_GROUP_ID')

developers: list = [381956774]