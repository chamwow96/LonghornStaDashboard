"""
Main dashboard UI for Texas Longhorns Football Stats
"""
import streamlit as st
import pandas as pd
import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'latest_stats.json')

def load_stats():
    try:
        with open(DATA_PATH, 'r') as f:
            data = json.load(f)
        df = pd.DataFrame(data['stats'])
        return data, df
    except Exception as e:
        st.error(f"Error loading stats: {e}")
        return None, pd.DataFrame()

def main():
    st.title("🏈 Texas Longhorns Football Stats Dashboard")
    data, df = load_stats()
    if data is None:
        st.warning("No stats available. Please run the data fetcher.")
        return
    # Example: Show team record
    st.header("Team Record by Week")
    if 'record_by_week' in data:
        st.line_chart(pd.DataFrame(data['record_by_week']))
    # Example: Show player leaderboard
    st.header("Player Leaderboard: Passing Yards")
    if not df.empty and 'passing_yards' in df.columns:
        st.dataframe(df[['player','passing_yards']].sort_values('passing_yards', ascending=False))

    st.set_page_config(page_title="Texas Longhorns Football Stats Dashboard", layout="wide")
    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Select Page",
        [
            "Team Record by Week",
            "QBR & Player Highlights",
            "Scoring Trends",
            "Offense vs Defense",
            "Player Leaderboards",
            "Opponent Comparison",
            "Game Summaries & Box Scores",
            "General & Advanced Stats"
        ]
    )

    # Helper: get stat value
    def get_stat(stat_name):
        row = df[df['statName'] == stat_name]
        if not row.empty:
            return row.iloc[0]['statValue']
        return None

    record_df = None
    if 'record_by_week' in data:
        record_df = pd.DataFrame(data['record_by_week'])

    if page == "Team Record by Week":
        st.header("Team Record by Week (W/L)")
        if record_df is not None and all(col in record_df.columns for col in ['W', 'L']):
            st.line_chart(record_df[['W', 'L']].astype(int))
            st.dataframe(record_df)
        else:
            st.info("No W/L data available.")

    elif page == "QBR & Player Highlights":
        st.header("QBR Rating of Starting QB & Player Highlights")
        st.info("QBR and player highlights require player-level stats from the API.")
        st.write("Arch Manning QBR:", get_stat("archManningQBR"))
        st.write("Arch Manning Heisman Odds:", get_stat("archManningHeismanOdds"))
        st.write("Trey Wingo TDs:", get_stat("treyWingoTDs"))
        st.write("Simmons Sacks:", get_stat("simmonsSacks"))
        st.write("Kicker FG%:", get_stat("kickerFGPct"))

    elif page == "Scoring Trends":
        st.header("Scoring Trends Over Time")
        st.info("Scoring trends require per-game stats from the API.")

    elif page == "Offense vs Defense":
        st.header("Offensive vs Defensive Stats")
        stats = {
            "Total Yards": (get_stat("totalYards"), get_stat("totalYardsOpponent")),
            "Passing Yards": (get_stat("netPassingYards"), get_stat("netPassingYardsOpponent")),
            "Rushing Yards": (get_stat("rushingYards"), get_stat("rushingYardsOpponent")),
            "Turnovers": (get_stat("turnovers"), get_stat("turnoversOpponent")),
            "Sacks": (get_stat("sacks"), get_stat("sacksOpponent")),
            "Tackles for Loss": (get_stat("tacklesForLoss"), get_stat("tacklesForLossOpponent")),
        }
        st.table(pd.DataFrame(stats, index=["Texas", "Opponent"]).T)

    elif page == "Player Leaderboards":
        st.header("Player Leaderboard: Passing/Rushing/Receiving Yards")
        st.info("Player leaderboards require player-level stats from the API.")

    elif page == "Opponent Comparison":
        st.header("Opponent Comparison Charts")
        st.info("Opponent comparison requires opponent-level stats from the API.")

    elif page == "Game Summaries & Box Scores":
        st.header("Game Summaries with Box Scores")
        st.info("Game summaries require per-game box score data from the API.")

    elif page == "General & Advanced Stats":
        st.header("General & Advanced Stats")
        st.subheader("General")
        st.write("AP Poll:", get_stat("apPoll"))
        if record_df is not None and all(col in record_df.columns for col in ['W', 'L']):
            st.write("W/L Record:", f"{record_df['W'].sum()}-{record_df['L'].sum()}")
        else:
            st.write("W/L Record: N/A")
        st.write("Next Matchup:", get_stat("nextMatchup"))
        st.write("Betting Odds for Next Matchup:", get_stat("bettingOddsNextMatchup"))
        st.subheader("Offense")
        st.write("National Ranking:", get_stat("offenseNationalRank"))
        st.write("Yards Per Game (YPG):", get_stat("offenseYPG"))
        st.write("Points Per Game (PPG):", get_stat("offensePPG"))
        st.write("Advanced Offense Stat:", get_stat("offenseAdvancedStat"))
        st.subheader("Defense")
        st.write("National Ranking:", get_stat("defenseNationalRank"))
        st.write("Yards Per Game (YPG):", get_stat("defenseYPG"))
        st.write("Points Per Game (PPG):", get_stat("defensePPG"))
        st.write("Advanced Defense Stat:", get_stat("defenseAdvancedStat"))
        st.subheader("Havoc Stats")
        st.write("Turnover Margin:", get_stat("turnoverMargin"))
        st.write("Sacks:", get_stat("sacks"))
        st.write("Interceptions:", get_stat("interceptions"))
        st.write("Fumbles:", get_stat("fumblesLost"))
    # ...add more visualizations as needed...

if __name__ == "__main__":
    main()
