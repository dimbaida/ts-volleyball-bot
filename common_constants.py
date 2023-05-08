import os
import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB = os.getenv('DB')
DB_PORT = os.getenv('DB_PORT')
BOT_TOKEN = os.getenv('BOT_TOKEN')
TS_GROUP_ID = os.getenv('TS_GROUP_ID')
MASTER_TG_ID = os.getenv('MASTER_TG_ID')

ICONS = {
    'train': '\U0001F3D0',
    'game': '\U0001F3C5',
    'yes': '\U00002705',
    'no': '\U0000274C',
    'right_arrow': '\U0000279C',
    'party': '\U0001F389'}
