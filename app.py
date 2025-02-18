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

# Custom CSS with dark/light mode support
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
    
    # Use the batting team names for both selectors for consistency.
    col1, col2 = st.columns(2)
    with col1:
        team1 = st.selectbox("Select Team 1", sorted(df['batting_team'].unique()))
    with col2:
        team2 = st.selectbox("Select Team 2", sorted(df['batting_team'].unique()))
        
    if team1 and team2:
        if team1 == team2:
            st.error("Please select two different teams for head-to-head analysis.")
            return

        # Compute match-level aggregates for matches where both teams batted.
        match_summary = (
            df[df['batting_team'].isin([team1, team2])]
            .groupby(['match_id', 'batting_team'])['total_runs']
            .sum()
            .reset_index()
        )
        match_pivot = match_summary.pivot(index='match_id', columns='batting_team', values='total_runs')
        match_pivot = match_pivot.dropna()  # only consider matches where both teams batted
        
        matches_played = len(match_pivot)
        team1_wins = (match_pivot[team1] > match_pivot[team2]).sum()
        team2_wins = (match_pivot[team2] > match_pivot[team1]).sum()
        ties = (match_pivot[team1] == match_pivot[team2]).sum()
        
        team1_total_runs = match_pivot[team1].sum()
        team2_total_runs = match_pivot[team2].sum()
        
        # Display match-level results.
        colA, colB, colC, colD, colE, colF = st.columns(6)
        with colA:
            st.metric("Matches Played", f"{matches_played}")
        with colB:
            st.metric(f"{team1} Wins", f"{team1_wins}")
        with colC:
            st.metric(f"{team2} Wins", f"{team2_wins}")
        with colD:
            st.metric("Tied Matches", f"{ties}")
        with colE:
            st.metric(f"{team1} Total Runs", f"{team1_total_runs}")
        with colF:
            st.metric(f"{team2} Total Runs", f"{team2_total_runs}")
        
        # For phase-wise analysis, filter the ball-by-ball head-to-head data.
        head_to_head_data = df[
            ((df['batting_team'] == team1) & (df['bowling_team'] == team2)) |
            ((df['batting_team'] == team2) & (df['bowling_team'] == team1))
        ]
        
        st.subheader("Phase-wise Analysis")
        def get_phase_stats(team, phase_start, phase_end):
            # Get batting stats for this team in the specified phase.
            phase_batting = head_to_head_data[
                (head_to_head_data['over'] >= phase_start) &
                (head_to_head_data['over'] <= phase_end) &
                (head_to_head_data['batting_team'] == team)
            ]
            runs = phase_batting['total_runs'].sum()
            balls = len(phase_batting)
            overs = balls / 6
            rr = runs / overs if overs > 0 else 0
            # Get wickets taken by the team while bowling in that phase.
            phase_bowling = head_to_head_data[
                (head_to_head_data['over'] >= phase_start) &
                (head_to_head_data['over'] <= phase_end) &
                (head_to_head_data['bowling_team'] == team)
            ]
            wickets = phase_bowling['is_wicket'].sum()
            # Economy is computed for the batting innings (runs per over).
            economy = runs / overs if overs > 0 else 0
            return runs, rr, wickets, economy
        
        phases = [
            ("Powerplay (1-6)", 1, 6),
            ("Middle Overs (7-15)", 7, 15),
            ("Death Overs (16-20)", 16, 20)
        ]
        for phase_name, start, end in phases:
            st.write(f"**{phase_name}**")
            t1_runs, t1_rr, t1_wickets, t1_econ = get_phase_stats(team1, start, end)
            t2_runs, t2_rr, t2_wickets, t2_econ = get_phase_stats(team2, start, end)
            col1_phase, col2_phase = st.columns(2)
            with col1_phase:
                st.metric(f"{team1} Runs", f"{t1_runs:.0f}")
                st.metric("Run Rate", f"{t1_rr:.2f}")
                st.metric("Wickets Taken", f"{t1_wickets}")
                st.metric("Economy", f"{t1_econ:.2f}")
            with col2_phase:
                st.metric(f"{team2} Runs", f"{t2_runs:.0f}")
                st.metric("Run Rate", f"{t2_rr:.2f}")
                st.metric("Wickets Taken", f"{t2_wickets}")
                st.metric("Economy", f"{t2_econ:.2f}")
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
            
    else:
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

