
from src.inforadar_api import get_live_games, get_prematch_games, get_game_odds


class Predictor:
    def __init__(self):
        self.odds_history = {}

    def is_in_timing_window(self, game, sport_id):
        time_data = game.get("time", {})
        if sport_id == 1:
            tm = time_data.get("tm", 0)
            md = time_data.get("md", 0)
            if (md == 0 and 10 <= tm <= 20) or (md == 1 and 10 <= tm <= 20):
                return True
        return False

    def update_odds_history(self, event_id, odds_data):
        if event_id not in self.odds_history:
            self.odds_history[event_id] = []
        self.odds_history[event_id].append(odds_data)
        if len(self.odds_history[event_id]) > 20:
            self.odds_history[event_id].pop(0)

    def check_odds_drop(self, event_id, current_odds):
        if event_id not in self.odds_history:
            return False, None, None, None
        history = self.odds_history[event_id]
        if not history:
            return False, None, None, None
        for market in current_odds:
            market_name = market.get("name")
            if market_name not in ["1X2", "Total"]:
                continue
            rows_names = market.get("rowsNames", [])
            odds_snapshots = market.get("odds", [])
            if not odds_snapshots:
                continue
            latest_snapshot = odds_snapshots[0]
            
            if market_name == "Total":
                # Check the total line (row2) to exclude Asian lines (2.25, 2.75, etc.)
                total_line = latest_snapshot.get("row2")
                if total_line is not None:
                    # Try to convert to float if it's a string
                    try:
                        total_line = float(total_line)
                    except (ValueError, TypeError):
                        continue  # Skip if we can't parse the line
                    # Only accept lines where the decimal part is 0 or 0.5
                    decimal_part = total_line % 1
                    if not (decimal_part == 0 or decimal_part == 0.5):
                        continue  # Skip Asian lines like 2.25, 2.75
                candidates = [
                    (rows_names[0], latest_snapshot.get("row1"), total_line),
                    (rows_names[2], latest_snapshot.get("row3"), total_line)
                ]
            elif market_name == "1X2":
                candidates = [
                    (rows_names[0], latest_snapshot.get("row1"), None),
                    (rows_names[1], latest_snapshot.get("row2"), None),
                    (rows_names[2], latest_snapshot.get("row3"), None)
                ]
            else:
                continue
            for pred_label, current_odd, line in candidates:
                if current_odd and 1.5 <= current_odd <= 2.0:
                    for hist_odds in history:
                        for hist_market in hist_odds:
                            if hist_market.get("name") != market_name:
                                continue
                            hist_snapshots = hist_market.get("odds", [])
                            for hist_snap in hist_snapshots:
                                if market_name == "Total":
                                    hist_candidates = [
                                        hist_snap.get("row1"),
                                        hist_snap.get("row3")
                                    ]
                                else:
                                    hist_candidates = [
                                        hist_snap.get("row1"),
                                        hist_snap.get("row2"),
                                        hist_snap.get("row3")
                                    ]
                                for hist_odd in hist_candidates:
                                    if hist_odd and hist_odd >= 4.0:
                                        # Format prediction with line if it's Total
                                        full_prediction = pred_label
                                        if market_name == "Total" and line is not None:
                                            full_prediction = f"{pred_label} {line}"
                                        return True, market_name, full_prediction, current_odd
        return False, None, None, None

    def filter_picks(self, sport_id):
        picks = []
        # Check only live games
        for game_type, get_games in [("live", get_live_games)]:
            print(f"Getting {game_type} games for sport {sport_id}...", flush=True)
            games_response = get_games(sport_id)
            if not games_response or games_response.get("success") != 1:
                print(f"Failed to get games for sport {sport_id}!", flush=True)
                continue
            games = games_response.get("results", [])
            print(f"Got {len(games)} {game_type} games for sport {sport_id}", flush=True)
            for game in games:
                event_id = game.get("id")
                home = game.get("home", {}).get("name", "Unknown")
                away = game.get("away", {}).get("name", "Unknown")
                print(f"Checking game {event_id}: {home} vs {away}", flush=True)
                if not event_id:
                    continue
                try:
                    odds_data = get_game_odds(sport_id, event_id)
                    print(f"Got odds data for {home} vs {away}: {len(odds_data) if odds_data else 0} markets", flush=True)
                except Exception as e:
                    print(f"Error getting odds for {home} vs {away}: {e}", flush=True)
                    continue
                self.update_odds_history(event_id, odds_data)
                # For prematch games, skip timing window check
                if game_type == "live" and not self.is_in_timing_window(game, sport_id):
                    print(f"Game {home} vs {away} not in timing window, skipping", flush=True)
                    continue
                drop_detected, pred_type, prediction, odds = self.check_odds_drop(event_id, odds_data)
                print(f"Drop detected for {home} vs {away}: {drop_detected} (odds: {odds})", flush=True)
                if drop_detected and 1.7 <= odds <= 2.2:
                    home_team = game.get("home", {}).get("name", "Unknown")
                    away_team = game.get("away", {}).get("name", "Unknown")
                    league = game.get("league", {}).get("name", "Unknown")
                    score = game.get("scores", "Not started")
                    if score is None:
                        score = "Not started"
                    time_data = game.get("time", {})
                    time_str = str(time_data.get("tm", 0)) if game_type == "live" else "Prematch"
                    pick = {
                        "sport": "Soccer" if sport_id == 1 else "Basketball",
                        "league": league,
                        "home": home_team,
                        "away": away_team,
                        "score": score,
                        "time": time_str,
                        "prediction_type": pred_type,
                        "prediction": prediction,
                        "odds": odds,
                        "event_id": event_id
                    }
                    picks.append(pick)
        return picks

