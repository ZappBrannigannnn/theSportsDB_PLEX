
# THE PLEX SPORTSDB SCANNER AND AGENT      
# by ZAPP_BRANNIGAN

THE SCANNER AND AGENT ARE INTENDED FOR USE TOGETHER

***REMEMBER***: There is an API limit of 100 requests per minute. You will get a 429 error if exceeded. This may require you to add your collection a few items at a time.

INSTALLATION
1.	Place the "Series" folder in your "\Plex Media Server\Scanners\" folder
2.	Place the "SportsDBAgent.bundle" folder in your "\Plex Media Server\Plug-ins\" folder
3. In the SCANNERS/SERIES/YourSportsDB_API_KEY.json file, enter your API KEY

IN PLEX 
1.  Create your new sports library as a Tv Show
2.	Select SportsDBAgent as the agent.
3.	Select SportsDBScanner as the scanner (might be selected automatically when SportsDBAgent is selected)
4.  Enter your API KEY in the AGENT settings or in Advanced library settings.

FOLDER STRUCTURE
1. Your library folder can be called whatever you want (usually "SPORTS")
2. In your LIBRARY folder place your LEAGUE folders
3. LEAGUE folders must be named exactly as the league in thesportsdb.com
4. In your LEAGUE folders, place the SEASON folders
5. SEASON folders must be named exactly as the seasons in thesportsdb.com
6. In the season folders, place your match video files

FILE NAMING
1. The agent was deisgned so you wouldn't have to rename video files
    But there are some requirements
    The files must contain:
        A) Either a date or a round number 
            - DATE IS PREFERRED AS IT RETURNS FEWER RESULTS TO MATCH AGAINST
            - ROUND NUMBERS CAN COME IN DIFFERENT PATTERNS
            - IF A FILENAME HAS BOTH THE DATE WILL BE USED
        B) The teams involved (doesn't have to be the full length name, but definitely their unique words.)
2. Examples of filenames and the folder structure of what this SCANNER and AGENT were tested on:

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

THESE FILENAMES DID HAVE TO ALTERED FROM THIS:
"E:\SPORTS\ATP World Tour\2023\Wimbledon 2023.Final.Carlos Alcaraz - Novak Djokovic.mp4"
"E:\SPORTS\ATP World Tour\2023\ATP USOpen 2023 R16 Djokovic v Gojo SS 720p H264 English.mp4"

TO THIS:
"E:\SPORTS\ATP World Tour\2023\Wimbledon.ROUND 38.2023.Final.Carlos Alcaraz - Novak Djokovic.mp4"
"E:\SPORTS\ATP World Tour\2023\ATP USOpen 2023-09-04 Djokovic v Gojo SS 720p H264 English.mp4"
TO INCLUDE THE ROUND OR DATE AS IT IS IN theSportsDB.com

- I would suggest trying it without renaming first. And if it fails to find a match or grabs the wrong one then rename and scan again. 
- Adding dates is always going to be better than adding rounds.


#######################################################################################################################################################################

The SCANNER works by:
1.  Using the league folder as the show
2.  Using the season folders as the seasons
3.  For seasons like "2021-2022" the hyphen is removed and displayed as 20212022. Plex doesn't allow non-numerical characters as seasons
4.  It grabs the date from the filename
5.  If the date is not there it grabs the round
6.  It gets all events for the league/season/date(or round)
7.  It matches words from the filename against the team names and alternate team names in those events
8.  The event with the highest matching score is the event used
9.  The date for the event (minus the hyphens + the relative play order for the date) is used as the episode number so the matches are sorted properly in plex
10. All of this is done in the scanner so that we can name the episodes as the date and sort properly in plex

The AGENT works by:
1.  Checking if the league name is in a map file made in the scanner that pairs league names with their ids
2.  Gets the matching ID
3.  Gets metadata for the league
4.  Uses the season number (re-adds the hyphen if needed)
5.  (Hopefully we can figure out a way to get season posters from the API v1)
5.  It grabs the date from the filename
6.  If the date is not there it grabs the round
7.  It gets all events for the league/season/date(or round)
8.  It matches words from the filename against the team names and alternate team names in those events. 
9.  The event with the highest matching score is the event used
10. It gets metadata for that event and applies it to the episode

There's a little more to it but that's basically it.
