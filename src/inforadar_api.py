import requests
import time
import random

BASE_URL = "https://inforadar.live/api/v1/"

# Polite User-Agent to identify our bot
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
}

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds between retries
MIN_DELAY_BETWEEN_CALLS = 0.5  # minimum random delay between API calls
MAX_DELAY_BETWEEN_CALLS = 1.5  # maximum random delay between API calls

# Track last call time to add delays
_last_call_time = 0


def _add_random_delay():
    """Add a small random delay between API calls to avoid detection"""
    global _last_call_time
    current_time = time.time()
    time_since_last_call = current_time - _last_call_time
    if time_since_last_call < MIN_DELAY_BETWEEN_CALLS:
        # Add random delay
        delay = random.uniform(MIN_DELAY_BETWEEN_CALLS, MAX_DELAY_BETWEEN_CALLS)
        time.sleep(delay)
    _last_call_time = time.time()


def _make_api_request(url, params):
    """Make an API request with retries for transient errors"""
    _add_random_delay()
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, params=params, headers=HEADERS, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt == MAX_RETRIES - 1:
                # Last attempt, re-raise the error
                raise
            print(f"API request failed (attempt {attempt+1}/{MAX_RETRIES}): {e}")
            time.sleep(RETRY_DELAY * (attempt + 1))  # Exponential backoff


def get_live_games(sport_id, page=1, per_page=500):
    url = f"{BASE_URL}live_games/"
    params = {"sport_id": sport_id, "page": page, "per_page": per_page}
    return _make_api_request(url, params)


def get_prematch_games(sport_id, page=1, per_page=500):
    url = f"{BASE_URL}prematch_games/"
    params = {"sport_id": sport_id, "page": page, "per_page": per_page}
    return _make_api_request(url, params)


def get_finished_games(sport_id, page=1, per_page=50):
    url = f"{BASE_URL}finished_games/"
    params = {"sport_id": sport_id, "page": page, "per_page": per_page}
    return _make_api_request(url, params)


def get_game_odds(sport_id, event_id):
    if sport_id == 1:
        sport = "soccer"
    elif sport_id == 18:
        sport = "basketball"
    else:
        raise ValueError(f"Unsupported sport_id: {sport_id}")
    url = f"{BASE_URL}{sport}/game/odds"
    params = {"event_id": event_id, "odds_market": "8,5,6,1,2,3"}
    return _make_api_request(url, params)
