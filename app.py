
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import zipfile

# Set page config
st.set_page_config(
    page_title="IPL Analytics Dashboard",
    page_icon="🏏",
    layout="wide"
)

# Custom CSS with dark theme
st.markdown("""
    <style>
    /* Main container and background */
    .main {
        padding: 2rem;
        background-color: #1a1a1a;
        color: #ffffff;
    }
    
    /* Metric cards */
    .stMetric {
        background-color: #2d2d2d;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #3d3d3d;
        color: #ffffff;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #00a6ed !important;
    }
    
    /* Player stats container */
    .player-stats {
        background-color: #2d2d2d;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        color: #ffffff;
    }
    
    /* DataFrames and tables */
    .dataframe {
        background-color: #2d2d2d !important;
        color: #ffffff !important;
    }
    
    /* Selectbox and other inputs */
    .stSelectbox, .stRadio > label {
        color: #ffffff !important;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #2d2d2d;
    }
    
    /* Plots */
    .js-plotly-plot {
        background-color: #2d2d2d !important;
    }
    
    /* Warning messages */
    .stAlert {
        background-color: #473a3a !important;
        color: #ffffff !important;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        background: #1a1a1a;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #3d3d3d;
        border-radius: 5px;
    }
    
    /* Links */
    a {
        color: #00a6ed !important;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #00a6ed;
        color: #ffffff;
    }
    
    /* Improve contrast for metric values */
    .stMetric .css-1wivap2 {
        color: #00a6ed !important;
    }
    </style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    with zipfile.ZipFile('deliveries.csv.zip') as z:
        with z.open('deliveries.csv') as file:
            df = pd.read_csv(file)
    return df

def calculate_matchup_stats(df, batsman, bowler):
    """Calculate detailed head-to-head stats between a batsman and bowler"""
    matchup_df = df[(df['batter'] == batsman) & (df['bowler'] == bowler)]
    
    stats = {
        'Total Balls': len(matchup_df),
        'Runs Scored': matchup_df['batsman_runs'].sum(),
        'Wickets': matchup_df['is_wicket'].sum(),
        'Dot Balls': len(matchup_df[matchup_df['batsman_runs'] == 0]),
        'Boundaries': len(matchup_df[matchup_df['batsman_runs'] >= 4]),
        'Strike Rate': (matchup_df['batsman_runs'].sum() / max(1, len(matchup_df))) * 100,
        'Dismissal Rate': (matchup_df['is_wicket'].sum() / max(1, len(matchup_df))) * 100
    }
    
    # Phase-wise breakdown
    phases = {
        'Powerplay': matchup_df[matchup_df['over'] <= 6],
        'Middle Overs': matchup_df[(matchup_df['over'] > 6) & (matchup_df['over'] <= 15)],
        'Death Overs': matchup_df[matchup_df['over'] > 15]
    }
    
    phase_stats = {}
    for phase, phase_df in phases.items():
        if len(phase_df) > 0:
            phase_stats[phase] = {
                'Balls': len(phase_df),
                'Runs': phase_df['batsman_runs'].sum(),
                'Wickets': phase_df['is_wicket'].sum(),
                'Strike Rate': (phase_df['batsman_runs'].sum() / max(1, len(phase_df))) * 100
            }
    
    return stats, phase_stats

def analyze_pressure_situations(df, player_name, role='batsman'):
    """Analyze player performance in pressure situations"""
    if role == 'batsman':
        player_df = df[df['batter'] == player_name]
        
        # Define pressure situations
        death_overs = player_df[player_df['over'] >= 16]
        powerplay = player_df[player_df['over'] <= 6]
        
        stats = {
            'Death Overs SR': (death_overs['batsman_runs'].sum() / max(1, len(death_overs))) * 100,
            'Powerplay SR': (powerplay['batsman_runs'].sum() / max(1, len(powerplay))) * 100,
            'Death Overs Runs': death_overs['batsman_runs'].sum(),
            'Powerplay Runs': powerplay['batsman_runs'].sum(),
            'Death Overs Boundaries': len(death_overs[death_overs['batsman_runs'] >= 4]),
            'Powerplay Boundaries': len(powerplay[powerplay['batsman_runs'] >= 4])
        }
    else:
        player_df = df[df['bowler'] == player_name]
        
        death_overs = player_df[player_df['over'] >= 16]
        powerplay = player_df[player_df['over'] <= 6]
        
        stats = {
            'Death Overs Economy': (death_overs['total_runs'].sum() / max(1, len(death_overs)/6)),
            'Powerplay Economy': (powerplay['total_runs'].sum() / max(1, len(powerplay)/6)),
            'Death Overs Wickets': death_overs['is_wicket'].sum(),
            'Powerplay Wickets': powerplay['is_wicket'].sum(),
            'Death Overs Dots': len(death_overs[death_overs['batsman_runs'] == 0]),
            'Powerplay Dots': len(powerplay[powerplay['batsman_runs'] == 0])
        }
    
    return stats

def calculate_partnership_analysis(df):
    """Analyze batting partnerships"""
    partnerships = []
    
    for match_id in df['match_id'].unique():
        match_df = df[df['match_id'] == match_id]
        current_partners = []
        partnership_runs = 0
        
        for _, ball in match_df.iterrows():
            if ball['batter'] not in current_partners:
                current_partners.append(ball['batter'])
            if len(current_partners) == 2:
                partnership_runs += ball['batsman_runs']
                if ball['is_wicket']:
                    partnerships.append({
                        'match_id': match_id,
                        'partners': tuple(sorted(current_partners)),
                        'runs': partnership_runs,
                        'batting_team': ball['batting_team'],
                        'bowling_team': ball['bowling_team']
                    })
                    current_partners = [ball['batter']]
                    partnership_runs = 0
    
    return pd.DataFrame(partnerships)

def analyze_progressive_performance(df, player_name, role='batsman'):
    """Track player's performance progression over time"""
    if role == 'batsman':
        performance_df = df[df['batter'] == player_name].groupby('match_id').agg({
            'batsman_runs': 'sum',
            'is_wicket': 'sum'
        }).reset_index()
        
        performance_df['rolling_average'] = performance_df['batsman_runs'].rolling(window=5, min_periods=1).mean()
        
    else:
        performance_df = df[df['bowler'] == player_name].groupby('match_id').agg({
            'is_wicket': 'sum',
            'total_runs': 'sum'
        }).reset_index()
        
        performance_df['rolling_economy'] = (performance_df['total_runs'] / 
                                           (df[df['bowler'] == player_name].groupby('match_id').size() / 6))
    
    return performance_df

def player_profiles_page(df):
    st.header("Advanced Player Analysis")
    
    player_type = st.radio("Select Player Type", ["Batsman", "Bowler"])
    
    if player_type == "Batsman":
        players = sorted(df['batter'].unique())
        selected_player = st.selectbox("Select Batsman", players)
        
        # Basic Stats
        player_df = df[df['batter'] == selected_player]
        total_runs = player_df['batsman_runs'].sum()
        total_balls = len(player_df)
        strike_rate = (total_runs / total_balls) * 100 if total_balls > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Runs", f"{total_runs:,}")
        with col2:
            st.metric("Strike Rate", f"{strike_rate:.2f}")
        with col3:
            st.metric("Boundaries", f"{len(player_df[player_df['batsman_runs'] >= 4])}")
        with col4:
            st.metric("Innings", f"{player_df['match_id'].nunique()}")
        
        # Pressure Situation Analysis
        st.subheader("Performance Under Pressure")
        pressure_stats = analyze_pressure_situations(df, selected_player, 'batsman')
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Death Overs Strike Rate", f"{pressure_stats['Death Overs SR']:.2f}")
            st.metric("Death Overs Boundaries", pressure_stats['Death Overs Boundaries'])
        with col2:
            st.metric("Powerplay Strike Rate", f"{pressure_stats['Powerplay SR']:.2f}")
            st.metric("Powerplay Boundaries", pressure_stats['Powerplay Boundaries'])
        
        # Progressive Performance
        st.subheader("Form Analysis")
        progress_df = analyze_progressive_performance(df, selected_player, 'batsman')
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=progress_df.index, y=progress_df['rolling_average'],
                                mode='lines+markers', name='5-Match Rolling Average'))
        fig.update_layout(title="Batting Form Trend", xaxis_title="Matches", yaxis_title="Runs")
        st.plotly_chart(fig, use_container_width=True)
        
    else:  # Bowler analysis
        players = sorted(df['bowler'].unique())
        selected_player = st.selectbox("Select Bowler", players)
        
        # Basic Stats
        player_df = df[df['bowler'] == selected_player]
        total_wickets = player_df['is_wicket'].sum()
        total_overs = len(player_df) / 6
        economy = player_df['total_runs'].sum() / total_overs if total_overs > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Wickets", total_wickets)
        with col2:
            st.metric("Economy Rate", f"{economy:.2f}")
        with col3:
            st.metric("Dot Balls", f"{len(player_df[player_df['batsman_runs'] == 0])}")
        with col4:
            st.metric("Matches", f"{player_df['match_id'].nunique()}")
        
        # Pressure Situation Analysis
        st.subheader("Performance Under Pressure")
        pressure_stats = analyze_pressure_situations(df, selected_player, 'bowler')
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Death Overs Economy", f"{pressure_stats['Death Overs Economy']:.2f}")
            st.metric("Death Overs Wickets", pressure_stats['Death Overs Wickets'])
        with col2:
            st.metric("Powerplay Economy", f"{pressure_stats['Powerplay Economy']:.2f}")
            st.metric("Powerplay Wickets", pressure_stats['Powerplay Wickets'])
        
        # Form Analysis
        st.subheader("Bowling Form")
        progress_df = analyze_progressive_performance(df, selected_player, 'bowler')
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=progress_df.index, y=progress_df['rolling_economy'],
                                mode='lines+markers', name='5-Match Rolling Economy'))
        fig.update_layout(title="Economy Rate Trend", xaxis_title="Matches", yaxis_title="Economy")
        st.plotly_chart(fig, use_container_width=True)

