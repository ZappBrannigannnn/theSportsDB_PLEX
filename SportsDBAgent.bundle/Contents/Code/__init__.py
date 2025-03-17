# region IMPORTS

import time, os, datetime
import requests
import sys
import json
import io
from api_client import get_league_info
from api_client import get_team_images
from api_client import get_season_posters
from api_client import get_event_id
from api_client import get_event_info
import png

# endregion

# region GLOBAL VARIABLES 

API_KEY = ""  # API Key will be set at startup
API_BASE_URL = "https://www.thesportsdb.com/api/v1/json/"
SPORTSDB_API = ""

BASE_DIR = ""
if os.name == 'nt':  # Windows
	BASE_DIR = os.getenv('LOCALAPPDATA')
else:  # Linux/Debian
	BASE_DIR = "/var/lib/plexmediaserver/Library/Application Support"

PLEX_PLUGIN_DATA_DIR = ""
PLEX_PLUGIN_DATA_DIR = os.path.join(
	BASE_DIR,
	'Plex Media Server',
	'Plug-in Support',
	'Data',
	'com.plexapp.agents.SportsDBAgent',
	'DataItems'
)
if not os.path.exists(PLEX_PLUGIN_DATA_DIR):
	os.makedirs(PLEX_PLUGIN_DATA_DIR)

# endregion

# region LOGGING 

def LogMessage(dbgline):
	# Wrapper function to log messages using Plex's Log object.bool
	timestamp = time.strftime("%H:%M:%S - ")
	
	try:
		Log.Debug("{}{}".format(timestamp, dbgline))  # Correct Plex logging
	except NameError:
		print("⚠ Log object is not available. Running in a non-Plex environment.")

# endregion

# region APIKEY_get FUNCTION 

def APIKEY_get():
	# Retrieve API Key and store it globally.
	global API_KEY
	global API_BASE_URL
	global SPORTSDB_API

	API_KEY = Prefs['theSportsDBAPIKey']
	if not API_KEY:
		LogMessage("❌ No theSportsDB API key provided.")
		return None  # Stop if no key

	# Construct the API URL
	SPORTSDB_API = str("{}{}".format(API_BASE_URL, API_KEY))

# endregion

# region START FUNCTION 

def Start():
	# Required function for Plex plugins to initialize the agent.
	LogMessage("\n\n")
	LogMessage("🔥 START FUNCTION TRIGGERED.")

	APIKEY_get()  # Call APIKEY_get function\

# endregion

# region SportsScannerAgent CLASS START 

class SportsDBAgent(Agent.TV_Shows):
	name = 'SportsDBAgent'
	languages = ['en']
	primary_provider = True
	fallback_provider = ['com.plexapp.agents.localmedia']
	accepts_from = ['com.plexapp.agents.localmedia']
	cached_leagues = {}  # Cache to store league details to avoid repeated API calls.

