# -*- coding: utf-8 -*-

# region IMPORTS
import sys
import os

# Add SportsDBScannerHelpers to sys.path
helpers_dir = os.path.join(os.path.dirname(__file__), 'SportsDBScannerHelpers')
if helpers_dir not in sys.path:
	sys.path.append(helpers_dir)

import re, os.path, random
import Media, VideoFiles, Stack, Utils
import time
from datetime import datetime
import urllib3
from logging_config import LogMessage # LOGGING_CONFIG.PY
import json
from scan_api_client import get_league_id
from scan_api_client import get_event_id
# endregion

# region GET API KEY and Create SPORTSDB API

# Get the absolute path to settings.json (same directory as script)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # Get current script directory
SETTINGS_FILE = os.path.join(SCRIPT_DIR, "YourSportsDB_API_KEY.json")  # Construct full path
# Check if the settings file exists
if not os.path.exists(SETTINGS_FILE):
	raise FileNotFoundError("ERROR: settings.json not found! Please create the file and add your API key.")
# Read settings.json
with open(SETTINGS_FILE, "r") as file:
	settings = json.load(file)
# Get API Key from JSON
API_KEY = settings.get("API_KEY")
if not API_KEY:
	raise ValueError("ERROR: No API Key found in settings.json!")

# Build API URL
API_BASE_URL = "https://www.thesportsdb.com/api/v1/json/"
SPORTSDB_API = "{}{}".format(API_BASE_URL, API_KEY)

# endregion

# region SCAN FUNCTION

# region scan function start
def Scan(path, files, mediaList, subdirs, language=None, root=None):
	global SPORTSDB_API
	LogMessage("")
	LogMessage("►► STARTING SCAN")
