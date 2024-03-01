from dataclasses import dataclass
from typing import List
import yaml


@dataclass
class Settings:
    alert_channel: str
    alert_polling_interval: int
    alert_backoff_polling_interval: int
    info_channels: List[str]
    info_polling_interval: int
    timezone_name: str
    region_to_monitor: int
    analyzer_prompt: str
    webhooks: List['WebhookConfig']
    firebase_credentials_path: str
    log_level: str


@dataclass
class WebhookConfig:
    name: str
    method: str
    url: str
    query_args: List['QueryArg']
    payload: dict


@dataclass
class QueryArg:
    name: str
    value: str


def load_settings(file_path):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
        return parse_settings(config)


def parse_settings(config):
    settings = Settings(
        alert_channel=config.get('alert_channel', ''),
        alert_polling_interval=config.get('alert_polling_interval', 5),
        alert_backoff_polling_interval=config.get('alert_backoff_polling_interval', 60),
        info_channels=config.get('info_channels', []),
        info_polling_interval=config.get('info_polling_interval', 5),
        timezone_name=config.get('timezone_name', 'Europe/Kyiv'),
        region_to_monitor=config.get('region_to_monitor', 14),
        analyzer_prompt=config.get('analyzer_prompt', ''),
        webhooks=[parse_webhook(webhook) for webhook in config.get('webhooks', [])],
        firebase_credentials_path=config.get('firebase_credentials_path', '/etc/pyalerts/account.json'),
        log_level=config.get('log_level', 'INFO')
    )
    return settings


def parse_webhook(webhook):
    return WebhookConfig(
        name=webhook.get('name', ''),
        method=webhook.get('method', ''),
        url=webhook.get('url', ''),
        query_args=[parse_query_arg(arg) for arg in webhook.get('query_args', [])],
        payload=webhook.get('payload', {})
    )


def parse_query_arg(arg):
    return QueryArg(
        name=arg.get('name', ''),
        value=arg.get('value', '')
    )
