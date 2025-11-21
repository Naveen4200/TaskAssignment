import logging
import json
import requests

logger = logging.getLogger(__name__)


class WhatsAppService:
    def __init__(self):
        # Your WhatsApp Cloud API configuration
        self.phone_number_id = "803242889549753"  # STATIC for now
        self.access_token = (
            "EAATjVTKVX4sBP800DSRIUPxod8ETNK6XaQwzEKQzcmPVX0A6gl1WNIjjxFZCoZ"
            "CN1fGLBVN7TuXxHpZCN3CTT2WVejhyfMDBybYveDVKVPKLT5egq4EWdee7M7Ho3jza1jra"
            "jlXvjFwBJu5jsk6QFNc6VuZAdxVf0RpOHfDn4QKEOChWxQTOwVqwZCrh77i6Vpv8aKinyox"
            "BHf4wtfMwWvUT0YrSZBpuUkmsHpLX2JZAy7aL5ZCyG5oJFgZDZD"
        )

        self.url = f"https://graph.facebook.com/v19.0/{self.phone_number_id}/messages"

    async def send_message(self, phone_number: str, message: str) -> bool:

        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "text",
            "text": {"body": message}
        }

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        try:
            res = requests.post(self.url, headers=headers, data=json.dumps(payload))
            logger.info(f"WhatsApp API Status: {res.status_code}")
            logger.info(f"Response: {res.json()}")

            return res.status_code == 200

        except Exception as e:
            logger.error(f"WhatsApp send_message error: {e}")
            return False


whatsapp_service = WhatsAppService()


# Wrapper function you can call anywhere
async def send_whatsapp_message(phone_number: str, message: str):
    return await whatsapp_service.send_message(phone_number, message)
