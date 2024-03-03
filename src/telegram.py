from typing import List
import requests
from dataclasses import dataclass
from datetime import datetime
from bs4 import BeautifulSoup, SoupStrainer
import app_logger

logger = app_logger.get(__name__)

@dataclass
class Message:
    id: int
    author: str
    text: str
    date: datetime


def fetch_latest_messages(channel_name, limit=20, newer_than: datetime = None, stop_list: List[str] = []) -> List[Message]:
    url = f"https://t.me/s/{channel_name}"
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.content, 'html.parser', parse_only=SoupStrainer('div', attrs={'class': lambda L: 'tgme_widget_message' in L.split()}))
        messages = []
        for message_div in soup:
            id = message_div['data-post']
            author = channel_name
            text_node = message_div.css.select_one('.tgme_widget_message_bubble > .tgme_widget_message_text')
            if text_node:
                stripped_strings = text_node.stripped_strings
                text = ' '.join([s for s in stripped_strings if s not in stop_list])
            else:
                continue
            date_str = message_div.select_one(
                '.tgme_widget_message_footer time[datetime]')['datetime']
            date = datetime.fromisoformat(date_str)
            message = Message(id=id, author=author, text=text, date=date)
            if newer_than and message.date < newer_than:
                continue
            messages.append(message)
        return messages[-limit:]
    except Exception as e:
        logger.error(f"Error fetching messages from {channel_name}: {e}")
        return []
