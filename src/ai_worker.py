import os
import json
import logging
from dataclasses import dataclass
from collections import deque
from threading import Lock
from typing import List
from openai import OpenAI
from pytz import timezone
from telegram import Message
from message_bus import message_bus
from config import Settings

logger = logging.getLogger(__name__)


@dataclass
class AiAlert:
    alert: bool
    attacker: str = "UNKNOWN"
    text: str = None
    confidence: float = None
    original_text: str = None

    @staticmethod
    def from_dict(data: dict):
        return AiAlert(
            alert=data.get('alert'),
            attacker=data.get('attacker', "UNKNOWN"),
            text=data.get('text', "<No text>"),
            confidence=data.get('confidence', 0.0),
            original_text=data.get('original_text', "<No original text>"),
        )


class AiWorker:
    def __init__(self, settings: Settings):
        self.history = deque(maxlen=10)
        self.state_lock = Lock()
        self.ai_enabled = False
        self.system_prompt = settings.analyzer_prompt
        self.target_timezone = timezone(settings.timezone_name)
        self.chatgpt_api = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

    def start(self):
        message_bus.subscribe('new_messages', self.process_messages)
        message_bus.subscribe('alert', self.process_alert_event)
        message_bus.subscribe('clear', self.process_clear_event)

    def process_alert_event(self, _):
        with self.state_lock:
            self.history.clear()
            self.ai_enabled = True
            logger.debug("AI analyzer enabled")

    def process_clear_event(self, _):
        with self.state_lock:
            self.history.clear()
            self.ai_enabled = False
            logger.debug("AI analyzer disabled")

    def process_messages(self, messages: List[Message]):
        with self.state_lock:
            if not self.ai_enabled:
                return

        for message in messages:
            self.history.append(message)

        system_messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        user_messages = [
            {"role": "user", "content": f"{msg.date.astimezone(self.target_timezone).time()} {msg.author}: {msg.text}"} for msg in self.history
        ]
        debug_messages = "\n".join([msg['content'] for msg in user_messages])
        logger.debug(f"Sending messages to AI: \n{debug_messages}")
        try:
            ai_response = self.chatgpt_api.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=system_messages + user_messages,
                temperature=0.1,
            )
            response = json.loads(ai_response.choices[0].message.content)
            ai_response = AiAlert.from_dict(response)
            if ai_response.alert:
                message_bus.publish('ai_alert', ai_response)
        except Exception as e:
            logger.error(f"Error processing messages with AI: {e}")
