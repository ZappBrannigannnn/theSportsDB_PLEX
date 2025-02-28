# -*- coding: utf-8 -*-

# region IMPORTS

import re
import certifi
import requests
from logging_config import LogMessage
from dateutil import parser

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
		data = response.json()

		if "leagues" in data:
			for league in data["leagues"]:
				if league["strLeague"].lower() == league_name.lower():
					league_id = league.get("idLeague", None)
					#LogMessage("✅ Found League ID: {}".format(league_id))
					break  # Stop loop once the league is found

	except urllib3.exceptions.HTTPError as e:
		LogMessage("⚠ HTTP Error (1): {} - {}".format(e.code, e.reason))
		return None
	except urllib3.exceptions.RequestError as e:
		LogMessage("⚠ URL Error (1): {}".format(e.reason))
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
				return parsed_date.strftime("%Y-%m-%d")  # ✅ Return only if parsing succeeds
			except ValueError:
				continue  # ✅ Keep checking the next regex pattern

	return None  # ✅ If no valid date was found, return None




# endregion

# region (-2-) Get ROUND from filename

def extract_round_from_filename(filename):
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
	
	compiled_patterns = [re.compile(p, re.IGNORECASE) for p in patterns]

	# Check for numeric patterns first
	for pattern in compiled_patterns:
		match = pattern.search(filename)
		if match:
			try:
				return int(match.group(1))  # ✅ Convert to int safely
			except (IndexError, ValueError):
				continue  # ✅ Skip any incorrect matches

	# Case-insensitive check for "State of Origin"
	if re.search(r"state of origin", filename, re.IGNORECASE):
		return "00"  # ✅ Return round 00 as string

	return None  # ✅ Returns None if no match is found

	# endregion

# region (-3A- and -5-) Get LEAGUE's events on DATE

def get_events_on_date(formatted_date, league_id, SPORTSDB_API):
	events_on_date_url = "{}/eventsday.php?d={}&l={}".format(SPORTSDB_API, formatted_date, league_id)

	try:
		response = requests.get(events_on_date_url, verify=certifi.where(), timeout=10)
		response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
		event_date_data = response.json()

		if "events" in event_date_data and event_date_data["events"]:
			#LogMessage("✅ Retrieved {} events for: {}".format(formatted_date, league_id))
			return event_date_data["events"]  # Uses 'event_date_data' instead of 'data'

		else:
			LogMessage("\n❌ No events found for date: {}".format(formatted_date))
			return None

	except urllib2.URLError as e:
		LogMessage("\n⚠ API Request Error: {}".format(e))
		return None

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
		event_round_data = response.json()

		if "events" in event_round_data and event_round_data["events"]:
			#LogMessage("✅ Retrieved ROUND {} events For: {} season: {}".format(round_number, league_id, season_name))
			return event_round_data["events"]

		else:
			LogMessage("❌ No events found for round: {}".format(round_number))
			return []

	except requests.exceptions.RequestException as e:
		LogMessage("❌ API Request Error: {}".format(e))
		return []

# endregion

# region (-4-) Get MATCHING EVENT

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
				i -= 1  # Adjust index after removal
				break
		i += 1
	
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

	# Apply tiebreaker if needed
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

		return event_id, event_title, event_date

	LogMessage("❌ No match found for filename: {}".format(filename))
	return None, None, None  # ✅ Returns a consistent tuple when no match is found

# endregion

# endregion

# region (-6-) Get EVENT ORDER NUMBER

def get_event_order_number(event_date_data, event_id):
	# Sort events by 'strTimestamp' in ascending order
	sorted_events = sorted(event_date_data, key=lambda x: x.get("strTimestamp", ""), reverse=False)

	# Find the position of the event_id after sorting
	for index, event in enumerate(sorted_events, start=1):  # 1-based index
		if str(event.get("idEvent")) == str(event_id):  # Ensure string comparison
			return index  # Return the order number

	return None  # If not found, return None

# endregion

# region GET_EVENT_ID function

# region get_event_id initialize
def get_event_id(league_id, season_name, filename, SPORTSDB_API):
	LogMessage("🔍 Getting event ID from API for: {}".format(filename))
	# Initialize event_id and event data placeholders
	event_id = None
	event_date_data = None
	event_round_data = None
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
		LogMessage("⚠️ No date for: {}. Trying to get round.".format(filename))
		round_number = extract_round_from_filename(filename)
		LogMessage("🗨️ ROUND: {}".format(round_number))

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
		return None, None, None, None  # ✅ Ensures the script moves to the next file without retrying
		# endregion

	# region (^4^) Get matching event by matching the filename against event data

	# Assign the available event data to a common variable
	event_date_round_data = event_date_data or event_round_data

	# Ensure there's event data before calling find_matching_event
	if not event_date_round_data:
		LogMessage("❌ No event data available for matching: {}".format(filename))
		return None  # Prevents calling `find_matching_event` with None

	event_match = find_matching_event(filename, event_date_round_data)

	if event_match is None:
		LogMessage("❌ No matching events found for filename: {}".format(filename))
		return None

	event_id, event_title, event_date = event_match

	if event_id is None:
		LogMessage("❌ No matching events found for filename: {}".format(filename))
		return None

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
			LogMessage("✅ Total events on date(A): {}".format(total_events_on_date))
		else:
			LogMessage("❌ No events found for date: {} (League: {})".format(event_date, league_id))
			return None

	else:
		# If event_date_data exists (from having it in the filename in the first place)
		total_events_on_date = len(event_date_data)
		LogMessage("✅ Total events on date(B): {}".format(total_events_on_date))

	# endregion

	# region (^6^) Get event order number

	order_number = get_event_order_number(event_date_data, event_id)

	if order_number:
		LogMessage("✅ Found event_id {} at order_number: {} (sorted by time)".format(event_id, order_number))
	else:
		LogMessage("❌ event_id {} not found in event_date_data".format(event_id))

		# endregion
		
	return event_id, event_title, event_date, order_number

# endregion