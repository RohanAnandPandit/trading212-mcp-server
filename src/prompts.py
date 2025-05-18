from src.mcp_server import mcp, client


# ---- MCP Prompts ----

@mcp.prompt("analyse_trading212_data")
def analyse_trading212_data_prompt():
    """Analyse trading212 data."""
    prompt = """You are a professional financial expert analysing the user's 
    financial data using Trading212. You should be extremely cautious when 
    giving financial advice. Use the currency from the account info."""
    try:
        account_info = client.get_account_info()
    except Exception as e:
        print(f"Error fetching account info: {e}")
        return prompt

    return f"""
    {prompt}
    Currency: {account_info.currencyCode}
    """
