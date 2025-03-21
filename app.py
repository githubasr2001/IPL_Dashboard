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

# Custom CSS for styling
st.markdown(
    """
    <style>
    :root {
        --primary-bg: #f8f9fa;
        --secondary-bg: #ffffff;
        --text-color: #2c3e50;
        --accent-color: #007bff;
    }
    @media (prefers-color-scheme: dark) {
        :root {
            --primary-bg: #2c3e50;
            --secondary-bg: #1e1e1e;
            --text-color: #ecf0f1;
            --accent-color: #66b2ff;
        }
    }
    body {
        background-color: var(--primary-bg) !important;
        color: var(--text-color) !important;
    }
    [data-testid="stSidebar"] {
        background-color: var(--secondary-bg) !important;
        color: var(--text-color) !important;
    }
    .metric-card {
        background-color: var(--secondary-bg) !important;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    .chart-container {
        background-color: var(--secondary-bg) !important;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    .stButton>button {
        background-color: var(--accent-color);
        color: var(--secondary-bg);
        border: none;
        border-radius: 5px;
        padding: 0.5em 1em;
    }
    </style>
    """,
    unsafe_allow_html=True
)

@st.cache_data
def load_data():
    """Load the IPL deliveries dataset from a zip file."""
    try:
        with zipfile.ZipFile('deliveries.csv.zip') as z:
            with z.open('deliveries.csv') as file:
                df = pd.read_csv(file)
        
        # Standardize team names
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
    """Display head-to-head analysis between two teams."""
    st.header("Head to Head Analysis 🤝")
    
    col1, col2 = st.columns(2)
    with col1:
        team1 = st.selectbox("Select Team 1", sorted(df['batting_team'].unique()))
    with col2:
        team2 = st.selectbox("Select Team 2", sorted(df['bowling_team'].unique()))
        
    if team1 and team2:
        if team1 == team2:
            st.error("Please select two different teams for head-to-head analysis.")
            return
        
        team_vs_team = df[
            ((df['batting_team'] == team1) & (df['bowling_team'] == team2)) |
            ((df['batting_team'] == team2) & (df['bowling_team'] == team1))
        ]
        
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
        team1_highest = team1_stats.groupby('match_id')['total_runs'].sum().max() or 0
        
        # Team 2 Metrics
        team2_runs = team2_stats['total_runs'].sum()
        team2_balls = len(team2_stats)
        team2_overs = team2_balls / 6
        team2_rr = team2_runs / team2_overs if team2_overs > 0 else 0
        team2_wickets = team_vs_team[team_vs_team['bowling_team'] == team2]['is_wicket'].sum()
        team2_runs_conceded = team1_stats['total_runs'].sum()
        team2_overs_bowled = len(team1_stats) / 6
        team2_economy = team2_runs_conceded / team2_overs_bowled if team2_overs_bowled > 0 else 0
        team2_highest = team2_stats.groupby('match_id')['total_runs'].sum().max() or 0
        
        st.subheader("Individual Innings Statistics")
        colA, colB = st.columns(2)
        with colA:
            st.markdown(f"### {team1} Statistics")
            st.metric("Total Runs", f"{team1_runs:,.0f}")
            st.metric("Run Rate", f"{team1_rr:.2f}")
            st.metric("Wickets Taken", f"{team1_wickets}")
            st.metric("Economy Rate", f"{team1_economy:.2f}")
            st.metric("Overs Bowled", f"{team1_overs_bowled:.1f}")
            st.metric("Runs Conceded", f"{team1_runs_conceded:,.0f}")
            st.metric("Highest Innings Score", f"{team1_highest:,.0f}")
        with colB:
            st.markdown(f"### {team2} Statistics")
            st.metric("Total Runs", f"{team2_runs:,.0f}")
            st.metric("Run Rate", f"{team2_rr:.2f}")
            st.metric("Wickets Taken", f"{team2_wickets}")
            st.metric("Economy Rate", f"{team2_economy:.2f}")
            st.metric("Overs Bowled", f"{team2_overs_bowled:.1f}")
            st.metric("Runs Conceded", f"{team2_runs_conceded:,.0f}")
            st.metric("Highest Innings Score", f"{team2_highest:,.0f}")
        
        match_summary = (
            df[df['batting_team'].isin([team1, team2])]
            .groupby(['match_id', 'batting_team'])['total_runs']
            .sum()
            .reset_index()
        )
        match_pivot = match_summary.pivot(index='match_id', columns='batting_team', values='total_runs')
        match_pivot = match_pivot.dropna()
        
        matches_played = len(match_pivot)
        team1_wins = (match_pivot[team1] > match_pivot[team2]).sum()
        team2_wins = (match_pivot[team2] > match_pivot[team1]).sum()
        ties = (match_pivot[team1] == match_pivot[team2]).sum()
        
        st.subheader("Match Results")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Matches Played", f"{matches_played}")
        with col2:
            st.metric(f"{team1} Wins", f"{team1_wins}")
        with col3:
            st.metric(f"{team2} Wins", f"{team2_wins}")
        with col4:
            st.metric("Tied Matches", f"{ties}")
        
        st.subheader("Phase-wise Analysis")
        def get_phase_stats(team_data, phase_start, phase_end):
            phase_df = team_data[(team_data['over'] >= phase_start) & (team_data['over'] <= phase_end)]
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
            st.write(f"**{phase_name}**")
            t1_runs, t1_rr, t1_wickets, t1_eco = get_phase_stats(team1_stats, start, end)
            t2_runs, t2_rr, t2_wickets, t2_eco = get_phase_stats(team2_stats, start, end)
            
            colX, colY = st.columns(2)
            with colX:
                st.metric(f"{team1} Runs", f"{t1_runs:.0f}")
                st.metric("Run Rate", f"{t1_rr:.2f}")
                st.metric("Wickets", f"{t1_wickets}")
                st.metric("Economy", f"{t1_eco:.2f}")
            with colY:
                st.metric(f"{team2} Runs", f"{t2_runs:.0f}")
                st.metric("Run Rate", f"{t2_rr:.2f}")
                st.metric("Wickets", f"{t2_wickets}")
                st.metric("Economy", f"{t2_eco:.2f}")
    else:
        st.info("Please select two teams.")