def matchup_analysis_page(df):
    st.header("Player Matchup Analysis")
    
    col1, col2 = st.columns(2)
    with col1:
        batsman = st.selectbox("Select Batsman", sorted(df['batter'].unique()))
    with col2:
        bowler = st.selectbox("Select Bowler", sorted(df['bowler'].unique()))
    
    if batsman and bowler:
        stats, phase_stats = calculate_matchup_stats(df, batsman, bowler)
        
        # Overall Stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Runs", stats['Runs Scored'])
        with col2:
            st.metric("Balls Faced", stats['Total Balls'])
        with col3:
            st.metric("Strike Rate", f"{stats['Strike Rate']:.2f}")
        with col4:
            st.metric("Wickets", stats['Wickets'])
        
        # Phase-wise Analysis
        st.subheader("Phase-wise Matchup")
        phase_df = pd.DataFrame([
            {
                'Phase': phase,
                'Runs': data['Runs'],
                'Balls': data['Balls'],
                'Strike Rate': data['Strike Rate'],
                'Wickets': data['Wickets']
            }
            for phase, data in phase_stats.items()
        ])
        
        st.dataframe(phase_df)
        
        # Visualization
        fig = go.Figure()
        fig.add_trace(go.Bar(x=phase_df['Phase'], y=phase_df['Strike Rate'], name='Strike Rate'))
        fig.update_layout(title=f"{batsman} vs {bowler} - Phase-wise Performance")
        st.plotly_chart(fig, use_container_width=True)

