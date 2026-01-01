🌦️ Weatherman

Smart Weather Alerts & Static Daily Dashboard

Weatherman is a personal, automation-driven weather intelligence system designed to deliver high-signal weather alerts and a clean daily weather overview without noise, polling, or unreliable client-side logic.

Unlike traditional weather apps that constantly push updates, Weatherman focuses on:

Event-based alerts

Human-centric thresholds

Reliability over interactivity

Static rendering for zero runtime failures

🎯 Project Goals

This project was built to answer a simple question:

“How can I get only the weather alerts that actually matter to me, without being spammed?”

Key goals:

Avoid notification fatigue

Alert only when weather crosses meaningful thresholds

Respect sleep hours (quiet hours)

Provide a visual context only when needed

Keep infrastructure simple, cheap, and reliable

✨ Core Features
🌧️ Rain Alerts

Detects rain expected soon (near-term forecast)

Fires once per rain event

Automatically resets after rain passes

Prevents repeated notifications for the same event

Example:

🌧️ Rain Alert
Rain expected around 6:40 PM.
Take an umbrella ☔

❄️ Smart Cold Weather Alerts (Threshold-Based)

Cold alerts trigger only when temperature crosses below a defined threshold, not merely because it is cold.

Temperature thresholds (Celsius):
Threshold	Meaning	Alert Type
≤ 15°C	Cool weather	Informational
≤ 10°C	Cold	Notice
≤ 5°C	Very cold	Warning
≤ 0°C	Freezing	Critical
Important behavior:

Uses feels-like temperature (wind + humidity aware)

Sends only one alert per threshold crossing

Never sends multiple alerts in a single run

Will alert again only after warming above a threshold and dropping again later

This avoids alert spam while still capturing meaningful weather changes.

🌙 Quiet Hours Logic

To prevent unnecessary disturbances:

Quiet hours are defined as 11 PM – 6 AM

During quiet hours:

Informational alerts (15°C, 10°C, 5°C) are suppressed

Freezing alerts (≤ 0°C) always break through

This mirrors real-world alerting systems where safety overrides convenience.

🧠 Example Behavior Matrix
Scenario	Alert Sent?
16°C → 14°C (daytime)	✅ Yes (15°C alert)
14°C → 9°C (daytime)	✅ Yes (10°C alert)
9°C → 4°C (night)	❌ No (quiet hours)
4°C → −2°C (night)	✅ Yes (freezing alert)
−2°C → −6°C	❌ No (already below)
−6°C → 6°C	❌ No (warming)
6°C → −1°C (new cold front)	✅ Yes
🖼️ Daily Weather Dashboard (Static)

Weatherman generates a fully rendered static HTML dashboard once per day.

Why static?

No JavaScript fetch

No client-side API calls

No caching or Safari quirks

Guaranteed to work on any device

Dashboard shows:

City & date

Current temperature

Feels-like temperature

Weather description

Daily high / low

Rain probability

Wind & humidity

Morning / Noon / Evening / Night temperature ranges

Access:

Hosted via GitHub Pages

Linked directly from the daily push notification

🧠 Architecture Overview
OpenWeather API
      ↓
GitHub Actions (scheduled / manual)
      ↓
Python scripts
      ↓
Static HTML generation
      ↓
GitHub Pages
      ↓
Push notification → tap → dashboard

Key design choice:

No live polling, no browser logic, no API keys on the client

📁 Repository Structure
/
├── docs/
│   └── index.html              # Generated daily dashboard
├── generate_index_html.py      # Builds static dashboard HTML
├── rain_alert.py               # Rain + cold alert engine
└── .github/workflows/
    └── generate_dashboard.yml  # Automation pipeline

🔐 Secrets & Configuration
Required GitHub Secrets

Add under Settings → Secrets → Actions:

Secret	Purpose
OPENWEATHER_API_KEY	Weather data
PUSHOVER_TOKEN	Push notification app token
PUSHOVER_USER	Push notification user key
Environment Configuration

Configured inside GitHub Actions:

CITY: McKinney
LAT: "33.1546624"
LON: "-96.7180288"
TZ: America/Chicago


Units are fixed to Celsius by design.

⚙️ How Automation Works
Dashboard Generation

Runs once per day via cron

Can be triggered manually

Generates docs/index.html

Automatically committed and deployed

Alert Engine

Intended to run every 10–15 minutes

Stateless across runs except for a small state file

Sends notifications only when a new event occurs

🧠 State Management

A small JSON state file tracks:

Whether a rain alert has already been sent

Last recorded feels-like temperature

This allows the system to:

Detect threshold crossings

Avoid duplicate alerts

Reset naturally when conditions change

📱 Notification UX Philosophy

Notifications are designed to be:

Short

Actionable

Rare

Trustworthy

Example cold alert:

🥶 Freezing Alert

Current: -2°C
Feels like: -6°C

Risk of frost or icy surfaces.

🛠️ Design Principles

Event-driven, not condition-driven

Human-centric metrics

Static over dynamic

Automation over manual checks

Silence is success

🚀 Possible Future Enhancements

Forecast-based cold alerts (“will drop below 0°C in 2 hours”)

Commute-hour sensitivity

Weekend vs weekday behavior

Configurable thresholds via environment variables

7-day static forecast

UI polish via Figma

Additional alert channels (email, Slack)

📜 License

Personal project.
Feel free to fork, adapt, and extend.

🙌 Credits

OpenWeather API

Pushover Notifications

GitHub Actions

GitHub Pages

✅ Summary

Weatherman is not a weather app — it is a signal system.

It tells you:

When weather changes

When weather matters

And stays silent the rest of the time

That is intentional.
