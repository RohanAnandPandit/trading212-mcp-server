import json
import os
import pytest
from unittest.mock import patch, MagicMock


def make_config(tmp_path, accounts, default):
    config = {"default": default, "accounts": accounts}
    p = tmp_path / "accounts.json"
    p.write_text(json.dumps(config))
    return str(p)


@patch("accounts.Trading212Client")
def test_loads_accounts_from_file(MockClient, tmp_path):
    path = make_config(tmp_path, [
        {"name": "sumeet", "api_key": "k1", "api_secret": "s1", "environment": "live"},
        {"name": "wife",   "api_key": "k2", "api_secret": "s2", "environment": "live"},
    ], default="sumeet")

    from accounts import AccountRegistry
    registry = AccountRegistry(config_path=path)

    assert registry.account_names() == ["sumeet", "wife"]
    assert registry.default_name() == "sumeet"
    assert MockClient.call_count == 2


@patch("accounts.Trading212Client")
def test_get_client_returns_correct_instance(MockClient, tmp_path):
    mock_sumeet = MagicMock()
    mock_wife = MagicMock()
    MockClient.side_effect = [mock_sumeet, mock_wife]

    path = make_config(tmp_path, [
        {"name": "sumeet", "api_key": "k1", "api_secret": "s1", "environment": "live"},
        {"name": "wife",   "api_key": "k2", "api_secret": "s2", "environment": "live"},
    ], default="sumeet")

    from accounts import AccountRegistry
    registry = AccountRegistry(config_path=path)

    assert registry.get_client("sumeet") is mock_sumeet
    assert registry.get_client("wife") is mock_wife


@patch("accounts.Trading212Client")
def test_get_client_raises_on_unknown_account(MockClient, tmp_path):
    path = make_config(tmp_path, [
        {"name": "sumeet", "api_key": "k1", "api_secret": "s1", "environment": "live"},
    ], default="sumeet")

    from accounts import AccountRegistry
    registry = AccountRegistry(config_path=path)

    with pytest.raises(ValueError, match="Account 'xyz' not found"):
        registry.get_client("xyz")


@patch("accounts.Trading212Client")
def test_all_clients_returns_all(MockClient, tmp_path):
    path = make_config(tmp_path, [
        {"name": "sumeet", "api_key": "k1", "api_secret": "s1", "environment": "live"},
        {"name": "wife",   "api_key": "k2", "api_secret": "s2", "environment": "live"},
    ], default="sumeet")

    from accounts import AccountRegistry
    registry = AccountRegistry(config_path=path)

    all_clients = registry.all_clients()
    assert set(all_clients.keys()) == {"sumeet", "wife"}


@patch("accounts.Trading212Client")
def test_resolve_none_returns_default(MockClient, tmp_path):
    path = make_config(tmp_path, [
        {"name": "sumeet", "api_key": "k1", "api_secret": "s1", "environment": "live"},
        {"name": "wife",   "api_key": "k2", "api_secret": "s2", "environment": "live"},
    ], default="sumeet")

    from accounts import AccountRegistry
    registry = AccountRegistry(config_path=path)

    result = registry.resolve(None)
    assert list(result.keys()) == ["sumeet"]


@patch("accounts.Trading212Client")
def test_resolve_all_returns_all_accounts(MockClient, tmp_path):
    path = make_config(tmp_path, [
        {"name": "sumeet", "api_key": "k1", "api_secret": "s1", "environment": "live"},
        {"name": "wife",   "api_key": "k2", "api_secret": "s2", "environment": "live"},
    ], default="sumeet")

    from accounts import AccountRegistry
    registry = AccountRegistry(config_path=path)

    result = registry.resolve("all")
    assert set(result.keys()) == {"sumeet", "wife"}


@patch("accounts.Trading212Client")
def test_resolve_string_returns_named_account(MockClient, tmp_path):
    path = make_config(tmp_path, [
        {"name": "sumeet", "api_key": "k1", "api_secret": "s1", "environment": "live"},
        {"name": "wife",   "api_key": "k2", "api_secret": "s2", "environment": "live"},
    ], default="sumeet")

    from accounts import AccountRegistry
    registry = AccountRegistry(config_path=path)

    result = registry.resolve("wife")
    assert list(result.keys()) == ["wife"]


@patch("accounts.Trading212Client")
def test_resolve_list_returns_subset(MockClient, tmp_path):
    path = make_config(tmp_path, [
        {"name": "sumeet", "api_key": "k1", "api_secret": "s1", "environment": "live"},
        {"name": "wife",   "api_key": "k2", "api_secret": "s2", "environment": "live"},
        {"name": "son",    "api_key": "k3", "api_secret": "s3", "environment": "demo"},
    ], default="sumeet")

    from accounts import AccountRegistry
    registry = AccountRegistry(config_path=path)

    result = registry.resolve(["wife", "son"])
    assert set(result.keys()) == {"wife", "son"}


@patch("accounts.Trading212Client")
def test_fallback_to_env_vars_when_no_config_file(MockClient):
    with patch.dict(os.environ, {
        "TRADING212_API_KEY": "envkey",
        "TRADING212_API_SECRET": "envsecret",
        "ENVIRONMENT": "live",
    }):
        from accounts import AccountRegistry
        registry = AccountRegistry(config_path="/nonexistent/path/accounts.json")

    assert registry.default_name() == "default"
    assert "default" in registry.account_names()
    MockClient.assert_called_once_with(
        api_key="envkey", api_secret="envsecret", environment="live"
    )


def test_raises_when_no_config_and_no_env_vars():
    with patch.dict(os.environ, {}, clear=True):
        for key in ["TRADING212_API_KEY", "TRADING212_API_SECRET"]:
            os.environ.pop(key, None)

        from accounts import AccountRegistry
        with pytest.raises(ValueError, match="No accounts configured"):
            AccountRegistry(config_path="/nonexistent/path/accounts.json")