# endregion

	# SEARCH FUNCTION

	# region seach start
	def search(self, results, media, lang, manual, **kwargs):
		LogMessage("\n\n")
		LogMessage("🔥 SEARCH FUNCTION TRIGGERED")
	# endregion

		# region SEARCH STEP 1: Fetch the league ID from the JSON file
		
		# region Define the path to the league map JSON file
		league_map_path = os.path.join(PLEX_PLUGIN_DATA_DIR, "SportsDB_League_Map.json")
		"""LogMessage("League map path: {}".format(league_map_path))"""
		# endregion

		# region OPEN THE LEAGUE DATA FILE AND CHECK IF THE LEAGUE EXISTS
		try:
			with io.open(league_map_path, "r") as f:
				league_data = json.load(f)
				leagues = league_data.get("leagues", [])
		except Exception as e:
			LogMessage("❌ Error reading JSON file: {}".format(str(e)))
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
					"""LogMessage("✅ League '{}' ID: {} found in the JSON file.".format(show_title, league_id))"""
					break
			else:
				LogMessage("❌ League '{}' not found in the JSON file.".format(show_title))
				return
		else:
			LogMessage("❌ Show title is missing. Skipping league ID lookup.")
			return

		# endregion

		# endregion

		# region SEARCH STEP 2: Get league metadata info

		# Get all the league metadata
		league_metadata = get_league_info(league_id, SPORTSDB_API)

		if league_metadata == None:
			LogMessage("❌ No metadata found for league ID (1): {}".format(league_id))
			LogMessage("STOPPING")
			return  # Stop execution early if no metadata from API 

		# endregion

		# region SEARCH STEP 3: Update "Results"

		league_identifier = "{}".format(league_id) # Store the league ID in metadata.id
		league_year = league_metadata["intFormedYear"] # Get the year from the metadata
		league_thumb = league_metadata["strPoster"] # Get the the thumb from the metadata

		# Add to the SHOW result
		results.Append(MetadataSearchResult(
			id=league_identifier,
			name=show_title,
			year=league_year,
			lang=lang,
			thumb=league_thumb,
			score=100  # Full confidence match
		))

		# endregion

	# UPDATE FUNCTION / LEAGUE METADATA / EPISODE EVERYTHING 

	# region (1) call_get_league_info (CALLED BY UPDATE)
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
			"""LogMessage("✅ Retrieved fanart / background images for league: {}".format(league_id))"""
			metadata.art[fanart_url] = Proxy.Preview(HTTP.Request(fanart_url, sleep=0.5).content, sort_order=1)

	# endregion

	# region (2) call_get_team_images (CALLED BY UPDATE)
	def call_get_team_images(self, metadata, league_id):
		team_images = get_team_images(league_id, SPORTSDB_API)  # This is a LIST

		if not team_images:
			LogMessage("❌ No team images found for League ID: {}.Stopping.".format(league_id))
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

	# region (3) Fetch All Season Posters for league
	def call_get_season_posters(self, metadata, media, league_id, season_number):
		"""LogMessage("🔍 Fetching season posters for League ID: {} | Season: {}".format(league_id, season_number_split))"""

		# Get season posters from API (Returns dictionary {season_number: poster_url})
		season_posters = get_season_posters(league_id, SPORTSDB_API)

		if not season_posters:
			LogMessage("❌ Something went wrong getting season posters for League ID: {}".format(league_id))
			return  # Stop if no valid posters are available
		else:
			return season_posters

		# DELETE ### Debugging
		"""LogMessage("✅ Found season posters for League ID: {}:\n{}".format(league_id, season_posters))"""

	# endregion

	# region (3) Fetch & Apply Season Poster
	def apply_season_poster(self, metadata, media, league_id, season_number, season_posters):

		# Convert season number if it's 8 characters long (e.g., 20242025 -> 2024-2025)
		if len(str(season_number)) == 8:
			season_number_split = season_number[:4] + "-" + season_number[4:]
		else:
			season_number_split = str(season_number)  # Keep it unchanged for regular seasons

		# Find the correct season poster using the formatted season number
		"""LogMessage("🔍 season_posters {}...".format(season_posters))"""
		this_season_poster = season_posters.get(season_number_split)  # Use the proper season number

		if not this_season_poster:
			LogMessage("❌ No valid poster found for Season {}.".format(season_number))
			return  # Stop if no poster found

		# Ensure the season metadata exists before applying the poster
		if season_number in metadata.seasons:
			metadata.seasons[season_number].posters[this_season_poster] = Proxy.Preview(
				HTTP.Request(this_season_poster, sleep=0.5).content, sort_order=1
			)
		else:
			LogMessage("⚠️ Season {} metadata not found, cannot apply poster.".format(season_number))

		# endregion

	# region (5) Get the event id
	def call_get_event_id(self, season_number, episode_number, episode_path, league_id):

		league_name = os.path.basename(os.path.dirname(os.path.dirname(episode_path)))

		event_id = get_event_id(league_name, season_number, episode_number, episode_path, league_id, SPORTSDB_API)
		
		return event_id
	# endregion

	# region (6) Get event metadata
	def call_get_event_metadata(self, event_id):
		
		event_metadata = get_event_info(SPORTSDB_API, event_id)

		return event_metadata
	# endregion

	# region (7.1) Create Custom Event Images

	# region (7.1.1) Download Image
	def download_image(self, url, custom_image_path):
		try:
			response = requests.get(url, stream=True)
			if response.status_code == 200:
				with io.open(custom_image_path, "wb") as file:
					for chunk in response.iter_content(1024):
						file.write(chunk)
				return custom_image_path
			else:
				LogMessage("❌ Failed to download image: {}".format(url))
				return None
		except Exception as e:
			LogMessage("❌ Error downloading image: {}".format(e))
			return None
	# endregion

	# region (7.1.2) Resize Image
	def resize_image(self, image_pixels, orig_w, orig_h, new_w, new_h):
		resized_pixels = []

		for y in range(new_h):
			# Find corresponding source row in original image
			src_y = int(y * orig_h / new_h)
			src_row = image_pixels[src_y]  # Get the closest original row

			# Scale row horizontally
			new_row = []
			for x in range(new_w):
				src_x = int(x * orig_w / new_w)  # Find closest x position
				new_row.extend(src_row[src_x * 4:src_x * 4 + 4])  # Copy RGBA pixels

			resized_pixels.append(tuple(new_row))  # Convert list to tuple for PurePNG

		return resized_pixels # home_team_pixels / away_team_pixels replaced

	# endregion

	# region (7.1.3) Paste Image to base image
	def paste_image(self, base_pixels, team_pixels, team_x, team_y):
		base_h = len(base_pixels)  # Base image height
		base_w = len(base_pixels[0]) // 4  # Base image width (RGBA = 4 channels per pixel)

		team_h = len(team_pixels)  # Team image height
		team_w = len(team_pixels[0]) // 4  # Team image width

		# Loop through the team image pixels
		for y in range(team_h):
			dest_y = team_y + y  # Calculate position on base image

			if dest_y < 0 or dest_y >= base_h:  # Ensure we are within base image bounds
				continue

			team_row = team_pixels[y]  # Get the current row of the team image
			base_row = list(base_pixels[dest_y])  # Copy the base image row to modify

			for x in range(team_w):
				dest_x = team_x + x  # Calculate position on base image

				if dest_x < 0 or dest_x >= base_w:  # Ensure we are within base image bounds
					continue

				# Get team pixel (RGBA)
				team_pixel = team_row[x * 4:x * 4 + 4]  # 4 channels (R,G,B,A)

				# If pixel is not fully transparent, paste it
				if team_pixel[3] > 0:  # Alpha channel > 0 means visible
					base_row[dest_x * 4:dest_x * 4 + 4] = team_pixel

			base_pixels[dest_y] = tuple(base_row)  # Convert back to tuple and save

		return base_pixels  # Return updated image

	# endregion

	# region (7.1.4) Create and write to thumbnail json file
	def write_event_thumbnail_json(self, episode_filename):
		# Define the path to the JSON file
		thumbnail_json_path = os.path.join(PLEX_PLUGIN_DATA_DIR, "Event_Thumbnail_Map.json")

		# Ensure the file exists
		if not os.path.exists(thumbnail_json_path):
			with io.open(thumbnail_json_path, "w", encoding="utf-8") as f:
				json.dump({}, f, ensure_ascii=False)

		# Load the existing JSON data safely
		try:
			with io.open(thumbnail_json_path, "r", encoding="utf-8") as f:
				try:
					data = json.load(f)
				except ValueError:  # Python 2 JSONDecodeError is ValueError
					data = {}  # If file is empty or corrupted, reset it
		except IOError:
			data = {}  # If file does not exist or cannot be read

		# Convert `episode_filename` to Unicode (Python 2 safety)
		if isinstance(episode_filename, str):
			episode_filename = unicode(episode_filename, "utf-8")

		# Remove file extension and use as a dictionary key
		episode_key = os.path.splitext(episode_filename)[0]
		data[episode_key] = "exists"

		# Convert `json.dumps()` output to Unicode before writing
		try:
			with io.open(thumbnail_json_path, "w", encoding="utf-8") as f:
				json_string = json.dumps(data, ensure_ascii=False, indent=4)

				# **Fix: Convert to Unicode before writing**
				if isinstance(json_string, str):
					json_string = unicode(json_string, "utf-8")

				f.write(json_string)  # ✅ Now it's Unicode

			"""LogMessage("✅ Updated JSON file with episode: {}".format(episode_filename))"""
		except Exception as e:
			LogMessage("❌ Error updating JSON file: {}".format(str(e)))

	# endregion		

	# region (7.1) Create Custom Event Images
	def create_episode_thumb(self, episode_filename, event_metadata, metadata, episode_path, custom_image_path):

		# region Collect team Images to use for custom event thumb
		home_team_name = event_metadata.get('strHomeTeam')
		away_team_name = event_metadata.get('strAwayTeam')

		# ignore trailing spaces
		home_team_name = home_team_name.strip()
		away_team_name = away_team_name.strip()

		# Get team images from metadata roles by looking for team names
		home_team_thumb = None
		away_team_thumb = None

		for role in metadata.roles:
			role_name = getattr(role, 'name', '')  # Get the role's name safely
			role_photo = getattr(role, 'photo', None)  # Get the role's photo safely

			if role_name and home_team_name in role_name:
				home_team_thumb = role_photo
				"""LogMessage("✅ Found home team image: {}".format(home_team_thumb, custom_image_path))"""

			if role_name and away_team_name in role_name:
				away_team_thumb = role_photo
				"""LogMessage("✅ Found away team image: {}".format(away_team_thumb, custom_image_path))"""
			
		# endregion

		# region Download Badges
		temp_dir = os.path.join(
			BASE_DIR,
			'Plex Media Server',
			'Plug-in Support',
			'Data',
			'com.plexapp.agents.sportsdbagent',
			'EventImages',
			'temp'
		)
		if not os.path.exists(temp_dir):
			os.makedirs(temp_dir)

		if home_team_thumb and home_team_thumb.startswith("http"):
			temp_home_path = os.path.join(temp_dir, "home_team.png")
			home_team_thumb = self.download_image(home_team_thumb, temp_home_path)

		if away_team_thumb and away_team_thumb.startswith("http"):
			temp_away_path = os.path.join(temp_dir, "away_team.png")
			away_team_thumb = self.download_image(away_team_thumb, temp_away_path)

		# endregion

		# region Get base image
		base_img_path = os.path.join(
			BASE_DIR,
			'Plex Media Server',
			'Plug-ins',
			'SportsDBAgent.bundle',
			'Contents',
			'Resources',
			'base_event_img.png'
		)

		try:
			# Check if base image exists
			if not os.path.exists(base_img_path):
				LogMessage("❌ Base event image is missing: {}".format(base_img_path))
				return None
			# endregion

			# region Define logo sizes and y-position (FOR EASY EDITING) ######################################
			logo_width = 1200 
			logo_height = 1200
			y_position = 1150 - (logo_height // 2) # 304 from "Reference locations from base image" ^^^
			# endregion

			# region Read and Resize base image
			base_reader = png.Reader(filename=base_img_path)
			base_w, base_h, base_pixels, base_info = base_reader.asRGBA()
			base_pixels = list(base_pixels)  # Convert `imap` to a list
			# endregion

			# region Read, Resize and Add home team image
			if home_team_thumb and os.path.exists(home_team_thumb):
				home_reader = png.Reader(filename=home_team_thumb)
				home_w, home_h, home_team_pixels, _ = home_reader.asRGBA()

				home_team_pixels = list(home_team_pixels)  # Convert `imap` to a list
				home_team_pixels = self.resize_image(home_team_pixels, home_w, home_h, logo_width, logo_height)

				# Adjust position to center
				home_x = 837 - (logo_width // 2)  # 279 from "Reference locations from base image" ^^^

				# Overlay home logo
				base_pixels = self.paste_image(base_pixels, home_team_pixels, home_x, y_position)
			# endregion

			# region Read, Resize and Add away team image
			if away_team_thumb and os.path.exists(away_team_thumb):
				away_reader = png.Reader(filename=away_team_thumb)
				away_w, away_h, away_team_pixels, _ = away_reader.asRGBA()

				away_team_pixels = list(away_team_pixels)  # Convert `imap` to a list
				away_team_pixels = self.resize_image(away_team_pixels, away_w, away_h, logo_width, logo_height)

				# Adjust position to center
				away_x = 3003 - (logo_width // 2) # 1001 from "Reference locations from base image" ^^^

				# Overlay away logo
				base_pixels = self.paste_image(base_pixels, away_team_pixels, away_x, y_position)
			# endregion

			# region Save final image
			with io.open(custom_image_path, "wb") as f:
				writer = png.Writer(width=base_w, height=base_h, alpha=True)
				writer.write(f, base_pixels)

			"""LogMessage("✅ Match image saved to: {}".format(custom_image_path))"""

			## (7.1.4) Create and add to thumbnail json (used to determine when to delete custom thumbnails)
			self.write_event_thumbnail_json(episode_filename)

		except Exception as e:
			LogMessage("❌ Error creating episode thumbnail: {}".format(e))
			return None

			# endregion

	# endregion

	# region (7) APPLY EPISODE METADATA
	def update_episode_metadata(self, metadata, media, event_metadata, episode, season_number, episode_number, episode_path):

		# region Pull specific metadatas from event_metadata
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
		# endregion

		# region Assign metadata
		episode.title = ("Round {} {}".format(round_num, eventtitle))
		episode.summary = my_summary

		# Handle date safely
		if date:
			try:
				episode.originally_available_at = datetime.datetime.strptime(date, "%Y-%m-%d").date()
			except ValueError:
				LogMessage("❌ ERROR: Invalid date format: {}".format(date))

		if fanart and fanart.startswith("http"):
			try:
				episode.art[fanart] = Proxy.Preview(HTTP.Request(fanart, sleep=0.5).content, sort_order=1)
			except Exception as e:
				LogMessage("❌ ERROR: Failed to assign fanart: {}".format(e))

		# Assign images correctly (validate URLs first)
		if thumb and thumb.startswith("http"):
			try:
				episode.thumbs[thumb] = Proxy.Preview(HTTP.Request(thumb, sleep=0.5).content, sort_order=1)
			except Exception as e:
				LogMessage("❌ ERROR: Failed to assign thumb: {}".format(e))
		# endregion
		
		# region If no thumb, create one
		if not thumb:
			LogMessage("❌ No thumb found for: {} - S{}E{}. Going to create one.".format(eventtitle, season_number, episode_number))

			# Get the filename from episode_path without the extension
			episode_filename = os.path.splitext(os.path.basename(episode_path))[0]

			# region Define the custom image path
			output_dir = os.path.join(
				BASE_DIR,
				'Plex Media Server',
				'Plug-in Support',
				'Data',
				'com.plexapp.agents.sportsdbagent',
				'EventImages',
			)
			if not os.path.exists(output_dir):
				os.makedirs(output_dir)
				
			# Define the final image path
			custom_image_path = os.path.join(output_dir, episode_filename + ".png")
			# endregion

			# Call the create_episide_thumb function
			self.create_episode_thumb(episode_filename,event_metadata, metadata, episode_path, custom_image_path)

			try:
				# Remove existing thumbnails explicitly
				for key in episode.thumbs.keys():
					del episode.thumbs[key]

				if os.path.exists(custom_image_path):
					with io.open(custom_image_path, "rb") as img_file:
						episode.thumbs[custom_image_path] = Proxy.Media(img_file.read())
					"""LogMessage("🖼️ Successfully applied custom backup image.")"""
				"""
				else:
					LogMessage("❌ ERROR: Custom image file not found: {}".format(custom_image_path))"""

			except Exception as e:
				LogMessage("❌ ERROR: Failed to assign custom backup image: {}".format(e))

		"""LogMessage("✅ Successfully updated metadata for: {} - S{}E{}".format(eventtitle, season_number, episode_number))"""
		# endregion
		
	# endregion

	# region (8) Clean up custom event images
	def cleanup_custom_event_images(self, media):
		"""LogMessage("🧹 Running cleanup for custom event images...")"""

		# region get the json file and check it
		# Define the path to the JSON file
		thumbnail_json_path = os.path.join(PLEX_PLUGIN_DATA_DIR, "Event_Thumbnail_Map.json")

		# Check if the JSON file exists
		if not os.path.exists(thumbnail_json_path):
			LogMessage("⚠️ No event thumbnail JSON file found. Skipping cleanup.")
			return  # No cleanup needed
		# endregion

		# region Get list of saved image names
		# Load the JSON data as event_thumbnail_map
		try:
			with io.open(thumbnail_json_path, "r", encoding="utf-8") as f:
				try:
					event_thumbnail_map = json.load(f)
				except ValueError as e:
					LogMessage("❌ Invalid JSON format. Resetting file.")
					event_thumbnail_map = {}  # Reset the dictionary
		except IOError as e:
			LogMessage("❌ Error reading JSON file: {}".format(str(e)))
			return
		
		# Save the list of recorded episode filenames (from JSON) to saved_images
		saved_images = set(event_thumbnail_map.keys())
		# endregion

		# region Get list of all current episode filenames currently in the Plex library as all_episodes
		all_episodes = set()

		# Loop through all seasons and episodes
		for season in media.seasons.values():
			for episode in season.episodes.values():
				if episode.items and episode.items[0].parts:
					episode_filename = os.path.splitext(os.path.basename(episode.items[0].parts[0].file))[0]
					all_episodes.add(episode_filename)
		# endregion

		# region Figure what images to delete and where they are
		images_to_delete = saved_images - all_episodes

		# Define the directory where images are stored
		event_images_dir = os.path.join(
			BASE_DIR,
			'Plex Media Server',
			'Plug-in Support',
			'Data',
			'com.plexapp.agents.sportsdbagent',
			'EventImages'
		)
		# endregion

		# region Delete images that are no longer needed
		for filename in images_to_delete:
			image_path = os.path.join(event_images_dir, filename + ".png")

			if os.path.exists(image_path):
				try:
					os.remove(image_path)
					"""LogMessage("🗑️ Deleted unused custom event image: {}".format(image_path))"""
				except Exception as e:
					LogMessage("❌ Error deleting image {}: {}".format(image_path, str(e)))
			else:
				LogMessage("⚠️ Image file not found, skipping: {}".format(image_path))

			# Remove entry from JSON file
			del event_thumbnail_map[filename]
		# endregion

		# region Save the updated JSON file
		try:
			with io.open(thumbnail_json_path, "w", encoding="utf-8") as f:
				json_string = json.dumps(event_thumbnail_map, ensure_ascii=False, indent=4)

				# Ensure the JSON string is Unicode before writing
				if isinstance(json_string, str):
					json_string = unicode(json_string, 'utf-8')

				# Write the JSON string to the file
				f.write(json_string)

			"""LogMessage("✅ Updated JSON file after cleanup.")"""
		except Exception as e:
			LogMessage("❌ Error updating JSON file: {}".format(str(e)))
		# endregion
		
		"""LogMessage("🧹 Cleanup complete!")"""

	# endregion

	# region UPDATE FUNCTION

	def update(self, metadata, media, lang, force):
		LogMessage("\n\n")
		LogMessage("🔥 UPDATE FUNCTION TRIGGERED for League ID: {}".format(metadata.id))

		# region UPDATE STEPS (1) & (2) FILL IN LEAGUE/SHOW METADATA (fanart & team images)

		# Assign league ID
		league_id = metadata.id

		# Check if the league already has an art (fanart/background)
		if not metadata.art:
			# UPDATE STEP (1): Get league metadata
			self.call_get_league_info(metadata, league_id)
		"""
		else:
			LogMessage("🖼️ League ID {} already has art applied: {}".format)"""
 
		# Check if the league's roles are already populated
		if not metadata.roles:
			# UPDATE STEP (2): Get team images
			self.call_get_team_images(metadata, league_id)
		"""
		else:
			LogMessage("👥 League ID {} already has roles applied. First role: {}".format(
				league_id, metadata.roles[0].name if metadata.roles[0] else "Unknown"))"""
		
		# endregion

		# region STEP (3) Get all season posters and apply to seasons
		season_posters = get_season_posters(league_id, SPORTSDB_API)

		for season_number in media.seasons:

			# Check if the season poster already exists
			if not metadata.seasons[season_number].posters:
				"""LogMessage("🖼️ Season {} is missing a poster. Fetching from season data grabbed already...".format(season_number))"""
				self.apply_season_poster(metadata, media, league_id, season_number, season_posters)
			"""
			else:
				LogMessage("🖼️ Season {} already has a poster.".format(season_number))"""

			# endregion

			# region STEP (4) ITERATE THROUGH EPISODES
			for episode_number in media.seasons[season_number].episodes:
				episode = metadata.seasons[season_number].episodes[episode_number]
				episode_media = media.seasons[season_number].episodes[episode_number]
					
				# Ensure episode media exists before accessing file path
				if not episode_media.items or not episode_media.items[0].parts:
					LogMessage("❌ ERROR: Missing media parts for S{}E{}, skipping.".format(season_number, episode_number))
					continue

				# Determine if individual scan (likely a refresh metadata)
				refresh_metadata = False
				number_of_episodes = len(media.seasons[season_number].episodes)
				if number_of_episodes == 1:
					if episode.thumbs:
						refresh_metadata = True

				# Check if episode has already been processed based on thumbs
				if episode.thumbs and not refresh_metadata:
					LogMessage("✅ Skipping existing episode S{}E{} (Thumbnail exists)".format(season_number, episode_number))
					continue

				# Extract episode's file path
				episode_path = episode_media.items[0].parts[0].file
				LogMessage("\n")
				LogMessage("🎬 Processing Episode: S{}E{}\n                                                                 🎬 Path: {}\n".format(season_number, episode_number, episode_path))

		# endregion

				# region STEP (5) GET THE EVENT ID

				event_id = self.call_get_event_id(season_number, episode_number, episode_path, league_id)

				# If no event ID is found
				if not event_id:
					LogMessage("❌ ERROR: No event ID found for S{}E{}, applying backup image and skipping.".format(season_number, episode_number))

					# Apply the backup event image
					thumb_url = "http://127.0.0.1:32400/:/plugins/com.plexapp.agents.sportsdbagent/resources/event_backup_img.jpg"

					try:
						# Remove existing thumbnails explicitly
						for key in episode.thumbs.keys():
							del episode.thumbs[key]

						# Now assign correctly via Plex HTTP request
						image_data = HTTP.Request(thumb_url, sleep=0.5).content
						episode.thumbs[thumb_url] = Proxy.Preview(image_data, sort_order=1)

					except Exception as e:
						LogMessage("❌ ERROR: Failed to assign backup image: {}".format(e))

					continue  # Skip this episode because no event ID

				# endregion

				# region STEP (6) FETCH EVENT METADATA

				event_metadata = self.call_get_event_metadata(event_id)

				if not event_metadata:
					LogMessage("❌ ERROR: No event metadata found for Event ID {}, skipping.".format(event_id))
					continue  # Skip this episode if no metadata
				
				"""LogMessage("✅ Applying Metadata for S{}E{} - Event: {}".format(season_number, episode_number, event_metadata.get("strEvent", "Unknown Event")))"""

				# endregion

				# region STEP (7) UPDATE EPISODE METADATA
				self.update_episode_metadata(metadata, media, event_metadata, episode, season_number, episode_number, episode_path)

				# endregion

		# STEP (8)🧹 Run cleanup after everything is updated
		self.cleanup_custom_event_images(media)

		LogMessage("\n")
		LogMessage("✅ UPDATE FUNCTION COMPLETED SUCCESSFULLY.\n")

		# endregion