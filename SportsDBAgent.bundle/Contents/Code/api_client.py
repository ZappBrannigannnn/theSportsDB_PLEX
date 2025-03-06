# region IMPORTS ########################################################################################
import re
import urllib2
import json
import time
import inspect
import codecs
from dateutil import parser
from functools import reduce
from difflib import SequenceMatcher
import io
# endregion

# region LOGGING ########################################################################################
def LogMessage(dbgline):
	timestamp = time.strftime("%H:%M:%S - ")

	try:
		Log.Debug("{}{}".format(timestamp, dbgline))  # Correct Plex logging
	except NameError:
		print("❌ Log object is not available. Running in a non-Plex environment.")
# endregion

# region LEAGUE LEVEL AND TEAM IMAGE STUFF ##############################################################

# region get_league_info FROM API #######################################################################
def get_league_info(league_id, SPORTSDB_API):
	league_info_url = "{}/lookupleague.php?id={}".format(SPORTSDB_API, league_id)

	try:
		response = urllib2.urlopen(league_info_url, timeout=10)
		data = json.load(response)

		if "leagues" in data and data["leagues"]:
			league_metadata = data["leagues"][0]  # First (and only) league entry

			LogMessage("✅ Retrieved league metadata for: {}".format(league_id))
			return league_metadata  # Return the dictionary with metadata

		else:
			LogMessage("❌ No metadata found for league ID: {}".format(league_id))
			return None

	except urllib2.URLError as e:
		LogMessage("⚠ API Request Error: {}".format(e))
		return None
# endregion

# region get_team_images FROM API #######################################################################
def get_team_images(league_id, SPORTSDB_API):
	team_images_url = "{}/lookup_all_teams.php?id={}".format(SPORTSDB_API, league_id)

	try:
		response = urllib2.urlopen(team_images_url, timeout=10)
		data = json.load(response)

		if "teams" in data and data["teams"]:
			team_images = data["teams"]
			LogMessage("✅ Retrieved team images for: {}".format(league_id))
			return team_images  # Return the dictionary with metadata

		else:
			LogMessage("❌ No team images found for league ID: {}".format(league_id))
			return None

	except urllib2.URLError as e:
		LogMessage("⚠ API Request Error: {}".format(e))
		return None
# endregion

# endregion

# region GET SEASON POSTER FROM API #####################################################################
def get_season_posters(league_id, SPORTSDB_API):

	season_posters_url = ("{}/search_all_seasons.php?id={}&poster=1".format(SPORTSDB_API, league_id))

	# https://www.thesportsdb.com/api/v1/json/98752398/search_all_seasons.php?id=4328&poster=1

	try:
		response = urllib2.urlopen(season_posters_url, timeout=10)
		data = json.load(response)

		if "seasons" not in data or not data["seasons"]:
			LogMessage("❌ No season posters found for League ID: {}".format(league_id))
			return {}

		# Convert list to dictionary {season_number: poster_url}
		season_poster_dict = {}

		for season in data["seasons"]:
			season_number = season.get("strSeason")
			poster_url = season.get("strPoster")

			if season_number and poster_url:  # Only store seasons with a valid poster
				season_poster_dict[season_number] = poster_url

		return season_poster_dict  # Return dictionary

	except urllib2.URLError as e:
		LogMessage("⚠ API Request Error: {}".format(e))
		return {}

# endregion

# region GET EVENT ID STUFF #############################################################################

# region (1) Get DATE from filename

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

