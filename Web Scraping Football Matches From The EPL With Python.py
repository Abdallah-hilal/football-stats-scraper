import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# Define URL for Premier League stats
url = "https://fbref.com/en/comps/9/Premier-League-Stats"
data = requests.get(url)
soup = BeautifulSoup(data.text, 'lxml')

# Find the stats table
standings_table = soup.find('table', id="results2024-202591_overall")
if standings_table is None:
    print("Table not found! The website structure may have changed.")
    exit()

# Extract team links
links = [link.get("href") for link in standings_table.find_all('a')]
team_links = [f"https://fbref.com{link}" for link in links if "/squads/" in link]

# Scrape data for Liverpool as an example
liver_url = team_links[0]
liver_data = requests.get(liver_url)
matches = pd.read_html(liver_data.text, match='Scores & Fixtures')[0]

# Extract shooting data
liver_soup = BeautifulSoup(liver_data.text, 'lxml')
shooting = liver_soup.find_all('div', class_="filter")

if len(shooting) > 2:
    shots = shooting[2].find_all('a')
else:
    print("Not enough elements found in shooting list.")
    exit()

shots = [l.get('href') for l in shots if l and 'all_comps/shooting' in l]
if not shots:
    print("No shooting data found.")
    exit()

data = requests.get(f"https://fbref.com{shots[0]}")
shooting = pd.read_html(data.text, match="Shooting")[0]
shooting.columns = shooting.columns.droplevel()

# Merge shooting data with match data
liverpool_data = matches.merge(shooting[["Date", "Sh", "SoT", "Dist", "FK", "PK", "PKatt"]], on="Date")
print(liverpool_data.head())

# Scrape multiple seasons
years = list(range(2022, 2020, -1))
all_matches = []
standings_url = url

for year in years:
    data = requests.get(standings_url)
    soup = BeautifulSoup(data.text, 'lxml')
    
    standings_table = soup.select_one('table.stats_table')
    if standings_table is None:
        print(f"Standings table not found for {year}")
        continue
    
    team_links = [f"https://fbref.com{l.get('href')}" for l in standings_table.find_all('a') if '/squads/' in l]
    previous_season_link = soup.select("a.prev")
    
    if previous_season_link:
        previous_season = previous_season_link[0].get("href")
        standings_url = f"https://fbref.com{previous_season}"
    else:
        print("No previous season found.")
        break
    
    for team_url in team_links:
        team_name = team_url.split("/")[-1].replace("-Stats", "").replace("-", " ")
        
        data = requests.get(team_url)
        matches = pd.read_html(data.text, match="Scores & Fixtures")[0]
        
        soup = BeautifulSoup(data.text, 'lxml')
        links = [l.get("href") for l in soup.find_all('a')]
        shooting_links = [l for l in links if l and 'all_comps/shooting/' in l]
        
        if not shooting_links:
            print(f"No shooting data for {team_name}")
            continue
        
        data = requests.get(f"https://fbref.com{shooting_links[0]}")
        shooting = pd.read_html(data.text, match="Shooting")[0]
        shooting.columns = shooting.columns.droplevel()
        
        try:
            team_data = matches.merge(shooting[["Date", "Sh", "SoT", "Dist", "FK", "PK", "PKatt"]], on="Date")
        except ValueError:
            print(f"Skipping {team_name} due to missing data.")
            continue
        
        team_data = team_data[team_data["Comp"] == "Premier League"]
        team_data["Season"] = year
        team_data["Team"] = team_name
        all_matches.append(team_data)
        
        time.sleep(2)  

# Combine all data
if all_matches:
    match_df = pd.concat(all_matches)
    match_df.columns = [c.lower() for c in match_df.columns]
    print(match_df.head())
else:
    print("No match data collected.")