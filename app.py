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

# Custom CSS with dark/light mode support (removed problematic CSS block)
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
    .css-1d391kg {
        background-color: var(--secondary-bg) !important;
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
        if team1 == team2:
            st.error("Please select two different teams for head-to-head analysis.")
            return
        
        # Filter ball-by-ball records for matches between the two teams
        team_vs_team = df[
            ((df['batting_team'] == team1) & (df['bowling_team'] == team2)) |
            ((df['batting_team'] == team2) & (df['bowling_team'] == team1))
        ]
        
        # Detailed ball-by-ball metrics (each team's innings)
        team1_stats = team_vs_team[team_vs_team['batting_team'] == team1]
        team2_stats = team_vs_team[team_vs_team['batting_team'] == team2]
        
        # Team 1 Metrics
        team1_runs = team1_stats['total_runs'].sum()
        team1_balls = len(team1_stats)
        team1_overs = team1_balls / 6
        team1_rr = team1_runs / team1_overs if team1_overs > 0 else 0
        team1_wickets = team_vs_team[team_vs_team['bowling_team'] == team1]['is_wicket'].sum()
        team1_overs_bowled = len(team2_stats) / 6
        team1_economy = team1_runs / team1_overs if team1_overs > 0 else 0
        team1_highest = team1_stats.groupby('match_id')['total_runs'].sum().max() or 0
        
        # Team 2 Metrics
        team2_runs = team2_stats['total_runs'].sum()
        team2_balls = len(team2_stats)
        team2_overs = team2_balls / 6
        team2_rr = team2_runs / team2_overs if team2_overs > 0 else 0
        team2_wickets = team_vs_team[team_vs_team['bowling_team'] == team2]['is_wicket'].sum()
        team2_overs_bowled = len(team1_stats) / 6
        team2_economy = team2_runs / team2_overs if team2_overs > 0 else 0
        team2_highest = team2_stats.groupby('match_id')['total_runs'].sum().max() or 0
        
        # Display individual innings statistics
        st.subheader("Individual Innings Statistics")
        colA, colB = st.columns(2)
        with colA:
            st.markdown(f"### {team1} Statistics")
            st.metric("Total Runs", f"{team1_runs:,.0f}")
            st.metric("Run Rate", f"{team1_rr:.2f}")
            st.metric("Wickets Taken", f"{team1_wickets}")
            st.metric("Economy Rate", f"{team1_economy:.2f}")
            st.metric("Overs Bowled", f"{team1_overs_bowled:.1f}")
            st.metric("Highest Innings Score", f"{team1_highest:,.0f}")
        with colB:
            st.markdown(f"### {team2} Statistics")
            st.metric("Total Runs", f"{team2_runs:,.0f}")
            st.metric("Run Rate", f"{team2_rr:.2f}")
            st.metric("Wickets Taken", f"{team2_wickets}")
            st.metric("Economy Rate", f"{team2_economy:.2f}")
            st.metric("Overs Bowled", f"{team2_overs_bowled:.1f}")
            st.metric("Highest Innings Score", f"{team2_highest:,.0f}")
        
        # Compute match-level results (only consider matches where both teams played)
        match_summary = (
            df[df['batting_team'].isin([team1, team2])]
            .groupby(['match_id', 'batting_team'])['total_runs']
            .sum()
            .reset_index()
        )
        match_pivot = match_summary.pivot(index='match_id', columns='batting_team', values='total_runs')
        match_pivot = match_pivot.dropna()  # only matches where both teams batted
        
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
        
        # Phase-wise Analysis (Powerplay, Middle, Death)
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
                
        # Batsman vs Bowler Analysis
        st.subheader("Batsman vs Bowler Analysis 🏏")
        
        # Get top batsmen from team1
        team1_batsmen = (team1_stats.groupby('batter')['batsman_runs']
                         .sum()
                         .sort_values(ascending=False)
                         .head(10)
                         .index.tolist())
        
        # Get top batsmen from team2
        team2_batsmen = (team2_stats.groupby('batter')['batsman_runs']
                         .sum()
                         .sort_values(ascending=False)
                         .head(10)
                         .index.tolist())
        
        # Get top bowlers from team1
        team1_bowlers = (team_vs_team[team_vs_team['bowling_team'] == team1]
                         .groupby('bowler')['is_wicket']
                         .sum()
                         .sort_values(ascending=False)
                         .head(10)
                         .index.tolist())
        
        # Get top bowlers from team2
        team2_bowlers = (team_vs_team[team_vs_team['bowling_team'] == team2]
                         .groupby('bowler')['is_wicket']
                         .sum()
                         .sort_values(ascending=False)
                         .head(10)
                         .index.tolist())
        
        tab1, tab2 = st.tabs([f"{team1} Batsmen vs {team2} Bowlers", f"{team2} Batsmen vs {team1} Bowlers"])
        
        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                selected_batsman = st.selectbox(f"Select {team1} Batsman", sorted(team1_batsmen))
            with col2:
                selected_bowler = st.selectbox(f"Select {team2} Bowler", sorted(team2_bowlers))
            
            if selected_batsman and selected_bowler:
                # Filter for specific batsman-bowler combination
                matchup_df = team_vs_team[
                    (team_vs_team['batter'] == selected_batsman) & 
                    (team_vs_team['bowler'] == selected_bowler)
                ]
                
                total_balls = len(matchup_df)
                total_runs = matchup_df['batsman_runs'].sum()
                wickets = matchup_df['is_wicket'].sum()
                dot_balls = len(matchup_df[matchup_df['batsman_runs'] == 0])
                fours = len(matchup_df[matchup_df['batsman_runs'] == 4])
                sixes = len(matchup_df[matchup_df['batsman_runs'] == 6])
                sr = (total_runs / total_balls * 100) if total_balls > 0 else 0
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Balls", f"{total_balls}")
                    st.metric("Total Runs", f"{total_runs}")
                with col2:
                    st.metric("Wickets", f"{wickets}")
                    st.metric("Strike Rate", f"{sr:.2f}")
                with col3:
                    st.metric("Dot Balls", f"{dot_balls} ({dot_balls/total_balls*100:.1f}%)" if total_balls > 0 else "0")
                    st.metric("Boundaries", f"{fours} fours, {sixes} sixes")
                
                # Run distribution pie chart
                run_counts = matchup_df['batsman_runs'].value_counts().sort_index().reset_index()
                run_counts.columns = ['Runs', 'Count']
                
                fig = px.pie(
                    run_counts, 
                    values='Count', 
                    names='Runs',
                    title=f"Run Distribution: {selected_batsman} vs {selected_bowler}",
                    color_discrete_sequence=px.colors.sequential.Blues
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            col1, col2 = st.columns(2)
            with col1:
                selected_batsman = st.selectbox(f"Select {team2} Batsman", sorted(team2_batsmen))
            with col2:
                selected_bowler = st.selectbox(f"Select {team1} Bowler", sorted(team1_bowlers))
            
            if selected_batsman and selected_bowler:
                # Filter for specific batsman-bowler combination
                matchup_df = team_vs_team[
                    (team_vs_team['batter'] == selected_batsman) & 
                    (team_vs_team['bowler'] == selected_bowler)
                ]
                
                total_balls = len(matchup_df)
                total_runs = matchup_df['batsman_runs'].sum()
                wickets = matchup_df['is_wicket'].sum()
                dot_balls = len(matchup_df[matchup_df['batsman_runs'] == 0])
                fours = len(matchup_df[matchup_df['batsman_runs'] == 4])
                sixes = len(matchup_df[matchup_df['batsman_runs'] == 6])
                sr = (total_runs / total_balls * 100) if total_balls > 0 else 0
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Balls", f"{total_balls}")
                    st.metric("Total Runs", f"{total_runs}")
                with col2:
                    st.metric("Wickets", f"{wickets}")
                    st.metric("Strike Rate", f"{sr:.2f}")
                with col3:
                    st.metric("Dot Balls", f"{dot_balls} ({dot_balls/total_balls*100:.1f}%)" if total_balls > 0 else "0")
                    st.metric("Boundaries", f"{fours} fours, {sixes} sixes")
                
                # Run distribution pie chart
                run_counts = matchup_df['batsman_runs'].value_counts().sort_index().reset_index()
                run_counts.columns = ['Runs', 'Count']
                
                fig = px.pie(
                    run_counts, 
                    values='Count', 
                    names='Runs',
                    title=f"Run Distribution: {selected_batsman} vs {selected_bowler}",
                    color_discrete_sequence=px.colors.sequential.Blues
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Please select two teams.")

def analyze_batsman(df, player):
    player_df = df[df['batter'] == player]
    total_runs = player_df['batsman_runs'].sum()
    total_balls = len(player_df)
    dismissals = player_df['is_wicket'].sum()
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
    three_wicket_hauls = len(player_df.groupby('match_id')['is_wicket'].sum()[
        player_df.groupby('match_id')['is_wicket'].sum() >= 3
    ])
    
    return {
        'wickets': wickets,
        'economy': runs / overs if overs > 0 else 0,
        'average': runs / wickets if wickets > 0 else float('inf'),
        'best_bowling': f"{player_df.groupby('match_id')['is_wicket'].sum().max()}/{player_df.groupby('match_id')['total_runs'].sum().min()}",
        'three_wicket_hauls': three_wicket_hauls,
        'overs_bowled': overs,
        'runs_conceded': runs
    }

def player_analysis_page(df):
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
            
            fig1 = px.bar(team_stats, 
                          x='bowling_team', 
                          y='batsman_runs',
                          title=f"{player}'s Runs Against Different Teams",
                          labels={'bowling_team': 'Team', 'batsman_runs': 'Runs'})
            st.plotly_chart(fig1, use_container_width=True)
            
            fig2 = px.scatter(team_stats,
                              x='Strike Rate',
                              y='Average',
                              size='batsman_runs',
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
            
            # Add Batsman vs Bowler Analysis
            st.subheader("Batsman vs Specific Bowlers")
            bowler_stats = (player_df.groupby('bowler').agg({
                'batsman_runs': 'sum',
                'batter': 'size',
                'is_wicket': 'sum'
            }).reset_index())
            
            bowler_stats['Strike Rate'] = (bowler_stats['batsman_runs'] / bowler_stats['batter'] * 100).round(2)
            bowler_stats = bowler_stats[bowler_stats['batter'] >= 6]  # At least 1 over faced
            bowler_stats = bowler_stats.sort_values('batsman_runs', ascending=False).head(10)
            
            st.dataframe(bowler_stats.rename(columns={
                'bowler': 'Bowler',
                'batsman_runs': 'Runs',
                'batter': 'Balls Faced',
                'is_wicket': 'Dismissals'
            }), use_container_width=True)
            
            # Select specific bowler for detailed analysis
            selected_bowler = st.selectbox(
                "Select a bowler for detailed analysis", 
                sorted(bowler_stats['bowler'].tolist())
            )
            
            if selected_bowler:
                # Filter for specific batsman-bowler combination
                matchup_df = player_df[player_df['bowler'] == selected_bowler]
                
                total_balls = len(matchup_df)
                total_runs = matchup_df['batsman_runs'].sum()
                wickets = matchup_df['is_wicket'].sum()
                dot_balls = len(matchup_df[matchup_df['batsman_runs'] == 0])
                fours = len(matchup_df[matchup_df['batsman_runs'] == 4])
                sixes = len(matchup_df[matchup_df['batsman_runs'] == 6])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Balls", f"{total_balls}")
                    st.metric("Total Runs", f"{total_runs}")
                with col2:
                    st.metric("Wickets", f"{wickets}")
                    st.metric("Strike Rate", f"{(total_runs / total_balls * 100):.2f}" if total_balls > 0 else "0")
                with col3:
                    st.metric("Dot Balls", f"{dot_balls} ({dot_balls/total_balls*100:.1f}%)" if total_balls > 0 else "0")
                    st.metric("Boundaries", f"{fours} fours, {sixes} sixes")
                
                # Run distribution pie chart
                run_counts = matchup_df['batsman_runs'].value_counts().sort_index().reset_index()
                run_counts.columns = ['Runs', 'Count']
                
                fig = px.pie(
                    run_counts, 
                    values='Count', 
                    names='Runs',
                    title=f"Run Distribution: {player} vs {selected_bowler}",
                    color_discrete_sequence=px.colors.sequential.Blues
                )
                st.plotly_chart(fig, use_container_width=True)
            
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
            
            fig1 = px.bar(team_stats,
                          x='batting_team',
                          y='is_wicket',
                          title=f"{player}'s Wickets Against Different Teams",
                          labels={'batting_team': 'Team', 'is_wicket': 'Wickets'})
            st.plotly_chart(fig1, use_container_width=True)
            
            fig2 = px.scatter(team_stats,
                              x='Economy',
                              y='is_wicket',
                              size='Overs',
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
            
            # Add Bowler vs Batsman Analysis
            st.subheader("Bowler vs Specific Batsmen")
            batsman_stats = (player_df.groupby('batter').agg({
                'batsman_runs': 'sum',
                'bowler': 'size',
                'is_wicket': 'sum'
            }).reset_index())
            
            batsman_stats['Economy'] = (batsman_stats['batsman_runs'] / (batsman_stats['bowler']/6)).round(2)
            batsman_stats = batsman_stats[batsman_stats['bowler'] >= 6]  # At least 1 over
            batsman_stats = batsman_stats.sort_values('is_wicket', ascending=False).head(10)
            
            st.dataframe(batsman_stats.rename(columns={
                'batter': 'Batsman',
                'batsman_runs': 'Runs Conceded',
                'bowler': 'Balls Bowled',
                'is_wicket': 'Wickets Taken'
            }), use_container_width=True)
            
            # Select specific batsman for detailed analysis
            selected_batsman = st.selectbox(
                "Select a batsman for detailed analysis", 
                sorted(batsman_stats['batter'].tolist())
            )
            
            if selected_batsman:
                # Filter for specific bowler-batsman combination
                matchup_df = player_df[player_df['batter'] == selected_batsman]
                
                total_balls = len(matchup_df)
                total_runs = matchup_df['batsman_runs'].sum()
                wickets = matchup_df['is_wicket'].sum()
                dot_balls = len(matchup_df[matchup_df['batsman_runs'] == 0])
                fours = len(matchup_df[matchup_df['batsman_runs'] == 4])
                sixes = len(matchup_df[matchup_df['batsman_runs'] == 6])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Balls", f"{total_balls}")
                    st.metric("Total Wickets", f"{wickets}")
                with col2:
                    
                    st.metric("Runs Conceded", f"{total_runs}")
                    st.metric("Economy", f"{(total_runs * 6 / total_balls):.2f}" if total_balls > 0 else "0")
                with col3:
                    st.metric("Dot Balls", f"{dot_balls} ({dot_balls/total_balls*100:.1f}%)" if total_balls > 0 else "0")
                    st.metric("Boundaries Conceded", f"{fours} fours, {sixes} sixes")
                
                # Run distribution pie chart
                run_counts = matchup_df['batsman_runs'].value_counts().sort_index().reset_index()
                run_counts.columns = ['Runs', 'Count']
                
                fig = px.pie(
                    run_counts, 
                    values='Count', 
                    names='Runs',
                    title=f"Run Distribution: {player} vs {selected_batsman}",
                    color_discrete_sequence=px.colors.sequential.Reds
                )
                st.plotly_chart(fig, use_container_width=True)

def team_analysis_page(df):
    st.header("Team Analysis 🏏")
    
    team = st.selectbox("Select Team", sorted(df['batting_team'].unique()))
    
    if team:
        # Team as batting team
        batting_df = df[df['batting_team'] == team]
        
        # Team as bowling team
        bowling_df = df[df['bowling_team'] == team]
        
        # Overall team stats
        total_runs_scored = batting_df['total_runs'].sum()
        total_runs_conceded = bowling_df['total_runs'].sum()
        total_wickets_taken = bowling_df['is_wicket'].sum()
        total_wickets_lost = batting_df['is_wicket'].sum()
        
        st.subheader("Team Overview")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Runs Scored", f"{total_runs_scored:,}")
        with col2:
            st.metric("Total Runs Conceded", f"{total_runs_conceded:,}")
        with col3:
            st.metric("Wickets Taken", f"{total_wickets_taken}")
        with col4:
            st.metric("Wickets Lost", f"{total_wickets_lost}")
        
        # Get unique seasons/years
        df['season'] = df['match_id'].astype(str).str[:4].astype(int)
        seasons = sorted(df['season'].unique())
        
        # Performance over seasons
        st.subheader("Performance Over Seasons")
        season_batting = (batting_df.groupby('season')['total_runs']
                         .sum()
                         .reset_index())
        season_bowling = (bowling_df.groupby('season')['total_runs']
                         .sum()
                         .reset_index())
        
        # Create season performance figure
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(
            go.Bar(
                x=season_batting['season'],
                y=season_batting['total_runs'],
                name="Runs Scored",
                marker_color='blue'
            )
        )
        
        fig.add_trace(
            go.Bar(
                x=season_bowling['season'],
                y=season_bowling['total_runs'],
                name="Runs Conceded",
                marker_color='red'
            )
        )
        
        fig.update_layout(
            title=f"{team}'s Performance Over Seasons",
            xaxis_title="Season",
            yaxis_title="Runs",
            barmode='group',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Top performers
        st.subheader("Top Performers")
        
        tab1, tab2 = st.tabs(["Batting", "Bowling"])
        
        with tab1:
            # Top batsmen for the team
            top_batsmen = (batting_df.groupby('batter')['batsman_runs']
                        .sum()
                        .sort_values(ascending=False)
                        .head(10)
                        .reset_index())
            
            fig1 = px.bar(
                top_batsmen,
                x='batter',
                y='batsman_runs',
                title=f"Top 10 Run Scorers for {team}",
                labels={'batter': 'Batsman', 'batsman_runs': 'Runs'},
                color='batsman_runs',
                color_continuous_scale=px.colors.sequential.Blues
            )
            st.plotly_chart(fig1, use_container_width=True)
            
            # Calculate detailed stats for top 5 batsmen
            top5_batsmen = top_batsmen.head(5)['batter'].tolist()
            batsmen_stats = []
            
            for batsman in top5_batsmen:
                stats = analyze_batsman(batting_df, batsman)
                stats['name'] = batsman
                batsmen_stats.append(stats)
            
            batsmen_df = pd.DataFrame(batsmen_stats)
            batsmen_df = batsmen_df[[
                'name', 'total_runs', 'balls_faced', 'strike_rate', 'average',
                'fours', 'sixes', 'fifties', 'centuries', 'highest_score'
            ]]
            
            st.dataframe(batsmen_df.rename(columns={
                'name': 'Batsman',
                'total_runs': 'Runs',
                'balls_faced': 'Balls',
                'strike_rate': 'Strike Rate',
                'average': 'Average',
                'fours': 'Fours',
                'sixes': 'Sixes',
                'fifties': 'Fifties',
                'centuries': 'Centuries',
                'highest_score': 'Highest Score'
            }).set_index('Batsman'), use_container_width=True)
        
        with tab2:
            # Top bowlers for the team
            top_bowlers = (bowling_df.groupby('bowler')['is_wicket']
                        .sum()
                        .sort_values(ascending=False)
                        .head(10)
                        .reset_index())
            
            fig2 = px.bar(
                top_bowlers,
                x='bowler',
                y='is_wicket',
                title=f"Top 10 Wicket Takers for {team}",
                labels={'bowler': 'Bowler', 'is_wicket': 'Wickets'},
                color='is_wicket',
                color_continuous_scale=px.colors.sequential.Reds
            )
            st.plotly_chart(fig2, use_container_width=True)
            
            # Calculate detailed stats for top 5 bowlers
            top5_bowlers = top_bowlers.head(5)['bowler'].tolist()
            bowlers_stats = []
            
            for bowler in top5_bowlers:
                stats = analyze_bowler(bowling_df, bowler)
                stats['name'] = bowler
                bowlers_stats.append(stats)
            
            bowlers_df = pd.DataFrame(bowlers_stats)
            bowlers_df = bowlers_df[[
                'name', 'wickets', 'overs_bowled', 'runs_conceded',
                'economy', 'average', 'three_wicket_hauls', 'best_bowling'
            ]]
            
            st.dataframe(bowlers_df.rename(columns={
                'name': 'Bowler',
                'wickets': 'Wickets',
                'overs_bowled': 'Overs',
                'runs_conceded': 'Runs Conceded',
                'economy': 'Economy',
                'average': 'Average',
                'three_wicket_hauls': '3+ Wickets',
                'best_bowling': 'Best Bowling'
            }).set_index('Bowler'), use_container_width=True)
        
        # Opposition analysis
        st.subheader("Performance Against Opposition")
        
        # Batting performance against teams
        batting_vs_teams = (batting_df.groupby('bowling_team')
                           .agg({'total_runs': 'sum', 'is_wicket': 'sum'})
                           .reset_index())
        batting_vs_teams['avg_runs_per_wicket'] = (
            batting_vs_teams['total_runs'] / batting_vs_teams['is_wicket'].replace(0, 1)
        ).round(2)
        
        # Bowling performance against teams
        bowling_vs_teams = (bowling_df.groupby('batting_team')
                           .agg({'total_runs': 'sum', 'is_wicket': 'sum'})
                           .reset_index())
        bowling_vs_teams['avg_runs_per_wicket'] = (
            bowling_vs_teams['total_runs'] / bowling_vs_teams['is_wicket'].replace(0, 1)
        ).round(2)
        
        tab3, tab4 = st.tabs(["Batting vs Teams", "Bowling vs Teams"])
        
        with tab3:
            fig3 = px.bar(
                batting_vs_teams,
                x='bowling_team',
                y='total_runs',
                title=f"{team}'s Batting Performance Against Different Teams",
                labels={'bowling_team': 'Opposition', 'total_runs': 'Runs Scored'},
                color='avg_runs_per_wicket',
                color_continuous_scale=px.colors.sequential.Blues,
                hover_data=['is_wicket', 'avg_runs_per_wicket']
            )
            st.plotly_chart(fig3, use_container_width=True)
        
        with tab4:
            fig4 = px.bar(
                bowling_vs_teams,
                x='batting_team',
                y='is_wicket',
                title=f"{team}'s Bowling Performance Against Different Teams",
                labels={'batting_team': 'Opposition', 'is_wicket': 'Wickets Taken'},
                color='avg_runs_per_wicket',
                color_continuous_scale=px.colors.sequential.Reds_r,  # Reversed so that lower avg is better
                hover_data=['total_runs', 'avg_runs_per_wicket']
            )
            st.plotly_chart(fig4, use_container_width=True)

def tournament_stats_page(df):
    st.header("Tournament Statistics 🏆")
    
    # Season selector
    df['season'] = df['match_id'].astype(str).str[:4].astype(int)
    seasons = sorted(df['season'].unique())
    selected_season = st.selectbox("Select Season", seasons, index=len(seasons)-1)
    
    season_data = df[df['season'] == selected_season]
    
    # Overall tournament metrics
    total_matches = season_data['match_id'].nunique()
    total_runs = season_data['total_runs'].sum()
    total_fours = len(season_data[season_data['batsman_runs'] == 4])
    total_sixes = len(season_data[season_data['batsman_runs'] == 6])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Matches", f"{total_matches}")
    with col2:
        st.metric("Total Runs", f"{total_runs:,}")
    with col3:
        st.metric("Total Fours", f"{total_fours:,}")
    with col4:
        st.metric("Total Sixes", f"{total_sixes:,}")
    
    st.subheader("Team Performance")
    
    # Team runs scored in the season
    team_runs = (season_data.groupby('batting_team')['total_runs']
                .sum()
                .sort_values(ascending=False)
                .reset_index())
    
    fig1 = px.bar(
        team_runs,
        x='batting_team',
        y='total_runs',
        title=f"Runs Scored by Teams in {selected_season}",
        labels={'batting_team': 'Team', 'total_runs': 'Runs'},
        color='total_runs',
        color_continuous_scale=px.colors.sequential.Blues
    )
    st.plotly_chart(fig1, use_container_width=True)
    
    # Top run scorers in the season
    top_batsmen = (season_data.groupby('batter')['batsman_runs']
                  .sum()
                  .sort_values(ascending=False)
                  .head(10)
                  .reset_index())
    
    # Get team for each batsman (most common team they batted for)
    batsman_teams = {}
    for batsman in top_batsmen['batter']:
        batsman_teams[batsman] = season_data[season_data['batter'] == batsman]['batting_team'].mode()[0]
    
    top_batsmen['team'] = top_batsmen['batter'].map(batsman_teams)
    
    fig2 = px.bar(
        top_batsmen,
        x='batter',
        y='batsman_runs',
        title=f"Top Run Scorers in {selected_season}",
        labels={'batter': 'Batsman', 'batsman_runs': 'Runs'},
        color='team',
        hover_data=['team']
    )
    st.plotly_chart(fig2, use_container_width=True)
    
    # Top wicket takers in the season
    top_bowlers = (season_data.groupby('bowler')['is_wicket']
                  .sum()
                  .sort_values(ascending=False)
                  .head(10)
                  .reset_index())
    
    # Get team for each bowler (most common team they bowled for)
    bowler_teams = {}
    for bowler in top_bowlers['bowler']:
        bowler_teams[bowler] = season_data[season_data['bowler'] == bowler]['bowling_team'].mode()[0]
    
    top_bowlers['team'] = top_bowlers['bowler'].map(bowler_teams)
    
    fig3 = px.bar(
        top_bowlers,
        x='bowler',
        y='is_wicket',
        title=f"Top Wicket Takers in {selected_season}",
        labels={'bowler': 'Bowler', 'is_wicket': 'Wickets'},
        color='team',
        hover_data=['team']
    )
    st.plotly_chart(fig3, use_container_width=True)
    
    # Phase-wise analysis
    st.subheader("Phase-wise Tournament Analysis")
    
    # Define phases
    def get_phase(over):
        if over <= 6:
            return "Powerplay (1-6)"
        elif over <= 15:
            return "Middle Overs (7-15)"
        else:
            return "Death Overs (16-20)"
    
    season_data['phase'] = season_data['over'].apply(get_phase)
    
    # Phase-wise runs and wickets
    phase_stats = season_data.groupby('phase').agg({
        'total_runs': 'sum',
        'is_wicket': 'sum'
    }).reset_index()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig4 = px.pie(
            phase_stats,
            values='total_runs',
            names='phase',
            title=f"Phase-wise Runs Distribution in {selected_season}"
        )
        st.plotly_chart(fig4, use_container_width=True)
    
    with col2:
        fig5 = px.pie(
            phase_stats,
            values='is_wicket',
            names='phase',
            title=f"Phase-wise Wickets Distribution in {selected_season}"
        )
        st.plotly_chart(fig5, use_container_width=True)
    
    # Team-wise phase analysis
    team_phase = season_data.groupby(['batting_team', 'phase']).agg({
        'total_runs': 'sum',
        'is_wicket': 'sum'
    }).reset_index()
    
    selected_team = st.selectbox("Select Team for Phase Analysis", sorted(season_data['batting_team'].unique()))
    
    if selected_team:
        team_phase_data = team_phase[team_phase['batting_team'] == selected_team]
        
        fig6 = px.bar(
            team_phase_data,
            x='phase',
            y='total_runs',
            title=f"{selected_team}'s Phase-wise Performance in {selected_season}",
            text='total_runs',
            color='phase',
            barmode='group'
        )
        st.plotly_chart(fig6, use_container_width=True)

def main():
    # Load data
    df = load_data()
    
    if df is None:
        st.error("Failed to load data. Please check that the data file exists and is accessible.")
        return
        
    # Add a title and information about the dashboard
    st.title("🏏 IPL Analytics Dashboard (2008-2024)")
    st.markdown("""
    Explore ball-by-ball data from Indian Premier League matches from 2008 to 2024. 
    This dashboard provides comprehensive player, team, and match statistics.
    """)
    
    # Navigation
    pages = {
        "Tournament Statistics": tournament_stats_page,
        "Team Analysis": team_analysis_page,
        "Player Analysis": player_analysis_page,
        "Head to Head": head_to_head_page
    }
    
    selected_page = st.sidebar.radio("Navigation", list(pages.keys()))
    
    # Display selected page
    pages[selected_page](df)
    
    # Dashboard info in sidebar
    st.sidebar.markdown("---")
    st.sidebar.info("""
    ### About
    This dashboard analyzes IPL ball-by-ball data, offering insights into player and team performance across seasons.
    
    ### Data Source
    IPL ball-by-ball data from 2008 to 2024.
    """)

if __name__ == "__main__":
    main()
                
