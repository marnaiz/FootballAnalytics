# -*- coding: utf-8 -*-
"""
Code to make comparisons between 2 players using radar chart plots
"""
import requests
import os
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.offline as pyo
from scipy import stats

'''
Get data from players to compare.
'''
def get_players_data(players,season,league_id):
    players_league = []
    for player in players:
        url = 'https://api-football-v1.p.rapidapi.com/v2/players/player/{}/{}'.format(player,season)
        response = requests.request('GET', url, headers=headers)
        player_dict = json.loads(response.text)['api']['players'] 
        player_laliga = list(filter(lambda x: x['league_id'] == league_id, player_dict))[0]
        players_league.append(player_laliga)
    return players_league

'''
Calculate stats per 90 minutes.
'''
def get_90min_stats(player,stat1,stat2):
    return round(player[stat1][stat2] * 90 / player['games']['minutes_played'],2)

'''
Calculate percentile.
'''
def get_score(ref_list,stat):
    return round(stats.percentileofscore(ref_list, stat),0)

'''
Create a list of players from the chosen competition.
'''
def get_league_stats(league_id):
    url = 'https://api-football-v1.p.rapidapi.com/v2/teams/league/{}'.format(league_id)
    response = requests.request('GET', url, headers=headers)
    teams_dict = json.loads(response.text)['api']['teams']
    team_ids = [d['team_id'] for d in teams_dict]
    players_in_league = []
    for team_id in team_ids:
        player_data_list = get_teams_stats(team_id,league_id)
        players_in_league += player_data_list        
    players_df = pd.DataFrame(players_in_league)
    return  players_df

'''
Create a list of players from the chosen team.
'''
def get_teams_stats(team_id,league_id):
    url = 'https://api-football-v1.p.rapidapi.com/v2/players/team/{}/2020-2021'.format(team_id)
    response = requests.request('GET', url, headers=headers)
    team_dict = json.loads(response.text)['api']['players']
    laliga_stats = list(filter(lambda x: x['league_id'] == league_id and x['games']['appearences'] > 5, team_dict)) #Filter players with more than 5 appearences in the league
    player_data_list = []
    for player in laliga_stats:
        data = {'player_id': player['player_id'],
                'player_name': player['player_name'],
                'Goals_90min': get_90min_stats(player,'goals','total'),
                'Assists_90min': get_90min_stats(player,'goals','assists'),
                'Shots_90min': get_90min_stats(player,'shots','on'),
                'TShots_90min': get_90min_stats(player,'shots','total'),
                'Passes_acc': player['passes']['accuracy'],
                'TPasses_90min': get_90min_stats(player,'passes','total'),
                'KeyPasses_90min': get_90min_stats(player,'passes','key'),
                'Dribbles_90min': get_90min_stats(player,'dribbles','success'),
                'ADribbles_90min': get_90min_stats(player,'dribbles','attempts'),
                'Duels_90min': get_90min_stats(player,'duels','won'),
                'TDuels_90min': get_90min_stats(player,'duels','total'),
                'DFouls_90min': get_90min_stats(player,'fouls','drawn'),
                'CFouls_90min': get_90min_stats(player,'fouls','committed'),          
                'Interceptions_90min': get_90min_stats(player,'tackles','interceptions'),
                }
        player_data_list.append(data)
    return player_data_list



