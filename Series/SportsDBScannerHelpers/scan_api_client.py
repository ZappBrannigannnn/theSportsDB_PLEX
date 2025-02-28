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

# region GET EVENT ID

# region (1) Get DATE from filename

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
				return parsed_date.strftime("%Y-%m-%d")
			except ValueError:
				continue

# endregion

# region (2) Get ROUND from filename

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
	
	for pattern in patterns:
		match = re.search(pattern, filename, re.IGNORECASE)
		if match:
			return int(match.group(1))  # ✅ Correctly returns the first valid match

	return None  # ✅ Returns None if no pattern matches

	# endregion

# region (3) Get LEAGUE's events in ROUND

def get_events_in_round(league_id, season_name, round_number, SPORTSDB_API):
	# if the saeson number is 8 characters (########) split with hyphen (####-####)
	if len(str(season_name)) == 8:
		season_name = season_name[:4] + "-" + season_name[4:]

	events_in_round_url = "{}/eventsround.php?id={}&r={}&s={}".format(SPORTSDB_API, league_id, round_number, season_name)

	try:
		response = requests.get(events_in_round_url, verify=certifi.where(), timeout=10)
		response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
		event_date_round_data = response.json()

		if "events" in event_date_round_data and event_date_round_data["events"]:
			#LogMessage("✅ Retrieved ROUND {} events For: {} season: {}".format(round_number, league_id, season_name))
			return event_date_round_data["events"]

		else:
			LogMessage("\n❌ No events found for round: {}".format(round_number))
			return None

	except urllib2.URLError as e:
		LogMessage("\n⚠ API Request Error: {}".format(e))
		return None

# endregion

# region (3) Get LEAGUE's events on DATE

def get_events_on_date(formatted_date, league_id, SPORTSDB_API):
	events_on_date_url = "{}/eventsday.php?d={}&l={}".format(SPORTSDB_API, formatted_date, league_id)

	try:
		response = requests.get(events_on_date_url, verify=certifi.where(), timeout=10)
		response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
		event_date_round_data = response.json()

		if "events" in event_date_round_data and event_date_round_data["events"]:
			#LogMessage("✅ Retrieved {} events for: {}".format(formatted_date, league_id))
			return event_date_round_data["events"]  # Uses 'event_date_round_data' instead of 'data'

		else:
			LogMessage("\n❌ No events found for date: {}".format(formatted_date))
			return None

	except urllib2.URLError as e:
		LogMessage("\n⚠ API Request Error: {}".format(e))
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
		return event_id, event_title, event_date
	else:
		LogMessage("❌ No match found (unexpected case)")
		return None

# endregion

# endregion

# GET_EVENT_ID function

# region (1) Get DATE from filename

def get_event_id(league_id, season_name, filename, SPORTSDB_API):
	# Initialize event_id
	event_id = None
	
	formatted_date = get_date_from_filename(filename)
	if formatted_date:
		LogMessage("🗨️ EPISODE: {}".format(filename))
		LogMessage("🗨️ DATE: {}".format(formatted_date))
	
	# endregion
	
# region (2) Get ROUND if no DATE in filename

	if formatted_date is None:
		round_number = extract_round_from_filename(filename)
		LogMessage("🗨️ EPISODE: {}".format(filename))
		LogMessage("🗨️ ROUND: {}".format(round_number))

		if round_number is None:
			LogMessage("⚠️ No date or round found in filename: {}".format(filename))
			return None

			# endregion
	
		

# region (3) Get EVENTS in ROUND or DATE

		else:
			event_date_round_data = get_events_in_round(league_id, season_name, round_number, SPORTSDB_API)
	else:
		event_date_round_data = get_events_on_date(formatted_date, league_id, SPORTSDB_API)
	
	# If no event data
	if event_date_round_data is None:
		LogMessage("\n❌ No events found for date: {}".format(formatted_date))
		return None

		# endregion

# region (4) Get matching event by matching the filename against the event_date_round_data

	event_id, event_title, event_date = find_matching_event(filename, event_date_round_data)

	if event_id is None:
		LogMessage("❌ No matching events found for filename: {}".format(filename))
		return None
	else:
		return event_id, event_title, event_date

	# endregion

# endregion