import pandas as pd
import time
from nba_api.stats.endpoints import leaguegamefinder, playbyplayv2

def get_l4_stats():
    print("Fetching 2025-26 Season Games...")
    # Get all regular season games for the current year
    gamefinder = leaguegamefinder.LeagueGameFinder(season_nullable='2025-26', league_id_nullable='00', season_type_nullable='Regular Season')
    games = gamefinder.get_data_frames()[0]
    games = games.drop_duplicates(subset=['GAME_ID'])
    
    all_data = []
    # To keep it fast for GitHub Actions, we only scrape the most recent 50 games daily
    # You can increase this for a one-time "full season" run
    game_ids = games['GAME_ID'].head(50).tolist()

    for gid in game_ids:
        try:
            pbp = playbyplayv2.PlayByPlayV2(game_id=gid).get_data_frames()[0]
            p4 = pbp[pbp['PERIOD'] == 4]
            if p4.empty: continue
            
            # Find score at exactly or just after 4:00 remaining
            # PCTIMESTRING is 'MM:SS'
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
            time.sleep(0.5) # Prevent API lockout
        except:
            continue
            
    pd.DataFrame(all_data).to_csv('nba_data.csv', index=False)

if __name__ == "__main__":
    get_l4_stats()
