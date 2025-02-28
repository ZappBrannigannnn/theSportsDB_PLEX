# IMPORTS ########################################################################################
# region

import re
import urllib2
import json
import time
import inspect
import codecs
from dateutil import parser
from functools import reduce
from difflib import SequenceMatcher

# endregion

# LOGGING ########################################################################################
# region

def LogMessage(dbgline):
	timestamp = time.strftime("\n%H:%M:%S - ")

	try:
		Log.Debug("{}{}".format(timestamp, dbgline))  # Correct Plex logging
	except NameError:
		print("\n❌ Log object is not available. Running in a non-Plex environment.")

# endregion

# LEAGUE LEVEL AND TEAM IMAGE STUFF ##############################################################
# region

# get_league_info FROM API #######################################################################
# region

def get_league_info(league_id, SPORTSDB_API):
	league_info_url = "{}/lookupleague.php?id={}".format(SPORTSDB_API, league_id)

	try:
		response = urllib2.urlopen(league_info_url, timeout=10)
		data = json.load(response)

		if "leagues" in data and data["leagues"]:
			league_metadata = data["leagues"][0]  # First (and only) league entry

			LogMessage("\n✅ Retrieved league metadata for: {}".format(league_id))
			return league_metadata  # Return the dictionary with metadata

		else:
			LogMessage("\n❌ No metadata found for league ID: {}".format(league_id))
			return None

	except urllib2.URLError as e:
		LogMessage("\n⚠ API Request Error: {}".format(e))
		return None

# endregion

# get_team_images FROM API #######################################################################
# region

def get_team_images(league_id, SPORTSDB_API):
	team_images_url = "{}/lookup_all_teams.php?id={}".format(SPORTSDB_API, league_id)

	try:
		response = urllib2.urlopen(team_images_url, timeout=10)
		data = json.load(response)

		if "teams" in data and data["teams"]:
			team_images = data["teams"]
			LogMessage("\n✅ Retrieved team images for: {}".format(league_id))
			return team_images  # Return the dictionary with metadata

		else:
			LogMessage("\n❌ No team images found for league ID: {}".format(league_id))
			return None

	except urllib2.URLError as e:
		LogMessage("\n⚠ API Request Error: {}".format(e))
		return None
	
# endregion

# endregion
# LEAGUE LEVEL AND TEAM IMAGE STUFF ##############################################################


"""
# get_seaon_metadata FROM API (WAITING FOR SPORTSDB REPLY) #######################################
# region

def get_season_metadata(league_id, season_id, API_KEY):
	LogMessage("\n🔍 Fetching season metadata for League ID: {} and Season ID: {}".format(league_id, season_id))

	API_BASE_URL_V2 = "https://www.thesportsdb.com/api/v2/json/"  # Ensure this is correct

	season_posters_url = "{}list/seasonposters/{}".format(API_BASE_URL_V2, league_id)
	season_stuff_url = "{}list/seasons/{}".format(API_BASE_URL_V2, league_id)

	LogMessage("\n🗨️ Season Posters API URL: {}".format(season_posters_url))
	LogMessage("\n🗨️ Season Stuff API URL: {}".format(season_stuff_url))

	headers = {
		"X-API-KEY": "{}".format(API_KEY),  # Corrected header format for Python 2
		"Content-Type": "application/json"
	}

	# Function to make an API request using urllib2
	def make_request(url):
		try:
			request = urllib2.Request(url)  # Create request object
			for key, value in headers.items():
				request.add_header(key, value)  # Add headers manually

			response = urllib2.urlopen(request, timeout=10)  # Send request
			data = json.load(response)  # Parse JSON response

			LogMessage("DATA RESULTS: {}".format(data))
			return data
		except urllib2.HTTPError as e:
			LogMessage("\n⚠ HTTP Error: {} - {}".format(e.code, e.reason))
			return None
		except urllib2.URLError as e:
			LogMessage("\n⚠ URL Error: {}".format(e.reason))
			return None
		except Exception as e:
			LogMessage("\n⚠ Unexpected Error: {}".format(str(e)))
			return None

	# Fetch season posters
	data1 = make_request(season_posters_url)

	# Fetch season stuff
	data2 = make_request(season_stuff_url)

	return {"season_posters": data1, "season_stuff": data2}

# endregion
"""


