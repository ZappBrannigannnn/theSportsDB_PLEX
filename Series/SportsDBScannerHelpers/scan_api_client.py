# -*- coding: utf-8 -*-

# region IMPORTS

import re
import os
import sys
import certifi
import requests
from logging_config import LogMessage
from dateutil import parser
import json

import unicodedata


# endregion

# region GET LEAGUE ID FROM API

def get_league_id(league_name, SPORTSDB_API):
	LogMessage("🔍 Getting league ID from API for: {}".format(league_name))

	league_id = None  # Always initialize league_id

	league_list_url = "{}/all_leagues.php".format(SPORTSDB_API)

	#LogMessage("🗨️ League List URL: {}".format(league_list_url))

	try:
		response = requests.get(league_list_url, verify=certifi.where(), timeout=10)
		response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
		try:
			data = response.json()
		except (AttributeError, ValueError):  # Handle missing `.json()` or invalid JSON
			data = json.loads(response.text or '{}')  # Ensure it's always a dict

		if "leagues" in data:
			for league in data["leagues"]:
				if league["strLeague"].lower() == league_name.lower():
					league_id = league.get("idLeague", None)
					#LogMessage("✅ Found League ID: {}".format(league_id))
					break  # Stop loop once the league is found


	except requests.exceptions.HTTPError as e:
		LogMessage("⚠ HTTP Error (1): {} - {}".format(e.response.status_code, str(e)))
		return None
	except requests.exceptions.RequestException as e:
		LogMessage("⚠ URL Error (1): {}".format(str(e)))
		return None
	except ValueError:
		LogMessage("🚨 ERROR: Invalid JSON response from API (1)")
		return None
	except Exception as e:
		LogMessage("🚨 Unexpected Error (1): {}".format(str(e)))
		return None

	# If no league was found, return None values
	if not league_id:
		# Log no match found
		LogMessage("NO MATCH FOUND FOR {}".format(league_name))
		return None

	return league_id

# endregion

# region GET EVENT ID helpers

# region (-1-) Get DATE from filename

def get_date_from_filename(filename):
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
				return parsed_date.strftime("%Y-%m-%d")  # Return only if parsing succeeds
			except ValueError:
				continue  # Keep checking the next regex pattern

	return None  # If no valid date was found, return None




# endregion

# region (-2-) Get ROUND from filename

