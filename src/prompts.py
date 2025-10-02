from textwrap import dedent
from mcp_server import mcp, client


# ---- MCP Prompts ----


@mcp.prompt("analyse_trading212_data")
def analyse_trading212_data_prompt():
    """Analyse trading212 data."""

    prompt = dedent(
        """You are a professional financial expert analysing the user's 
    financial data using Trading212. You should be extremely cautious when 
    giving financial advice. Use the currency from the account info if the currency of the instrument is not given.
    
    Special currency codes:
    GBX represents pence (p) which is 1/100 of a British Pound Sterling (GBP)
    """
    )

    try:
        account_info = client.get_account_info()
    except Exception as e:
        print(f"Error fetching account info: {e}")
        return prompt

    return dedent(
        f"""
    {prompt}
    Currency: {account_info.currencyCode}
    """
    )