def player_analysis_page(df):
    """Display detailed analysis for a selected batsman or bowler."""
    st.header("Player Analysis 🏃")
    
    player_type = st.radio("Select Player Type", ["Batsman", "Bowler"])
    
    if player_type == "Batsman":
        player = st.selectbox("Select Batsman", sorted(df['batter'].unique()))
        if player:
            player_df = df[df['batter'] == player]
            total_runs = player_df['batsman_runs'].sum()
            balls_faced = len(player_df)
            strike_rate = (total_runs / balls_faced * 100) if balls_faced > 0 else 0
            fours = len(player_df[player_df['batsman_runs'] == 4])
            sixes = len(player_df[player_df['batsman_runs'] == 6])
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Runs", f"{total_runs:,}")
            with col2:
                st.metric("Strike Rate", f"{strike_rate:.2f}")
            with col3:
                st.metric("Fours", f"{fours}")
            with col4:
                st.metric("Sixes", f"{sixes}")
            
            st.subheader("Performance Against Teams")
            team_stats = player_df.groupby('bowling_team').agg({
                'batsman_runs': 'sum',
                'batter': 'size',
                'is_wicket': 'sum'
            }).reset_index()
            team_stats['Strike Rate'] = (team_stats['batsman_runs'] / team_stats['batter'] * 100).round(2)
            team_stats['Average'] = (team_stats['batsman_runs'] / team_stats['is_wicket'].replace(0, 1)).round(2)
            
            fig1 = px.bar(team_stats, x='bowling_team', y='batsman_runs',
                          title=f"{player}'s Runs Against Different Teams",
                          labels={'bowling_team': 'Team', 'batsman_runs': 'Runs'})
            st.plotly_chart(fig1, use_container_width=True)
            
            fig2 = px.scatter(team_stats, x='Strike Rate', y='Average', size='batsman_runs',
                              hover_data=['bowling_team'],
                              title=f"{player}'s Performance Metrics Against Teams")
            st.plotly_chart(fig2, use_container_width=True)
            
            st.subheader("Detailed Statistics by Team")
            detailed_stats = team_stats.rename(columns={
                'bowling_team': 'Team',
                'batsman_runs': 'Runs',
                'batter': 'Balls Faced',
                'is_wicket': 'Dismissals'
            })
            st.dataframe(detailed_stats, use_container_width=True)
            
    else:  # Bowler analysis
        player = st.selectbox("Select Bowler", sorted(df['bowler'].unique()))
        if player:
            player_df = df[df['bowler'] == player]
            total_wickets = player_df['is_wicket'].sum()
            balls_bowled = len(player_df)
            overs = balls_bowled / 6
            runs_conceded = player_df['total_runs'].sum()
            economy = (runs_conceded / overs) if overs > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Wickets", f"{total_wickets}")
            with col2:
                st.metric("Overs Bowled", f"{overs:.1f}")
            with col3:
                st.metric("Runs Conceded", f"{runs_conceded}")
            with col4:
                st.metric("Economy", f"{economy:.2f}")
            
            st.subheader("Performance Against Teams")
            team_stats = player_df.groupby('batting_team').agg({
                'is_wicket': 'sum',
                'total_runs': 'sum',
                'bowler': 'size'
            }).reset_index()
            team_stats['Overs'] = (team_stats['bowler'] / 6).round(1)
            team_stats['Economy'] = (team_stats['total_runs'] / team_stats['Overs']).round(2)
            
            fig1 = px.bar(team_stats, x='batting_team', y='is_wicket',
                          title=f"{player}'s Wickets Against Different Teams",
                          labels={'batting_team': 'Team', 'is_wicket': 'Wickets'})
            st.plotly_chart(fig1, use_container_width=True)
            
            fig2 = px.scatter(team_stats, x='Economy', y='is_wicket', size='Overs',
                              hover_data=['batting_team'],
                              title=f"{player}'s Performance Metrics Against Teams")
            st.plotly_chart(fig2, use_container_width=True)
            
            st.subheader("Detailed Statistics by Team")
            detailed_stats = team_stats.rename(columns={
                'batting_team': 'Team',
                'is_wicket': 'Wickets',
                'total_runs': 'Runs Conceded',
                'bowler': 'Balls Bowled'
            })
            st.dataframe(detailed_stats, use_container_width=True)

