import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

TRANSPORT = os.getenv("TRANSPORT", "stdio")
ACCOUNTS_CONFIG = os.getenv("ACCOUNTS_CONFIG", "accounts.json")
