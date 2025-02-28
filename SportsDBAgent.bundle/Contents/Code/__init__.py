# region IMPORTS ########################################################################################

import time, os, datetime
import requests
import sys
import json
import io

from api_client import get_league_info
from api_client import get_team_images
#from api_client import get_season_metadata
from api_client import get_event_id
from api_client import get_event_info

# endregion

# region GLOBAL VARIABLES ###############################################################################

API_KEY = ""  # API Key will be set at startup
API_BASE_URL = "https://www.thesportsdb.com/api/v1/json/"
SPORTSDB_API = ""

# endregion

# region LOGGING ########################################################################################

def LogMessage(dbgline):
	# Wrapper function to log messages using Plex's Log object.bool
	timestamp = time.strftime("\n%H:%M:%S - ")
	
	try:
		Log.Debug("{}{}".format(timestamp, dbgline))  # Correct Plex logging
	except NameError:
		print("\n⚠ Log object is not available. Running in a non-Plex environment.")

# endregion

# region APIKEY_get FUNCTION ############################################################################

def APIKEY_get():
	# Retrieve API Key and store it globally.
	global API_KEY
	global API_BASE_URL
	global SPORTSDB_API

	API_KEY = Prefs['theSportsDBAPIKey']
	if not API_KEY:
		LogMessage("\n❌ No theSportsDB API key provided.")
		return None  # Stop if no key

	LogMessage("\n✅ Got API key from settings.")

	# Construct the API URL
	SPORTSDB_API = str("{}{}".format(API_BASE_URL, API_KEY))

# endregion

# region START FUNCTION #################################################################################

def Start():
	# Required function for Plex plugins to initialize the agent.
	LogMessage("\n🔥 START FUNCTION TRIGGERED.")

	APIKEY_get()  # Call APIKEY_get function\

# endregion

# region SportsScannerAgent CLASS START #################################################################

class SportsDBAgent(Agent.TV_Shows):
	name = 'SportsDBAgent'
	languages = ['en']
	primary_provider = True
	fallback_provider = ['com.plexapp.agents.localmedia']
	accepts_from = ['com.plexapp.agents.localmedia']
	cached_leagues = {}  # Cache to store league details to avoid repeated API calls.