def extract_round_from_filename(filename, league_name):
	# Extracts the round number from a filename, checking standard patterns first and falling back to a JSON file for special cases.

	patterns = [
		r"Round (\d+)",     	# Round 12
		r"Round-(\d+)",     	# Round-12
		r"Round_(\d+)",     	# Round_12
		r"Round\.(\d+)",    	# Round.12
		r"Round(\d+)",      	# Round12

		r"R (\d+)",     		# R 12
		r"R-(\d+)",     		# R-12
		r"R_(\d+)",     		# R_12
		r"R\.(\d+)",    		# R.12
		r"R(\d+)",      		# R12

		r"Matchweek (\d+)",     # Matchweek 5
		r"Matchweek-(\d+)",     # Matchweek-5
		r"Matchweek_(\d+)",     # Matchweek_5
		r"Matchweek\.(\d+)",    # Matchweek.5
		r"Matchweek(\d+)",      # Matchweek5

		r"Match Week (\d+)",    # Match Week 7
		r"Match-Week-(\d+)",    # Match-Week-7
		r"Match_Week_(\d+)",    # Match_Week_7
		r"Match\.Week\.(\d+)",  # Match.Week.7

		r"MW (\d+)",    		# MW 10
		r"MW-(\d+)",    		# MW-10
		r"MW_(\d+)",    		# MW_10
		r"MW\.(\d+)",   		# MW.10
		r"MW(\d+)",     		# MW10
		r"M(\d+)",      		# M10

		r"Week (\d+)",  		# Week 3
		r"Week-(\d+)",  		# Week-3
		r"Week_(\d+)",  		# Week_3
		r"Week\.(\d+)", 		# Week.3
		r"Week(\d+)",   		# Week3

		r"Gameweek (\d+)",  	# Gameweek 9
		r"Gameweek-(\d+)",  	# Gameweek-9
		r"Gameweek_(\d+)",  	# Gameweek_9
		r"Gameweek\.(\d+)", 	# Gameweek.9
		r"Gameweek(\d+)", 		# Gameweek9

		r"GW (\d+)",  			# GW 4
		r"GW-(\d+)",  			# GW-4
		r"GW_(\d+)",  			# GW_4
		r"GW\.(\d+)", 			# GW.4
		r"GW(\d+)",   			# GW4
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

	LogMessage("►► No ROUND found in filename: {}".format(filename))

	# If no numeric round was found, check the special cases from JSON
	if os.name == 'nt':  # Windows
		json_filepath = os.path.join(os.getenv('LOCALAPPDATA'),
									"Plex Media Server",
									"Scanners", "Series",
									"SpecialRoundsMap.json")
	else:  # Debian/Linux

		config_home = "/var/lib/plexmediaserver/Library/Application Support"
		json_filepath = os.path.join(config_home,
									"Plex Media Server",
									"Scanners",
									"Series",
									"SpecialRoundsMap.json")

	if not os.path.exists(json_filepath):
		LogMessage("►► JSON file not found: {}".format(json_filepath))
		return None

	LogMessage("►► Checking for special cases in SpecialRoundsMap.json.")

	try:
		# Opening the json file
		with open(json_filepath, "r") as file:
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
	return None

	# endregion

# region (-3A- and -5-) Get LEAGUE's events on DATE

def get_events_on_date(formatted_date, league_id, SPORTSDB_API):
	events_on_date_url = "{}/eventsday.php?d={}&l={}".format(SPORTSDB_API, formatted_date, league_id)

	try:
		response = requests.get(events_on_date_url, verify=certifi.where(), timeout=10)
		response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
		try:
			event_date_data = response.json()
		except AttributeError:  # Python 2 fallback
			event_date_data = json.loads(response.text)

		if "events" in event_date_data and event_date_data["events"]:
			#LogMessage("✅ Retrieved {} events for: {}".format(formatted_date, league_id))
			return event_date_data["events"]  # Uses 'event_date_data' instead of 'data'

		else:
			LogMessage("❌ No events found for date: {}".format(formatted_date))
			return None

	except requests.exceptions.RequestException as e:
		LogMessage("❌ API Request Error (1): {}".format(e))
		return []

# endregion

# region (-3B-) Get LEAGUE's events in ROUND

def get_events_in_round(league_id, season_name, round_number, SPORTSDB_API):
	# if the saeson number is 8 characters (########) split with hyphen (####-####)
	if len(str(season_name)) == 8:
		season_name = season_name[:4] + "-" + season_name[4:]

	events_in_round_url = "{}/eventsround.php?id={}&r={}&s={}".format(SPORTSDB_API, league_id, round_number, season_name)

	try:
		response = requests.get(events_in_round_url, verify=certifi.where(), timeout=10)
		response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
		try:
			event_round_data = response.json()
		except (AttributeError, ValueError):  # Handle missing `.json()` or invalid JSON
			event_round_data = json.loads(response.text or '{}')  # Ensure it's always a dict


		if "events" in event_round_data and event_round_data["events"]:
			#LogMessage("✅ Retrieved ROUND {} events For: {} season: {}".format(round_number, league_id, season_name))
			return event_round_data["events"]

		else:
			LogMessage("❌ No events found for round: {}".format(round_number))
			return []

	except requests.exceptions.RequestException as e:
		LogMessage("❌ API Request Error (2): {}".format(e))
		return []

# endregion

# region (-4-) Get MATCHING EVENT

# region (4.1) clean_text HELPER FUNCTION

def clean_text(text):
	# Converts text to lowercase, remove punctuation non-ascii encoding, and splits into words

    if not text:
        return []
    
    # Ensure text is Unicode in Python 2
    if isinstance(text, str):  # Python 2 `str` is bytes
        text = text.decode('utf-8')  # Convert to Unicode
    
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore')  # Normalize Unicode
    text = text.lower().replace("_", " ")  # Convert to lowercase and normalize underscores
    words = re.split(r"\W+", text)  # Split on non-word characters (removes punctuation)
    
    return [w for w in words if w]  # Return a list of words, removing empty strings

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
	while i < len(words):
		for phrase in stop_phrases:
			# Check if the current and next words match the stop phrase
			if words[i:i + len(phrase)] == list(phrase):
				# Remove the stop phrase
				words[i:i + len(phrase)] = []
				i -= 1  # Adjust index after removal
				break
		i += 1
	
	#LogMessage("STOP PHRASES WITH LEAGUE NAME ADDED: {}".format(stop_phrases))

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

		return event_id, event_title, event_date

	LogMessage("❌ No match found for filename: {}".format(filename))
	return None, None, None  # Returns a consistent tuple when no match is found

# endregion

# endregion

# region (-6-) Get EVENT ORDER NUMBER

def get_event_order_number(event_date_data, event_id):
	# Sort events by 'strTimestamp' in ascending order
	sorted_events = sorted(event_date_data, key=lambda x: x.get("strTimestamp", "") or "0000-00-00 00:00:00", reverse=False)

	# Find the position of the event_id after sorting
	for index, event in enumerate(sorted_events, start=1):  # 1-based index
		if str(event.get("idEvent")) == str(event_id):  # Ensure string comparison
			return index  # Return the order number

	return None  # If not found, return None

# endregion

# region GET_EVENT_ID function

# region get_event_id initialize
def get_event_id(league_name, league_id, season_name, filename, SPORTSDB_API):
	LogMessage("🔍 Getting event ID from API for: {}".format(filename))
	
	# Initialize event_id and event data placeholders
	event_id = None
	event_date_data = None
	event_round_data = None
	round_number = None
	# endregion

	# region (^1^) Get DATE from filename
	formatted_date = get_date_from_filename(filename)

	if formatted_date is not None:
		LogMessage("🗨️ DATE: {}".format(formatted_date))
		# endregion

		# region (^3^) Fetch events for the given date
		event_date_data = get_events_on_date(formatted_date, league_id, SPORTSDB_API)
		# endregion

	# region (^2^) Get ROUND from filename if no DATE is found
	else:
		LogMessage("⚠️ No date for: {}".format(filename))
		LogMessage("🗨️ Trying to get round.")
		round_number = extract_round_from_filename(filename, league_name)
		LogMessage("✅ Retrieved ROUND {}\n".format(round_number))

		# If no date or round is found, return None
		if round_number is None:
			LogMessage("⚠️ No date or round found in filename: {}".format(filename))
			return None, None, None, None
			# endregion

		# region (^3^) Fetch events for the given round number
		event_round_data = get_events_in_round(league_id, season_name, round_number, SPORTSDB_API)
		# endregion

	# region If no events are found for either date or round, log & mark file as "skipped"
	if not event_date_data and (event_round_data is None or event_round_data == []):
		LogMessage("❌ No events found for date: {} or round: {}. Skipping event matching.".format(
			formatted_date if formatted_date else "N/A", 
			round_number if round_number else "N/A"
		))
		return None, None, None, None  # Ensures the script moves to the next file without retrying
		# endregion

	# region (^4^) Get matching event by matching the filename against event data

	# Assign the available event data to a common variable
	event_date_round_data = event_date_data or event_round_data

	# Ensure there's event data before calling find_matching_event
	if not event_date_round_data:
		LogMessage("❌ No event data available for matching: {}".format(filename))
		return None, None, None, None  # Prevents calling `find_matching_event` with None

	event_match = find_matching_event(league_name, filename, event_date_round_data)

	if event_match is None:
		LogMessage("❌ No matching events found for filename: {}".format(filename))
		return None, None, None, None

	event_id, event_title, event_date = event_match

	if event_id is None:
		LogMessage("❌ No matching events found for filename: {}".format(filename))
		return None, None, None, None

	# endregion

	# region (^5^) Get total number of events on date

	if not event_date_data:
		# If no event date from api for the matched event then stop (it was matched by round)
		if event_date is None:
			LogMessage("❌ Cannot fetch events because event_date is None. Meaning we didn't get a matched event.")
			return None  # Prevents calling API with None

		# Change this to formatted_date variable for use with the old function.
		formatted_date = event_date
		# Use the same get_events_on_date function.
		event_date_data = get_events_on_date(formatted_date, league_id, SPORTSDB_API)

		if event_date_data:
			total_events_on_date = len(event_date_data)
			#LogMessage("✅ (i) Total events on date: {}".format(total_events_on_date))
		else:
			LogMessage("❌ No events found for date: {} (League: {})".format(event_date, league_id))
			return None

	else:
		# If event_date_data exists (from having it in the filename in the first place)
		total_events_on_date = len(event_date_data)
		#LogMessage("✅ (ii) Total events on date: {}".format(total_events_on_date))

	# endregion

	# region (^6^) Get event order number

	order_number = get_event_order_number(event_date_data, event_id)

	if order_number:
		LogMessage("✅ Found event_id {} at order_number: {} (sorted by timestamp)\n".format(event_id, order_number))
	else:
		LogMessage("❌ event_id {} not found in event_date_data".format(event_id))

		# endregion
		
	return event_id, event_title, event_date, order_number

# endregion