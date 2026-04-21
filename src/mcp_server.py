from mcp.server.fastmcp import FastMCP
from dotenv import find_dotenv, load_dotenv
from accounts import AccountRegistry
from config import ACCOUNTS_CONFIG

load_dotenv(find_dotenv())

mcp = FastMCP(
    name="Trading212",
    dependencies=["hishel", "pydantic"],
    stateless_http=True,
    host="127.0.0.1",
    port=8000,
)

registry = AccountRegistry(config_path=ACCOUNTS_CONFIG)
