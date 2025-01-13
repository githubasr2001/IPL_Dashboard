
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
    # Read the compressed CSV file
    with zipfile.ZipFile('deliveries.csv.zip') as z:
        with z.open('deliveries.csv') as file:
            df = pd.read_csv(file)
    
    team_mapping = {
        'Delhi Daredevils': 'Delhi Capitals',
        'Deccan Chargers': 'Sunrisers Hyderabad',
        'Kings XI Punjab': 'Punjab Kings',
        'Pune Warriors': 'Rising Pune Supergiant',
        'Rising Pune Supergiants': 'Rising Pune Supergiant',
        'Gujarat Lions': 'Gujarat Titans',
        'Royal Challengers Bangalore': 'Royal Challengers Bengaluru'
    }
    
    df['batting_team'] = df['batting_team'].replace(team_mapping)
    df['bowling_team'] = df['bowling_team'].replace(team_mapping)
    
    return df

def calculate_player_stats(df, player_name, stat_type='batsman'):
    if stat_type == 'batsman':
        player_df = df[df['batter'] == player_name]
        
        stats = {
            'Total Runs': player_df['batsman_runs'].sum(),
            'Balls Faced': len(player_df),
            'Strike Rate': (player_df['batsman_runs'].sum() / len(player_df)) * 100,
            'Fours': len(player_df[player_df['batsman_runs'] == 4]),
            'Sixes': len(player_df[player_df['batsman_runs'] == 6]),
            'Dot Balls': len(player_df[player_df['batsman_runs'] == 0]),
            'Average': player_df['batsman_runs'].sum() / max(1, sum(player_df['is_wicket'])),
            'Highest Score': player_df.groupby(['match_id'])['batsman_runs'].sum().max(),
            'Teams Played For': player_df['batting_team'].unique().tolist(),
            'Powerplay Runs': player_df[player_df['over'] <= 6]['batsman_runs'].sum(),
            'Death Overs Runs': player_df[player_df['over'] >= 16]['batsman_runs'].sum()
        }
        
        # Phase-wise performance
        phase_runs = {
            'Powerplay (1-6)': player_df[player_df['over'] <= 6]['batsman_runs'].sum(),
            'Middle (7-15)': player_df[(player_df['over'] > 6) & (player_df['over'] <= 15)]['batsman_runs'].sum(),
            'Death (16-20)': player_df[player_df['over'] >= 16]['batsman_runs'].sum()
        }
        
        # Team-wise performance
        team_wise = player_df.groupby('bowling_team')['batsman_runs'].agg([
            'sum', 'count', 
            lambda x: len(x[x == 4]),  # fours
            lambda x: len(x[x == 6])   # sixes
        ]).reset_index()
        team_wise.columns = ['Team', 'Runs', 'Balls', 'Fours', 'Sixes']
        team_wise['Strike Rate'] = (team_wise['Runs'] / team_wise['Balls']) * 100
        
        return stats, phase_runs, team_wise
    
    else:  # bowler
        player_df = df[df['bowler'] == player_name]
        
        stats = {
            'Wickets': player_df['is_wicket'].sum(),
            'Overs Bowled': len(player_df) // 6,
            'Runs Conceded': player_df['total_runs'].sum(),
            'Economy': (player_df['total_runs'].sum() / (len(player_df) / 6)),
            'Dot Balls': len(player_df[player_df['batsman_runs'] == 0]),
            'Average': player_df['total_runs'].sum() / max(1, player_df['is_wicket'].sum()),
            'Teams Played For': player_df['bowling_team'].unique().tolist(),
            'Powerplay Wickets': player_df[player_df['over'] <= 6]['is_wicket'].sum(),
            'Death Overs Wickets': player_df[player_df['over'] >= 16]['is_wicket'].sum()
        }
        
        # Phase-wise performance
        phase_stats = {
            'Powerplay (1-6)': {
                'Wickets': player_df[player_df['over'] <= 6]['is_wicket'].sum(),
                'Economy': (player_df[player_df['over'] <= 6]['total_runs'].sum() / 
                          (len(player_df[player_df['over'] <= 6]) / 6))
            },
            'Middle (7-15)': {
                'Wickets': player_df[(player_df['over'] > 6) & (player_df['over'] <= 15)]['is_wicket'].sum(),
                'Economy': (player_df[(player_df['over'] > 6) & (player_df['over'] <= 15)]['total_runs'].sum() / 
                          (len(player_df[(player_df['over'] > 6) & (player_df['over'] <= 15)]) / 6))
            },
            'Death (16-20)': {
                'Wickets': player_df[player_df['over'] >= 16]['is_wicket'].sum(),
                'Economy': (player_df[player_df['over'] >= 16]['total_runs'].sum() / 
                          (len(player_df[player_df['over'] >= 16]) / 6))
            }
        }
        
        # Team-wise performance
        team_wise = player_df.groupby('batting_team').agg({
            'is_wicket': 'sum',
            'total_runs': 'sum',
            'batsman_runs': lambda x: len(x[x == 0])  # dot balls
        }).reset_index()
        team_wise.columns = ['Team', 'Wickets', 'Runs Conceded', 'Dot Balls']
        team_wise['Economy'] = team_wise['Runs Conceded'] / (len(player_df) / 6)
        
        return stats, phase_stats, team_wise

