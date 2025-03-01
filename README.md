
# THE PLEX SPORTSDB SCANNER AND AGENT      
# BY ZAPP_BRANNIGAN                                                      

1. The Scanner and Agent are intended for use together
2. In the SCANNERS/SERIES folder, enter your API KEY in the YourSportsDB_API_KEY.json file
3. Your API KEY must aslo be entered in the AGENT settings in Plex.
4. In your LIBRARY (SPORTS) folder place your LEAGUE folders
5. The LEAGUE folders must be named exactly as the league in thesportsdb.com
6. In your league folders, place the SEASON folders
7. The SEASON folders must be named exactly as the seasons in thesportsdb.com
8. In the season folders, place your match video files
9. The agent was deisgned so you wouldn't have to rename downloaded video files
    But there are some requirements
    The files must contain:
        A) Either a date or a round number 
            - DATE IS PREFERRED AS IT RETURNS FEWER RESULTS TO MATCH AGAINST
            - IF A FILENAME HAS BOTH THE DATE WILL BE USED
        B) The teams involved (doesn't have to be the full length name)
10. Examples of filenames and the folder structure of what this SCANNER and AGENT were tested on:

"E:\SPORTS\Australian National Rugby League\2021\NRL 2021 - Round 25 - Titans vs Warriors 1080p.mp4"
"E:\SPORTS\Australian National Rugby League\2021\NRL 2021 Round 8 - Dragons v Tigers 576p x264.mp4"
"E:\SPORTS\Australian National Rugby League\2022\NRL 2022 Round 3 - Sea Eagles v Bulldogs 720p50 H.264.mp4"
"E:\SPORTS\Australian National Rugby League\2022\2022 - Round 8 - Eels vs Cowboys 1080p.mp4"
"E:\SPORTS\Australian National Rugby League\2023\NRL - 2023 - Round 23 - Raiders vs Tigers 1080p.mp4"
"E:\SPORTS\Australian National Rugby League\2023\NRL 2023 Round 5 - Sharks v Warriors 720p50 H.264.mp4"
"E:\SPORTS\Australian National Rugby League\2024\NRL 2024 Round 2 - Sea Eagles v Roosters 1080p H.264.mp4"
"E:\SPORTS\Australian National Rugby League\2024\NRL 2024 Round 9 - Knights v Warriors - 720p.mp4"

"E:\SPORTS\English Premier League\2020-2021\2020.09.26_EPL_2020_21_R.02_Crystal_Palace_vs_Everton_[rgfootball.net]_720p.50_SSU.mp4"
"E:\SPORTS\English Premier League\2020-2021\English.Premier.League.2020.2021.Week.01.Leeds.United.vs.Liverpool.720p.HDTV.x264-SceneGroup.mp4"
"E:\SPORTS\English Premier League\2021-2022\2022.05.01_EPL_2021_22_R.35_West_Ham_United_vs_Arsenal_FC_[rgfootball.net]_720p.50_SSU.mp4"
"E:\SPORTS\English Premier League\2021-2022\Premier.League.2021.2022.Round.12.Chelsea.vs.Leicester.720p.HDTV.x265-ReleaseHQ.mp4"
"E:\SPORTS\English Premier League\2022-2023\Premier.League.2022-2023.MW18.SNF.Brighton.and.Hove.Albion-Arsenal.SkyPLHD.1080p.IPTV.AAC2.0.x264.Eng-WB60.mp4"
"E:\SPORTS\English Premier League\2023-2024\Soccer Premier League Manchester City Arsenal 31 03 2024 1080p25.mp4"

THESE ONES WORKED BECAUSE THEY WERE THE ONLY ONES ON THE SPECIFIC DATE:
"E:\SPORTS\English Premier League\2022-2023\20230811_EPL_23.24_R.01_BUR_vs_MCI_[rgfootball.net]_720p.50_STU.mp4"
"E:\SPORTS\English Premier League\2023-2024\20240816_EPL_24.25_R.01_MUN_vs_FUL_[rgfootball.net]_720p.25.mp4"

"E:\SPORTS\Formula 1\2023\Formula 1 2023 Round 01 BahrainGP Practice 1 F1 Live 1080p.mp4"
"E:\SPORTS\Formula 1\2023\Formula 1 2023 Round 01 BahrainGP Practice 3 F1 Live 1080p.mp4"
"E:\SPORTS\Formula 1\2023\Formula 1 2023 Round 19 UnitedStatesGP Race F1 Live 1080p.mp4"
"E:\SPORTS\Formula 1\2023\Formula.1.2023.Round.02.SaudiArabianGP.Practice.2.F1.Live.1080p.mp4"
"E:\SPORTS\Formula 1\2023\Formula.1.2023.Round.03.AustralianGP.Qualifying.F1.Live.720p.mp4"

THESE FILESNAMES DID HAVE TO ALTERED FROM THIS:
"E:\SPORTS\ATP World Tour\2023\Wimbledon 2023.Final.Carlos Alcaraz - Novak Djokovic.mp4"
"E:\SPORTS\ATP World Tour\2023\ATP USOpen 2023 R16 Djokovic v Gojo SS 720p H264 English.mp4"
TO THIS:
"E:\SPORTS\ATP World Tour\2023\Wimbledon.ROUND 38.2023.Final.Carlos Alcaraz - Novak Djokovic.mp4"
"E:\SPORTS\ATP World Tour\2023\ATP USOpen 2023-09-04 Djokovic v Gojo SS 720p H264 English.mp4"
TO INCLUDE THE ROUND OR DATE AS IT IS IN theSportsDB.com

- I would suggest trying it without renaming first. And if it fails to find a match or grabs the wrong one then rename and scan again. 
- Adding dates is always going to be better than adding rounds.