# GET EVENT ID STUFF #############################################################################
# region

# (1) Get DATE from filename
# region

def extract_date_from_filename(filename):
	# Match common date formats
	date_patterns = [
		r"(\d{4}-\d{2}-\d{2})",            # YYYY-MM-DD
		r"(\d{4}/\d{2}/\d{2})",            # YYYY/MM/DD
		r"(\d{4}\.\d{2}\.\d{2})",          # YYYY.MM.DD
		r"(\d{4}_\d{2}_\d{2})",            # YYYY_MM_DD

		r"(\d{2}-\d{2}-\d{4})",            # MM-DD-YYYY or DD-MM-YYYY
		r"(\d{2}/\d{2}/\d{4})",            # MM/DD/YYYY or DD/MM/YYYY
		r"(\d{2}\.\d{2}\.\d{4})",          # MM.DD.YYYY or DD.MM.YYYY
		r"(\d{2}_\d{2}_\d{4})",            # MM_DD_YYYY or DD_MM_YYYY

		r"(\d{2}-\d{4}-\d{2})",            # DD-YYYY-MM
		r"(\d{2}/\d{4}/\d{2})",            # DD/YYYY/MM
		r"(\d{2}\.\d{4}\.\d{2})",          # DD.YYYY.MM
		r"(\d{2}_\d{4}_\d{2})",            # DD_YYYY_MM

		r"(\d{4}-\d{2}-\d{2})",            # YYYY-DD-MM
		r"(\d{4}/\d{2}/\d{2})",            # YYYY/DD/MM
		r"(\d{4}\.\d{2}\.\d{2})",          # YYYY.DD.MM
		r"(\d{4}_\d{2}_\d{2})",            # YYYY_DD_MM

		r"(\d{8})",                        # YYYYMMDD
		r"(\d{6})",                        # YYMMDD

		r"(\d{4} \d{2} \d{2})",            # YYYY MM DD (spaces)
		r"(\d{2} \d{2} \d{4})",            # MM DD YYYY or DD MM YYYY (spaces)

		r"(\d{2}-\d{2}-\d{2})",            # MM-DD-YY or DD-MM-YY
		r"(\d{2}/\d{2}/\d{2})",            # MM/DD/YY or DD/MM/YY
		r"(\d{2}\.\d{2}\.\d{2})",          # MM.DD.YY or DD.MM.YY
		r"(\d{2}_\d{2}_\d{2})",            # MM_DD_YY or DD_MM_YY

		r"(\d{4}-[A-Za-z]{3}-\d{2})",      # YYYY-MMM-DD
		r"([A-Za-z]{3}[- ]\d{1,2}[- ]\d{4})",  # MMM-DD-YYYY
		r"(\d{1,2}[- ]?[A-Za-z]{3}[- ]?\d{4})",  # DD-MMM-YYYY
		r"([A-Za-z]{3,9} \d{1,2}, \d{4})", # Month DD, YYYY
		r"(\d{4}\d{2}\d{2}_\d{6})",        # YYYYMMDD_HHMMSS
	]

	for pattern in date_patterns:
		match = re.search(pattern, filename)
		if match:
			date_str = match.group(1)
			try:
				parsed_date = parser.parse(date_str, dayfirst=False)
				return parsed_date.strftime("%Y-%m-%d")
			except ValueError:
				continue

# endregion

