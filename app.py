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
        
        # Team name mapping
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
        
        # Calculate metrics
        team1_stats = team_vs_team[team_vs_team['batting_team'] == team1]
        team2_stats = team_vs_team[team_vs_team['batting_team'] == team2]
        
        # Team 1 Metrics
        team1_runs = team1_stats['total_runs'].sum()
        team1_overs = len(team1_stats) / 6
        team1_rr = team1_runs / team1_overs if team1_overs > 0 else 0
        team1_wickets = team_vs_team[team_vs_team['bowling_team'] == team1]['is_wicket'].sum()
        team1_economy = (team2_stats['total_runs'].sum() / (len(team2_stats) / 6)) if len(team2_stats) > 0 else 0
        
        # Team 2 Metrics
        team2_runs = team2_stats['total_runs'].sum()
        team2_overs = len(team2_stats) / 6
        team2_rr = team2_runs / team2_overs if team2_overs > 0 else 0
        team2_wickets = team_vs_team[team_vs_team['bowling_team'] == team2]['is_wicket'].sum()
        team2_economy = (team1_stats['total_runs'].sum() / (len(team1_stats) / 6)) if len(team1_stats) > 0 else 0
        
        # Display metrics
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(f"{team1} Statistics")
            st.metric("Total Runs", f"{team1_runs:,.0f}")
            st.metric("Run Rate", f"{team1_rr:.2f}")
            st.metric("Wickets Taken", f"{team1_wickets}")
            st.metric("Economy Rate", f"{team1_economy:.2f}")
            
        with col2:
            st.subheader(f"{team2} Statistics")
            st.metric("Total Runs", f"{team2_runs:,.0f}")
            st.metric("Run Rate", f"{team2_rr:.2f}")
            st.metric("Wickets Taken", f"{team2_wickets}")
            st.metric("Economy Rate", f"{team2_economy:.2f}")
            
        # Phase-wise Analysis
        st.subheader("Phase-wise Analysis")
        
        def get_phase_stats(team_data, phase_start, phase_end):
            phase_df = team_data[
                (team_data['over'] >= phase_start) & 
                (team_data['over'] <= phase_end)
            ]
            runs = phase_df['total_runs'].sum()
            overs = len(phase_df) / 6
            rr = runs / overs if overs > 0 else 0
            wickets = phase_df['is_wicket'].sum()
            return runs, rr, wickets
        
        phases = [
            ("Powerplay (1-6)", 1, 6),
            ("Middle Overs (7-15)", 7, 15),
            ("Death Overs (16-20)", 16, 20)
        ]
        
        for phase_name, start, end in phases:
            st.write(f"\n{phase_name}")
            t1_runs, t1_rr, t1_wickets = get_phase_stats(team1_stats, start, end)
            t2_runs, t2_rr, t2_wickets = get_phase_stats(team2_stats, start, end)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric(f"{team1} Runs", f"{t1_runs:.0f}")
                st.metric("Run Rate", f"{t1_rr:.2f}")
                st.metric("Wickets", f"{t1_wickets}")
            with col2:
                st.metric(f"{team2} Runs", f"{t2_runs:.0f}")
                st.metric("Run Rate", f"{t2_rr:.2f}")
                st.metric("Wickets", f"{t2_wickets}")

