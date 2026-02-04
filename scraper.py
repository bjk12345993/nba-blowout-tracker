import pandas as pd
import time
from nba_api.stats.endpoints import leaguegamefinder, playbyplayv2

# This part "tricks" the NBA into thinking you are a regular browser
HEADERS = {
    'Host': 'stats.nba.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Origin': 'https://www.nba.com',
    'Referer': 'https://www.nba.com/',
    'Connection': 'keep-alive',
}

def get_l4_stats():
    print("Fetching 2025-26 Season Games...")
    try:
        gamefinder = leaguegamefinder.LeagueGameFinder(
            season_nullable='2025-26', 
            league_id_nullable='00', 
            season_type_nullable='Regular Season',
            headers=HEADERS,
            timeout=60
        )
        games = gamefinder.get_data_frames()[0]
        games = games.drop_duplicates(subset=['GAME_ID'])
        
        all_data = []
        # We only do the 15 most recent games to keep the "robot" fast and safe
        game_ids = games['GAME_ID'].head(15).tolist()

        for gid in game_ids:
            try:
                pbp = playbyplayv2.PlayByPlayV2(game_id=gid, headers=HEADERS).get_data_frames()[0]
                p4 = pbp[pbp['PERIOD'] == 4]
                if p4.empty: continue
                
                l4_start = p4[p4['PCTIMESTRING'] <= '04:00'].iloc[0]
                final = p4.iloc[-1]

                def parse(s):
                    if not s or '-' not in str(s): return 0, 0
                    return map(int, str(s).replace(" ","").split('-'))

                v_start, h_start = parse(l4_start['SCORE'])
                v_end, h_end = parse(final['SCORE'])

                game_info = games[games['GAME_ID'] == gid].iloc[0]
                all_data.append({
                    "Date": game_info['GAME_DATE'],
                    "Away": game_info['MATCHUP'].split(' ')[0],
                    "Home": game_info['MATCHUP'].split(' ')[-1],
                    "Away_L4": v_end - v_start,
                    "Home_L4": h_end - h_start
                })
                print(f"Processed game {gid}")
                time.sleep(2.0) # Longer pause to avoid getting banned
            except Exception as e:
                print(f"Error on game {gid}: {e}")
                continue
                
        pd.DataFrame(all_data).to_csv('nba_data.csv', index=False)
        print("Success! Data saved to nba_data.csv")
    except Exception as e:
        print(f"Failed to fetch game list: {e}")

if __name__ == "__main__":
    get_l4_stats()
