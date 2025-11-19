# import logging
#
# logger = logging.getLogger(__name__)
#
#
# class WhatsAppService:
#     def __init__(self):
#         # Initialize your WhatsApp service here (Twilio, etc.)
#         self.is_configured = False
#
#     @staticmethod
#     async def send_message(phone_number: str, message: str) -> bool:
#         """
#         Send WhatsApp message immediately
#         """
#         try:
#             # Implementation for your WhatsApp provider
#             # Example for Twilio:
#             # from twilio.rest import Client
#             # client = Client(account_sid, auth_token)
#             # message = client.messages.create(
#             #     body=message,
#             #     from_='whatsapp:+14155238886',
#             #     to=f'whatsapp:{phone_number}'
#             # )
#
#             logger.info(f"📱 WhatsApp message sent to {phone_number}: {message}")
#             return True
#         except Exception as e:
#             logger.error(f"Failed to send WhatsApp message: {e}")
#             return False
#
#
# whatsapp_service = WhatsAppService()
#
# # WhatsApp service functions (placeholder - implement based on your WhatsApp provider)
# async def send_whatsapp_message(phone_number: str, message: str, task_id: int):
#     """
#     Send immediate WhatsApp message
#     Implement this based on your WhatsApp provider (Twilio, etc.)
#     """
#     print(f"📱 Sending WhatsApp to {phone_number}: {message}")
#     # Implementation for Twilio/WhatsApp Business API would go here
#     # For now, we'll just log it
#     return True


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
        """
        Send a WhatsApp template message (hello_world)
        phone_number: recipient phone number
        message: dynamic text (but template must support variables)
        """

        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "template",
            "template": {
                "name": "hello_world",
                "language": {"code": "en_US"}
            }
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
async def send_whatsapp_message(phone_number: str, message: str, task_id: int):
    logger.info(f"📨 Sending WhatsApp (task_id={task_id}) → {phone_number}")
    return await whatsapp_service.send_message(phone_number, message)