# region (2) Get ROUND from filename
def extract_round_from_filename(filename, league_name):
	# Extracts the round number from a filename, checking standard patterns first and falling back to a JSON file for special cases.

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
	
	flags = re.IGNORECASE
	compiled_patterns = [re.compile(p, flags) for p in patterns]

	# First, check for numeric round matches (fastest)
	for pattern in compiled_patterns:
		match = pattern.search(filename)
		if match:
			try:
				return int(match.group(1))  # Convert match to integer
			except ValueError:
				continue  # Skip any incorrect matches

	LogMessage("►► No numeric round found in filename: {}".format(filename))

	# If no numeric round was found, check the special cases from JSON
	json_filepath = "C:/Users/mjc_c/AppData/Local/Plex Media Server/Scanners/Series/SpecialRoundsMap.json"

	if not os.path.exists(json_filepath):
		LogMessage("►► JSON file not found: {}".format(json_filepath))
		return None

	LogMessage("►► Checking for special cases in SpecialRoundsMap.json.")

	try:
		# Opening the json file
		with io.open(json_filepath, "r") as file:
			special_cases = json.load(file)

			# Remove metadata keys before processing
			special_cases.pop("_comment", None)
			special_cases.pop("_instructions", None)

	except Exception as e:
		LogMessage("►► Error reading JSON file: {}".format(str(e)))
		return None  # If JSON fails or doesn't exist, return None

	if not isinstance(special_cases, dict):
		return None  # Ensure it's a valid dictionary

	# Get league mappings (or default)
	league_mappings = special_cases.get(league_name, special_cases.get("default", {}))

	# Preprocess mappings: Lowercase all keywords for fast lookup
	if league_mappings:
		league_mappings = {k.lower(): v for k, v in league_mappings.items()}

	# Normalize filename to lowercase before checking for special cases
	lower_filename = filename.lower()


	for keyword, round_value in league_mappings.items():
		# Use word-boundary regex to ensure exact word matching
		if re.search(r"\b" + re.escape(keyword) + r"\b", lower_filename, re.IGNORECASE):
			LogMessage("►► Special case found! League: {}, Keyword: {}, Round: {}".format(league_name, keyword, round_value))
			return round_value

	LogMessage("►► No special cases found in filename: {}".format(filename))
	return None  # Return None if no match is found

	# endregion

# region (3) Get LEAGUE's events on the specific DATE
def get_events_on_date(formatted_date, league_id, SPORTSDB_API):
	events_on_date_url = "{}/eventsday.php?d={}&l={}".format(SPORTSDB_API, formatted_date, league_id)

	try:
		response = urllib2.urlopen(events_on_date_url, timeout=10)
		event_date_round_data = json.load(response)

		if "events" in event_date_round_data and event_date_round_data["events"]:
			#LogMessage("✅ Retrieved events on date: {} for: {}".format(formatted_date, league_id))
			return event_date_round_data["events"]  # Uses 'event_date_round_data' instead of 'data'

		else:
			LogMessage("❌ No events found for date: {}".format(formatted_date))
			return None

	except urllib2.URLError as e:
		LogMessage("⚠ API Request Error: {}".format(e))
		return None

# endregion

# region (3) Get LEAGUE's events in a specific ROUND
def get_events_in_round(round_number, league_id, SPORTSDB_API, season_number):

	LogMessage("🔎 Getting events in round: {} for: {} season: {}".format(round_number, league_id, season_number))
	
	# if the season number is 8 characters (########) split with hyphen (####-####)
	if len(str(season_number)) == 8:
		season_number = season_number[:4] + "-" + season_number[4:]

	events_in_round_url = "{}/eventsround.php?id={}&r={}&s={}".format(SPORTSDB_API, league_id, round_number, season_number)

	try:
		response = urllib2.urlopen(events_in_round_url, timeout=10)
		event_date_round_data = json.load(response) 

		if "events" in event_date_round_data and event_date_round_data["events"]:
			#LogMessage("✅ Retrieved events in round {} For: {} season: {}".format(round_number, league_id, season_number))
			return event_date_round_data["events"]

		else:
			LogMessage("❌ No events found for round: {}".format(round_number))
			return None

	except urllib2.URLError as e:
		LogMessage("⚠ API Request Error: {}".format(e))
		return None

# endregion

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
def remove_stop_phrases(words, league_name): # Remove multi-word stop phrases from a list of words.

	# Convert league name into a list of words ( to add to stop phrases)
	league_name_words = clean_text(league_name)
	# Only create ONE stop phrase for the full league name
	league_stop_phrase = (tuple(league_name_words),)  # Keep as one unit

	# Combinations of adjacent words or single words to be removed from matching
	stop_phrases = [
			("vs",),           # Single-word stop phrase
			("and",),       
			("the",),
			("fc",)				# Can also be adjacent groups of words. For example: ("formula", "1"),
		]

	# Add league name stop phrases (league names with numbers can mess up matching)
	stop_phrases.extend(league_stop_phrase)

	i = 0
	while i < len(words):  # Stop before the last word to avoid index errors
		for phrase in stop_phrases:
			# Check if the current and next words match the stop phrase
			if words[i:i + len(phrase)] == list(phrase):
				# Remove the stop phrase
				words[i:i + len(phrase)] = []
				i = i - 1  # Use standard subtraction instead of -=
				break
		i = i + 1  # Use standard addition instead of +=
	
	return words

