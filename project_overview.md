# 🏈 Texas Longhorns Football Stats Dashboard (API-Driven)

## 🚀 Project Overview

A Python web app that displays live stats for Texas Longhorns football using data pulled from an external API. The app is deployed on PythonAnywhere and updates itself on a scheduled basis, without requiring manual file uploads. All API credentials are securely managed using environment variables.

---

## 📦 Core Stack

| Component   | Technology      |
|-------------|------------------|
| App Backend | Python (3.10+)   |
| Frontend    | Streamlit or Flask |
| Data Format | JSON (API Response) |
| Scheduler   | PythonAnywhere Scheduled Task |
| Deployment  | PythonAnywhere (WSGI if Flask) |

---

## 🧱 Project Structure

longhorns_dashboard/
│
├── app.py # Main dashboard UI
├── fetch_api_data.py # Pulls + caches latest API data
├── data/
│ └── latest_stats.json # Most recent stats
├── .env # Local dev secrets (ignored in Git)
├── requirements.txt # Dependencies
└── project_overview.md # This file


---

## 🔁 Data Automation Workflow

1. **`fetch_api_data.py`** runs periodically to pull the latest stats from the API.
2. API response is processed into a Pandas DataFrame.
3. Result is saved to `data/latest_stats.json`.
4. **`app.py`** reads this file and displays interactive charts/tables.

---

## 🔒 Secure API Key Handling

**NEVER** hardcode your API key in Python files.

### ✅ Recommended Practice

- In `fetch_api_data.py`, load your API key securely:

```python
import os
API_KEY = os.getenv("LONGHORNS_API_KEY")



---

### 📊 ****Planned Visualizations****
Defining what the dashboard should show:

## 📊 Planned Visualizations

- [ ] Team record by week (W/L)
- [ ] QBR Rating of the starting QB
- [ ] Scoring trends over time
- [ ] Offensive vs Defensive stats (e.g., yards, turnovers)
- [ ] Player leaderboard: passing/rushing/receiving yards
- [ ] Opponent comparison charts
- [ ] Game summaries with box scores

# Other Stats to Include

General: AP Poll | WL Record | Next Matchup | Betting Odds for Next Matchup
Offense: national ranking | YPG | PPG | Advanced Offense stat
Defense: national ranking | YPG | PPG | advanced defense stat
Player highlights: Arch Manning QBR | Arch Manning Heisman Odds | Trey Wingo TDs | Simmons Sacks | Kicker FG%
Havoc: turnover margin | sacks | INTs | fumbles


## 🛠️ Dev Tasks

- [ ] Set up project folder structure
- [ ] Create API data fetcher
- [ ] Store API credentials securely
- [ ] Parse nested JSON into Pandas DataFrame
- [ ] Build visual dashboard (Streamlit or Flask)
- [ ] Deploy to PythonAnywhere
- [ ] Set up daily scheduled task

## ✅ Testing & Validation

- Confirm successful API response (200 OK)
- Check schema consistency
- Validate saved JSON has expected fields
- Test dashboard render with sample data
## 📝 License & Attribution

- Stats provided by collegefootballdata.com
- This project is for personal/educational use only