def milestones_page(df):
    """Display IPL milestones and records."""
    st.header("Milestones & Records 🏆")
    
    tab1, tab2, tab3 = st.tabs(["Batting Records", "Bowling Records", "Team Records"])
    
    with tab1:
        st.subheader("Batting Milestones")
        st.write("### Fastest Fifties")
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
        fastest_fifties = calculate_fastest_fifties(df)
        st.dataframe(fastest_fifties)
        
        st.write("### Most Sixes")
        most_sixes = (df[df['batsman_runs'] == 6]
                      .groupby('batter', as_index=False)
                      .size()
                      .rename(columns={'size': 'Sixes'})
                      .sort_values('Sixes', ascending=False)
                      .head(10))
        st.dataframe(most_sixes)
        
    with tab2:
        st.subheader("Bowling Records")
        st.write("### Most Wickets")
        most_wickets = (df.groupby('bowler', as_index=False)['is_wicket']
                        .sum()
                        .sort_values('is_wicket', ascending=False)
                        .head(10))
        st.dataframe(most_wickets)
        
    with tab3:
        st.subheader("Team Records")
        st.write("### Highest Team Totals")
        highest_totals = (df.groupby(['match_id', 'batting_team'], as_index=False)['total_runs']
                          .sum()
                          .sort_values('total_runs', ascending=False)
                          .head(10))
        st.dataframe(highest_totals)