def head_to_head_comparison(df, team1, team2):
    # Filter matches between the two teams
    h2h_df = df[((df['batting_team'] == team1) & (df['bowling_team'] == team2)) |
                ((df['batting_team'] == team2) & (df['bowling_team'] == team1))]
    
    # Team Stats
    team_stats = {}
    for team in [team1, team2]:
        batting_df = h2h_df[h2h_df['batting_team'] == team]
        bowling_df = h2h_df[h2h_df['bowling_team'] == team]
        
        team_stats[team] = {
            'Total Runs Scored': batting_df['total_runs'].sum(),
            'Wickets Lost': batting_df['is_wicket'].sum(),
            'Wickets Taken': bowling_df['is_wicket'].sum(),
            'Fours Hit': len(batting_df[batting_df['batsman_runs'] == 4]),
            'Sixes Hit': len(batting_df[batting_df['batsman_runs'] == 6]),
            'Run Rate': (batting_df['total_runs'].sum() / 
                        (batting_df['over'].max() + 1)),
            'Economy Rate': (bowling_df['total_runs'].sum() / 
                           (bowling_df['over'].max() + 1))
        }
    
    # Top Performers
    top_batsmen = h2h_df.groupby('batter')['batsman_runs'].agg([
        'sum', 'count',
        lambda x: len(x[x == 4]),  # fours
        lambda x: len(x[x == 6])   # sixes
    ]).reset_index()
    top_batsmen.columns = ['Batsman', 'Runs', 'Balls', 'Fours', 'Sixes']
    top_batsmen['Strike Rate'] = (top_batsmen['Runs'] / top_batsmen['Balls']) * 100
    
    top_bowlers = h2h_df.groupby('bowler').agg({
        'is_wicket': 'sum',
        'total_runs': 'sum',
        'batsman_runs': lambda x: len(x[x == 0])  # dot balls
    }).reset_index()
    top_bowlers.columns = ['Bowler', 'Wickets', 'Runs Conceded', 'Dot Balls']
    
    return team_stats, top_batsmen.sort_values('Runs', ascending=False), top_bowlers.sort_values('Wickets', ascending=False)