# endregion

def compute_match_score(filename_words, event_words, league_name):

	# Convert sets to lists for ordered processing
	event_words = list(event_words)        # Convert set to list

	# Remove stop phrases from event_words
	event_words = remove_stop_phrases(event_words, league_name)

	# Convert back to sets for intersection
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

	return len(common_words), common_words  # Score is the count of matching words
# endregion

# region (4.3) find_matching_event FUNCTION

def find_matching_event(league_name, filename, event_date_round_data):
	
	# Split filename into words
	filename_words = clean_text(filename)
	# Convert set to lists for ordered processing
	filename_words = list(filename_words)

	# Remove stop phrases from filename_words
	filename_words = remove_stop_phrases(filename_words, league_name)

	# Convert back to sets for intersection
	filename_words = set(filename_words)

	# Initialize best_match and best_score
	best_matches = []  # Store all matches with the best score
	best_score = 0

	# region (FIRST PASS) Get the necessary info from event_date_round_data
	for event in event_date_round_data:
		event_name = event.get("strEvent", "")
		event_id = event.get("idEvent", "Unknown ID")

		event_text = "{} {} {}".format(event_name, event.get("strHomeTeam", ""), event.get("strAwayTeam", ""))
		event_words = clean_text(event_text)

		# Compute match score (higher = better match)
		match_score, common_words = compute_match_score(filename_words, event_words, league_name)

		# Store match details
		extra_words = len(event_words) - len(common_words)

		# region NEVER DELETE THESE LOGS (JUST COMMENT THEM OUT IF NEEDED!!!!)
		LogMessage("Event ID: {}".format(event_id))
		LogMessage("Filename words: {}".format(filename_words))
		LogMessage("🆚 Event words: {}".format(event_words))
		LogMessage("  Common words: {}".format(common_words))
		LogMessage("➡ Match Score: {}".format(match_score))
		LogMessage("Event Name: {}\n".format(event_name))
		# endregion NEVER DELETE THESE LOGS (JUST COMMENT THEM OUT IF NEEDED!!!!)

		# Update best matches
		if match_score > best_score:
			best_score = match_score
			best_matches = [{"event": event, "extra_words": extra_words, "common_words":common_words}]
		elif match_score == best_score:
			best_matches.append({"event": event, "extra_words": extra_words, "common_words":common_words})

		# endregion

	# region (TIEBREAKER 1): Choose the event with the **fewest extra words**
	if len(best_matches) > 1:
		LogMessage("📢 Multiple events with the same match score. Applying Tiebreaker 1 (Fewest Extra Words)...")

		# Log each event being considered before choosing
		for match in best_matches:
			event = match["event"]
			event_id = event.get("idEvent", "Unknown ID")
			event_name = event.get("strEvent", "")

			LogMessage("Event ID: {}".format(event_id))
			LogMessage("Filename words: {}".format(filename_words))
			LogMessage("🆚 Event words: {}".format(clean_text("{} {} {}".format(event_name, event.get('strHomeTeam', ''), event.get('strAwayTeam', '')))))
			LogMessage("  Common words: {}".format(match["common_words"]))
			LogMessage("  Extra Words: {}".format(match["extra_words"]))
			LogMessage("\n")

		# Pick the event with the fewest extra words
		best_match = min(best_matches, key=lambda x: x["extra_words"])["event"]

	else:
		best_match = best_matches[0]["event"] if best_matches else None
		# endregion

	# region (TIEBREAKER 2): If still tied, **add event description** and recompute
	if len(best_matches) > 1:
		LogMessage("📢 Still tied... Applying Tiebreaker 2 (Including Event Description)...")

		updated_matches = []
		for match in best_matches:
			event = match["event"]

			# Ensure all fields are Unicode (Python 2 fix)
			event_text = u"{} {} {} {}".format(
				unicode(event.get("strEvent", ""), "utf-8") if isinstance(event.get("strEvent", ""), str) else event.get("strEvent", ""),
				unicode(event.get("strHomeTeam", ""), "utf-8") if isinstance(event.get("strHomeTeam", ""), str) else event.get("strHomeTeam", ""),
				unicode(event.get("strAwayTeam", ""), "utf-8") if isinstance(event.get("strAwayTeam", ""), str) else event.get("strAwayTeam", ""),
				unicode(event.get("strDescriptionEN", ""), "utf-8") if isinstance(event.get("strDescriptionEN", ""), str) else event.get("strDescriptionEN", "")
			)

			event_words = clean_text(event_text)

			match_score, common_words = compute_match_score(filename_words, event_words, event.get("strLeague"))
			extra_words = len(event_words) - len(common_words)

			# Log updated match score
			LogMessage("Event ID: {}".format(event.get("idEvent")))
			LogMessage("Filename words: {}".format(filename_words))
			LogMessage("🆚 Updated Event words: {}".format(event_words))
			LogMessage("  Common words: {}".format(common_words))
			LogMessage("➡ New Match Score: {}".format(match_score))
			LogMessage("Event Name: {}\n".format(event.get("strEvent")))

			updated_matches.append({"event": event, "extra_words": extra_words, "score": match_score})

		# Determine best match after Tiebreaker 2
		best_score = max(m["score"] for m in updated_matches)
		best_matches = [m for m in updated_matches if m["score"] == best_score]

		best_match = best_matches[0]["event"] if best_matches else None

		# endregion

	# Final Match Decision
	if best_match:
		event_id = best_match.get("idEvent")
		event_title = best_match.get("strEvent")
		event_date = best_match.get("dateEvent")

		LogMessage("✅ Matched filename: {}".format(filename))
		LogMessage("✅ With event {}".format(event_title))
		LogMessage("✅ Event_id: {}".format(event_id))
		LogMessage("✅ Match score: {}".format(best_score))

		return event_id

	LogMessage("❌ No match found for filename: {}".format(filename))
	return None