def records_page(df):
    st.header("Advanced Records & Analysis")
    
    # Enhanced Fastest Fifties Analysis
    st.subheader("Fastest Fifties Analysis")
    
    fastest_fifties = []
    for match_id in df['match_id'].unique():
        match_df = df[df['match_id'] == match_id]
        for batter in match_df['batter'].unique():
            batter_df = match_df[match_df['batter'] == batter]
            runs = batter_df['batsman_runs'].cumsum()
            if runs.max() >= 50:
                balls_to_fifty = runs[runs >= 50].index[0] - batter_df.index[0] + 1
                fastest_fifties.append({
                    'Batsman': batter,
                    'Balls': balls_to_fifty,
                    'Total Score': runs.max(),
                    'Against': match_df['bowling_team'].iloc[0],
                    'Match ID': match_id,
                    'Batting Team': match_df['batting_team'].iloc[0]
                })
    
    fifty_df = pd.DataFrame(fastest_fifties).sort_values('Balls')
    
    # Display top 10 fastest fifties with context
    st.dataframe(fifty_df.head(10))
    
    # Partnership Records
    st.subheader("Notable Partnerships")
    partnerships_df = calculate_partnership_analysis(df)
    top_partnerships = partnerships_df.nlargest(10, 'runs')
    
    st.dataframe(top_partnerships[['partners', 'runs', 'batting_team', 'bowling_team']])
    
    # Phase Specialists Analysis
    st.subheader("Phase Specialists")
    
    # Define phases
    df['phase'] = pd.cut(df['over'], 
                        bins=[-np.inf, 6, 15, np.inf],
                        labels=['Powerplay', 'Middle Overs', 'Death Overs'])
    
    # Batting Phase Specialists
    batting_phase_stats = []
    for phase in ['Powerplay', 'Middle Overs', 'Death Overs']:
        phase_df = df[df['phase'] == phase]
        batsman_stats = phase_df.groupby('batter').agg({
            'batsman_runs': 'sum',
            'match_id': 'nunique',
            'batter': 'size'  # number of balls
        }).reset_index()
        
        batsman_stats['strike_rate'] = (batsman_stats['batsman_runs'] / batsman_stats['batter']) * 100
        batsman_stats['phase'] = phase
        batsman_stats = batsman_stats[batsman_stats['match_id'] >= 5]  # minimum 5 matches
        batting_phase_stats.append(batsman_stats)
    
    # Bowling Phase Specialists
    bowling_phase_stats = []
    for phase in ['Powerplay', 'Middle Overs', 'Death Overs']:
        phase_df = df[df['phase'] == phase]
        bowler_stats = phase_df.groupby('bowler').agg({
            'total_runs': 'sum',
            'is_wicket': 'sum',
            'match_id': 'nunique',
            'bowler': 'size'  # number of balls
        }).reset_index()
        
        bowler_stats['economy'] = (bowler_stats['total_runs'] / bowler_stats['bowler']) * 6
        bowler_stats['phase'] = phase
        bowler_stats = bowler_stats[bowler_stats['match_id'] >= 5]  # minimum 5 matches
        bowling_phase_stats.append(bowler_stats)
    
    # Display Phase Specialists
    tab1, tab2 = st.tabs(["Batting Specialists", "Bowling Specialists"])
    
    with tab1:
        for phase in ['Powerplay', 'Middle Overs', 'Death Overs']:
            st.subheader(f"{phase} Batting Specialists")
            phase_data = pd.concat(batting_phase_stats)
            top_batsmen = phase_data[phase_data['phase'] == phase].nlargest(5, 'strike_rate')
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Highest SR", 
                         f"{top_batsmen['strike_rate'].iloc[0]:.2f}",
                         f"{top_batsmen['batter'].iloc[0]}")
            with col2:
                st.metric("Most Runs",
                         f"{phase_data[phase_data['phase'] == phase]['batsman_runs'].max()}",
                         f"{phase_data[phase_data['phase'] == phase].nlargest(1, 'batsman_runs')['batter'].iloc[0]}")
            
            st.dataframe(top_batsmen[['batter', 'batsman_runs', 'strike_rate', 'match_id']])
    
    with tab2:
        for phase in ['Powerplay', 'Middle Overs', 'Death Overs']:
            st.subheader(f"{phase} Bowling Specialists")
            phase_data = pd.concat(bowling_phase_stats)
            top_bowlers = phase_data[phase_data['phase'] == phase].nsmallest(5, 'economy')
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Best Economy",
                         f"{top_bowlers['economy'].iloc[0]:.2f}",
                         f"{top_bowlers['bowler'].iloc[0]}")
            with col2:
                st.metric("Most Wickets",
                         f"{phase_data[phase_data['phase'] == phase]['is_wicket'].max()}",
                         f"{phase_data[phase_data['phase'] == phase].nlargest(1, 'is_wicket')['bowler'].iloc[0]}")
            
            st.dataframe(top_bowlers[['bowler', 'economy', 'is_wicket', 'match_id']])
    
    # Death Over Specialists - Combined Analysis
    st.subheader("Death Overs Impact Players")
    death_overs_df = df[df['phase'] == 'Death Overs']
    
    # Calculate Impact Score for both batsmen and bowlers
    batsmen_impact = death_overs_df.groupby('batter').agg({
        'batsman_runs': lambda x: (sum(x) / len(x)) * 100,  # Strike Rate
        'match_id': 'nunique'
    }).reset_index()
    batsmen_impact = batsmen_impact[batsmen_impact['match_id'] >= 5]
    
    bowlers_impact = death_overs_df.groupby('bowler').agg({
        'total_runs': lambda x: (sum(x) / len(x)) * 6,  # Economy
        'is_wicket': 'sum',
        'match_id': 'nunique'
    }).reset_index()
    bowlers_impact = bowlers_impact[bowlers_impact['match_id'] >= 5]
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Best Death Over Batsmen")
        st.dataframe(batsmen_impact.nlargest(5, 'batsman_runs'))
    with col2:
        st.subheader("Best Death Over Bowlers")
        st.dataframe(bowlers_impact.nsmallest(5, 'total_runs'))


def main():
    st.title("🏏 Advanced IPL Analytics Dashboard")
    
    # Load data
    try:
        df = load_data()
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return
    
    # Navigation
    pages = {
        "Player Profiles": player_profiles_page,
        "Matchup Analysis": matchup_analysis_page,
        "Records & Statistics": records_page
    }
    
    # Sidebar
    st.sidebar.title("Navigation")
    selection = st.sidebar.radio("Go to", list(pages.keys()))
    
    # Season filter in sidebar
    if 'season' in df.columns:
        seasons = sorted(df['season'].unique())
        selected_season = st.sidebar.multiselect(
            "Select Season(s)",
            seasons,
            default=seasons[-1:]
        )
        
        # Filter data based on selected season
        if selected_season:
            df = df[df['season'].isin(selected_season)]
    
    # Display current date and last update
    st.sidebar.markdown("---")
    st.sidebar.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d')}")
    
    # Display selected page
    pages[selection](df)

if __name__ == "__main__":
    main()


