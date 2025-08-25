import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import csv
import time
import re

class MatchStatsScraper:
    def __init__(self, csvFiles):
        self.csvFiles = csvFiles
        self.driver = webdriver.Chrome()

    def scrapeAllPages(self):
        allMatchIds = self.getAllMatchIds() 
        allMatchStats = []
        for i in range(len(allMatchIds ) -1): 
            if(i % 100 == 0): 
                self.start_driver()
            basicMatchStats = self.getBasicStats(allMatchIds[i]) 
            allMatchStats.append(basicMatchStats)
        df=  pd.DataFrame(allMatchStats)
        df.to_csv(r"WebScraping/BasicStats")

    def start_driver(self):
        #Restart the Chrome driver (e.g. every 100 matches) 
        if self.driver:
            self.driver.quit()
        self.driver = webdriver.Chrome()

    def getAllMatchIds(self): 
        #Read all Match_IDs from the provided CSVs. 
        allMatchIds = []
        for i in self.csvFiles: 
            df = pd.read_csv(i)
            allMatchIds.extend(df['Match_ID'].to_numpy())
        return allMatchIds

    def getBasicStats(self, matchID): 
       #Open a match API/URL with Selenium and return the page source. 
        url = f"https://www.sofascore.com/api/v1/event/{matchID}"
        self.driver.get(url)
     
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "pre"))
        )
        json_text = self.driver.find_element(By.TAG_NAME, "pre").text
        data = json.loads(json_text)
        match_info = {}
        event = data.get("event", {})
        home = event.get("homeTeam", {})
        away = event.get("awayTeam", {})

        
        status = event.get('status').get('type')
        print(status)
        score = event.get("homeScore", {}).get("current"), event.get("awayScore", {}).get("current")
        match_info["matchID"] = matchID
        match_info["homeTeam"] = home.get("name")
        match_info["awayTeam"] = away.get("name")
        match_info["homeScore"] = score[0]
        match_info["awayScore"] = score[1]
        if(score[1] != None): 
            if(match_info['awayScore'] > match_info['homeScore']): 
                match_info['result'] = 'A'

            elif(match_info['awayScore'] < match_info['homeScore']): 
                match_info['result'] = 'H'
            elif(match_info['awayScore'] == match_info['homeScore']): 
                match_info['result'] = 'D'
        else: match_info['result'] = None

        match_info["season"] = event.get("season", {}).get("year")
        match_info["round"] = event.get("roundInfo").get('round')
        match_info["startDate"] = event.get("startTimestamp")  
        match_info["league"] = event.get("tournament", {}).get("name")
         
        match_info["stadium"] = event.get("venue").get('stadium').get('name')
        print(match_info)
        return  match_info
    


 
scraper = MatchStatsScraper([
    r'WebScraping\bundesMatches.csv',
    r'WebScraping\laLigaMatches.csv',
    r'WebScraping\ligueMatches.csv',
    r'WebScraping\premMatches.csv',
    r'WebScraping\serieMatches.csv'
])

data = scraper.scrapeAllPages() 
