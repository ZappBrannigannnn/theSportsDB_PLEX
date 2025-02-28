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

# API CLIENT IMPORTS
from scan_api_client import get_league_id
from scan_api_client import get_event_id

# endregion

# region GET API KEY and SPORTSDB API

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
			return  # Not enough depth to extract metadata

		league_name = path_parts[-2]  # LEAGUE = Show Name
		season_name = path_parts[-1]  # SEASON Folder (e.g., "2023", "2021-2022", "Spring 2023")

		#LogMessage("►► League: {}\n►► Season: {}".format(league_name, season_name))

	except Exception as e:
		LogMessage("►► Error extracting metadata: {}".format(str(e)))
		return

	# endregion

	# region GET LEAGUE ID FROM JSON OR API CLIENT

	# Get the Plex plugin data directory
	plex_plugin_data_dir = os.path.join(
		os.getenv('LOCALAPPDATA'),  # AppData\Local on Windows
		'Plex Media Server',
		'Plug-in Support',
		'Data',
		'com.plexapp.agents.SportsDBAgent',  # Replace with your plugin name
		'DataItems'
	)

	if not os.path.exists(plex_plugin_data_dir):
		os.makedirs(plex_plugin_data_dir)

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
	for league in leagues:
		if league["name"] == league_name:
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
			LogMessage("►► Added new league to JSON file: '{}' with ID: {}".format(league_name, league_id))
		except Exception as e:
			LogMessage("►►  Error updating JSON file: {}".format(str(e)))

	# endregion

	# region IF THE LEAGUE EXISTS, GET THE LEAGUE ID FROM THE LIST

	else:
		league_id = league["id"]

	# endregion

	# region GET EVENT ID

	# Iterate through files
	for file in files:
		filename = os.path.basename(file)  # Extracts the actual file name, e.g., "episodeXYZ123.mp4"

		
		# Get the event ID from the API_CLIENT
		LogMessage("\nProcessing: {}\nSeason: {}\nFilename: {}\nWith URL: {}".format(league_id, season_name, filename, SPORTSDB_API))
		event_id, event_title, event_date, order_number = get_event_id(league_id, season_name, filename, SPORTSDB_API)

		# endregion

		# region UPDATE	mediaList

		season_number = season_name.replace("-", "")  # replace the "-" with ""
		event_year = event_date.split("-")[0]
		event_date = event_date.replace("-", "")

		# If order_number is over 2 digits, then remove all but the last 2 (plex only allows 10 digit episode numbers)
		if len(str(order_number)) > 2:
			order_number = int(str(order_number)[-2:])

		# Add order_number to event_date with a buffer of 2 digits
		event_date = event_date + str(order_number).zfill(2)
		
		LogMessage("►► LEAGUE / SHOW NAME: {}".format(league_name))
		LogMessage("►► LEAGUE ID {}".format(league_id))
		LogMessage("►► SEASON: {}".format(season_number))
		LogMessage("►► EVENT TITLE: {}".format(event_title))
		LogMessage("►► EVENT ID: {}".format(event_id))
		LogMessage("►► EVENT DATE: {}".format(event_date))
		LogMessage("►► EVENT YEAR: {}".format(event_year))

		# Create Media.Episode object for Plex
		media = Media.Episode(
			league_name.encode("utf-8"),     # Show Name / League Name
			season_number.encode("utf-8"),   # Season Number
			str(event_date).encode("utf-8"),   # Episode Number (Event ID)
			event_title.encode("utf-8"),     # Episode Title (Event Name)
			str(event_year).encode("utf-8"), # Episode Year
)
		
		media.parts.append(file) # Append the file path
		mediaList.append(media)

		LogMessage("►► Processed 'media' {}\n".format(media))

		# endregion

	LogMessage("►► FINISHED SCAN\n")