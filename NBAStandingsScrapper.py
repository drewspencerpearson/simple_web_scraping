# Drew Pearson
# dp6tk
# Homework: Python and Web Scraper

import pandas as pd
from bs4 import BeautifulSoup as bsp
import requests
import numpy as np
from matplotlib import pyplot as plt
import os

def get_headers(table):
    """This function takes in the html of the table we are trying to extract from and finds the headers
    for each column
    parametrs:
    table: (html script) the html script of the table that is visualized on the website
    returns:
    headers: (list) list of the headers for each column in the table """
    header = table.find_all('tr')[0]
    headers = []
    for th in header.find_all('th'):
        headers.append(th.text) 
    return headers

def get_stats(table, teams, headers):
    """This function gets the statistics for each team. then returns a pandas dataframe that has a row for every team
    and their statistics. 
    
    Parameters:
    table: (html) This is the html of the ESPN tables that have all the data we are trying to extract
    teams: (list) This is an ordered list of the teams we are retrieving the stats from. The order is from first place to 
    last place, which is the same order the table is in
    headers: (list) This is the list of all the column headers team_name, wins, losses, etc.
    
    Returns:
    final_df: (pandas df) This dataframe will have a row for each team and their corresponding statistics"""
    for i, tr in enumerate(table.find_all('tr')[1:]):
        stats = [teams[i]]
        for td in tr.find_all('td'):
            stats.append(td.text)
        if i == 0:
            final_df = pd.DataFrame(np.array([stats]), columns = headers)
        else:
            append_df = pd.DataFrame(np.array([stats]), columns = headers)
            final_df = final_df.append(append_df)
    return final_df  


def get_final_standings(soup):
    """This function goes through the html script that we pulled down and finds the team names in order of their final
    rankings for each division (east and west). Then returns the ordered lists.
    Parameters:
    soup: (beautiful soup object) A Beautiful soup object of all the HTML from the website
    returns:
    east_order, west_order: two lists that have the team names in order from first to last in the east and west division
    """

    # Trial and inspecting the source website, I found that East is at position 0 and west is at position 2

    # Cycle through each team and append them to the list
    east_order, west_order = [], []
    for team in soup.find_all('tbody')[0].find_all('tr'):
        # in the early 2000s there were teams that no longer exist, so their image is empty. So I had to find a workaround
        try:
            east_order.append(team.find_all('img')[0]['alt'])
        except IndexError:
            east_order.append(team.text)

    for team in soup.find_all('tbody')[2].find_all('tr'):
        try:
            west_order.append(team.find_all('img')[0]['alt'])
        except:
            west_order.append(team.text)
    
    return east_order, west_order

def get_annual_statistics(soup, east, west, headers):
    """This function gets the final standings for the east and west and then gets the statistics for each team
    returns the east_stats and west_stats, whcih are the statistics for each team in the east and the west.
    Parameter:
    souo: (beautiful soup object) beautiful soup object of the html from the website
    east: (beatiful soup object) this is html for just the table corresponding to the east
    west: (beatiful soup object) this is html for just the table corresponding to the west
    headers: (list) list of headers to use for the columns.
    returns:
    east_stats, west_stats: pandas dataframes that have a row for each team and their statistics. 1 for east, 1 for west"""
    east_order, west_order = get_final_standings(soup)
    
    east_stats = get_stats(east, east_order, headers)
    west_stats = get_stats(west, west_order, headers)
    
    return east_stats, west_stats