def team_analysis_page(df):
    st.header("Team Analysis")
    
    selected_team = st.selectbox("Select Team", sorted(df['batting_team'].unique()))
    
    team_df = df[df['batting_team'] == selected_team]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Runs", f"{team_df['total_runs'].sum():,}")
    with col2:
        st.metric("Total Matches", f"{team_df['match_id'].nunique():,}")
    with col3:
        st.metric("Run Rate", f"{(team_df['total_runs'].sum() / (team_df['over'].max() + 1)):.2f}")
    
    # Phase-wise Analysis
    st.subheader("Phase-wise Performance")
    phases = {
        'Powerplay (1-6)': team_df[team_df['over'] <= 6],
        'Middle Overs (7-15)': team_df[(team_df['over'] > 6) & (team_df['over'] <= 15)],
        'Death Overs (16-20)': team_df[team_df['over'] >= 16]
    }
    
    phase_metrics = []
    for phase_name, phase_df in phases.items():
        phase_metrics.append({
            'Phase': phase_name,
            'Runs': phase_df['total_runs'].sum(),
            'Run Rate': phase_df['total_runs'].sum() / (phase_df['over'].nunique()),
            'Wickets': phase_df['is_wicket'].sum()
        })
    
    phase_df = pd.DataFrame(phase_metrics)
    fig = go.Figure(data=[
        go.Bar(name='Runs', y=phase_df['Phase'], x=phase_df['Runs'], orientation='h'),
        go.Bar(name='Run Rate', y=phase_df['Phase'], x=phase_df['Run Rate'], orientation='h')
    ])
    fig.update_layout(barmode='group')
    st.plotly_chart(fig, use_container_width=True)