def player_analysis_page(df):
    st.header("Player Analysis 🏃")
    
    # Player type selection
    player_type = st.radio("Select Player Type", ["Batsman", "Bowler", "All-Rounder"])
    
    if player_type == "Batsman":
        player = st.selectbox("Select Batsman", sorted(df['batter'].unique()))
        if player:
            player_stats = analyze_batsman(df, player)
            
            # Display overall stats
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Runs", f"{player_stats['total_runs']:,.0f}")
            with col2:
                st.metric("Strike Rate", f"{player_stats['strike_rate']:.2f}")
            with col3:
                st.metric("Average", f"{player_stats['average']:.2f}")
            with col4:
                st.metric("Highest Score", f"{player_stats['highest_score']}")
            
            # Phase-wise performance
            st.subheader("Phase-wise Performance")
            display_phase_performance(df, player, 'batsman')
            
            # Form analysis
            st.subheader("Form Analysis")
            display_form_trend(df, player, 'batsman')
            
    elif player_type == "Bowler":
        player = st.selectbox("Select Bowler", sorted(df['bowler'].unique()))
        if player:
            player_stats = analyze_bowler(df, player)
            
            # Display overall stats
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Wickets", f"{player_stats['wickets']}")
            with col2:
                st.metric("Economy", f"{player_stats['economy']:.2f}")
            with col3:
                st.metric("Average", f"{player_stats['average']:.2f}")
            with col4:
                st.metric("Best Bowling", f"{player_stats['best_bowling']}")
            
            # Phase-wise performance
            st.subheader("Phase-wise Performance")
            display_phase_performance(df, player, 'bowler')
            
            # Form analysis
            st.subheader("Form Analysis")
            display_form_trend(df, player, 'bowler')
            
    else:  # All-Rounder
        player = st.selectbox("Select All-Rounder", 
                            sorted(set(df['batter'].unique()) & set(df['bowler'].unique())))
        if player:
            batting_stats = analyze_batsman(df, player)
            bowling_stats = analyze_bowler(df, player)
            
            st.subheader("Batting Stats")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Runs", f"{batting_stats['total_runs']:,.0f}")
            with col2:
                st.metric("Strike Rate", f"{batting_stats['strike_rate']:.2f}")
            with col3:
                st.metric("Average", f"{batting_stats['average']:.2f}")
                
            st.subheader("Bowling Stats")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Wickets", f"{bowling_stats['wickets']}")
            with col2:
                st.metric("Economy", f"{bowling_stats['economy']:.2f}")
            with col3:
                st.metric("Average", f"{bowling_stats['average']:.2f}")

def milestones_page(df):
    st.header("Milestones & Records 🏆")
    
    tab1, tab2, tab3 = st.tabs(["Batting Records", "Bowling Records", "Team Records"])
    
    with tab1:
        st.subheader("Batting Milestones")
        
        # Fastest Fifties
        fastest_fifties = calculate_fastest_fifties(df)
        st.write("Fastest Fifties")
        st.dataframe(fastest_fifties)
        
        # Fastest Centuries
        fastest_centuries = calculate_fastest_centuries(df)
        st.write("Fastest Centuries")
        st.dataframe(fastest_centuries)
        
        # Most Sixes and Fours
        col1, col2 = st.columns(2)
        with col1:
            most_sixes = calculate_most_sixes(df)
            st.write("Most Sixes")
            st.dataframe(most_sixes)
        with col2:
            most_fours = calculate_most_fours(df)
            st.write("Most Fours")
            st.dataframe(most_fours)
            
    with tab2:
        st.subheader("Bowling Milestones")
        
        # Best Bowling Figures
        best_bowling = calculate_best_bowling(df)
        st.write("Best Bowling Figures")
        st.dataframe(best_bowling)
        
        # Most Wickets
        most_wickets = calculate_most_wickets(df)
        st.write("Most Wickets")
        st.dataframe(most_wickets)
        
        # Best Economy Rates
        best_economy = calculate_best_economy(df)
        st.write("Best Economy Rates (Min. 20 overs)")
        st.dataframe(best_economy)
        
    with tab3:
        st.subheader("Team Records")
        
        # Highest Team Totals
        highest_totals = calculate_highest_totals(df)
        st.write("Highest Team Totals")
        st.dataframe(highest_totals)
        
        # Best Team Strike Rates
        team_sr = calculate_team_strike_rates(df)
        st.write("Best Team Strike Rates")
        st.dataframe(team_sr)

# Helper functions for analysis
def analyze_batsman(df, player):
    player_df = df[df['batter'] == player]
    total_runs = player_df['batsman_runs'].sum()
    total_balls = len(player_df)
    dismissals = player_df['is_wicket'].sum()
    
    return {
        'total_runs': total_runs,
        'strike_rate': (total_runs / total_balls * 100) if total_balls > 0 else 0,
        'average': total_runs / dismissals if dismissals > 0 else total_runs,
        'highest_score': player_df.groupby('match_id')['batsman_runs'].sum().max()
    }

def analyze_bowler(df, player):
    player_df = df[df['bowler'] == player]
    wickets = player_df['is_wicket'].sum()
    runs = player_df['total_runs'].sum()
    overs = len(player_df) / 6
    
    return {
        'wickets': wickets,
        'economy': runs / overs if overs > 0 else 0,
        'average': runs / wickets if wickets > 0 else float('inf'),
        'best_bowling': f"{player_df.groupby('match_id')['is_wicket'].sum().max()}/{player_df.groupby('match_id')['total_runs'].sum().min()}"
    }

