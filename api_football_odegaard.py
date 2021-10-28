# -*- coding: utf-8 -*-
"""
The purpose of this code is to analyse Martin Ødegaard's performance over the 19/20 season at Real Sociedad 

"""
import requests
import os
import json
import plotly.graph_objects as go
import plotly.offline as pyo
from colour import Color


'''
This function get data of the player using FOOTBALL-API
and create the graphic.
'''
def create_graphic(league,team_img_source,player_img_source):
    
    data = {'% Goals': league['goals']['total'] * 100 / league['shots']['on'] if league['shots']['on'] else 0,
            '% Passes': league['passes']['accuracy'],
            '% Dribbles': league['dribbles']['success'] * 100 / league['dribbles']['attempts'] if league['dribbles']['attempts'] else 0,
            '% Shots': league['shots']['on'] * 100 / league['shots']['total'] if league['shots']['total'] else 0,
            '% Duels': league['duels']['won'] * 100 / league['duels']['total'] if league['duels']['total'] else 0,
            '% Tackles': league['tackles']['interceptions'] * 100 / league['tackles']['total'] if league['tackles']['total'] else 0,
            }
    
    categories = list(data.keys())
    player_stats = list(data.values())
    red = Color("red")
    colors = list(red.range_to(Color("green"),10))
    
    fig = go.Figure(
        data=[
            go.Scatterpolar(r=player_stats, theta=categories, fill='toself', name=league['player_name']),
    
        ],
        layout=go.Layout(
            title=go.layout.Title(text=league['player_name'], font=dict(size=50), x=0.5),
            polar={'radialaxis': {'visible': True}},
            showlegend=False,
            template='plotly_dark',
            annotations=[
                dict(
                    x=1,
                    y=0.95,
                    text=league['team_name'],
                    showarrow=False,
                    font=dict(size=30)
                ),
                
                dict(
                    x=1,
                    y=0.88,
                    text=league['league'] + ' ' + league['season'],
                    showarrow=False,
                    font=dict(size=20)
                ),
                
                dict(
                    x=1,
                    y=0.83,
                    text=league['position'],
                    showarrow=False,
                    font=dict(size=20)
                ),
                
                dict(
                    x=1,
                    y=0.78,
                    text='Age: '+ str(league['age']),
                    showarrow=False,
                    font=dict(size=15)
                ),   
                
                dict(
                    x=1,
                    y=0.74,
                    text='Height: '+ str(league['height']),
                    showarrow=False,
                    font=dict(size=15)
                ),  
    
                dict(
                    x=1,
                    y=0.70,
                    text='Weight: '+ str(league['weight']),
                    showarrow=False,
                    font=dict(size=15)
                ),              
                dict(
                    x=0.058,
                    y=0.83,
                    text= str(round(float(league['rating']),2)),
                    showarrow=False,
                    font=dict(size=50,
                              color= colors[int((round(float(league['rating']),1)))].get_hex())
                    
                ),
                dict(
                    x=0.07,
                    y=0.72,
                    text= 'Rating',
                    showarrow=False,
                    font=dict(size=23)
                    
                )                
            ]
        )
    )
    
    fig.add_layout_image(
        dict(
            #source="https://media.api-sports.io/football/teams/{}.png".format(str(league["team_id"])), #Doesn' work!!!
            source=team_img_source,
            xref="paper", yref="paper",
            x=0.95, y=1.15,
            sizex=0.2, sizey=0.2,
            xanchor="right", yanchor="top"
        )
    )

    fig.add_layout_image(
        dict(
            source=player_img_source,
            x=0.15, y=1.15,
            sizex=0.3, sizey=0.3,
            xanchor="right", yanchor="top"
        )
    )
    
    fig.update_layout(
    font_family='"Overpass", sans-serif',
    )

    pyo.plot(fig)
    

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
#leagues = response.text
#'season':2019-20, 'league_id':775

url = 'https://api-football-v1.p.rapidapi.com/v2/teams/league/775'
#response = requests.request('GET', url, headers=headers)
#teams = response.text
# Real Sociedad 'team_id':548 

url = 'https://api-football-v1.p.rapidapi.com/v2/players/squad/548/2019-2020'
#response = requests.request('GET', url, headers=headers)
#squad = response.text
#id M. Ødegaard = 37127

# Martin Ødegaard stats
url = 'https://api-football-v1.p.rapidapi.com/v2/players/player/37127/2019-2020'

response = requests.request('GET', url, headers=headers)
player_dict = json.loads(response.text)['api']['players']    
    
'''
You can run this code using files in data folder
'''

file = open("./data/odegaard_data.json","r+")
content = file.read()
file.close()
player_dict = json.loads(content)['api']['players']
  
'''
Paste images url, preferably images of teams from Transfermarkt and players images from FifaRosters
'''       
team_img_source = "https://tmssl.akamaized.net/images/wappen/head/681.png"
player_img_source = "https://www.fifarosters.com/assets/players/fifa21/faces/222665.png" 
for league in player_dict:
    data = create_graphic(league,team_img_source,player_img_source)