# endregion

	# region SEARCH FUNCTION / SERIES / SHOW / LEAGUE LEVEL STUFF  ######################################

	def search(self, results, media, lang, manual, **kwargs):
		LogMessage("\n🔥 SEARCH FUNCTION TRIGGERED")

		# region STEP 1: Fetch the league ID from the JSON file

		# region GET THE LEAGUE MAP LOCATION
		plex_plugin_data_dir = os.path.join(
			os.getenv('LOCALAPPDATA'),  # AppData\Local on Windows
			'Plex Media Server',
			'Plug-in Support',
			'Data',
			'com.plexapp.agents.SportsDBAgent',  # Replace with your plugin name
			'DataItems'
	)

		# Define the path to the JSON file
		league_map_path = os.path.join(plex_plugin_data_dir, "SportsDB_League_Map.json")

		LogMessage("\nLeague map path: {}".format(league_map_path))
		
		# endregion

		# region OPEN THE LEAGUE DATA FILE AND CHECK IF THE LEAGUE EXISTS
		try:
			with io.open(league_map_path, "r") as f:
				league_data = json.load(f)
				leagues = league_data.get("leagues", [])
		except Exception as e:
			LogMessage("\n❌ Error reading JSON file: {}".format(str(e)))
			leagues = []
		# endregion

		# region SEE IF THE LEAGUE IS IN THE JSON FILE

		# Apply media.show to a usable variable (show_title)
		show_title = None
		show_title = media.show

		league_id = None
		if show_title:
			for league in leagues:
				if league["name"] == show_title:
					league_id = league["id"]
					# Log the league ID pulled from json file matching
					#LogMessage("\n✅ League '{}' ID: {} found in the JSON file.".format(show_title, league_id))
					break
			else:
				LogMessage("\n❌ League '{}' not found in the JSON file.".format(show_title))
				return
		else:
			LogMessage("\n❌ Show title is missing. Skipping league ID lookup.")
			return

		# endregion

		# endregion

		# STEP 2: Get league metadata info
		# region

		# Get all the league metadata
		league_metadata = get_league_info(league_id, SPORTSDB_API)

		if league_metadata == None:
			LogMessage("\n❌ No metadata found for league ID (1): {}\nSTOPPING".format(league_id))
			return  # Stop execution early if no metadata from API 

		# endregion

		# STEP 3: Update "Results"
		# region

		# Store only the league ID in metadata.id
		league_identifier = "{}".format(league_id)
		# Get the year from the metadata
		league_year = league_metadata["intFormedYear"]
		# Get the the thumb from the metadata
		league_thumb = league_metadata["strPoster"]
		# Get the art from the metadata (doesn't seem to be being use anymore too lazy to test right now)
		league_art = league_metadata["strFanart1"]

		# Return a minimal search result (Plex will auto-select)
		results.Append(MetadataSearchResult(
			id=league_identifier,
			name=show_title,
			year=league_year,
			lang=lang,
			thumb=league_thumb,
			score=100  # Full confidence match
		))

		# endregion

	# endregion

	# region UPDATE FUNCTION / LEAGUE METADATA / EPISODE EVERYTHING #####################################

	# (1) call_get_league_info (CALLED BY UPDATE)
	# region
	def call_get_league_info(self, metadata, league_id):

		league_metadata = get_league_info(league_id, SPORTSDB_API)

		# Update the metadata with the retrieved league information.
		metadata.title = league_metadata['strLeague']
		metadata.summary = league_metadata['strDescriptionEN']
		if not league_metadata['strSport'] in metadata.genres:
			metadata.genres.add(league_metadata['strSport'])

		try:
			year = int(league_metadata['intFormedYear'])  # Ensure it's an integer
			metadata.originally_available_at = datetime.datetime(year, 1, 1)  # Convert to a date (Jan 1st)
		except (KeyError, ValueError, TypeError):
			pass  # Handle missing/invalid data gracefully

		# Ensure tags do not contain empty values
		metadata.tags = list(filter(None, [
			league_metadata.get("strLeagueAlternate", ""),
			league_metadata.get("strCountry", "")
		]))

		fanart_url = league_metadata.get("strFanart1")
		if fanart_url:
			LogMessage("\n✅ Retrieved fanart / background images for league: {}".format(league_id))
			metadata.art[fanart_url] = Proxy.Preview(HTTP.Request(fanart_url, sleep=0.5).content, sort_order=1)

	# endregion

	# (2) call_get_team_images (CALLED BY UPDATE)
	# region
	def call_get_team_images(self, metadata, league_id):
		team_images = get_team_images(league_id, SPORTSDB_API)  # This is a LIST

		if not team_images:
			LogMessage("\n❌ No team images found for League ID: {}.\nStopping.".format(league_id))
			return  

		metadata.roles.clear()  # Clear existing roles if needed

		# Loop directly since `team_images` is a list
		for team in team_images:
			if isinstance(team, dict):  # Ensure it's a dictionary
				team_name = team.get("strTeam", "Unknown Team")
				team_logo = team.get("strBadge")

				if team_logo:
					role = metadata.roles.new()
					role.name = team_name  # Team name in the "actor" section
					role.role = "Team"  # Generic role
					role.photo = team_logo  # URL to team logo

	# endregion




	"""
	# (3) Season images CAN'T GET SUMMARY TO WORK!!!
	# region
	def season_stuff(self, metadata, media, league_id):
		# Ensure seasons have posters and artwork by fetching from TheSportsDB if missing.        
		LogMessage("\n🔍 Checking SEASON metadata for show: {}".format(metadata.title))

		for season_id in media.seasons:
			LogMessage("\n📅 Processing Season: {}".format(season_id))

			# Create season metadata if it doesn't exist albeit empty (initialize)
			if season_id not in metadata.seasons:
				LogMessage("\n⚠️ Season {} does not exist in metadata.".format(season_id))
				metadata.seasons[season_id] = Metadata.Season()
			else:
				LogMessage("\n✅ Season {} already exists in metadata.".format(season_id))
			
			# Assign to be used in API search
			season_metadata = metadata.seasons[season_id]

			# Skip if season already has both poster & artwork
			if season_metadata.art and season_metadata.posters:
				LogMessage("\n✅ Season {} already has artwork and posters.".format(season_id))
				continue
			else:
				LogMessage("\n⚠️ Season {} does not have both poster and artwork.".format(season_id))

			# Fetch season metadata from TheSportsDB API ###<><><><><><><><><><><><><><><><<<<<<>>>><><<<<<<<><><

			# Make season_id usable before using it for the API
			season_id = str(season_id)

			season_data = get_season_metadata(league_id, season_id, API_KEY)

			if not season_data:
				LogMessage("\n⚠️ No metadata found for Season {}!".format(season_id))
				continue

			# Get poster and fanart URLs
			poster_url = season_data.get("strPoster")
			fanart_url = season_data.get("strFanart")

			# Download and assign missing poster
			if not season_metadata.posters and poster_url:
				season_metadata.posters[poster_url] = Proxy.Preview(HTTP.Request(poster_url, sleep=0.5).content, sort_order=1)
				LogMessage("\n✅ Added poster for Season {}: {}".format(season_id, poster_url))

			# Download and assign missing artwork
			if not season_metadata.art and fanart_url:
				season_metadata.art[fanart_url] = Proxy.Preview(HTTP.Request(fanart_url, sleep=0.5).content, sort_order=1)
				LogMessage("\n✅ Added artwork for Season {}: {}".format(season_id, fanart_url))

		LogMessage("\n🎉 Season metadata update complete!")

	# endregion
	"""




	# (5) Get the event id
	# region

	def call_get_event_id(self, season_number, episode_number, episode_path, league_id):

		event_id = get_event_id(season_number, episode_number, episode_path, league_id, SPORTSDB_API)
		
		return event_id

	# endregion

	# (6) Get event metadata
	# region

	def call_get_event_metadata(self, event_id):
		
		event_metadata = get_event_info(SPORTSDB_API, event_id)

		return event_metadata

	# endregion

	# (7) UPDATE EPISODE METADATA
	# region

	def update_episode_metadata(self, metadata, media, event_metadata, episode, season_number, episode_number, episode_path):

		# Extract metadata safely with fallback values
		eventtitle = event_metadata.get('strEvent', 'Unknown Event') or 'Unknown Event'
		summary = event_metadata.get('strDescriptionEN', 'No SportsDBdescription available.') or 'No SportsDB description available.'
		date = event_metadata.get('dateEvent', '') or ''
		time = event_metadata.get('strTime', '') or ''

		round_num = str(event_metadata.get('intRound', 'Unknown'))
		spectators = str(event_metadata.get('intSpectators')) if event_metadata.get('intSpectators') is not None else "Unknown number of spectators"

		venue = event_metadata.get('strVenue', 'Unknown Venue') or 'Unknown Venue'
		city = event_metadata.get('strCity', 'Unknown City') or 'Unknown City'
		country = event_metadata.get('strCountry', 'Unknown Country') or 'Unknown Country'

		thumb = event_metadata.get('strThumb', '') or ''
		fanart = event_metadata.get('strFanart', '') or ''

		# Format summary
		my_summary = ("Round {} {}\n{} in {},{}\n{} in attendance\n{}".format(round_num, date, venue, city, country, spectators, summary))

		# Assign metadata
		episode.title = ("Round {} {}".format(round_num, eventtitle))
		episode.summary = my_summary

		# Handle date safely
		if date:
			try:
				episode.originally_available_at = datetime.datetime.strptime(date, "%Y-%m-%d").date()
			except ValueError:
				LogMessage("\n❌ ERROR: Invalid date format: {}".format(date))

		# Assign images correctly (validate URLs first)
		if thumb and thumb.startswith("http"):
			try:
				episode.thumbs[thumb] = Proxy.Preview(HTTP.Request(thumb, sleep=0.5).content, sort_order=1)
			except Exception as e:
				LogMessage("\n❌ ERROR: Failed to assign thumb: {}".format(e))

		if fanart and fanart.startswith("http"):
			try:
				episode.art[fanart] = Proxy.Preview(HTTP.Request(fanart, sleep=0.5).content, sort_order=1)
			except Exception as e:
				LogMessage("\n❌ ERROR: Failed to assign fanart: {}".format(e))

		#LogMessage("\n✅ Successfully updated metadata for: {} - S{}E{}".format(eventtitle, season_number, episode_number))

	# endregion

	# region UPDATE FUNCTION

	def update(self, metadata, media, lang, force):
		LogMessage("\n🔥 UPDATE FUNCTION TRIGGERED for League ID: {}".format(metadata.id))

		# region UPDATE STEPS (1) & (2) FILL IN LEAGUE/SHOW METADATA (fanart & team images)

		league_id = metadata.id

		# Check if the league already has an art (fanart/background)
		if metadata.art:
			LogMessage("\n🖼️ League ID {} already has art applied: {}".format(
				league_id, list(metadata.art.keys())[0]))
		else:
			# UPDATE STEP (1): Get league metadata
			self.call_get_league_info(metadata, league_id)

		# Check if the league's roles are already populated
		if metadata.roles:
			LogMessage("\n👥 League ID {} already has roles applied. First role: {}".format(
				league_id, metadata.roles[0].name if metadata.roles[0] else "Unknown"))
		else:
			# UPDATE STEP (2): Get team images
			self.call_get_team_images(metadata, league_id)

		# endregion



		""" TEST
		# STEP (3): Get season stuff maybe here
		self.season_stuff(metadata, media, league_id)
		"""

		""" ### CAN I DELETE THIS????? ###
		for season_number in media.seasons:
			LogMessage("\n\nSeasonnnnnnnnnnnnnn: {}".format(season_number))
			
			for episode_number in media.seasons[season_number].episodes:
				episode_media = media.seasons[season_number].episodes[episode_number]
				
				for item in episode_media.items:
					file_path = item.parts[0].file  # Access the file path
					LogMessage("\nEpisode: {}, File: {}\n\n".format(episode_number, file_path))
			"""
		


		# region STEP (4) ITERATE THROUGH SEASONS AND EPISODES

		# Iterate through each season
		for season_number in media.seasons:
			# Iterate through each episode
			for episode_number in media.seasons[season_number].episodes:
				episode = metadata.seasons[season_number].episodes[episode_number]
				episode_media = media.seasons[season_number].episodes[episode_number]

				# Ensure episode media exists before accessing file path
				if not episode_media.items or not episode_media.items[0].parts:
					LogMessage("\n❌ ERROR: Missing media parts for S{}E{}, skipping.".format(season_number, episode_number))
					continue

				# Extract episode's file path
				episode_path = episode_media.items[0].parts[0].file
				LogMessage("\n🎬 Processing Episode: S{}E{} - Path: {}".format(season_number, episode_number, episode_path))

		# endregion

				# region STEP (5) GET THE EVENT ID

				event_id = self.call_get_event_id(season_number, episode_number, episode_path, league_id)

				if not event_id:
					LogMessage("\n❌ ERROR: No event ID found for S{}E{}, skipping.".format(season_number, episode_number))
					continue  # Skip this episode if no event ID

				# endregion

				# region STEP (6) FETCH EVENT METADATA

				event_metadata = self.call_get_event_metadata(event_id)

				if not event_metadata:
					LogMessage("\n❌ ERROR: No event metadata found for Event ID {}, skipping.".format(event_id))
					continue  # Skip this episode if no metadata
				
				#LogMessage("\n✅ Applying Metadata for S{}E{} - Event: {}".format(season_number, episode_number, event_metadata.get("strEvent", "Unknown Event")))

				# endregion

				# region STEP (7) UPDATE EPISODE METADATA
				
				self.update_episode_metadata(metadata, media, event_metadata, episode, season_number, episode_number, episode_path)

				# endregion

		LogMessage("\n✅ UPDATE FUNCTION COMPLETED SUCCESSFULLY.")

		# endregion

	# endregion