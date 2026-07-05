
import sys
import os
import threading
import time
from flask import Flask
from src.predictor import Predictor
from src.telegram_bot import TelegramBot, escape_markdown
from src.inforadar_api import get_finished_games

# Add the project directory to Python's path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Create a simple Flask app for UptimeRobot to ping
app = Flask(__name__)

@app.route('/')
def home():
    return "Predictor Bot is running!"

def run_flask():
    """Run the Flask server in a background thread"""
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

def main():
    # Start Flask server in background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    predictor = Predictor()
    telegram_bot = TelegramBot()

    print("Bot started! Monitoring matches... Press Ctrl+C to stop.")
    # Send a test message to confirm bot is running
    try:
        telegram_bot.send_message("✅ Predictor Bot has started! Monitoring soccer and basketball matches for picks...")
    except Exception as e:
        print(f"Failed to send startup test message: {e}")

    try:
        while True:
            try:
                if telegram_bot.active_bet:
                    for sport_id in [1, 18]:
                        try:
                            finished_response = get_finished_games(sport_id)
                            if finished_response and finished_response.get("success") == 1:
                                finished_games = finished_response.get("results", [])
                                for game in finished_games:
                                    if game.get("id") == telegram_bot.active_bet:
                                        home_team = game.get("home", {}).get("name", "Unknown")
                                        away_team = game.get("away", {}).get("name", "Unknown")
                                        telegram_bot.send_message(f"Bet on {escape_markdown(home_team)} vs {escape_markdown(away_team)} has settled!")
                                        telegram_bot.clear_active_bet()
                                        break
                                if not telegram_bot.active_bet:
                                    break
                        except Exception as e:
                            error_msg = f"Error checking finished games (sport {sport_id}): {str(e)}"
                            print(error_msg)
                            telegram_bot.send_error(error_msg)
                            continue

                if not telegram_bot.has_active_bet():
                    for sport_id in [1, 18]:
                        try:
                            picks = predictor.filter_picks(sport_id)
                            if picks:
                                telegram_bot.send_alert(picks[0])
                                break
                        except Exception as e:
                            error_msg = f"Error checking picks (sport {sport_id}): {str(e)}"
                            print(error_msg)
                            telegram_bot.send_error(error_msg)
                            continue

            except Exception as e:
                error_msg = f"Main loop error: {str(e)}"
                print(error_msg)
                telegram_bot.send_error(error_msg)

            time.sleep(60)
    except KeyboardInterrupt:
        print("\nBot stopped by user.")
        try:
            telegram_bot.send_message("🛑 Predictor Bot has been stopped by user.")
        except Exception as e:
            print(f"Failed to send shutdown message: {e}")


if __name__ == "__main__":
    main()
