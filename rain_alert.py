#!/usr/bin/env python3
import os
import sys
import json
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# ================= CONFIG =================
LAT = float(os.getenv("LAT", "33.1546624"))
LON = float(os.getenv("LON", "-96.7180288"))
CITY = os.getenv("CITY", "McKinney")
TZ = ZoneInfo(os.getenv("TZ", "America/Chicago"))
UNITS = "metric"

OW_KEY = os.getenv("OPENWEATHER_API_KEY")
PUSH_TOKEN = os.getenv("PUSHOVER_TOKEN")
PUSH_USER = os.getenv("PUSHOVER_USER")

STATE_FILE = ".state/alert_state.json"

QUIET_START = 23  # 11 PM
QUIET_END = 6     # 6 AM

# Cold thresholds (Celsius)
# Ordered LOW → HIGH importance (we'll reverse when checking)
COLD_THRESHOLDS = [
    (15, "🧥 Cool Weather Alert", "A light jacket may be useful."),
    (10, "❄️ Cold Weather Alert", "Dress warmly if heading out."),
    (5,  "🧊 Very Cold Alert", "Cold conditions expected. Bundle up."),
    (0,  "🥶 Freezing Alert", "Risk of frost or icy surfaces."),
]

# ================= GUARDS =================
if not OW_KEY or not PUSH_TOKEN or not PUSH_USER:
    print("❌ Missing required environment variables")
    sys.exit(1)

# ================= HELPERS =================
def is_quiet_hours(hour: int) -> bool:
    return QUIET_START <= hour or hour < QUIET_END

def send_push(title, message, priority=1):
    r = requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": PUSH_TOKEN,
            "user": PUSH_USER,
            "title": title,
            "message": message,
            "priority": priority,
        },
        timeout=20,
    )
    print("Pushover:", r.status_code, r.text)

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {
        "rain_alerted": False,
        "last_feels_like": None
    }

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def crossed(prev, curr, threshold):
    """
    True only if temperature crossed BELOW the threshold
    """
    return prev is not None and prev > threshold >= curr

# ================= FETCH WEATHER =================
url = (
    "https://api.openweathermap.org/data/3.0/onecall"
    f"?lat={LAT}&lon={LON}&exclude=daily&units={UNITS}&appid={OW_KEY}"
)

data = requests.get(url, timeout=20).json()
now = datetime.now(TZ)
hour = now.hour

state = load_state()

# ================= 🌧️ RAIN ALERT =================
rain_soon = False
rain_time = None

for h in data.get("hourly", [])[:2]:
    if "rain" in h or any(w["main"].lower() == "rain" for w in h.get("weather", [])):
        rain_soon = True
        rain_time = datetime.fromtimestamp(h["dt"], TZ).strftime("%-I:%M %p")
        break

if rain_soon and not state["rain_alerted"]:
    send_push(
        "🌧️ Rain Alert",
        f"Rain expected around {rain_time}.\nTake an umbrella ☔",
        priority=1
    )
    state["rain_alerted"] = True

if not rain_soon:
    state["rain_alerted"] = False

# ================= ❄️ COLD ALERTS (FIXED LOGIC) =================
current_temp = round(data["current"]["temp"])
current_feels = round(data["current"]["feels_like"])
last_feels = state.get("last_feels_like")

alert_to_send = None

# Check most severe thresholds first
for threshold, title, advice in sorted(COLD_THRESHOLDS, reverse=True):
    if crossed(last_feels, current_feels, threshold):
        alert_to_send = (threshold, title, advice)
        break  # ONLY ONE alert per run

if alert_to_send:
    threshold, title, advice = alert_to_send

    # Quiet hours suppression (except freezing)
    if not (is_quiet_hours(hour) and threshold > 0):
        message = (
            f"Current: {current_temp}°C\n"
            f"Feels like: {current_feels}°C\n\n"
            f"{advice}"
        )

        send_push(
            title,
            message,
            priority=2 if threshold <= 0 else 1
        )

# Update state
state["last_feels_like"] = current_feels
save_state(state)

print("✅ Rain + cold alert check complete")
