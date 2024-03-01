from typing import List
import requests
from dataclasses import dataclass
from datetime import datetime
from bs4 import BeautifulSoup, SoupStrainer


@dataclass
class Message:
    id: int
    author: str
    text: str
    date: datetime


def fetch_latest_messages(channel_name, limit=20, newer_than: datetime = None) -> List[Message]:
    url = f"https://t.me/s/{channel_name}"
    response = requests.get(url, timeout=5)
    soup = BeautifulSoup(response.content, 'html.parser', parse_only=SoupStrainer('div', attrs={'class': lambda L: 'tgme_widget_message' in L.split()}))
    messages = []
    for message_div in soup:
        id = message_div['data-post']
        author = message_div.select_one(
            '.tgme_widget_message_author span').text.strip()
        text_node = message_div.css.select_one('.tgme_widget_message_bubble > .tgme_widget_message_text')
        if text_node:
            text = text_node.get_text('\n', strip=True)
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