'''
This function get data of the player using FOOTBALL-API
and create the graphic.
'''
def create_graphic(players_league,players_df, team1_img_source,player1_img_source,team2_img_source,player2_img_source):
    
    df_flags = pd.read_csv('data\countries_flags_url.csv')
    player_data_list = []
    for player in players_league:
        data = {'Goals': get_score(players_df['Goals_90min'], get_90min_stats(player,'goals','total')),
                'Assists': get_score(players_df['Assists_90min'], get_90min_stats(player,'goals','assists')),
                'Shots On': get_score(players_df['Shots_90min'], get_90min_stats(player,'shots','on')),
                'Total Shots': get_score(players_df['TShots_90min'], get_90min_stats(player,'shots','total')),
                'Passes Accuracy': get_score(players_df['Passes_acc'], player['passes']['accuracy']),
                'Total Passes': get_score(players_df['TPasses_90min'], get_90min_stats(player,'passes','total')),
                'Key Passes': get_score(players_df['KeyPasses_90min'], get_90min_stats(player,'passes','key')),
                'Success Dribbles': get_score(players_df['Dribbles_90min'], get_90min_stats(player,'dribbles','success')),
                'Attempts Dribbles': get_score(players_df['ADribbles_90min'], get_90min_stats(player,'dribbles','attempts')),
                'Won Duels': get_score(players_df['Duels_90min'], get_90min_stats(player,'duels','won')),
                'Total Duels': get_score(players_df['TDuels_90min'], get_90min_stats(player,'duels','total')),
                'Drawn Fouls': get_score(players_df['DFouls_90min'], get_90min_stats(player,'fouls','drawn')),
                'Committed Fouls': get_score(players_df['CFouls_90min'], get_90min_stats(player,'fouls','committed')),          
                'Interceptions': get_score(players_df['Interceptions_90min'], get_90min_stats(player,'tackles','interceptions')),
                }
        player_data_list.append(data)
    
    categories = list(data.keys())
    player1_stats = list(player_data_list[0].values())
    player2_stats = list(player_data_list[1].values())
    colors = ["Firebrick","Crimson","IndianRed","Salmon","DarkOrange","Gold","YellowGreen","ForestGreen","SteelBlue", "MediumStateBlue", "Darkorchid"]
    
    '''
    Add annotations with players' data
    '''
    
    annotations = []
    for player in players_league:
        if len(annotations) == 0:
            x=0
            x1=0
            x2=0
        else:
            x=1
            x1=0.9
            x2=0.95
        
        y = 0.7
        weight = player["weight"].split(' ')
        height = player["height"].split(' ')        
        annotation = [
            dict(
                x=x1+0.05,
                y=y,
                text=player['player_name'],
                showarrow=False,
                font=dict(size=30)
            ),
            dict(
                x=x,
                y=y-0.1,
                text=player['team_name'],
                showarrow=False,
                font=dict(size=20)
            ),                
            dict(
                x=x,
                y=y-0.15,
                text=player['position'],
                showarrow=False,
                font=dict(size=20)
            ),
            dict(
                x=x1,
                y=y-0.22,
                text=str(player['age']),
                showarrow=False,
                font=dict(size=20)
            ),   
            dict(
                x=x1+0.05,
                y=y-0.22,
                text=str(height[0]),
                showarrow=False,
                font=dict(size=20)
            ),   
            dict(
                x=x1+0.1,
                y=y-0.22,
                text=str(weight[0]),
                showarrow=False,
                font=dict(size=20)
            ),  
            dict(
                x=x1,
                y=y-0.26,
                text='yr',
                showarrow=False,
                font=dict(size=20)
            ),   
            dict(
                x=x1+0.05,
                y=y-0.26,
                text=str(height[1]),
                showarrow=False,
                font=dict(size=20)
            ),   
            dict(
                x=x1+0.1,
                y=y-0.26,
                text=str(weight[1]),
                showarrow=False,
                font=dict(size=20)
            ),  
            dict(
                x=x2+0.03,
                y=y-0.45,
                text= str(round(float(player['rating']),1)),
                showarrow=False,
                font=dict(size=50),
                bordercolor="White",
                borderwidth=2,
                borderpad=4,
                bgcolor=colors[int((round(float(player['rating']),1)))],
                opacity=0.8
                
            )
        ]          

        annotations += annotation
        
    '''
    Create polar chart with player's stats
    '''        
        
    fig = go.Figure(
        data=[
            go.Scatterpolar(r=player1_stats, theta=categories, fill='toself', name=players_league[0]['player_name']),
    
        ],
        layout=go.Layout(
            title=go.layout.Title(text=players_league[0]['league'] + ' ' + players_league[0]['season'], font=dict(size=50), x=0.5),
            polar={'radialaxis': {'visible': True}},
            showlegend=False,
            template='plotly_dark',
            annotations=annotations
        )
    )    
    
    fig.add_trace(
        go.Scatterpolar(r = player2_stats,theta = categories, fill='toself',name=players_league[1]['player_name'])
        )    
    
    '''
    Add teams images (url different from the one in the API because it doesn't work :( )
    '''         
    
    fig.add_layout_image(
        dict(
            #source="https://media.api-sports.io/football/teams/{}.png".format(str(league["team_id"])),
            source=team1_img_source,
            x=0.15, y=0.85,
            sizex=0.1, sizey=0.1,
            xanchor="left", yanchor="top"
        )
    )
    
    fig.add_layout_image(
        dict(
            #source="https://media.api-sports.io/football/teams/{}.png".format(str(league["team_id"])),
            source=team2_img_source,
            x=0.85, y=0.85,
            sizex=0.1, sizey=0.1,
            xanchor="right", yanchor="top"
        )
    )

    '''
    Add players images
    '''  
    fig.add_layout_image(
        dict(
            source=player1_img_source,
            x=0.005, y=1.10,
            sizex=0.28, sizey=0.28,
            xanchor="left", yanchor="top"
        )
    )    

    fig.add_layout_image(
        dict(
            source=player2_img_source,
            x=0.995, y=1.10,
            sizex=0.28, sizey=0.28,
            xanchor="right", yanchor="top"
        )
    )
    
    '''
    Add flags
    '''      
    
    fig.add_layout_image(
        dict(
            source=df_flags[df_flags["country"]==players_league[0]["birth_country"]]["image_url"].item(),
            x=0.01, y=0.685,
            sizex=0.045, sizey=0.045,
            xanchor="left", yanchor="top"
        )
    )    
    
    fig.add_layout_image(
        dict(
            source=df_flags[df_flags["country"]==players_league[1]["birth_country"]]["image_url"].item(),
            x=0.985, y=0.685,
            sizex=0.045, sizey=0.045,
            xanchor="right", yanchor="top"
        )
    )        
    
    '''
    Add lines between players' data
    '''      
    
    fig.add_shape(type="line",
        x0=0.91, y0=0.4, x1=0.91, y1=0.5,
        line=dict(width=3)
    )   
    fig.add_shape(type="line",
        x0=0.965, y0=0.4, x1=0.965, y1=0.5,
        line=dict(width=3)
    )  
    fig.add_shape(type="line",
        x0=0.035, y0=0.4, x1=0.035, y1=0.5,
        line=dict(width=3)
    )      
    fig.add_shape(type="line",
        x0=0.09, y0=0.4, x1=0.09, y1=0.5,
        line=dict(width=3)
    )      
    
    '''
    Add circles
    '''      
    
    fig.add_shape(type="circle",
        x0=-0.015, y0=0.75, x1=0.135, y1=1.13,
        line=dict(
            color="RoyalBlue",
            width=6
        ),
        fillcolor="LightSkyBlue",
        layer="below"
    )    
    fig.add_shape(type="circle",
        x0=0.865, y0=0.75, x1=1.015, y1=1.13,
        line=dict(
            color="Crimson",
            width=6
        ),
        fillcolor="LightPink",
        layer="below"
    )     
    

    '''
    Add legend
    '''      
    fig.add_annotation(x=1, y=-0.1,
                text="The values correspond to the percentile in which the player is in each statistic<br>evaluated per 90 minutes in relation to the rest of the players in La Liga last season.",
                showarrow=False)
    
    fig.add_layout_image(
        dict(
            source="https://cdn.pixabay.com/photo/2017/03/17/05/20/info-2150938_960_720.png", #Info icon
            x=0.67, y=-0.07,
            sizex=0.03, sizey=0.03,
            xanchor="left", yanchor="bottom"
        )
    )  
    

    fig.update_layout(
    font_family='"Overpass", sans-serif',
    )

    pyo.plot(fig)