# (2) Get ROUND from filename
# region
def extract_round_from_filename(filename):
	patterns = [
		r"Round (\d+)",     # Round 12
		r"Round-(\d+)",     # Round-12
		r"Round_(\d+)",     # Round_12
		r"Round\.(\d+)",    # Round.12
		r"Round(\d+)",      # Round12

		r"R (\d+)",     # R 12
		r"R-(\d+)",     # R-12
		r"R_(\d+)",     # R_12
		r"R\.(\d+)",    # R.12
		r"R(\d+)",      # R12

		r"Matchweek (\d+)",     # Matchweek 5
		r"Matchweek-(\d+)",     # Matchweek-5
		r"Matchweek_(\d+)",     # Matchweek_5
		r"Matchweek\.(\d+)",    # Matchweek.5
		r"Matchweek(\d+)",      # Matchweek5

		r"Match Week (\d+)",    # Match Week 7
		r"Match-Week-(\d+)",    # Match-Week-7
		r"Match_Week_(\d+)",    # Match_Week_7
		r"Match\.Week\.(\d+)",  # Match.Week.7

		r"MW (\d+)",    # MW 10
		r"MW-(\d+)",    # MW-10
		r"MW_(\d+)",    # MW_10
		r"MW\.(\d+)",   # MW.10
		r"MW(\d+)",     # MW10

		r"Week (\d+)",  # Week 3
		r"Week-(\d+)",  # Week-3
		r"Week_(\d+)",  # Week_3
		r"Week\.(\d+)", # Week.3
		r"Week(\d+)",   # Week3

		r"Gameweek (\d+)",  # Gameweek 9
		r"Gameweek-(\d+)",  # Gameweek-9
		r"Gameweek_(\d+)",  # Gameweek_9
		r"Gameweek\.(\d+)", # Gameweek.9
		r"Gameweek(\d+)", # Gameweek9

		r"GW (\d+)",  # GW 4
		r"GW-(\d+)",  # GW-4
		r"GW_(\d+)",  # GW_4
		r"GW\.(\d+)", # GW.4
		r"GW(\d+)",   # GW4
	]    
	
	for pattern in patterns:
		match = re.search(pattern, filename, re.IGNORECASE)
		if match:
			return int(match.group(1))  # ✅ Correctly returns the first valid match

	return None  # ✅ Returns None if no pattern matches

	# endregion

# (3) Get LEAGUE's events on the specific DATE
# region

def get_events_on_date(formatted_date, league_id, SPORTSDB_API):
	events_on_date_url = "{}/eventsday.php?d={}&l={}".format(SPORTSDB_API, formatted_date, league_id)

	try:
		response = urllib2.urlopen(events_on_date_url, timeout=10)
		event_date_round_data = json.load(response)

		if "events" in event_date_round_data and event_date_round_data["events"]:
			#LogMessage("\n✅ Retrieved events on date: {} for: {}".format(formatted_date, league_id))
			return event_date_round_data["events"]  # Uses 'event_date_round_data' instead of 'data'

		else:
			LogMessage("\n❌ No events found for date: {}".format(formatted_date))
			return None

	except urllib2.URLError as e:
		LogMessage("\n⚠ API Request Error: {}".format(e))
		return None

# endregion

# (3) Get LEAGUE's events in a specific ROUND
# region

def get_events_in_round(round_number, league_id, SPORTSDB_API, season_number):
	# if the season number is 8 characters (########) split with hyphen (####-####)

	LogMessage("\n🔎🔎🔎🔎 Getting events in round: {} for: {} season: {}".format(round_number, league_id, season_number))

	if len(str(season_number)) == 8:
		season_number = season_number[:4] + "-" + season_number[4:]

	events_in_round_url = "{}/eventsround.php?id={}&r={}&s={}".format(SPORTSDB_API, league_id, round_number, season_number)

	try:
		response = urllib2.urlopen(events_in_round_url, timeout=10)
		event_date_round_data = json.load(response) 

		if "events" in event_date_round_data and event_date_round_data["events"]:
			#LogMessage("\n✅ Retrieved events in round {} For: {} season: {}".format(round_number, league_id, season_number))
			return event_date_round_data["events"]

		else:
			LogMessage("\n❌ No events found for round: {}".format(round_number))
			return None

	except urllib2.URLError as e:
		LogMessage("\n⚠ API Request Error: {}".format(e))
		return None

