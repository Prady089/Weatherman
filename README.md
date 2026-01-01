# Weatherman

**Signal-Based Weather Intelligence with Zero Noise**

Weatherman reimagines weather notifications by treating them as signals, not streams. Built on automation and static generation principles, it delivers only the weather information that demands your attention—and stays silent otherwise.

## Philosophy

Most weather apps operate on a pull model: you check them when curious. Push-based apps suffer from notification fatigue, alerting you to every temperature fluctuation or cloud formation. Weatherman solves this by implementing **threshold-based event detection**—alerting only when weather crosses meaningful boundaries that affect your decisions.

**Core principle:** If the weather doesn't change your behavior, it doesn't warrant a notification.

## How It Works

### Rain Detection
Rain alerts fire when precipitation is detected in the near-term forecast, with built-in event deduplication to prevent notification spam. Once alerted to a rain event, the system automatically resets only after conditions clear.

```
🌧️ Rain Alert
Rain expected around 6:40 PM. Take an umbrella ☔
```

### Intelligent Temperature Monitoring

Rather than alerting whenever it's cold, Weatherman tracks **threshold crossings**—the moment weather transitions from one category to another. This mirrors how humans actually experience weather: we notice when it gets cold, not that it is cold.

**Temperature Thresholds:**

| Threshold | Category | Alert Priority |
|-----------|----------|----------------|
| ≤ 15°C | Cool | Informational |
| ≤ 10°C | Cold | Notice |
| ≤ 5°C | Very Cold | Warning |
| ≤ 0°C | Freezing | Critical |

**Key behaviors:**
- Uses apparent temperature (wind chill + humidity)
- Triggers once per threshold crossing
- Resets naturally when temperature rises and falls again
- Never sends multiple alerts in a single check

**Example scenario:** Temperature drops from 16°C to -2°C over several hours. You receive exactly two alerts: one at 15°C (cool threshold) and one at 0°C (freezing threshold). No redundant notifications.

### Quiet Hours Protection

The system respects human sleep patterns with configurable quiet hours (default: 11 PM - 6 AM).

**During quiet hours:**
- Informational alerts (15°C, 10°C, 5°C) are suppressed
- Critical alerts (≤ 0°C) always break through

This follows emergency alert system design: safety information overrides convenience.

### Alert Behavior Matrix

| Temperature Change | Time | Alert Sent? | Reason |
|-------------------|------|-------------|---------|
| 16°C → 14°C | 2 PM | ✅ Yes | Crossed 15°C threshold |
| 14°C → 9°C | 3 PM | ✅ Yes | Crossed 10°C threshold |
| 9°C → 4°C | 11 PM | ❌ No | Quiet hours (non-critical) |
| 4°C → -2°C | 1 AM | ✅ Yes | Freezing (critical override) |
| -2°C → -6°C | 2 AM | ❌ No | Already below threshold |
| -6°C → 6°C | Next day | ❌ No | Temperature rising |
| 6°C → -1°C | Later | ✅ Yes | New threshold crossing |

## Static Dashboard

Weatherman generates a fully pre-rendered HTML dashboard daily, eliminating common failure modes of dynamic weather apps.

**Why static matters:**
- No JavaScript API calls that can fail
- No CORS issues or authentication errors
- No Safari caching bugs
- Works perfectly on any device without internet
- Guaranteed render correctness

**Dashboard includes:**
- Current conditions with apparent temperature
- Today's high/low and precipitation probability
- Time-of-day breakdown (morning/noon/evening/night)
- Wind speed and humidity
- Weather description

**Access flow:** Daily notification → tap → instant dashboard load (already rendered)

## Technical Architecture

```
┌─────────────────┐
│ OpenWeather API │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ GitHub Actions  │ (scheduled: daily + every 15min)
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌─────────┐ ┌──────────────┐
│Dashboard│ │ Alert Engine │
│Generator│ │  (stateful)  │
└────┬────┘ └──────┬───────┘
     │             │
     ▼             ▼
┌─────────┐   ┌─────────┐
│  HTML   │   │Pushover │
│ (Pages) │   │  Alert  │
└─────────┘   └─────────┘
```

**Design decisions:**
- Stateless HTML generation for reliability
- Minimal stateful logic (only for alert deduplication)
- No client-side weather API calls
- No database dependencies
- Zero-cost hosting via GitHub Pages

## Repository Structure

```
weatherman/
├── docs/
│   └── index.html              # Daily dashboard (auto-generated)
├── generate_index_html.py      # Static dashboard builder
├── rain_alert.py               # Event detection engine
├── .github/workflows/
│   └── generate_dashboard.yml  # Automation pipeline
└── state.json                  # Alert deduplication state
```

## Configuration

### Required Secrets
Add to GitHub Settings → Secrets and variables → Actions:

| Secret | Purpose |
|--------|---------|
| `OPENWEATHER_API_KEY` | Weather data retrieval |
| `PUSHOVER_TOKEN` | Notification app token |
| `PUSHOVER_USER` | Notification recipient |

### Environment Variables
Set in GitHub Actions workflow:

```yaml
env:
  CITY: "McKinney"
  LAT: "33.1546624"
  LON: "-96.7180288"
  TZ: "America/Chicago"
```

## Automation Schedule

**Dashboard generation:** Once daily at 6:00 AM local time  
**Alert checks:** Every 15 minutes (configurable)

Both can be triggered manually via GitHub Actions interface.

## State Management

A minimal JSON state file persists between runs:

```json
{
  "rain_alert_sent": false,
  "last_feels_like": 12.5
}
```

This enables:
- Detection of threshold crossings (requires previous temperature)
- Rain event deduplication
- Natural state resets when conditions normalize

## Notification Design

Notifications follow information design principles:

**Structure:**
1. Visual indicator (emoji)
2. Alert category
3. Essential metrics
4. Actionable context

**Example:**
```
🥶 Freezing Alert

Current: -2°C
Feels like: -6°C

Risk of frost or icy surfaces.
```

**Characteristics:**
- Scannable in 2 seconds
- Clear severity indication
- Actionable information
- No redundant details

## Design Principles

1. **Event-driven, not condition-driven** — Alert on changes, not states
2. **Human-centric metrics** — Use apparent temperature, not raw readings
3. **Static over dynamic** — Pre-render to eliminate runtime failures
4. **Automation over polling** — Server-side scheduled checks
5. **Silence is success** — No alerts means everything is normal

## Possible Extensions

- **Forecast-based alerts:** "Freezing conditions expected in 3 hours"
- **Context-aware timing:** Different thresholds for commute hours vs weekends
- **Configurable thresholds:** User-defined temperature boundaries
- **Extended forecast:** 7-day static forecast on dashboard
- **Multi-channel delivery:** Email, Slack, Discord integration
- **Weather trends:** "Temperature dropping 10°C over next 6 hours"

## Why This Approach?

Traditional weather apps fail because they optimize for engagement rather than utility. They show you weather constantly because that's what keeps you opening the app. Weatherman inverts this: it assumes you're busy living your life and only interrupts when weather becomes decision-relevant.

**This is not a weather app. It's a signal system.**

It tells you when weather changes, when weather matters, and stays silent the rest of the time. That silence is the feature.

## Credits

Built with:
- [OpenWeather API](https://openweathermap.org/)
- [Pushover](https://pushover.net/)
- GitHub Actions + Pages

## License

Personal project. Fork, adapt, and extend as needed.

---

*"The best interface is no interface." — Golden Krishna*
