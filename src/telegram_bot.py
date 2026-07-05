
import requests
import time
from config.config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID


def escape_markdown(text):
    """Escape Markdown special characters for Telegram"""
    if text is None:
        return ""
    text = str(text)
    # List of Markdown characters to escape: \ ` * _ { } [ ] ( ) # + - . !
    escape_chars = r'\`*_{}[]()#+-.!'
    for char in escape_chars:
        text = text.replace(char, f"\\{char}")
    return text


class TelegramBot:
    def __init__(self):
        self.token = TELEGRAM_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.active_bet = None
        self.last_error_time = 0  # For rate limiting error messages
        self.error_cooldown = 300  # 5 minutes cooldown between error alerts

    def send_message(self, text):
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        params = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def send_error(self, error_msg):
        """Send an error alert to Telegram, with rate limiting"""
        current_time = time.time()
        if current_time - self.last_error_time < self.error_cooldown:
            print(f"Error (not sending to Telegram due to cooldown): {error_msg}")
            return
        
        try:
            message = f"⚠️ Predictor Bot Error:\n{escape_markdown(error_msg)}"
            self.send_message(message)
            self.last_error_time = current_time
            print(f"Sent error alert to Telegram: {error_msg}")
        except Exception as e:
            print(f"Failed to send error alert to Telegram: {e}")

    def send_alert(self, pick):
        sport_emoji = "⚽" if pick["sport"] == "Soccer" else "🏀"
        message = f"""NEW TIPSTER PICK 🎯
{sport_emoji} Sport: {escape_markdown(pick['sport'])}
🏆 League: {escape_markdown(pick['league'])}
Match: {escape_markdown(pick['home'])} vs {escape_markdown(pick['away'])}
Score: {escape_markdown(pick['score'])} (Time: {escape_markdown(pick['time'])}')
Prediction Type: {escape_markdown(pick['prediction_type'])}
Prediction: {escape_markdown(pick['prediction'])}
Odds: {escape_markdown(pick['odds'])}
📉 Drop Line: Yes
Bot is now tracking this match until settlement. No new picks will be made until this bet concludes!"""
        self.send_message(message)
        self.active_bet = pick["event_id"]

    def has_active_bet(self):
        return self.active_bet is not None

    def clear_active_bet(self):
        self.active_bet = None

