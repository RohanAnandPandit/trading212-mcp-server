import os
from dotenv import load_dotenv, find_dotenv

from mcp_server import mcp
from tools import *
from prompts import *
from resources import *

load_dotenv(find_dotenv())

# This is needed if you'd like to connect to a custom client
if __name__ == "__main__":
    mcp.run(transport=os.getenv('TRANSPORT', 'stdio'))