# endregion

# endregion

# >< >< >< >< >< >< >< >< >< >< >< >< >< >< >< >< >< >< >< >< >< >< >< >< >< >< >< >< >< >< >< >< >< >< #

# region get_event_id function START
def get_event_id(league_name, season_number, episode_number, episode_path, league_id, SPORTSDB_API):
	# Initialize event_id
	event_id = None

	# endregion

	# region (1) Get DATE from filename
	filename = os.path.basename(episode_path)
	formatted_date = extract_date_from_filename(filename)
	# LogMessage("🗨️ FORMATTED DATE: {} For Episode: {}".format(formatted_date, episode_path))
	# endregion

	# region (2) Get ROUND if no DATE from filename
	if formatted_date is None:
		round_number = extract_round_from_filename(filename, league_name)
		# LogMessage("🗨️ ROUND NUMBER: {}".format(round_number))

		if round_number is None:
			LogMessage("⚠️ No date or round found in filename: {}".format(filename))
			return None

			# endregion

		# region (3) Get EVENTS in ROUND or DATE
		else:
			event_date_round_data = get_events_in_round(round_number, league_id, SPORTSDB_API, season_number)
	else:
		event_date_round_data = get_events_on_date(formatted_date, league_id, SPORTSDB_API)
	
	# If no event data
	if event_date_round_data is None:
		LogMessage("❌ No events found for date: {}".format(formatted_date))
		return None
		# endregion

	# region 4) Get event ID by matching the filename against the event_date_round_data
	event_id = find_matching_event(league_name, filename, event_date_round_data)

	if event_id is None:
		LogMessage("❌ No matching events found for filename: {}".format(filename))
		return None
	else:
		return event_id

	# endregion

# endregion

# region GET EVENT INFO FROM API ########################################################################
def get_event_info(SPORTSDB_API, event_id):
	
	event_info_url = "{}/lookupevent.php?id={}".format(SPORTSDB_API, event_id)
	#LogMessage("🔍 Requesting from URL: {}".format(event_info_url))

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
			LogMessage("❌ No metadata found for event ID: {}".format(event_id))
			return None

	except urllib2.URLError as e:
		LogMessage("⚠ API Request Error: {}".format(e))
		return None
# endregion