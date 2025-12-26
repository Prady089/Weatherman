#!/usr/bin/env python3
import os
import sys
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# =========================
# CONFIG
# =========================
LAT = float(os.getenv("LAT", "33.1546624"))
LON = float(os.getenv("LON", "-96.7180288"))
CITY = os.getenv("CITY", "McKinney")
UNITS = os.getenv("UNITS", "metric")  # metric -> °C, imperial -> °F
TZ = ZoneInfo(os.getenv("TZ", "America/Chicago"))

# Time blocks (local hours)
BLOCKS = [
    ("🌅", "Morning", range(5, 11)),   # 5-10
    ("🌞", "Noon",    range(11, 16)),  # 11-15
    ("🌆", "Evening", range(16, 20)),  # 16-19
    ("🌙", "Night",   range(20, 24)),  # 20-23
]

# =========================
# ENV VARS
# =========================
OW_KEY = os.getenv("OPENWEATHER_API_KEY")
PUSH_TOKEN = os.getenv("PUSHOVER_TOKEN")
PUSH_USER = os.getenv("PUSHOVER_USER")

OPENAI_KEY = os.getenv("OPENAI_API_KEY")  # optional
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # optional

if not OW_KEY or not PUSH_TOKEN or not PUSH_USER:
    print("❌ Missing env vars. Need OPENWEATHER_API_KEY, PUSHOVER_TOKEN, PUSHOVER_USER.")
    sys.exit(1)

def send_push(title: str, message: str, priority: int = 0):
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

def ow_onecall():
    url = (
        "https://api.openweathermap.org/data/3.0/onecall"
        f"?lat={LAT}&lon={LON}&exclude=minutely,daily&units={UNITS}&appid={OW_KEY}"
    )
    r = requests.get(url, timeout=20)
    data = r.json()
    if r.status_code != 200:
        raise RuntimeError(f"OpenWeather HTTP {r.status_code}: {data}")
    if "hourly" not in data:
        raise RuntimeError(f"OpenWeather response missing hourly: {data}")
    return data

def fmt_temp(x: float) -> str:
    return f"{round(x)}°"

def dash_range(min_v, max_v) -> str:
    # use en dash –
    if min_v is None or max_v is None:
        return "--"
    lo = round(min_v)
    hi = round(max_v)
    return f"{lo}–{hi}°" if lo != hi else f"{lo}°"

def pick_icon_desc(current):
    desc = current.get("weather", [{}])[0].get("description", "").strip()
    if desc:
        # Capitalize first letter only
        return desc[:1].upper() + desc[1:]
    return "Weather"

def ai_insight_or_rules(facts: dict) -> str:
    """
    Return ONE practical line. If OPENAI_API_KEY exists, use it.
    Otherwise, use rule-based insight.
    """
    # Rule-based fallback
    def rules():
        swing = facts["high"] - facts["low"]
        rain = facts["rain_pct"]
        if rain >= 60:
            return "Rain likely today—keep an umbrella handy."
        if rain >= 30:
            return "Some chance of rain—good to be prepared."
        if swing >= 10:
            return "Big temperature swing—dress in layers."
        if facts["high"] >= 32:
            return "Hot day—hydrate and avoid peak sun."
        if facts["low"] <= 5:
            return "Cold periods—bundle up, especially at night."
        return "Looks like a fairly typical day—stay comfortable."

    if not OPENAI_KEY:
        return rules()

    # OpenAI call (optional)
    try:
        prompt = (
            "Write ONE short, practical weather tip (max 90 characters). "
            "No emojis. No quotes. No extra sentences.\n\n"
            f"City: {facts['city']}\n"
            f"Now: {facts['now']}°, {facts['desc']}\n"
            f"High: {facts['high']}°, Low: {facts['low']}°\n"
            f"Rain chance: {facts['rain_pct']}%\n"
        )

        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_KEY}"},
            json={
                "model": OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": "You are concise and practical."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.4,
                "max_tokens": 60,
            },
            timeout=25,
        )
        out = r.json()
        if r.status_code != 200:
            print("⚠️ OpenAI error:", r.status_code, out)
            return rules()
        text = out["choices"][0]["message"]["content"].strip()
        # force single line
        return " ".join(text.split())[:90]
    except Exception as e:
        print("⚠️ OpenAI exception:", e)
        return rules()

def main():
    data = ow_onecall()

    current = data.get("current", {})
    hourly = data["hourly"]  # next 48

    now_temp = current.get("temp", hourly[0].get("temp"))
    desc = pick_icon_desc(current)

    # High/low from next 24 hours
    next24 = hourly[:24]
    temps24 = [h.get("temp") for h in next24 if h.get("temp") is not None]
    high = round(max(temps24)) if temps24 else round(now_temp)
    low = round(min(temps24)) if temps24 else round(now_temp)

    # Rain %: max POP next 24 hours (0..1)
    pops = [h.get("pop", 0) for h in next24 if isinstance(h.get("pop", 0), (int, float))]
    rain_pct = round(100 * max(pops)) if pops else 0

    # Build block ranges
    # Group hourly by local hour
    block_ranges = []
    for emoji, _, hours in BLOCKS:
        block_temps = []
        for h in next24:
            ts = h.get("dt")
            if not ts:
                continue
            local_hour = datetime.fromtimestamp(ts, TZ).hour
            if local_hour in hours:
                t = h.get("temp")
                if t is not None:
                    block_temps.append(t)
        if block_temps:
            block_ranges.append((emoji, dash_range(min(block_temps), max(block_temps))))
        else:
            block_ranges.append((emoji, "--"))

    # Facts for AI/rules
    facts = {
        "city": CITY,
        "now": round(now_temp),
        "desc": desc,
        "high": high,
        "low": low,
        "rain_pct": rain_pct,
    }
    insight = ai_insight_or_rules(facts)

    # Compact layout
    # Line 1: header
    # Line 2: now + desc
    # Line 3: hi/low + rain
    # Line 4-5: emoji ranges
    line4 = f"{block_ranges[0][0]} {block_ranges[0][1]:<7}   {block_ranges[1][0]} {block_ranges[1][1]}"
    line5 = f"{block_ranges[2][0]} {block_ranges[2][1]:<7}   {block_ranges[3][0]} {block_ranges[3][1]}"

    message = (
        f"🌤️ Today – {CITY}\n\n"
        f"🧠 {insight}\n\n"
        f"{fmt_temp(now_temp)}  {desc}\n"
        f"⬆{high}° ⬇{low}°   🌧{rain_pct}%\n\n"
        f"{line4}\n"
        f"{line5}"
    )

    send_push("Daily Weather", message, priority=0)

if __name__ == "__main__":
    main()
