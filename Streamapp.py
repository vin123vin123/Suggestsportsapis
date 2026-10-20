import streamlit as st
import requests
import time

# Configure the Streamlit page layout
st.set_page_config(page_title="Live Soccer Dashboard", layout="wide", page_icon="⚽")

st.title("⚽ Real-Time Soccer Match Tracker")
st.write("Live data sourced directly from open score networks.")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("Settings")
# Fetch updates automatically every 30 seconds if checked
auto_refresh = st.sidebar.checkbox("Enable Auto-Refresh", value=True)
refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 10, 120, 30)

# Main leagues endpoint selector mapping
LEAGUES = {
    "English Premier League": "eng.1",
    "Spanish La Liga": "esp.1",
    "UEFA Champions League": "uefa.champions",
    "Italian Serie A": "ita.1",
    "German Bundesliga": "ger.1",
    "MLS": "usa.1"
}
selected_league = st.sidebar.selectbox("Choose a Competition", list(LEAGUES.keys()))
league_code = LEAGUES[selected_league]

# --- DATA FETCH FUNCTION ---
def fetch_live_scores(league):
    url = f"https://espn.com{league}/scoreboard"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Error connecting to network: {e}")
    return None

# --- MAIN RENDER LOGIC ---
data = fetch_live_scores(league_code)

if data and "events" in data:
    events = data["events"]
    
    if not events:
        st.info(f"No active or scheduled matches found today for {selected_league}.")
    else:
        # Loop through matches
        for match in events:
            # Extract basic team and fixture info
            match_name = match.get("name", "Unknown Match")
            status = match.get("status", {}).get("type", {}).get("detail", "Scheduled")
            is_live = match.get("status", {}).get("type", {}).get("state", "") == "in"
            
            competitors = match.get("competitions", [{}])[0].get("competitors", [])
            
            # Identify Home vs Away teams & scores
            home_team = next((c for c in competitors if c.get("homeAway") == "home"), {})
            away_team = next((c for c in competitors if c.get("homeAway") == "away"), {})
            
            home_name = home_team.get("team", {}).get("displayName", "Home")
            away_name = away_team.get("team", {}).get("displayName", "Away")
            home_score = home_team.get("score", "0")
            away_score = away_team.get("score", "0")
            
            # Formatting badges based on live match status
            status_badge = "🔴 LIVE" if is_live else "🕒 UPCOMING / FT"
            
            # Render match display containers
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 1, 2])
                
                with col1:
                    st.markdown(f"### {home_name}")
                with col2:
                    st.markdown(f"<h2 style='text-align: center;'>{home_score} - {away_score}</h2>", unsafe_html=True)
                    st.caption(f"<p style='text-align: center;'>{status_badge} ({status})</p>", unsafe_html=True)
                with col3:
                    st.markdown(f"<h3 style='text-align: right;'>{away_name}</h3>", unsafe_html=True)
                
                # Check for live match commentary/events if available
                details = match.get("competitions", [{}])[0].get("details", [])
                if details:
                    with st.expander("View Match Highlights/Goals"):
                        for detail in details:
                            team_id = detail.get("team", {}).get("id")
                            scoring_team = home_name if str(team_id) == str(home_team.get("id")) else away_name
                            clock = detail.get("clock", {}).get("displayValue", "")
                            event_text = detail.get("type", {}).get("text", "Goal")
                            player = detail.get("athletesInvolved", [{}])[0].get("displayName", "Player")
                            
                            st.write(f"⏱️ {clock} - **{event_text}** by {player} ({scoring_team})")

else:
    st.warning("Could not load events data at this time.")

# --- AUTO REFRESH TRIGGER ---
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