# endregion

# (4) FIND MATCHING EVENT
# region

# clean_text HELPER FUNCTION
# region (4) FIND MATCHING EVENT

# region (4.1) clean_text HELPER FUNCTION

def clean_text(text):
	# Convert text to lowercase, remove punctuation, and split into words
	if not text:
		return []  # Return empty list for missing values
	text = text.lower().replace("_", " ")  # Normalize underscores
	words = re.split(r"\W+", text)  # Split on non-word characters
	return [w for w in words if w]  # Remove empty strings and return a list

# endregion

# region (4.2) compute_match_score HELPER FUNCTION

# region (4.2.1) remove_stop_phrases from matching HELPER FUNCTION
def remove_stop_phrases(filename_words, stop_phrases): # Remove multi-word stop phrases from a list of words.

	i = 0
	while i < len(filename_words) - 1:  # Stop before the last word to avoid index errors
		for phrase in stop_phrases:
			# Check if the current and next words match the stop phrase
			if filename_words[i:i + len(phrase)] == list(phrase):
				# Remove the stop phrase
				filename_words[i:i + len(phrase)] = []
				i = i - 1  # Use standard subtraction instead of -=
				break
		i = i + 1  # Use standard addition instead of +=
	
	return filename_words


# endregion

def compute_match_score(filename_words, event_words):

	# Combinations of adjecant words or single words to be removed from matching
	stop_phrases = [
			("formula", "1"),  # League names with numbers can mess things up.
			("vs",),           # Single-word stop phrase
			("and",),       
			("the",),
			("fc",)   
		]

	# Convert sets to lists for ordered processing
	filename_words = list(filename_words)  # Convert set to list
	event_words = list(event_words)        # Convert set to list

	# Remove stop phrases from filename_words
	filename_words = remove_stop_phrases(filename_words, stop_phrases)
	# Remove stop phrases from event_words
	event_words = remove_stop_phrases(event_words, stop_phrases)

	# Convert back to sets for intersection
	filename_words = set(filename_words)
	event_words = set(event_words)

	# Compute match score based on hybrid matching logic
	common_words = set()
	for event_word in event_words:
		if len(event_word) < 3:  # Handle short words (1 or 2 characters)
			if event_word in filename_words:  # Exact match only
				common_words.add(event_word)
		else:  # Handle longer words (3 or more characters)
			for filename_word in filename_words:
				if event_word in filename_word:  # Substring match
					common_words.add(filename_word)

	return len(common_words), common_words, filename_words  # Score is the count of matching words
# endregion

# region (4.3) find_matching_event FUNCTION