def batsman_vs_bowler_page(df):
    """Display head-to-head analysis between a batsman and a bowler."""
    st.header("Batsman vs Bowler Analysis ⚔️")
    
    # Dropdowns for selecting batsman and bowler
    col1, col2 = st.columns(2)
    with col1:
        batsman = st.selectbox("Select Batsman", sorted(df['batter'].unique()))
    with col2:
        bowler = st.selectbox("Select Bowler", sorted(df['bowler'].unique()))
    
    if batsman and bowler:
        # Filter data for the selected batsman and bowler
        filtered_df = df[(df['batter'] == batsman) & (df['bowler'] == bowler)]
        
        if filtered_df.empty:
            st.warning(f"No data available for {batsman} against {bowler}.")
        else:
            # Calculate overall statistics
            balls_faced = len(filtered_df)
            runs_scored = filtered_df['batsman_runs'].sum()
            dismissals = filtered_df['is_wicket'].sum()
            average = runs_scored / dismissals if dismissals > 0 else float('inf')
            strike_rate = (runs_scored / balls_faced * 100) if balls_faced > 0 else 0
            
            # Display overall statistics
            st.subheader(f"{batsman} vs {bowler}")
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Runs Scored", f"{runs_scored}")
            with col2:
                st.metric("Balls Faced", f"{balls_faced}")
            with col3:
                st.metric("Times Dismissed", f"{dismissals}")
            with col4:
                st.metric("Batting Average", f"{average:.2f}" if dismissals > 0 else "N/A")
            with col5:
                st.metric("Strike Rate", f"{strike_rate:.2f}")
            
            # Per-innings performance
            match_stats = filtered_df.groupby(['match_id', 'inning']).agg({
                'batsman_runs': 'sum',
                'batter': 'size',  # Number of balls
                'is_wicket': 'sum'
            }).reset_index()
            match_stats['Dismissed'] = match_stats['is_wicket'].apply(lambda x: 'Yes' if x > 0 else 'No')
            match_stats['Strike Rate'] = (match_stats['batsman_runs'] / match_stats['batter'] * 100).round(2)
            match_stats = match_stats.rename(columns={'batsman_runs': 'Runs', 'batter': 'Balls'})
            match_stats = match_stats.sort_values(['match_id', 'inning'])
            
            # Cumulative statistics for visualization
            match_stats['Cumulative Runs'] = match_stats['Runs'].cumsum()
            match_stats['Cumulative Dismissals'] = match_stats['is_wicket'].cumsum()
            
            # Plot cumulative runs and dismissals
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(
                go.Scatter(x=match_stats.index, y=match_stats['Cumulative Runs'], name='Cumulative Runs', line=dict(color='blue')),
                secondary_y=False,
            )
            fig.add_trace(
                go.Scatter(x=match_stats.index, y=match_stats['Cumulative Dismissals'], name='Cumulative Dismissals', line=dict(color='red')),
                secondary_y=True,
            )
            fig.update_layout(
                title=f"{batsman} vs {bowler}: Performance Over Time",
                xaxis_title="Innings",
                yaxis_title="Cumulative Runs",
                yaxis2_title="Cumulative Dismissals",
                legend=dict(x=0.01, y=0.99),
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Display per-innings performance table
            st.subheader("Per-Innings Performance")
            st.dataframe(match_stats[['match_id', 'inning', 'Runs', 'Balls', 'Dismissed', 'Strike Rate']], use_container_width=True)
            
            st.info("For detailed player statistics, visit the Player Analysis page.")
    else:
        st.info("Please select both a batsman and a bowler.")

def main():
    """Main function to run the IPL Analytics Dashboard."""
    st.title("🏏 IPL Analytics Dashboard (2008-2024)")
    df = load_data()
    if df is None:
        return
    
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Select Page", 
                            ["Head to Head Analysis",
                             "Player Analysis",
                             "Milestones & Records",
                             "Batsman vs Bowler Analysis"])
    
    if page == "Head to Head Analysis":
        head_to_head_page(df)
    elif page == "Player Analysis":
        player_analysis_page(df)
    elif page == "Milestones & Records":
        milestones_page(df)
    elif page == "Batsman vs Bowler Analysis":
        batsman_vs_bowler_page(df)
    
    st.sidebar.markdown("---")
    st.sidebar.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d')}")

if __name__ == "__main__":
    main()