# Write here your API key
#os.environ['x_rapidapi_key'] = 'YourAPIKey' #Uncomment this line and write here your API key or set it in your env 

x_rapidapi_key = os.environ.get('x_rapidapi_key')

headers = {
    'x-rapidapi-key': x_rapidapi_key,
    'x-rapidapi-host': 'api-football-v1.p.rapidapi.com/v3/'
    }


'''
If you want to do the same with a different player 
you should run every request query and find the player you want.
'''

url = 'https://api-football-v1.p.rapidapi.com/v2/leagues/country/spain'
#response = requests.request('GET', url, headers=headers)
#leagues_dict = json.loads(response.text)['api']['leagues']    
#'season':2021-22, 'league_id':3513

url = 'https://api-football-v1.p.rapidapi.com/v2/teams/league/2833'
#response = requests.request('GET', url, headers=headers)
#teams_dict = json.loads(response.text)['api']['teams']
# Barcelona 'team_id':529 
# Real Madrid 'team_id':541 


url = 'https://api-football-v1.p.rapidapi.com/v2/players/squad/541/2021-2022'
# response = requests.request('GET', url, headers=headers)
# squad_dict = json.loads(response.text)['api']['players']
#id M. Depay = 667
#id K. Benzema = 759


'''
If you don't have access to FOOTBALL-API, you can read data from this code in data folder.
'''
with open('data\players_league.json') as f:
    players_league = json.load(f)

players_df = pd.read_csv('data\players20_21.txt', sep=";", header=0)


'''
If you do, then uncomment the following lines.
'''
#players_league = get_players_data(players=['667','759'],season='2021-2022',league_id=3513)
#players_df = get_league_stats('2833')


'''
Paste images url, preferably images of teams from Transfermarkt and players images from FifaRosters
'''   
team1_img_source = "https://tmssl.akamaized.net/images/wappen/head/131.png"
player1_img_source = "https://www.fifarosters.com/assets/players/fifa22/faces/202556.png" 
team2_img_source = "https://tmssl.akamaized.net/images/wappen/head/418.png"
player2_img_source = "https://www.fifarosters.com/assets/players/fifa22/faces/165153.png" 

create_graphic(players_league,players_df, team1_img_source,player1_img_source,team2_img_source,player2_img_source)