def display_opposition_analysis(df, player, role):
    if role == 'batsman':
        opposition_stats = df[df['batter'] == player].groupby('bowling_team').agg({
            'batsman_runs': 'sum',
            'batter': 'size',
            'is_wicket': 'sum'
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
    else:
        opposition_stats = df[df['bowler'] == player].groupby('batting_team').agg({
            'is_wicket': 'sum',
            'total_runs': 'sum',
            'bowler': 'size'
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
            dismissals = player_phase['is_wicket'].sum()
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(f"{phase_name} Runs", f"{runs}")
            with col2:
                st.metric("Balls", f"{balls}")
            with col3:
                st.metric("Strike Rate", f"{sr:.2f}")
            with col4:
                st.metric("Dismissals", f"{dismissals}")
        else:
            player_phase = phase_df[phase_df['bowler'] == player]
            wickets = player_phase['is_wicket'].sum()
            runs = player_phase['total_runs'].sum()
            balls = len(player_phase)
            overs = balls / 6
            economy = runs / overs if overs > 0 else 0
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(f"{phase_name} Wickets", f"{wickets}")
            with col2:
                st.metric("Overs", f"{overs:.1f}")
            with col3:
                st.metric("Runs Conceded", f"{runs}")
            with col4:
                st.metric("Economy", f"{economy:.2f}")
    st.write("### Most 5 Wicket Hauls")
    five_wickets = df.groupby(['match_id', 'bowler'])['is_wicket'].sum().reset_index()
    five_wicket_hauls = (five_wickets[five_wickets['is_wicket'] >= 5]
                         .groupby('bowler')
                         .size()
                         .reset_index(name='5W Hauls')
                         .sort_values('5W Hauls', ascending=False)
                         .head(10))
    st.dataframe(five_wicket_hauls)

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

def milestones_page(df):
    st.header("Milestones & Records 🏆")
    
    tab1, tab2, tab3 = st.tabs(["Batting Records", "Bowling Records", "Team Records"])
    
    with tab1:
        st.subheader("Batting Milestones")
        st.write("### Fastest Fifties")
        fastest_fifties = calculate_fastest_fifties(df)
        st.dataframe(fastest_fifties)
        
        st.write("### Fastest Centuries")
        fastest_centuries = calculate_fastest_centuries(df)
        st.dataframe(fastest_centuries)
        
        st.write("### Most Sixes")
        most_sixes = (df[df['batsman_runs'] == 6]
                      .groupby('batter', as_index=False)
                      .size()
                      .rename(columns={'size': 'Sixes'})
                      .sort_values('Sixes', ascending=False)
                      .head(10))
        st.dataframe(most_sixes)
        
        st.write("### Most Fours")
        most_fours = (df[df['batsman_runs'] == 4]
                      .groupby('batter', as_index=False)
                      .size()
                      .rename(columns={'size': 'Fours'})
                      .sort_values('Fours', ascending=False)
                      .head(10))
        st.dataframe(most_fours)
        
        st.write("### Most Centuries")
        centuries_by_player = df.groupby(['match_id', 'batter'])['batsman_runs'].sum().reset_index()
        centuries = (centuries_by_player[centuries_by_player['batsman_runs'] >= 100]
                     .groupby('batter', as_index=False)
                     .size()
                     .rename(columns={'size': 'Centuries'})
                     .sort_values('Centuries', ascending=False)
                     .head(10))
        st.dataframe(centuries)
        
        st.write("### Most Fifties")
        fifties_by_player = df.groupby(['match_id', 'batter'])['batsman_runs'].sum().reset_index()
        fifties = (fifties_by_player[
            (fifties_by_player['batsman_runs'] >= 50) & 
            (fifties_by_player['batsman_runs'] < 100)
        ].groupby('batter', as_index=False)
         .size()
         .rename(columns={'size': 'Fifties'})
         .sort_values('Fifties', ascending=False)
         .head(10))
        st.dataframe(fifties)
        
    with tab2:
        st.subheader("Bowling Records")
        st.write("### Best Bowling Figures")
        bowling_figures = df.groupby(['match_id', 'bowler'], as_index=False).agg({
            'is_wicket': 'sum',
            'total_runs': 'sum'
        })
        bowling_figures['figures'] = bowling_figures['is_wicket'].astype(str) + '/' + bowling_figures['total_runs'].astype(str)
        best_bowling = bowling_figures.nlargest(10, 'is_wicket').sort_values(['is_wicket', 'total_runs'], ascending=[False, True])
        st.dataframe(best_bowling[['bowler', 'figures', 'is_wicket', 'total_runs']])
        
        st.write("### Most Wickets")
        most_wickets = (df.groupby('bowler', as_index=False)['is_wicket']
                        .sum()
                        .sort_values('is_wicket', ascending=False)
                        .head(10))
        st.dataframe(most_wickets)
        
        st.write("### Best Economy Rates (Min. 20 overs)")
        bowler_stats = df.groupby('bowler', as_index=False).agg({
            'total_runs': 'sum',
            'bowler': 'size'
        })
        bowler_stats['overs'] = bowler_stats['bowler'] / 6
        bowler_stats['economy'] = bowler_stats['total_runs'] / bowler_stats['overs']
        best_economy = bowler_stats[bowler_stats['overs'] >= 20].sort_values('economy').head(10)
        st.dataframe(best_economy[['bowler', 'economy', 'overs', 'total_runs']])
        
        st.write("### Most 5 Wicket Hauls")
        five_wickets = df.groupby(['match_id', 'bowler'])['is_wicket'].sum().reset_index()
        five_wicket_hauls = (five_wickets[five_wickets['is_wicket'] >= 5]
                             .groupby('bowler', as_index=False)
                             .size()
                             .rename(columns={'size': '5W Hauls'})
                             .sort_values('5W Hauls', ascending=False)
                             .head(10))
        st.dataframe(five_wicket_hauls)
        
    with tab3:
        st.subheader("Team Records")
        st.write("### Highest Team Totals")
        highest_totals = (df.groupby(['match_id', 'batting_team'], as_index=False)['total_runs']
                          .sum()
                          .sort_values('total_runs', ascending=False)
                          .head(10))
        st.dataframe(highest_totals)
        
        st.write("### Best Team Strike Rates")
        team_stats = df.groupby('batting_team', as_index=False).agg({
            'total_runs': 'sum',
            'batting_team': 'size'
        })
        team_stats['strike_rate'] = (team_stats['total_runs'] / team_stats['batting_team']) * 100
        st.dataframe(team_stats.sort_values('strike_rate', ascending=False))
        
        st.write("### Most Team Wins")
        matches_won = (df.groupby('batting_team', as_index=False)['match_id']
                       .nunique()
                       .rename(columns={'batting_team': 'Team', 'match_id': 'Matches'})
                       .sort_values('Matches', ascending=False))
        st.dataframe(matches_won)

def display_form_trend(df, player, role):
    if role == 'batsman':
        performance = df[df['batter'] == player].groupby('match_id').agg({
            'batsman_runs': 'sum',
            'batter': 'size'
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
            title=f"{player}'s Batting Form",
            yaxis=dict(title='Runs'),
            yaxis2=dict(title='Strike Rate', overlaying='y', side='right'),
            showlegend=True,
            height=400
        )
    else:
        performance = df[df['bowler'] == player].groupby('match_id').agg({
            'is_wicket': 'sum',
            'total_runs': 'sum',
            'bowler': 'size'
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
            showlegend=True,
            height=400
        )
    st.plotly_chart(fig, use_container_width=True)

def main():
    st.title("🏏 IPL Analytics Dashboard (2008-2024)")
    df = load_data()
    if df is None:
        return
    
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Select Page", 
                            ["Head to Head Analysis",
                             "Player Analysis",
                             "Milestones & Records"])
    
    if page == "Head to Head Analysis":
        head_to_head_page(df)
    elif page == "Player Analysis":
        player_analysis_page(df)
    else:
        milestones_page(df)
    
    st.sidebar.markdown("---")
    st.sidebar.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d')}")

if __name__ == "__main__":
    main()
