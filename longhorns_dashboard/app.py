import json
import os
from typing import Dict, Any, List

import pandas as pd
import streamlit as st

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "latest_stats.json")
TEAM_NAME = "Texas"


@st.cache_data(show_spinner=False)
def load_data(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        st.warning("Data file not found. Run the fetcher to generate data/latest_stats.json.")
        return {"games": [], "team_stats": [], "player_stats": [], "rankings": [], "betting_lines": [], "next_game": {}}
    with open(path, "r") as f:
        return json.load(f)


def build_games_df(games: List[Dict[str, Any]]) -> pd.DataFrame:
    if not games:
        return pd.DataFrame()
    df = pd.json_normalize(games)
    # Normalize columns
    rename = {
        "startDate": "date",
        "homeTeam": "home",
        "awayTeam": "away",
        "homePoints": "home_pts",
        "awayPoints": "away_pts",
        "seasonType": "season_type",
    }
    df = df.rename(columns=rename)
    # Result column from perspective of TEAM_NAME
    def result(row):
        if pd.isna(row.get("home_pts")) or pd.isna(row.get("away_pts")):
            return "TBD"
        team_is_home = row.get("home") == TEAM_NAME
        us = row.get("home_pts") if team_is_home else row.get("away_pts")
        them = row.get("away_pts") if team_is_home else row.get("home_pts")
        if us > them:
            return f"W {us}-{them}"
        elif us < them:
            return f"L {us}-{them}"
        return f"T {us}-{them}"

    df["result"] = df.apply(result, axis=1)
    # Opponent column
    def opponent(row):
        return row.get("away") if row.get("home") == TEAM_NAME else row.get("home")

    df["opponent"] = df.apply(opponent, axis=1)
    # Keep useful columns
    keep = [
        "week",
        "date",
        "home",
        "away",
        "home_pts",
        "away_pts",
        "opponent",
        "result",
        "completed",
        "venue",
        "conferenceGame",
    ]
    df = df[[c for c in keep if c in df.columns]]
    # Format date column as MM/DD/YYYY and sort ascending
    if "date" in df.columns:
        df["_date_sort"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.sort_values("_date_sort")
        df["date"] = df["_date_sort"].dt.strftime("%m/%d/%Y")
        df = df.drop(columns=["_date_sort"])
    return df


def compute_record(games_df: pd.DataFrame) -> str:
    if games_df.empty:
        return "0-0"
    mask = games_df["completed"] == True  # noqa: E712
    df = games_df[mask].copy()
    if df.empty:
        return "0-0"
    wins = (df["result"].str.startswith("W")).sum()
    losses = (df["result"].str.startswith("L")).sum()
    ties = (df["result"].str.startswith("T")).sum()
    rec = f"{wins}-{losses}"
    if ties:
        rec += f"-{ties}"
    return rec


def latest_ap_rank(rankings: List[Dict[str, Any]]) -> Dict[str, Any]:
    # rankings is a list of poll weeks; inside each, polls list with {poll, ranks: [...]}
    best = None
    for wk in rankings:
        polls = wk.get("polls", [])
        for poll in polls:
            if poll.get("poll") == "AP Top 25":
                # choose the latest week (max seasonType, week ordering)
                key = (wk.get("seasonType", ""), wk.get("week", 0))
                if best is None or key > best[0]:
                    best = (key, poll)
    if not best:
        return {}
    ap = best[1]
    # find Texas rank
    for r in ap.get("ranks", []):
        if r.get("school") == TEAM_NAME:
            return {"poll": "AP Top 25", "rank": r.get("rank"), "points": r.get("points")}
    return {"poll": "AP Top 25", "rank": None}


def ap_rankings_over_time(rankings: List[Dict[str, Any]]) -> pd.DataFrame:
    # Build a DataFrame of Texas AP Top 25 ranks by week
    rows = []
    for wk in rankings:
        week = wk.get("week")
        season_type = wk.get("seasonType")
        polls = wk.get("polls", [])
        for poll in polls:
            if poll.get("poll") == "AP Top 25":
                for r in poll.get("ranks", []):
                    if r.get("school") == TEAM_NAME:
                        rows.append({
                            "week": week,
                            "season_type": season_type,
                            "rank": r.get("rank"),
                            "points": r.get("points"),
                        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("week")
    return df


def player_leaderboard(player_stats: List[Dict[str, Any]], category: str, top_n: int = 10) -> pd.DataFrame:
    if not player_stats:
        return pd.DataFrame()
    df = pd.DataFrame(player_stats)
    df = df[df["team"] == TEAM_NAME]
    if df.empty:
        return pd.DataFrame()
    if category:
        df = df[df["category"].str.lower() == category.lower()]
    # Fix: handle missing 'stat_type' by filling with 'stat_type' or fallback to 'stat_name' or 'category'
    if "stat_type" not in df.columns:
        if "stat_name" in df.columns:
            df["stat_type"] = df["stat_name"]
        else:
            df["stat_type"] = df["category"]
    df["stat_val"] = pd.to_numeric(df["stat"], errors="coerce").fillna(0)
    agg = df.groupby(["player", "stat_type"], as_index=False)["stat_val"].sum()
    pivot = agg.pivot_table(index="player", columns="stat_type", values="stat_val", aggfunc="sum").fillna(0)
    # Choose a primary sort column per category
    sort_cols = {
        "passing": ["yards", "touchdowns", "completions"],
        "rushing": ["yards", "touchdowns"],
        "receiving": ["yards", "touchdowns", "receptions"],
    }
    cols = sort_cols.get(category.lower(), list(pivot.columns))
    ordered_cols = [c for c in cols if c in pivot.columns] + [c for c in pivot.columns if c not in cols]
    out = pivot[ordered_cols].sort_values(by=ordered_cols[0] if ordered_cols else pivot.columns[0], ascending=False)
    return out.head(top_n).reset_index()


def main():
    st.set_page_config(page_title="Texas Longhorns Dashboard", layout="wide")
    st.title("Texas Longhorns Stat Dashboard")
    data = load_data(DATA_PATH)

    page = st.sidebar.selectbox(
        "Page",
        [
            "Overview",
            "Team Record by Week",
            "Scoring Trends",
            "QBR Rating",
            "Offense vs Defense",
            "Player Leaderboards",
            "Opponent Comparison",
            "Game Summaries",
            "Rankings",
            "Games",
            "Next Game",
            "Betting Lines"
        ],
    )

    games_df = build_games_df(data.get("games", []))

    if page == "Overview":
        st.subheader("Team Record")
        st.metric("Record", compute_record(games_df))
        st.subheader("Recent Games")
        st.dataframe(games_df.tail(5), use_container_width=True)

    elif page == "Team Record by Week":
        st.subheader("Team Record by Week (W/L)")
        if games_df.empty:
            st.info("No games available.")
        else:
            # Build W/L by week
            recs = []
            for _, row in games_df.iterrows():
                if row["completed"]:
                    result = row["result"]
                    week = row["week"]
                    recs.append({"week": week, "result": result})
            df = pd.DataFrame(recs)
            # Map W/L/T to numeric
            def wl_num(r):
                if r.startswith("W"): return 1
                if r.startswith("L"): return 0
                return 0.5
            df["W/L"] = df["result"].apply(wl_num)
            st.bar_chart(df.set_index("week")["W/L"], use_container_width=True)
            st.dataframe(df, use_container_width=True)

    elif page == "Scoring Trends":
        st.subheader("Scoring Trends Over Time")
        if games_df.empty:
            st.info("No games available.")
        else:
            # Points by week
            pts = games_df[["week", "home", "away", "home_pts", "away_pts"]].copy()
            pts["Texas_pts"] = pts.apply(lambda r: r["home_pts"] if r["home"] == TEAM_NAME else r["away_pts"], axis=1)
            pts["Opp_pts"] = pts.apply(lambda r: r["away_pts"] if r["home"] == TEAM_NAME else r["home_pts"], axis=1)
            pts = pts.sort_values("week")
            st.line_chart(pts.set_index("week")[["Texas_pts", "Opp_pts"]], use_container_width=True)
            st.dataframe(pts[["week", "Texas_pts", "Opp_pts"]], use_container_width=True)

    elif page == "QBR Rating":
        st.subheader("QBR Rating of Starting QB")
        st.info("QBR visualization coming soon.")

    elif page == "Offense vs Defense":
        st.subheader("Offensive vs Defensive Stats")
        st.info("Offense/Defense comparison charts coming soon.")

    elif page == "Opponent Comparison":
        st.subheader("Opponent Comparison Charts")
        st.info("Opponent comparison charts coming soon.")

    elif page == "Game Summaries":
        st.subheader("Game Summaries with Box Scores")
        st.info("Game summaries and box scores coming soon.")

    elif page == "Rankings":
        st.subheader("AP Top 25 (Latest)")
        ap = latest_ap_rank(data.get("rankings", []))
        if ap.get("rank"):
            st.metric("AP Rank", int(ap["rank"]))
        else:
            st.info("No AP Top 25 ranking found for Texas.")
        # List all AP Top 25 rankings for Texas
        st.subheader("Texas AP Top 25 Rankings by Week")
        ap_df = ap_rankings_over_time(data.get("rankings", []))
        if ap_df.empty:
            st.info("No AP Top 25 rankings found for Texas.")
        else:
            st.dataframe(ap_df, use_container_width=True)
            # Line chart: lower rank is better, so invert y-axis
            chart_df = ap_df.dropna(subset=["rank"])
            if not chart_df.empty:
                st.line_chart(
                    chart_df.set_index("week")["rank"],
                    use_container_width=True,
                )
                st.caption("Lower rank is better (1 = #1)")

    elif page == "Player Leaderboards":
        cat = st.selectbox("Category", ["passing", "rushing", "receiving"])
        top = st.slider("Top N", 5, 25, 10)
        lb = player_leaderboard(data.get("player_stats", []), cat, top)
        if lb.empty:
            st.info("No player stats available.")
        else:
            st.dataframe(lb, use_container_width=True)

    elif page == "Games":
        st.subheader("Season Games")
        if games_df.empty:
            st.info("No games available.")
        else:
            st.dataframe(games_df, use_container_width=True)

    elif page == "Next Game":
        st.subheader("Next Game")
        ng = data.get("next_game", {})
        if not ng:
            st.info("No upcoming game found.")
        else:
            cols = st.columns(3)
            cols[0].metric("Home", ng.get("homeTeam"))
            cols[1].metric("Away", ng.get("awayTeam"))
            # Format date as MM/DD/YYYY
            dt = ng.get("startDate")
            if dt:
                try:
                    dt_fmt = pd.to_datetime(dt).strftime("%m/%d/%Y")
                except Exception:
                    dt_fmt = dt
            else:
                dt_fmt = ""
            cols[2].metric("Date", dt_fmt)

    elif page == "Betting Lines":
        st.subheader("Betting Lines")
        lines = data.get("betting_lines", [])
        if not lines:
            st.info("No betting lines available.")
        else:
            # Expand lines details for each entry
            expanded = []
            for entry in lines:
                game_id = entry.get("gameId")
                for line in entry.get("lines", []):
                    out = {
                        "provider": line.get("provider"),
                        "spread": line.get("spread"),
                        "overUnder": line.get("overUnder"),
                        "homeTeam": entry.get("homeTeam"),
                        "awayTeam": entry.get("awayTeam"),
                        "gameId": game_id,
                        "startDate": entry.get("startDate"),
                    }
                    # Format date as MM/DD/YYYY
                    if out["startDate"]:
                        try:
                            out["startDate"] = pd.to_datetime(out["startDate"]).strftime("%m/%d/%Y")
                        except Exception:
                            pass
                    expanded.append(out)
            if not expanded:
                st.info("No betting lines available.")
            else:
                df = pd.DataFrame(expanded)
                # Sort by date ascending
                if "startDate" in df.columns:
                    df["_date_sort"] = pd.to_datetime(df["startDate"], errors="coerce")
                    df = df.sort_values("_date_sort")
                    df = df.drop(columns=["_date_sort"])
                st.dataframe(df, use_container_width=True)


if __name__ == "__main__":
    main()
