from mcp.server.fastmcp import FastMCP
from dotenv import find_dotenv, load_dotenv
from utils.client import Trading212Client

load_dotenv(find_dotenv())

mcp = FastMCP(name="Trading212", 
              dependencies=["hishel", "pydantic"], 
              stateless_http=True, 
              host="127.0.0.1", 
              port=8000)

client = Trading212Client()