# endregion

	# region GET LEAGUE AND SEASON NAMES FROM FOLDERS
	try:
		# Ensure we have enough folder depth (needs at least: /SPORTS/LEAGUE/SEASON/)
		path_parts = path.split(os.sep)
		if len(path_parts) < 2:
			return

		league_name = path_parts[-2]  # LEAGUE = Show Name
		season_name = path_parts[-1]  # SEASON Folder (e.g., "2023", "2021-2022")
		#<<
		LogMessage("►► League: {}".format(league_name))
		LogMessage("►► Season: {}".format(season_name))

	except Exception as e:
		LogMessage("►► ERROR: Getting the league and season folder words (something weird happened): {}".format(str(e)))
		return

	# endregion

	# region DEFINE/CREATE THE JSON FILE LOCATION TO WRITE THE LEAGUE MAP TO

	# Get the Plex plugin data directory to write the JSON league map to
	if os.name == 'nt':  # Windows
		base_dir = os.getenv('LOCALAPPDATA', os.path.expanduser("~"))
	else:  # Linux/Debian
	    base_dir = "/var/lib/plexmediaserver/Library/Application Support"

	plex_plugin_data_dir = os.path.join(
		base_dir,
		'Plex Media Server',
		'Plug-in Support',
		'Data',
		'com.plexapp.agents.SportsDBAgent',
		'DataItems'
	)

	# Create the Plex plugin data directory if it doesn't exist
	if not os.path.exists(plex_plugin_data_dir):
		"""LogMessage("plex_plugin_data_dir does not exist, creating it: {}".format(plex_plugin_data_dir))"""
		try:
			os.makedirs(plex_plugin_data_dir)
		except OSError as e:
			LogMessage("►► Error creating Plex plugin data directory (1): {}".format(str(e)))
			if not os.path.isdir(plex_plugin_data_dir):  # Ensure another process didn't create it
				LogMessage("►► Error creating Plex plugin data directory (2): {}".format(str(e)))
				raise

	# Define the league ID map file path and create if it doesn't exist
	league_id_map_file = os.path.join(plex_plugin_data_dir, "SportsDB_League_Map.json")
	if not os.path.exists(league_id_map_file):
		with open(league_id_map_file, "w") as f:
			json.dump({"leagues": []}, f)  # Initialize with an empty list for "leagues"

	# endregion

	# region OPEN THE LEAGUE DATA FILE AND CHECK IF THE LEAGUE EXISTS
	try:
		with open(league_id_map_file, "r") as f:
			league_data = json.load(f)
			leagues = league_data.get("leagues", [])
	except Exception as e:
		LogMessage("►► Error reading JSON file: {}".format(str(e)))
		leagues = []

	# Check if the league_name already exists in the leagues list
	league_exists = False
	league_id = None

	for league in leagues:
		if league["name"] == league_name:
			# Assign the id from json file to league_id
			league_id = league["id"]
			# if the matching league name's league id is none, keep league_exists as False
			if league_id is not None:
				# If the id is not None, set league_exists to True
				league_exists = True
			break
	# endregion

	# region IF THE LEAGUE DOES NOT EXIST, GET THE LEAGUE ID FROM THE API_CLIENT AND ADD IT TO THE LIST

	if not league_exists:

		# GET THE LEAGUE ID FROM THE API_CLIENT
		league_id = get_league_id(league_name, SPORTSDB_API)

		# Add the new league to the leagues list
		new_league = {"name": league_name, "id": league_id}  # Use the league_id from the API
		leagues.append(new_league)

		# Update the JSON file with the new league data
		try:
			with open(league_id_map_file, "w") as f:
				json.dump({"leagues": leagues}, f, indent=4)
			"""LogMessage("►► Added new league to JSON file: '{}' with ID: {}".format(league_name, league_id))"""
		except Exception as e:
			LogMessage("►►  Error updating JSON file: {}".format(str(e)))

	# endregion

	# region GET EVENT ID

	# region Iterate through files
	for file in files:
		filename = os.path.basename(file)  # Extracts the actual file name, e.g., "episodeXYZ123.mp4"

		# Ignore files that end with
		if not filename.endswith((".mp4", ".avi", ".mov", ".wmv", ".flv", ".mkv", ".mpeg", ".3gp", ".webm", ".m4v")):
			LogMessage("►► Skipping non-videofile: {}".format(filename))
			continue
		# endregion

		# region Get the event ID from the API_CLIENT
		LogMessage("►► Processing Filename: {}".format(filename))
		LogMessage("►► Processing League: {}".format(league_id))
		LogMessage("►► Season: {}\n".format(season_name))

		event_id, event_title, event_date, order_number = get_event_id(league_name, league_id, season_name, filename, SPORTSDB_API)
		# endregion

		# region Process the event info before applying.
		if event_id is None:
			event_id = "No event ID found"

		if event_title is None:
			event_title = filename.split(".")[0]	# filename minus extension

		if event_date is None:
			# Number based on timestamp
			event_date =  int(time.time()) % 10000000000	# Last 10 digits of timestamp
			event_year = season_name[:4]	# event_year is first 4 digits of season_number
		else:
			event_year = event_date.split("-")[0]	# get the first portion of the date before "-"
			event_date = event_date.replace("-", "") 	# remove the "-"
			event_date = str(event_date) + str(order_number).zfill(2)	# Add order_number to event_date with a buffer of 2 digits

		if order_number is None:
			order_number = "00"		# Default to 00
		else:
			order_number = str(order_number)[-2:]  # Keep only last 2 digits
		
		season_number = season_name.replace("-", "")  # remove the "-"

		LogMessage("►► LEAGUE / SHOW NAME: {}".format(league_name))
		LogMessage("►► LEAGUE ID {}".format(league_id))
		LogMessage("►► SEASON: {}".format(season_number))
		LogMessage("►► EVENT TITLE: {}".format(event_title))
		LogMessage("►► EVENT ID: {}".format(event_id))
		LogMessage("►► EVENT DATE & ORDER #: {}".format(event_date))
		LogMessage("►► EVENT YEAR: {}".format(event_year))

		# endregion

		# region Create Media.Episode object for Plex
		media = Media.Episode(
			league_name.encode("utf-8"),     # Show Name / League Name
			season_number.encode("utf-8"),   # Season Number
			str(event_date).encode("utf-8"),   # Episode Number (Event ID)
			event_title.encode("utf-8"),     # Episode Title (Event Name)
			str(event_year).encode("utf-8"), # Episode Year
)
		
		media.parts.append(file) # Append the file path
		mediaList.append(media)

		LogMessage("►► Processed 'media' {}\n\n".format(media))

	LogMessage("►► FINISHED SCAN\n")
	# endregion
