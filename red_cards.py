# -*- coding: utf-8 -*-
"""
Created on Fri Oct 22 12:17:59 2021

@author: User
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time 
from bs4 import BeautifulSoup as bs
import requests
import pandas as pd
import os
import json
import re
import unidecode

def get_matches_red(league_prefix, league, season):
    
    chrome_options = Options()
    chrome_options.binary_location = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
    driver = webdriver.Chrome(ChromeDriverManager().install())
    url = league_prefix + str(league['season']) + '-' + str(league['season']+1)
    driver.get('https://www.flashscore.es/futbol/' + url)
    driver.maximize_window()
    time.sleep(3)
    reject_cookies = driver.find_element_by_id('onetrust-reject-all-handler')
    reject_cookies.click()
    while True:    
        try:
            driver.find_element_by_link_text('Mostrar más partidos').click()
            time.sleep(5)
        except:
            break
    
    matches = driver.find_elements_by_class_name('event__match')
    df_match = pd.DataFrame()
    df_matches = pd.DataFrame()
    for match in matches:
        event = match.get_attribute('innerHTML')
        soup = bs(event, 'html.parser')
        regex = re.compile('card-ico icon--redCard.*')
        red_card = soup.find_all('svg', attrs={'class':regex})
        match_id = match.text.split('\n')
        df_match['homeTeam'] = [re.sub(' de ', ' ', unidecode.unidecode(match_id[1]))]
        df_match['awayTeam'] = [re.sub(' de ', ' ', unidecode.unidecode(match_id[2]))]
        df_match['season'] = season
        if red_card:
            df_match['red_card'] = True
        else:
            df_match['red_card'] = False
        df_matches = df_matches.append(df_match)
    
    driver.close()
    
    return df_matches


# API
def get_teams_api(league, season):
    
    league_id = str(league['league_id'])
    url = 'https://api-football-v1.p.rapidapi.com/v2/teams/league/' + league_id
    response = requests.request('GET', url, headers=headers)
    teams_dict = json.loads(response.text)['api']['teams']
    df_teams = pd.DataFrame(teams_dict)
    df_teams = df_teams[['team_id','name']]
    
    return df_teams


# API
def get_fixtures_api(league, season):
    
    league_id = str(league['league_id'])
    url = 'https://api-football-v1.p.rapidapi.com/v2/fixtures/league/' + league_id
    response = requests.request('GET', url, headers=headers)
    fixtures_dict = json.loads(response.text)['api']['fixtures']
    df_fixtures = pd.DataFrame(fixtures_dict)
    df_fixtures = df_fixtures[['fixture_id', 'event_date', 'homeTeam', 'awayTeam']]
    df_fixtures['homeTeamName'] = df_fixtures['homeTeam'].apply(lambda x: x.get('team_name'))
    df_fixtures = df_fixtures.sort_values(['event_date', 'homeTeamName'], ascending=[False, True]).reset_index()
    
    return df_fixtures


# API
def get_players_api(league, teams, season):
    
    years = str(league['season']) + '-' + str(league['season']+1)
    df_players_total = pd.DataFrame()
    try:
        for team in teams:
            url = 'https://api-football-v1.p.rapidapi.com/v2/players/team/{}/{}'.format(team,years)
            response = requests.request('GET', url, headers=headers)
            players_dict = json.loads(response.text)['api']['players']
            players_dict = list(filter(lambda x: x['games']['minutes_played']>0, players_dict))
            df_players = pd.DataFrame(players_dict)   
            df_players['minutes'] = df_players['games'].apply(lambda x: x.get('minutes_played'))
            df_players['n_goals'] = df_players['goals'].apply(lambda x: x.get('total'))
            df_players['n_assists'] = df_players['goals'].apply(lambda x: x.get('assists')) 
            df_players['n_keypasses'] = df_players['passes'].apply(lambda x: x.get('key')) 
            df_players['n_dribbles'] = df_players['dribbles'].apply(lambda x: x.get('success')) 
            df_players['n_fouls'] = df_players['fouls'].apply(lambda x: x.get('committed'))
            player_short = df_players[['player_id', 'player_name', 'position', 'minutes', 'n_goals', 'n_assists', 'n_keypasses', 'n_dribbles', 'n_fouls']]
            player_short_grouped = player_short.groupby(['player_id', 'player_name','position'], as_index=False).sum()
            ratio_dict = {'Goalkeeper': 0,
                          'Defender': 25,
                          'Midfielder': 50,
                          'Attacker': 75}
            player_short_grouped['position_ratio'] = player_short_grouped['position'].map(ratio_dict)       
            player_short_grouped['goals90min'] = round(player_short_grouped['n_goals'] * 90 / player_short_grouped['minutes'],2)
            player_short_grouped['assists90min'] = round(player_short_grouped['n_assists'] * 90 / player_short_grouped['minutes'],2)  
            player_short_grouped['keypasses90min'] = round(player_short_grouped['n_keypasses'] * 90 / player_short_grouped['minutes'],2)  
            player_short_grouped['dribbles90min'] = round(player_short_grouped['n_dribbles'] * 90 / player_short_grouped['minutes'],2)  
            player_short_grouped['fouls90min'] = round(player_short_grouped['n_fouls'] * 90 / player_short_grouped['minutes'],2)  
            player_short_grouped['ofensive_ratio'] = round(player_short_grouped['position_ratio'] + 10*player_short_grouped['goals90min']+ 5*player_short_grouped['assists90min'] + 3*player_short_grouped['keypasses90min'] + 3*player_short_grouped['dribbles90min'] - 5*player_short_grouped['fouls90min'],2) 
            df_players_total = df_players_total.append(player_short_grouped) 
        df_players_total = df_players_total[['player_id', 'player_name','position', 'ofensive_ratio']].groupby(['player_id', 'player_name', 'position'], as_index=False).mean()
            
        return df_players_total
    
    except Exception as e: 
        print(e)
        
        
# API
def get_events_api(league, red_list, season):
    
    df_events_final = pd.DataFrame()
    try:
        for event in red_list:
            time.sleep(3)
            url = 'https://api-football-v1.p.rapidapi.com/v2/events/' + str(event)
            response = requests.request('GET', url, headers=headers)
            events_dict = json.loads(response.text)['api']['events']
            events_df = pd.DataFrame(events_dict)        
            red_card_df = events_df[events_df['detail'] == 'Red Card']
            index_red_card = red_card_df.index
            subst = events_df[events_df['type'] == 'subst']
            goals = events_df[events_df['type'] == 'Goal']
            
            
            d = []
            for i in list(range(0,len(red_card_df))):
                team_id = events_df['team_id'][index_red_card[i]]
                minute = events_df['elapsed'][index_red_card[i]]
                substitution = subst[(subst['elapsed'] >= minute) & (subst['elapsed'] <= minute + 5) & (subst['team_id'] == team_id)]
                player_id = red_card_df.iloc[i].player_id
                if minute >= 0 and pd.notna(player_id): #Red cards out of the pitch (minutes<0) and not players (coaches)
                    if i+1 < len(red_card_df):
                        d.append(
                            {
                                'minute': minute,
                                'team_id': team_id,
                                'red_card': int(player_id),
                                'player_out': int(substitution['player_id'].iloc[0]) if len(substitution)!=0 else 0,
                                'player_in': int(substitution['assist_id'].iloc[0]) if len(substitution)!=0 else 0,
                                'goals_for_brc': goals[(goals.index < red_card_df.index[i])  & (goals['team_id'] == team_id)].shape[0],
                                'goals_against_brc': goals[(goals.index < red_card_df.index[i])  & (goals['team_id'] != team_id)].shape[0],
                                'goals_for_arc': goals[(goals.index > red_card_df.index[i]) & (goals.index < red_card_df.index[i+1])  & (goals['team_id'] == team_id)].shape[0],
                                'goals_against_arc': goals[(goals.index > red_card_df.index[i]) & (goals.index < red_card_df.index[i+1])  & (goals['team_id'] != team_id)].shape[0],
                            }
                        )
                        
                    else:
                        d.append(
                            {
                                'minute': minute,
                                'team_id': team_id,
                                'red_card': int(player_id),
                                'player_out': int(substitution['player_id'].iloc[0]) if len(substitution)!=0 else 0,
                                'player_in': int(substitution['assist_id'].iloc[0]) if len(substitution)!=0 else 0,
                                'goals_for_brc': goals[(goals.index < red_card_df.index[i])  & (goals['team_id'] == team_id)].shape[0],
                                'goals_against_brc': goals[(goals.index < red_card_df.index[i])  & (goals['team_id'] != team_id)].shape[0],
                                'goals_for_arc': goals[(goals.index > red_card_df.index[i])  & (goals['team_id'] == team_id)].shape[0],
                                'goals_against_arc': goals[(goals.index > red_card_df.index[i]) & (goals['team_id'] != team_id)].shape[0],
                            }
                        )  
                    
            df_final = pd.DataFrame(d)
            df_final['goals_diff_brc'] = df_final['goals_for_brc'] - df_final['goals_against_brc']
            df_final['goals_diff_arc'] = df_final['goals_for_arc'] - df_final['goals_against_arc']
            df_final['goals_diff'] = df_final['goals_diff_arc'] + df_final['goals_diff_brc']
            df_events_final = df_events_final.append(df_final) 
    
        return df_events_final    
        
    except Exception as e: 
        print(e)
            
    


def get_df_final(league_prefix, league):
    
    season = str(league['season'])
    country = league['country']

    df_matches = get_matches_red(league_prefix, league, season)
    df_teams = get_teams_api(league, season)
    df_fixtures = get_fixtures_api(league, season)
    df_players = get_players_api(league, df_teams['team_id'], season)
    index_list = list(df_matches.loc[df_matches['red_card'] == True].index)
    red_list = list(df_fixtures.loc[index_list,'fixture_id'])
    df_events_final = get_events_api(league, red_list, season)
        
    df_total = df_events_final.copy()
    df_total['country'] = country
    df_total['league'] = league['name']
    df_total['season'] = season
    df_total['team_name'] = df_total['team_id'].map(df_teams.set_index('team_id')['name'])
    df_total['red_card_position'] = df_total['red_card'].map(df_players.set_index('player_id')['position'])
    df_total['red_card'] = df_total['red_card'].map(df_players.set_index('player_id')['ofensive_ratio'])
    df_total['player_out'] = df_total['player_out'].map(df_players.set_index('player_id')['ofensive_ratio'])
    df_total['player_in'] = df_total['player_in'].map(df_players.set_index('player_id')['ofensive_ratio'])
    df_total['ratio_diff'] = round(df_total['player_in'] - df_total['player_out'],2)
    
    try:
        os.makedirs('datos')    
    except FileExistsError:
        print('Directory already exists')  
        
    df_total.to_csv(r'.\datos\total{}{}.txt'.format(country,season), header=True, index=0, sep=';', mode='a')    

    return df_total


#%%
# API
# Write here your API key
#os.environ['x_rapidapi_key'] = 'YourAPIKey' #Uncomment this line and write here your API key or set it in your env 

x_rapidapi_key = os.environ.get('x_rapidapi_key')

headers = {
    'x-rapidapi-key': x_rapidapi_key,
    'x-rapidapi-host': 'api-football-v1.p.rapidapi.com'
    }

datos = True

url = 'https://api-football-v1.p.rapidapi.com/v2/leagues'
response = requests.request('GET', url, headers=headers)
leagues_dict = json.loads(response.text)['api']['leagues']

leagues_dictionary = {'Spain': ['La Liga', 'spain/laliga-'], 
                      'England': ['Premier League', 'england/premier-league-'], 
                      'Germany': ['Bundesliga 1', 'germany/bundesliga-'], 
                      'Italy': ['Serie A', 'italy/serie-a-'], 
                      'France': ['Ligue 1', 'france/ligue-1-']
                      }

seasons = [2016, 2017, 2018, 2019, 2020]

for country in leagues_dictionary:
    name = leagues_dictionary[country][0]
    league_prefix = leagues_dictionary[country][1]
    for season in seasons:
        league = list(filter(lambda x: x['name'] == name and x['season'] == season and x['country'] == country, leagues_dict))
        df_total =  get_df_final(league_prefix, league)
