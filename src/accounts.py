import json
import os
from typing import Union
from utils.client import Trading212Client


class AccountRegistry:
    def __init__(self, config_path: str = None):
        config_path = config_path or os.getenv("ACCOUNTS_CONFIG", "accounts.json")
        self._clients: dict[str, Trading212Client] = {}
        self._default: str = None

        if os.path.exists(config_path):
            self._load_from_file(config_path)
        else:
            self._load_from_env()

    def _load_from_file(self, config_path: str) -> None:
        with open(config_path) as f:
            config = json.load(f)

        self._default = config["default"]
        for account in config["accounts"]:
            self._clients[account["name"]] = Trading212Client(
                api_key=account["api_key"],
                api_secret=account["api_secret"],
                environment=account["environment"],
            )

    def _load_from_env(self) -> None:
        api_key = os.getenv("TRADING212_API_KEY")
        api_secret = os.getenv("TRADING212_API_SECRET")
        environment = os.getenv("ENVIRONMENT", "demo")

        if not api_key or not api_secret:
            raise ValueError(
                "No accounts configured. Create accounts.json or set "
                "TRADING212_API_KEY and TRADING212_API_SECRET."
            )

        self._clients = {
            "default": Trading212Client(
                api_key=api_key, api_secret=api_secret, environment=environment
            )
        }
        self._default = "default"

    def get_client(self, name: str) -> Trading212Client:
        if name not in self._clients:
            available = ", ".join(self._clients.keys())
            raise ValueError(
                f"Account '{name}' not found. Available accounts: {available}"
            )
        return self._clients[name]

    def get_clients(self, names: list[str]) -> dict[str, Trading212Client]:
        return {name: self.get_client(name) for name in names}

    def all_clients(self) -> dict[str, Trading212Client]:
        return dict(self._clients)

    def account_names(self) -> list[str]:
        return list(self._clients.keys())

    def default_name(self) -> str:
        return self._default

    def resolve(self, account: Union[str, list[str], None]) -> dict[str, Trading212Client]:
        if account is None:
            return {self._default: self._clients[self._default]}
        if account == "all":
            return self.all_clients()
        if isinstance(account, list):
            return self.get_clients(account)
        return {account: self.get_client(account)}