def nba_standings(start_year, end_year):
    '''This function goes through every year and pulls down the standings from that year and then appends
    the final team standings and the team statistics to a final_df that will be accumalating every years standings 
    and statistics. The dataframes are broken down by division, east and west.
    parameters:
    start_year: (int) the year to start collecting the data
    end_year: (int) the year to end collecting the data
    returns:
    final_east: (pandas df) where each row corresponds to a team and their stats for a given year in the east
    final_west: (pandas df) where each row corresponds to a team and their stats for a given year in the west'''
    for i, year in enumerate(np.arange(start_year, end_year)):
        # create the url based on the year and pull down the html from the site based on that year
        url = 'https://www.espn.com/nba/standings/_/season/{}'.format(year)
        page = requests.get(url)
        soup = bsp(page.text, 'html.parser')

        # through inspecting the HTML on the website and trial and error, I found
        east = soup.find_all("div", {"class": "Table__Scroller"})[0]
        west = soup.find_all("div", {"class": "Table__Scroller"})[1]

        # Headers are the same each year, so we will get them once and never again
        if i == 0:
            headers = get_headers(east) # Headers will be the same east and west
            # the function gives us the statistical headers. Team name will be the first column, so we prepend that to the list
            headers.insert(0, 'team_name')

        east_stats, west_stats = get_annual_statistics(soup, east, west, headers)
        east_stats['year'] = year
        west_stats['year'] = year
        if i == 0:
            final_east = east_stats
            final_west = west_stats
        else:
            final_east = final_east.append(east_stats)
            final_west = final_west.append(west_stats)
        if len(east_stats)!= len(west_stats):
            print (east_stats)
            print ('\n')
            print (west_stats)
    return final_east, final_west

def get_wins(final_east, final_west):
    """Go through each year and get the total number of wins in the east and west"""
    east_wins, west_wins = [], []

    for year in final_east.year.unique():
        # Look only at the year of interest
        sub_east = final_east[final_east['year']==year]
        sub_west = final_west[final_west['year']==year]
        
        # append the east and west wins to a list
        east_wins.append(sum([int(x) for x in sub_east.W.values]))
        west_wins.append(sum([int(x) for x in sub_west.W.values]))
    return east_wins, west_wins


def plot_wins(final_east, final_west):
    """This function plots the wins for each division in each year"""
    # Get the east and west wins for each year
    east_wins, west_wins = get_wins(final_east, final_west)
    #Plot both the divisions add titles and legends
    plt.plot(east_wins, label = 'East')
    plt.plot(west_wins, label = 'West')
    plt.legend()
    start_year = min(final_east.year.values)
    end_year = max(final_east.year.values)
    xlabels = np.arange(start_year, end_year)
    plt.xticks(np.arange(0, len(xlabels)), labels = xlabels, rotation = 90 )
    plt.xlabel('Year')
    plt.ylabel('Wins')
    plt.title('Number of wins in the East and West by Year')
    plt.savefig('./division_wins.png')
    plt.show()

def get_team_wins(division, teams_dict):
    "This function gets the total number of wins for each team in the division"
    for team in division.team_name.unique():
        teams_dict[team] = sum([int(x) for x in division[division['team_name']==team].W.values])
    return teams_dict 


def plot_team_wins(final_east, final_west):
    """This function plots the total number of wins for each team"""
    plt.figure(figsize=[16,12])
    teams_dict = {}
    teams_dict = get_team_wins(final_east, teams_dict)
    teams_dict = get_team_wins(final_west, teams_dict)
    plt.bar(x = teams_dict.keys(), height = teams_dict.values())
    plt.xticks(rotation = 90)
    plt.savefig('./team_wins.png')
    plt.show()



def web_scraping(start_year, end_year, plot = True):
    """This function will pull down nba standings for each year between start and end year from ESPN.Com.
    it will write out the data to a csv file. 1 for east and 1 for west. If the user wants, it will plot
    some information about the two divisions as well."""
    final_east, final_west = nba_standings(start_year, end_year)
    try:
        final_east.to_csv('./data/east_standings_from_{}_to_{}.csv'.format(start_year, end_year-1), index = False)
        final_west.to_csv('./data/west_standings_from_{}_to_{}.csv'.format(start_year, end_year-1), index = False)
    except FileNotFoundError:
        os.mkdir('./data/')
        final_east.to_csv('./data/east_standings_from_{}_to_{}.csv'.format(start_year, end_year-1), index = False)
        final_west.to_csv('./data/west_standings_from_{}_to_{}.csv'.format(start_year, end_year-1), index = False)

    if plot:
        plot_wins(final_east, final_west)


if __name__ == "__main__":
	import argparse
	parser = argparse.ArgumentParser(description='Scrape ESPN for some NBA standings data')
	parser.add_argument('start_year', type = int, help = "Year to start pulling data")
	parser.add_argument('end_year', type = int, help = "Year to end pulling data")
	parser.add_argument('--plot', type = bool, help = 'Do you want to plot the data')
	parser.set_defaults(plot = True)
	args = parser.parse_args()
	web_scraping(args.start_year, args.end_year, args.plot)