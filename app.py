import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
import zipfile

# Page Configuration
st.set_page_config(
    page_title="IPL Analytics Dashboard 2008-2024",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better design
st.markdown("""
<style>
    .main {
        background-color: #f5f5f5;
    }
    .stApp {
        background: linear-gradient(to right, #f8f9fa, #e9ecef);
    }
    .css-1d391kg {
        background-color: #1e1e1e;
    }
    .st-emotion-cache-1wivap2 {
        font-size: 1.2rem;
        font-weight: bold;
        color: #2c3e50;
    }
    .metric-card {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    .chart-container {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    try:
        with zipfile.ZipFile('deliveries.csv.zip') as z:
            with z.open('deliveries.csv') as file:
                df = pd.read_csv(file)
        
        # Updated team name mapping
        team_mapping = {
            'Rising Pune Supergiants': 'Rising Pune Supergiant',
            'Royal Challengers Bangalore': 'Royal Challengers Bengaluru',
            'Royal Challengers Bengaluru': 'Royal Challengers Bengaluru'
        }
        
        df['batting_team'] = df['batting_team'].replace(team_mapping)
        df['bowling_team'] = df['bowling_team'].replace(team_mapping)
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

def head_to_head_page(df):
    st.header("Head to Head Analysis 🤝")
    
    col1, col2 = st.columns(2)
    with col1:
        team1 = st.selectbox("Select Team 1", sorted(df['batting_team'].unique()))
    with col2:
        team2 = st.selectbox("Select Team 2", sorted(df['bowling_team'].unique()))
        
    if team1 and team2:
        # Filter matches between selected teams
        team_vs_team = df[
            ((df['batting_team'] == team1) & (df['bowling_team'] == team2)) |
            ((df['batting_team'] == team2) & (df['bowling_team'] == team1))
        ]
        
        # Calculate detailed metrics
        team1_stats = team_vs_team[team_vs_team['batting_team'] == team1]
        team2_stats = team_vs_team[team_vs_team['batting_team'] == team2]
        
        # Team 1 Metrics
        team1_runs = team1_stats['total_runs'].sum()
        team1_balls = len(team1_stats)
        team1_overs = team1_balls / 6
        team1_rr = team1_runs / team1_overs if team1_overs > 0 else 0
        team1_wickets = team_vs_team[team_vs_team['bowling_team'] == team1]['is_wicket'].sum()
        team1_runs_conceded = team2_stats['total_runs'].sum()
        team1_overs_bowled = len(team2_stats) / 6
        team1_economy = team1_runs_conceded / team1_overs_bowled if team1_overs_bowled > 0 else 0
        
        # Team 2 Metrics
        team2_runs = team2_stats['total_runs'].sum()
        team2_balls = len(team2_stats)
        team2_overs = team2_balls / 6
        team2_rr = team2_runs / team2_overs if team2_overs > 0 else 0
        team2_wickets = team_vs_team[team_vs_team['bowling_team'] == team2]['is_wicket'].sum()
        team2_runs_conceded = team1_stats['total_runs'].sum()
        team2_overs_bowled = len(team1_stats) / 6
        team2_economy = team2_runs_conceded / team2_overs_bowled if team2_overs_bowled > 0 else 0
        
        # Display metrics
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(f"{team1} Statistics")
            st.metric("Total Runs", f"{team1_runs:,.0f}")
            st.metric("Run Rate", f"{team1_rr:.2f}")
            st.metric("Wickets Taken", f"{team1_wickets}")
            st.metric("Economy Rate", f"{team1_economy:.2f}")
            st.metric("Overs Bowled", f"{team1_overs_bowled:.1f}")
            st.metric("Runs Conceded", f"{team1_runs_conceded:,.0f}")
            
        with col2:
            st.subheader(f"{team2} Statistics")
            st.metric("Total Runs", f"{team2_runs:,.0f}")
            st.metric("Run Rate", f"{team2_rr:.2f}")
            st.metric("Wickets Taken", f"{team2_wickets}")
            st.metric("Economy Rate", f"{team2_economy:.2f}")
            st.metric("Overs Bowled", f"{team2_overs_bowled:.1f}")
            st.metric("Runs Conceded", f"{team2_runs_conceded:,.0f}")
            
        # Phase-wise Analysis
        st.subheader("Phase-wise Analysis")
        
        def get_phase_stats(team_data, phase_start, phase_end):
            phase_df = team_data[
                (team_data['over'] >= phase_start) & 
                (team_data['over'] <= phase_end)
            ]
            runs = phase_df['total_runs'].sum()
            balls = len(phase_df)
            overs = balls / 6
            rr = runs / overs if overs > 0 else 0
            wickets = phase_df['is_wicket'].sum()
            economy = runs / overs if overs > 0 else 0
            return runs, rr, wickets, economy
        
        phases = [
            ("Powerplay (1-6)", 1, 6),
            ("Middle Overs (7-15)", 7, 15),
            ("Death Overs (16-20)", 16, 20)
        ]
        
        for phase_name, start, end in phases:
            st.write(f"\n{phase_name}")
            t1_runs, t1_rr, t1_wickets, t1_eco = get_phase_stats(team1_stats, start, end)
            t2_runs, t2_rr, t2_wickets, t2_eco = get_phase_stats(team2_stats, start, end)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric(f"{team1} Runs", f"{t1_runs:.0f}")
                st.metric("Run Rate", f"{t1_rr:.2f}")
                st.metric("Wickets", f"{t1_wickets}")
                st.metric("Economy", f"{t1_eco:.2f}")
            with col2:
                st.metric(f"{team2} Runs", f"{t2_runs:.0f}")
                st.metric("Run Rate", f"{t2_rr:.2f}")
                st.metric("Wickets", f"{t2_wickets}")
                st.metric("Economy", f"{t2_eco:.2f}")

def analyze_batsman(df, player):
    player_df = df[df['batter'] == player]
    total_runs = player_df['batsman_runs'].sum()
    total_balls = len(player_df)
    dismissals = player_df['is_wicket'].sum()
    
    # Calculate additional metrics
    fifties = len(player_df.groupby('match_id')['batsman_runs'].sum()[
        player_df.groupby('match_id')['batsman_runs'].sum() >= 50
    ])
    centuries = len(player_df.groupby('match_id')['batsman_runs'].sum()[
        player_df.groupby('match_id')['batsman_runs'].sum() >= 100
    ])
    sixes = len(player_df[player_df['batsman_runs'] == 6])
    fours = len(player_df[player_df['batsman_runs'] == 4])
    
    return {
        'total_runs': total_runs,
        'strike_rate': (total_runs / total_balls * 100) if total_balls > 0 else 0,
        'average': total_runs / dismissals if dismissals > 0 else total_runs,
        'highest_score': player_df.groupby('match_id')['batsman_runs'].sum().max(),
        'fifties': fifties,
        'centuries': centuries,
        'sixes': sixes,
        'fours': fours,
        'balls_faced': total_balls
    }

def analyze_bowler(df, player):
    player_df = df[df['bowler'] == player]
    wickets = player_df['is_wicket'].sum()
    runs = player_df['total_runs'].sum()
    balls = len(player_df)
    overs = balls / 6
    
    # Calculate additional metrics
    three_wicket_hauls = len(player_df.groupby('match_id')['is_wicket'].sum()[
        player_df.groupby('match_id')['is_wicket'].sum() >= 3
    ])
    five_wicket_hauls = len(player_df.groupby('match_id')['is_wicket'].sum()[
        player_df.groupby('match_id')['is_wicket'].sum() >= 5
    ])
    
    return {
        'wickets': wickets,
        'economy': runs / overs if overs > 0 else 0,
        'average': runs / wickets if wickets > 0 else float('inf'),
        'best_bowling': f"{player_df.groupby('match_id')['is_wicket'].sum().max()}/{player_df.groupby('match_id')['total_runs'].sum().min()}",
        'three_wicket_hauls': three_wicket_hauls,
        'five_wicket_hauls': five_wicket_hauls,
        'overs_bowled': overs,
        'runs_conceded': runs
    }

def player_analysis_page(df):
    st.header("Player Analysis 🏃")
    
    player_type = st.radio("Select Player Type", ["Batsman", "Bowler", "All-Rounder"])
    
    if player_type == "Batsman":
        player = st.selectbox("Select Batsman", sorted(df['batter'].unique()))
        if player:
            stats = analyze_batsman(df, player)
            
            # Display comprehensive batting stats
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Runs", f"{stats['total_runs']:,.0f}")
                st.metric("Balls Faced", f"{stats['balls_faced']}")
            with col2:
                st.metric("Strike Rate", f"{stats['strike_rate']:.2f}")
                st.metric("Average", f"{stats['average']:.2f}")
            with col3:
                st.metric("Centuries", f"{stats['centuries']}")
                st.metric("Fifties", f"{stats['fifties']}")
            with col4:
                st.metric("Sixes", f"{stats['sixes']}")
                st.metric("Fours", f"{stats['fours']}")
            
            # Display phase-wise performance
            st.subheader("Phase-wise Performance")
            display_phase_performance(df, player, 'batsman')
            
            # Display form analysis
            st.subheader("Form Analysis")
            display_form_trend(df, player, 'batsman')
            
            # Display opposition analysis
            st.subheader("Performance Against Teams")
            display_opposition_analysis(df, player, 'batsman')
            
    elif player_type == "Bowler":
        player = st.selectbox("Select Bowler", sorted(df['bowler'].unique()))
        if player:
            stats = analyze_bowler(df, player)
            
            # Display comprehensive bowling stats
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Wickets", f"{stats['wickets']}")
                st.metric("Best Bowling", stats['best_bowling'])
            with col2:
                st.metric("Economy", f"{stats['economy']:.2f}")
                st.metric("Average", f"{stats['average']:.2f}")
            with col3:
                st.metric("3-Wicket Hauls", f"{stats['three_wicket_hauls']}")
                st.metric("5-Wicket Hauls", f"{stats['five_wicket_hauls']}")
            with col4:
                st.metric("Overs Bowled", f"{stats['overs_bowled']:.1f}")
                st.metric("Runs Conceded", f"{stats['runs_conceded']}")
            
            # Display phase-wise performance
            st.subheader("Phase-wise Performance")
            display_phase_performance(df, player, 'bowler')
            
            # Display form analysis
            st.subheader("Form Analysis")
            display_form_trend(df, player, 'bowler')
            
            # Display opposition analysis
            st.subheader("Performance Against Teams")
            display_opposition_analysis(df, player, 'bowler')
            
    else:  # All-Rounder
                player = st.selectbox("Select All-Rounder", 
                                    sorted(set(df['batter'].unique()) & set(df['bowler'].unique())))
                if player:
                    batting_stats = analyze_batsman(df, player)
                    bowling_stats = analyze_bowler(df, player)
                    
                    st.subheader("Batting Statistics")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Runs", f"{batting_stats['total_runs']:,.0f}")
                        st.metric("Balls Faced", f"{batting_stats['balls_faced']}")
                    with col2:
                        st.metric("Strike Rate", f"{batting_stats['strike_rate']:.2f}")
                        st.metric("Average", f"{batting_stats['average']:.2f}")
                    with col3:
                        st.metric("Centuries", f"{batting_stats['centuries']}")
                        st.metric("Fifties", f"{batting_stats['fifties']}")
                    with col4:
                        st.metric("Sixes", f"{batting_stats['sixes']}")
                        st.metric("Fours", f"{batting_stats['fours']}")
                    
                    st.subheader("Bowling Statistics")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Wickets", f"{bowling_stats['wickets']}")
                        st.metric("Best Bowling", bowling_stats['best_bowling'])
                    with col2:
                        st.metric("Economy", f"{bowling_stats['economy']:.2f}")
                        st.metric("Average", f"{bowling_stats['average']:.2f}")
                    with col3:
                        st.metric("3-Wicket Hauls", f"{bowling_stats['three_wicket_hauls']}")
                        st.metric("5-Wicket Hauls", f"{bowling_stats['five_wicket_hauls']}")
                    with col4:
                        st.metric("Overs Bowled", f"{bowling_stats['overs_bowled']:.1f}")
                        st.metric("Runs Conceded", f"{bowling_stats['runs_conceded']}")
                    
                    # Phase-wise Analysis for Both Skills
                    st.subheader("Phase-wise Batting Performance")
                    display_phase_performance(df, player, 'batsman')
                    
                    st.subheader("Phase-wise Bowling Performance")
                    display_phase_performance(df, player, 'bowler')
                    
                    # Form Analysis for Both Skills
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Batting Form")
                        display_form_trend(df, player, 'batsman')
                    with col2:
                        st.subheader("Bowling Form")
                        display_form_trend(df, player, 'bowler')
                    
                    # Opposition Analysis for Both Skills
                    st.subheader("Performance Against Teams (Batting)")
                    display_opposition_analysis(df, player, 'batsman')
                    
                    st.subheader("Performance Against Teams (Bowling)")
                    display_opposition_analysis(df, player, 'bowler')

def display_opposition_analysis(df, player, role):
    if role == 'batsman':
        opposition_stats = df[df['batter'] == player].groupby('bowling_team').agg({
            'batsman_runs': 'sum',
            'batter': 'size',  # balls faced
            'is_wicket': 'sum'  # dismissals
        }).reset_index()
        
        opposition_stats['strike_rate'] = (opposition_stats['batsman_runs'] / opposition_stats['batter']) * 100
        opposition_stats['average'] = opposition_stats['batsman_runs'] / opposition_stats['is_wicket'].replace(0, 1)
        
        fig = go.Figure(data=[
            go.Bar(name='Runs', y=opposition_stats['bowling_team'], x=opposition_stats['batsman_runs'], orientation='h'),
            go.Bar(name='Strike Rate', y=opposition_stats['bowling_team'], x=opposition_stats['strike_rate'], orientation='h')
        ])
        
        fig.update_layout(
            title=f"{player}'s Batting Performance vs Teams",
            barmode='group',
            height=400,
            margin=dict(l=0, r=0, t=40, b=0)
        )
        
    else:  # bowler
        opposition_stats = df[df['bowler'] == player].groupby('batting_team').agg({
            'is_wicket': 'sum',
            'total_runs': 'sum',
            'bowler': 'size'  # balls bowled
        }).reset_index()
        
        opposition_stats['economy'] = (opposition_stats['total_runs'] / (opposition_stats['bowler']/6))
        
        fig = go.Figure(data=[
            go.Bar(name='Wickets', y=opposition_stats['batting_team'], x=opposition_stats['is_wicket'], orientation='h'),
            go.Bar(name='Economy', y=opposition_stats['batting_team'], x=opposition_stats['economy'], orientation='h')
        ])
        
        fig.update_layout(
            title=f"{player}'s Bowling Performance vs Teams",
            barmode='group',
            height=400,
            margin=dict(l=0, r=0, t=40, b=0)
        )
    
    st.plotly_chart(fig, use_container_width=True)

def calculate_fastest_fifties(df):
    fifties = []
    for match_id in df['match_id'].unique():
        match_df = df[df['match_id'] == match_id]
        for batter in match_df['batter'].unique():
            batter_df = match_df[match_df['batter'] == batter]
            runs = batter_df['batsman_runs'].cumsum()
            if runs.max() >= 50:
                balls_to_fifty = runs[runs >= 50].index[0] - batter_df.index[0] + 1
                fifties.append({
                    'Batsman': batter,
                    'Balls': balls_to_fifty,
                    'Against': match_df['bowling_team'].iloc[0],
                    'Total Score': runs.max()
                })
    return pd.DataFrame(fifties).sort_values('Balls').head(10)

def calculate_fastest_centuries(df):
    centuries = []
    for match_id in df['match_id'].unique():
        match_df = df[df['match_id'] == match_id]
        for batter in match_df['batter'].unique():
            batter_df = match_df[match_df['batter'] == batter]
            runs = batter_df['batsman_runs'].cumsum()
            if runs.max() >= 100:
                balls_to_hundred = runs[runs >= 100].index[0] - batter_df.index[0] + 1
                centuries.append({
                    'Batsman': batter,
                    'Balls': balls_to_hundred,
                    'Against': match_df['bowling_team'].iloc[0],
                    'Total Score': runs.max()
                })
    return pd.DataFrame(centuries).sort_values('Balls').head(10)

def main():
    st.title("🏏 IPL Analytics Dashboard (2008-2024)")
    
    # Load data
    df = load_data()
    if df is None:
        return
    
    # Navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Select Page", 
                           ["Head to Head Analysis",
                            "Player Analysis",
                            "Milestones & Records"])
    
    # Display selected page
    if page == "Head to Head Analysis":
        head_to_head_page(df)
    elif page == "Player Analysis":
        player_analysis_page(df)
    else:
        milestones_page(df)
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d')}")

if __name__ == "__main__":
    main()