def find_matching_event(filename, event_date_round_data):
	
	filename_words = clean_text(filename)
	LogMessage("📂 Extracted words from filename: {}".format(filename_words))

	# Initialize best_match and best_score
	best_matches = []  # Store all matches with the best score
	best_score = 0

	for event in event_date_round_data:
		event_name = event.get("strEvent", "")
		event_id = event.get("idEvent", "Unknown ID")
		event_text = "{} {} {}".format(event.get("strEvent", ""), event.get("strHomeTeam", ""), event.get("strAwayTeam", ""))
		event_words = clean_text(event_text)

		# Compute match score (higher = better match)
		match_score, common_words, filename_words = compute_match_score(filename_words, event_words)

		# NEVER DELETE THESE LOGS (JUST COMMENT THEM OUT!!!!)
		LogMessage("\nEvent ID: {}".format(event_id))
		LogMessage("Filename words: {}".format(filename_words))
		LogMessage("🆚 Event words: {}".format(event_words))
		LogMessage("  Common words: {}".format(common_words))
		LogMessage("➡ Match Score: {}".format(match_score))
		LogMessage("Event Name: {}\n".format(event_name))
		# NEVER DELETE THESE LOGS (JUST COMMENT THEM OUT!!!!)

		if match_score > best_score:
			best_score = match_score

			best_matches = [{"event": event, "extra_words": len(event_words) - len(common_words)}]  # Reset best_matches
		elif match_score == best_score:
			# Calculate extra words for this event
			extra_words = len(event_words) - len(common_words)
			best_matches.append({"event": event, "extra_words": extra_words})  # Add to best_matches if tied

	# Handle ties
	if len(best_matches) > 1:
		LogMessage("📢 Multiple events with the same match score. Applying tiebreaker...")
		# Select the event with the fewest extra words
		best_match = min(best_matches, key=lambda x: x["extra_words"])["event"]
	else:
		best_match = best_matches[0]["event"] if best_matches else None

	if best_match:
		event_id = best_match.get("idEvent")
		event_title = best_match.get("strEvent")
		event_date = best_match.get("dateEvent")

		LogMessage("✅ Matched filename: {}".format(filename))
		LogMessage("✅ With event {}".format(event_title))
		LogMessage("✅ Event_id: {}".format(event_id))
		LogMessage("✅ Match score: {}".format(best_score))
		return event_id
	else:
		LogMessage("❌ No match found (unexpected case)")
		return None

# endregion

# get_event_id function START
# region

def get_event_id(season_number, episode_number, episode_path, league_id, SPORTSDB_API):
	# Initialize event_id
	event_id = None

	# endregion

	# (1) Get DATE from filename
	# region

	filename = os.path.basename(episode_path)
	formatted_date = extract_date_from_filename(filename)
	# LogMessage("\n🗨️ FORMATTED DATE: {} For Episode: {}".format(formatted_date, episode_path))

	# endregion

	# (2) Get ROUND if no DATE from filename
	# region

	if formatted_date is None:
		round_number = extract_round_from_filename(filename)
		# LogMessage("\n🗨️ ROUND NUMBER: {}".format(round_number))

		if round_number is None:
			LogMessage("\n⚠️ No date or round found in filename: {}".format(filename))
			return None

			# endregion

		# (3) Get EVENTS in ROUND or DATE
		# region

		else:
			event_date_round_data = get_events_in_round(round_number, league_id, SPORTSDB_API, season_number)
	else:
		event_date_round_data = get_events_on_date(formatted_date, league_id, SPORTSDB_API)
	
	# If no event data
	if event_date_round_data is None:
		LogMessage("\n❌ No events found for date: {}".format(formatted_date))
		return None

		# endregion

	# (4) Get event ID by matching the filename against the event_date_round_data
	# region

	event_id = find_matching_event(filename, event_date_round_data)

	if event_id is None:
		LogMessage("\n❌ No matching events found for filename: {}".format(filename))
		return None
	else:
		return event_id

	# endregion

# endregion
# GET EVENT ID STUFF #############################################################################

# endregion

# get_event_info FROM API ########################################################################
# region

def get_event_info(SPORTSDB_API, event_id):
	
	event_info_url = "{}/lookupevent.php?id={}".format(SPORTSDB_API, event_id)
	#LogMessage("\n🔍 Requesting from URL: {}".format(event_info_url))

	try:
		response = urllib2.urlopen(event_info_url, timeout=10)
		data = json.load(response)  # JSON automatically loads as Unicode in Python 2.7

		if "events" in data and data["events"]:
			event_metadata = data["events"][0]  # First (and only) event entry

			# 🚀 Convert all keys to standard strings (to avoid Unicode issues)
			if isinstance(event_metadata, dict):
				event_metadata = {str(k): str(v) if isinstance(v, unicode) else v for k, v in event_metadata.items()}

			return event_metadata  # Return the corrected dictionary

		else:
			LogMessage("\n❌ No metadata found for event ID: {}".format(event_id))
			return None

	except urllib2.URLError as e:
		LogMessage("\n⚠ API Request Error: {}".format(e))
		return None

# endregion