def display_phase_performance(df, player, role):
    phases = [
        ("Powerplay", 1, 6),
        ("Middle Overs", 7, 15),
        ("Death Overs", 16, 20)
    ]
    
    for phase_name, start, end in phases:
        phase_df = df[(df['over'] >= start) & (df['over'] <= end)]
        
        if role == 'batsman':
            player_phase = phase_df[phase_df['batter'] == player]
            runs = player_phase['batsman_runs'].sum()
            balls = len(player_phase)
            sr = (runs / balls * 100) if balls > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(f"{phase_name} Runs", f"{runs}")
            with col2:
                st.metric("Balls", f"{balls}")
            with col3:
                st.metric("Strike Rate", f"{sr:.2f}")
        else:
            player_phase = phase_df[phase_df['bowler'] == player]
            wickets = player_phase['is_wicket'].sum()
            runs = player_phase['total_runs'].sum()
            overs = len(player_phase) / 6
            economy = runs / overs if overs > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(f"{phase_name} Wickets", f"{wickets}")
            with col2:
                st.metric("Overs", f"{overs:.1f}")
            with col3:
                st.metric("Economy", f"{economy:.2f}")

def display_form_trend(df, player, role):
    if role == 'batsman':
        performance = df[df['batter'] == player].groupby('match_id').agg({
            'batsman_runs': 'sum',
            'batter': 'size'  # number of balls
        }).reset_index()
        
        performance['strike_rate'] = (performance['batsman_runs'] / performance['batter']) * 100
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=performance.index,
            y=performance['batsman_runs'],
            name='Runs',
            line=dict(color='blue')
        ))
        fig.add_trace(go.Scatter(
            x=performance.index,
            y=performance['strike_rate'],
            name='Strike Rate',
            line=dict(color='red'),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title=f"{player}'s Form Trend",
            yaxis=dict(title='Runs'),
            yaxis2=dict(title='Strike Rate', overlaying='y', side='right'),
            showlegend=True
        )
        
    else:
        performance = df[df['bowler'] == player].groupby('match_id').agg({
            'is_wicket': 'sum',
            'total_runs': 'sum',
            'bowler': 'size'  # number of balls
        }).reset_index()
        
        performance['economy'] = (performance['total_runs'] / (performance['bowler']/6))
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=performance.index,
            y=performance['is_wicket'],
            name='Wickets',
            line=dict(color='green')
        ))
        fig.add_trace(go.Scatter(
            x=performance.index,
            y=performance['economy'],
            name='Economy',
            line=dict(color='red'),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title=f"{player}'s Bowling Form",
            yaxis=dict(title='Wickets'),
            yaxis2=dict(title='Economy', overlaying='y', side='right'),
            showlegend=True
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

def calculate_most_sixes(df):
    return df[df['batsman_runs'] == 6].groupby('batter').size().reset_index(
        name='Sixes').sort_values('Sixes', ascending=False).head(10)

def calculate_most_fours(df):
    return df[df['batsman_runs'] == 4].groupby('batter').size().reset_index(
        name='Fours').sort_values('Fours', ascending=False).head(10)

def calculate_best_bowling(df):
    bowling_figures = df.groupby(['match_id', 'bowler']).agg({
        'is_wicket': 'sum',
        'total_runs': 'sum'
    }).reset_index()
    return bowling_figures.sort_values(['is_wicket', 'total_runs'], 
                                     ascending=[False, True]).head(10)

def calculate_most_wickets(df):
    return df.groupby('bowler')['is_wicket'].sum().reset_index().sort_values(
        'is_wicket', ascending=False).head(10)

def calculate_best_economy(df):
    bowler_stats = df.groupby('bowler').agg({
        'total_runs': 'sum',
        'bowler': 'size'  # number of balls
    }).reset_index()
    bowler_stats['overs'] = bowler_stats['bowler'] / 6
    bowler_stats['economy'] = bowler_stats['total_runs'] / bowler_stats['overs']
    return bowler_stats[bowler_stats['overs'] >= 20].sort_values('economy').head(10)

def calculate_highest_totals(df):
    return df.groupby(['match_id', 'batting_team'])['total_runs'].sum().reset_index().sort_values(
        'total_runs', ascending=False).head(10)

def calculate_team_strike_rates(df):
    team_stats = df.groupby('batting_team').agg({
        'total_runs': 'sum',
        'batting_team': 'size'  # number of balls
    }).reset_index()
    team_stats['strike_rate'] = (team_stats['total_runs'] / team_stats['batting_team']) * 100
    return team_stats.sort_values('strike_rate', ascending=False)

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
