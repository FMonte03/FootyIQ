import json
import csv
import time
import re
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class SofaScoreSeleniumScraper:
    def __init__(self, base_urls: List[str], headless: bool = True):
        self.base_urls = base_urls if isinstance(base_urls, list) else [base_urls]
        self.tournaments = [self._parse_url(url) for url in self.base_urls]
        self._setup_driver(headless)
        
    def _parse_url(self, url: str) -> Dict:
        match = re.search(r'unique-tournament/(\d+)/season/(\d+)/events/round/(\d+)', url)
        if not match:
            raise ValueError(f"Invalid URL format: {url}")
        return {
            'tournament_id': int(match.group(1)),
            'season_id': int(match.group(2)),
            'start_round': int(match.group(3))
        }
        
    def _setup_driver(self, headless: bool):
        options = Options()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def _get_round_events(self, tournament_id: int, season_id: int, round_num: int) -> List[int]:
        url = f"https://www.sofascore.com/api/v1/unique-tournament/{tournament_id}/season/{season_id}/events/round/{round_num}"
        
        try:
            self.driver.get(url)
            time.sleep(0.3)
            
            json_data = self._extract_json(self.driver.page_source)
            return [event['id'] for event in json_data.get('events', []) if 'id' in event]
            
        except Exception as e:
            print(f"Error round {round_num}: {e}")
            return []
    
    def _extract_json(self, page_source: str) -> Dict:
        pre_match = re.search(r'<pre[^>]*>(.*?)</pre>', page_source, re.DOTALL)
        if pre_match:
            try:
                json_text = pre_match.group(1).strip()
                json_text = json_text.replace('&quot;', '"').replace('&lt;', '<').replace('&gt;', '>')
                return json.loads(json_text)
            except json.JSONDecodeError:
                pass
        
        if '"events"' in page_source:
            start_idx = page_source.find('{')
            if start_idx != -1:
                brace_count = 0
                for i, char in enumerate(page_source[start_idx:], start_idx):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            try:
                                return json.loads(page_source[start_idx:i+1])
                            except json.JSONDecodeError:
                                break
        return {}
    
    def scrape_all(self, max_rounds: int = 38) -> Dict[str, Dict[int, List[int]]]:
        all_data = {}
        
        for tournament in self.tournaments:
            tid, sid = tournament['tournament_id'], tournament['season_id']
            key = f"tournament_{tid}_season_{sid}"
            all_data[key] = {}
            
            for round_num in range(1, max_rounds + 1):
                all_data[key][round_num] = self._get_round_events(tid, sid, round_num)
        
        return all_data
    
    def save_csv(self, data: Dict[str, Dict[int, List[int]]], filename: str = "matches.csv"):
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Tournament_Season', 'Round', 'Match_ID'])
            
            for tournament_key, rounds_data in data.items():
                for round_num, match_ids in rounds_data.items():
                    for match_id in match_ids:
                        writer.writerow([tournament_key, round_num, match_id])
    
    def close(self):
        if hasattr(self, 'driver'):
            self.driver.quit()

def scrape_matches(urls: List[str], max_rounds: int = 38, filename: str = "matches.csv"):
    scraper = SofaScoreSeleniumScraper(urls)
    try:
        data = scraper.scrape_all(max_rounds)
        scraper.save_csv(data, filename)
        return data
    finally:
        scraper.close()

if __name__ == "__main__":
    urls = [
        'https://www.sofascore.com/api/v1/unique-tournament/34/season/77356/events/round/1',
        'https://www.sofascore.com/api/v1/unique-tournament/34/season/61736/events/round/1',
        'https://www.sofascore.com/api/v1/unique-tournament/34/season/52571/events/round/1',
        'https://www.sofascore.com/api/v1/unique-tournament/34/season/42273/events/round/1',
        'https://www.sofascore.com/api/v1/unique-tournament/34/season/37167/events/round/1'
    ]
    scrape_matches(urls, max_rounds=34, filename="ligueMatches.csv")