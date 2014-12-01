import json
import urllib2
import sys

from bs4 import BeautifulSoup
from sqlalchemy import create_engine

from storage import *


def format_time(period,time):
    m,s = map(float,time.split(':'))
    if period < 3:
        return (period-1)*1200. + 1200. - 60.*m + s
    else:
        return 2400. + (period-3)*300. + 300. - 60.*m + s

def get_game_date_links(yr='2012'):
    base_url = 'http://www.ncaa.com'
    url = '/'.join((base_url,'scoreboard','basketball-men','d1',yr,'11','28'))
    page = urllib2.urlopen(url)
    soup = BeautifulSoup(page)
    game_dates = soup.find('div', attrs={'id':'date-browser-view'})
    return [''.join((base_url,link['href'])) for link in game_dates.find_all('a')]


def get_game_links(game_date_link):
    soup = BeautifulSoup(urllib2.urlopen(game_date_link))
    return [link['href'] for link in soup.findAll('a', {'class':'gamecenter'})]


def get_data(game_link):
    base_url = 'http://data.ncaa.com'
    url = ''.join((base_url,'/jsonp',game_link,'/gameinfo.json'))
    jsonp_data = urllib2.urlopen(url).read()
    game_data = json.loads(jsonp_data[len('callbackWrapper('):-2])
    for tab in game_data['tabsArray'][0]:
        if tab['type'] == 'play-by-play':
            loc = tab['file']
            pbp_url = ''.join((base_url,loc))
            pbp_data = json.load(urllib2.urlopen(pbp_url))
            return game_data, pbp_data
    return game_data, None


def run(yr='2012'):
    engine = create_engine('sqlite:///play_by_play.db')
    store = Storage(engine)
    
    date_links = get_game_date_links(yr)
    for date_link in date_links:
        game_links = get_game_links(date_link)
        for game_link in game_links:
            game_data, pbp_data = get_data(game_link)
            if pbp_data:
                print game_link
                game_date = datetime.datetime.strptime(game_data['startDate'], '%Y-%m-%d').date()
                for team in pbp_data['meta']['teams']:
                    if team['homeTeam'] == 'true':
                        home = team['shortName']
                    else:
                        away = team['shortName']
        
                #create the game object
                game = store.save_game(home, away, game_date, 'ncb')
        
                #enter all plays
                for period in pbp_data['periods']:
                    per = int(period['periodNumber'])
                    for play in period['playStats']:
                        time = format_time(per, play['time'])
                        home_comment = play['homeText']
                        away_comment = play['visitorText']
                        if play['score']:
                            home_score, away_score = map(int, play['score'].split('-'))
                        else:
                            home_score = None
                            away_score = None
                        store.save_play(per, time, home_score, away_score, home_comment, away_comment, game)

if __name__=='__main__':
    if len(sys.argv) > 1:
        run(sys.argv[1])
    else:
        run()