def player_profiles_page(df):
    st.header("Player Profiles")
    
    # Player type selection
    player_type = st.radio("Select Player Type", ["Batsman", "Bowler"])
    
    if player_type == "Batsman":
        players = sorted(df['batter'].unique())
        selected_player = st.selectbox("Select Batsman", players)
        stats, phase_runs, team_wise = calculate_player_stats(df, selected_player, 'batsman')
        
        # Display stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Runs", f"{stats['Total Runs']:,}")
        with col2:
            st.metric("Strike Rate", f"{stats['Strike Rate']:.2f}")
        with col3:
            st.metric("Average", f"{stats['Average']:.2f}")
        with col4:
            st.metric("Highest Score", stats['Highest Score'])
        
        # Phase-wise performance
        st.subheader("Phase-wise Performance")
        fig = px.bar(
            x=list(phase_runs.keys()),
            y=list(phase_runs.values()),
            title="Runs in Different Phases"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Team-wise performance
        st.subheader("Performance Against Teams")
        st.dataframe(team_wise.sort_values('Runs', ascending=False))
        
        # Additional batting insights
        st.subheader("Additional Insights")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Fours", stats['Fours'])
            st.metric("Powerplay Runs", stats['Powerplay Runs'])
        with col2:
            st.metric("Sixes", stats['Sixes'])
            st.metric("Death Overs Runs", stats['Death Overs Runs'])
            
    else:  # Bowler
        players = sorted(df['bowler'].unique())
        selected_player = st.selectbox("Select Bowler", players)
        stats, phase_stats, team_wise = calculate_player_stats(df, selected_player, 'bowler')
        
        # Display stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Wickets", stats['Wickets'])
        with col2:
            st.metric("Economy", f"{stats['Economy']:.2f}")
        with col3:
            st.metric("Average", f"{stats['Average']:.2f}")
        with col4:
            st.metric("Dot Balls", stats['Dot Balls'])
        
        # Phase-wise performance
        st.subheader("Phase-wise Performance")
        phase_df = pd.DataFrame({
            'Phase': list(phase_stats.keys()),
            'Wickets': [phase['Wickets'] for phase in phase_stats.values()],
            'Economy': [phase['Economy'] for phase in phase_stats.values()]
        })

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(name="Wickets", x=phase_df['Phase'], y=phase_df['Wickets']), secondary_y=False)
        fig.add_trace(go.Scatter(name="Economy", x=phase_df['Phase'], y=phase_df['Economy'], mode='lines+markers'), secondary_y=True)
        
        fig.update_layout(
            title="Phase-wise Bowling Performance",
            yaxis_title="Wickets",
            yaxis2_title="Economy Rate"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Team-wise performance
        st.subheader("Performance Against Teams")
        st.dataframe(team_wise.sort_values('Wickets', ascending=False))
        
        # Additional bowling insights
        st.subheader("Additional Insights")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Overs Bowled", stats['Overs Bowled'])
            st.metric("Powerplay Wickets", stats['Powerplay Wickets'])
        with col2:
            st.metric("Runs Conceded", stats['Runs Conceded'])
            st.metric("Death Overs Wickets", stats['Death Overs Wickets'])

def player_profiles_page(df):
    st.header("Player Profiles")
    
    # Player type selection
    player_type = st.radio("Select Player Type", ["Batsman", "Bowler"])
    
    if player_type == "Batsman":
        players = sorted(df['batter'].unique())
        selected_player = st.selectbox("Select Batsman", players)
        stats, phase_runs, team_wise = calculate_player_stats(df, selected_player, 'batsman')
        
        # Display stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Runs", f"{stats['Total Runs']:,}")
        with col2:
            st.metric("Strike Rate", f"{stats['Strike Rate']:.2f}")
        with col3:
            st.metric("Average", f"{stats['Average']:.2f}")
        with col4:
            st.metric("Highest Score", stats['Highest Score'])
        
        # Phase-wise performance
        st.subheader("Phase-wise Performance")
        fig = px.bar(
            x=list(phase_runs.keys()),
            y=list(phase_runs.values()),
            title="Runs in Different Phases"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Team-wise performance
        st.subheader("Performance Against Teams")
        st.dataframe(team_wise.sort_values('Runs', ascending=False))
        
        # Additional batting insights
        st.subheader("Additional Insights")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Fours", stats['Fours'])
            st.metric("Powerplay Runs", stats['Powerplay Runs'])
        with col2:
            st.metric("Sixes", stats['Sixes'])
            st.metric("Death Overs Runs", stats['Death Overs Runs'])
            
    else:  # Bowler
        players = sorted(df['bowler'].unique())
        selected_player = st.selectbox("Select Bowler", players)
        stats, phase_stats, team_wise = calculate_player_stats(df, selected_player, 'bowler')
        
        # Display stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Wickets", stats['Wickets'])
        with col2:
            st.metric("Economy", f"{stats['Economy']:.2f}")
        with col3:
            st.metric("Average", f"{stats['Average']:.2f}")
        with col4:
            st.metric("Dot Balls", stats['Dot Balls'])
        
        # Phase-wise performance
        st.subheader("Phase-wise Performance")
        phase_df = pd.DataFrame({
            'Phase': list(phase_stats.keys()),
            'Wickets': [phase['Wickets'] for phase in phase_stats.values()],
            'Economy': [phase['Economy'] for phase in phase_stats.values()]
        })

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(name="Wickets", x=phase_df['Phase'], y=phase_df['Wickets']), secondary_y=False)
        fig.add_trace(go.Scatter(name="Economy", x=phase_df['Phase'], y=phase_df['Economy'], mode='lines+markers'), secondary_y=True)
        
        fig.update_layout(
            title="Phase-wise Bowling Performance",
            yaxis_title="Wickets",
            yaxis2_title="Economy Rate"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Team-wise performance
        st.subheader("Performance Against Teams")
        st.dataframe(team_wise.sort_values('Wickets', ascending=False))
        
        # Additional bowling insights
        st.subheader("Additional Insights")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Overs Bowled", stats['Overs Bowled'])
            st.metric("Powerplay Wickets", stats['Powerplay Wickets'])
        with col2:
            st.metric("Runs Conceded", stats['Runs Conceded'])
            st.metric("Death Overs Wickets", stats['Death Overs Wickets'])

def head_to_head_page(df):
    st.header("Head to Head Analysis")
    
    col1, col2 = st.columns(2)
    with col1:
        team1 = st.selectbox("Select First Team", sorted(df['batting_team'].unique()), key='team1')
    with col2:
        team2 = st.selectbox("Select Second Team", sorted(df['batting_team'].unique()), key='team2')
    
    if team1 != team2:
        team_stats, top_batsmen, top_bowlers = head_to_head_comparison(df, team1, team2)
        
        # Display team comparison
        st.subheader("Team Comparison")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"### {team1}")
            for stat, value in team_stats[team1].items():
                if isinstance(value, float):
                    st.metric(stat, f"{value:.2f}")
                else:
                    st.metric(stat, value)
        
        with col2:
            st.markdown(f"### {team2}")
            for stat, value in team_stats[team2].items():
                if isinstance(value, float):
                    st.metric(stat, f"{value:.2f}")
                else:
                    st.metric(stat, value)
        
        # Top performers
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Top Batsmen")
            st.dataframe(top_batsmen.head(10))
        
        with col2:
            st.subheader("Top Bowlers")
            st.dataframe(top_bowlers.head(10))
        
        # Head to head visualization
        st.subheader("Match-up Analysis")
        fig = go.Figure(data=[
            go.Bar(name=team1, x=['Runs Scored', 'Wickets Taken'], 
                  y=[team_stats[team1]['Total Runs Scored'], team_stats[team1]['Wickets Taken']]),
            go.Bar(name=team2, x=['Runs Scored', 'Wickets Taken'], 
                  y=[team_stats[team2]['Total Runs Scored'], team_stats[team2]['Wickets Taken']])
        ])
        fig.update_layout(barmode='group', title="Key Metrics Comparison")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Please select different teams for comparison")

def records_page(df):
    st.header("Records & Milestones")
    
    # Batting Records
    st.subheader("Batting Records")
    col1, col2 = st.columns(2)
    
    with col1:
        # Highest individual scores
        highest_scores = df.groupby(['match_id', 'batter'])['batsman_runs'].sum().sort_values(ascending=False)
        st.markdown("#### Highest Individual Scores")
        st.dataframe(highest_scores.head(10))
        
        # Most sixes
        most_sixes = df[df['batsman_runs'] == 6].groupby('batter').size().sort_values(ascending=False)
        st.markdown("#### Most Sixes")
        st.dataframe(most_sixes.head(10))
    
    with col2:
        # Fastest fifties (minimum 50 runs)
        fifties = df.groupby(['match_id', 'batter'])['batsman_runs'].agg(['sum', 'count']).reset_index()
        fifties = fifties[fifties['sum'] >= 50]
        fifties['balls_to_fifty'] = fifties['count']
        fifties = fifties.sort_values('balls_to_fifty').head(10)
        st.markdown("#### Fastest Fifties")
        st.dataframe(fifties[['batter', 'sum', 'balls_to_fifty']])
    
    # Bowling Records
    st.subheader("Bowling Records")
    col1, col2 = st.columns(2)
    
    with col1:
        # Best bowling figures
        bowling_figures = df.groupby(['match_id', 'bowler']).agg({
            'is_wicket': 'sum',
            'total_runs': 'sum'
        }).reset_index()
        bowling_figures = bowling_figures.sort_values(['is_wicket', 'total_runs'], ascending=[False, True])
        st.markdown("#### Best Bowling Figures")
        st.dataframe(bowling_figures.head(10))
    
    with col2:
        # Most dot balls
        dot_balls = df[df['batsman_runs'] == 0].groupby('bowler').size().sort_values(ascending=False)
        st.markdown("#### Most Dot Balls")
        st.dataframe(dot_balls.head(10))

def main():
    st.title("🏏 Advanced IPL Analytics Dashboard (2008-2024)")
    st.markdown("---")
    
    # Load data
    with st.spinner("Loading data..."):
        df = load_data()
    
    # Main Navigation
    pages = ["Team Analysis", "Player Profiles", "Head to Head Analysis", "Records & Milestones"]
    selected_page = st.sidebar.selectbox("Navigation", pages)
    
    if selected_page == "Team Analysis":
        team_analysis_page(df)
    elif selected_page == "Player Profiles":
        player_profiles_page(df)
    elif selected_page == "Head to Head Analysis":
        head_to_head_page(df)
    else:
        records_page(df)

if __name__ == "__main__":
    main()
