from dotenv import dotenv_values
import requests
config = dotenv_values(".env")


class Config():
    router_ip = config.get('ROUTER_IP', '192.168.8.1')
    username = config.get('ROUTER_USERNAME', 'admin')
    password = config.get('ROUTER_PASSWORD', 'admin')
    discord_webhook = config.get('DISCORD_WEBHOOK', '')


def send_discord_notification(message):
    if Config.discord_webhook:
        payload = {"content": message}
        try:
            requests.post(Config.discord_webhook, json=payload)
        except Exception as e:
            print(f"Failed to send Discord notification: {e}")
