import pandas as pd
import time
import os
from nba_api.stats.endpoints import leaguegamefinder, playbyplayv2

# Headers to make the NBA think we are a person on a laptop
HEADERS = {
    'Host': 'stats.nba.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.nba.com/',
    'Connection': 'keep-alive',
}

def run_scraper():
    # 1. Create an empty file first so GitHub Actions doesn't "fail" if we get blocked
    if not os.path.exists('nba_data.csv'):
        pd.DataFrame(columns=["Date","Away","Home","Away_L4","Home_L4"]).to_csv('nba_data.csv', index=False)

    print("Requesting games from NBA...")
    try:
        # Get the 10 most recent games
        finder = leaguegamefinder.LeagueGameFinder(
            season_nullable='2025-26', 
            league_id_nullable='00', 
            season_type_nullable='Regular Season',
            headers=HEADERS
        )
        games = finder.get_data_frames()[0].head(10)
        
        all_games_l4 = []

        for _, row in games.iterrows():
            gid = row['GAME_ID']
            matchup = row['MATCHUP'] # e.g. "LAL vs. BOS"
            print(f"Analyzing: {matchup}")

            try:
                # Fetch Play-by-Play
                pbp = playbyplayv2.PlayByPlayV2(game_id=gid, headers=HEADERS).get_data_frames()[0]
                
                # Filter for 4th Quarter (Period 4)
                p4 = pbp[pbp['PERIOD'] == 4].copy()
                
                # Get score at 4:00 and at the end
                # We look for the play closest to the 4-minute mark
                l4_plays = p4[p4['PCTIMESTRING'] <= '04:00']
                
                if not l4_plays.empty:
                    start_score = l4_plays.iloc[0]['SCORE']
                    end_score = p4.iloc[-1]['SCORE']

                    def split_pts(score_str):
                        if not score_str or '-' not in str(score_str): return 0, 0
                        return map(int, str(score_str).replace(" ","").split('-'))

                    v_start, h_start = split_pts(start_score)
                    v_end, h_end = split_pts(end_score)

                    all_games_l4.append({
                        "Date": row['GAME_DATE'],
                        "Away": matchup.split(' ')[0],
                        "Home": matchup.split(' ')[-1],
                        "Away_L4": v_end - v_start,
                        "Home_L4": h_end - h_start
                    })
                
                # Important: Wait 2 seconds so the NBA doesn't block your IP
                time.sleep(2)

            except Exception as e:
                print(f"Skipping game {gid}: {e}")
                continue

        # Save the results
        if all_games_l4:
            df = pd.DataFrame(all_games_l4)
            df.to_csv('nba_data.csv', index=False)
            print("Successfully updated nba_data.csv")
        else:
            print("No new L4 data found, but file is safe.")

    except Exception as e:
        print(f"NBA API is being difficult: {e}")

if __name__ == "__main__":
    run_scraper()
