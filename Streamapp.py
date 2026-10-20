import streamlit as st
import requests
import time

# Configure the Streamlit page layout
st.set_page_config(page_title="Live Soccer Dashboard", layout="wide", page_icon="⚽")

st.title("⚽ Real-Time Soccer Match Tracker")
st.write("Live data sourced directly from open score networks.")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("Settings")
auto_refresh = st.sidebar.checkbox("Enable Auto-Refresh", value=True)
refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 10, 120, 30)

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

# --- DATA FETCH FUNCTION WITH CACHING ---
@st.cache_data(ttl=15)  # Cache for 15 seconds to prevent rate-limiting and handle multiple users
def fetch_live_scores(league):
    # Fixed URL structure with trailing slash preserved
    url = f"https://espn.com{league}/scoreboard"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            st.sidebar.error(f"API Error: Status code {response.status_code}")
    except Exception as e:
        st.sidebar.error(f"Network Connection Issue: {e}")
    return None

# --- MAIN RENDER LOGIC ---
data = fetch_live_scores(league_code)

if data:
    # Safely get events; if it's missing, default to an empty list
    events = data.get("events", [])
    
    if not events:
        st.info(f"📅 No live or scheduled matches found today for {selected_league}. Try selecting another competition in the sidebar!")
    else:
        for match in events:
            match_name = match.get("name", "Unknown Match")
            status_obj = match.get("status", {})
            status_type = status_obj.get("type", {})
            
            status_detail = status_type.get("detail", "Scheduled")
            is_live = status_type.get("state", "") == "in"
            
            # Navigate nested competition array safely
            competitions = match.get("competitions", [{}])
            competitors = competitions[0].get("competitors", []) if competitions else []
            
            home_team = next((c for c in competitors if c.get("homeAway") == "home"), {})
            away_team = next((c for c in competitors if c.get("homeAway") == "away"), {})
            
            home_name = home_team.get("team", {}).get("displayName", "Home Team")
            away_name = away_team.get("team", {}).get("displayName", "Away Team")
            home_score = home_team.get("score", "0")
            away_score = away_team.get("score", "0")
            
            status_badge = "🔴 LIVE" if is_live else "🕒 UPCOMING / FT"
            
            # Display containers
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 1, 2])
                
                with col1:
                    st.subheader(home_name)
                with col2:
                    st.markdown(f"<h2 style='text-align: center; margin: 0;'>{home_score} - {away_score}</h2>", unsafe_html=True)
                    st.markdown(f"<p style='text-align: center; color: gray;'>{status_badge}<br><small>{status_detail}</small></p>", unsafe_html=True)
                with col3:
                    st.markdown(f"<h3 style='text-align: right;'>{away_name}</h3>", unsafe_html=True)
                
                # Check for live match commentary/events safely
                details = competitions[0].get("details", []) if competitions else []
                if details:
                    with st.expander("⚽ View Match Timeline"):
                        for detail in details:
                            team_id = detail.get("team", {}).get("id")
                            scoring_team = home_name if str(team_id) == str(home_team.get("id")) else away_name
                            clock = detail.get("clock", {}).get("displayValue", "??'")
                            event_text = detail.get("type", {}).get("text", "Goal")
                            
                            athletes = detail.get("athletesInvolved", [{}])
                            player = athletes[0].get("displayName", "Player") if athletes else "Unknown"
                            
                            st.write(f"⏱️ {clock} - **{event_text}**: {player} ({scoring_team})")
else:
    st.error("❌ Failed to receive data payload. Check your network or verify if the selected league's tournament is currently active.")

# --- AUTO REFRESH TRIGGER ---
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
