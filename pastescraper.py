#!/usr/bin/env python

"""

                Paste Scraper v1.3                
                                                  
                    by cry0 <3                    
                                                  
       touched inappropriately by s0ups </3       


-.     .-.     .-.     .-.     .-.     .-.     .-.
::\:::/:::\:::/:::\:::/:::\:::/:::\:::/:::\:::/:::
   ._.     ._.     ._.     ._.     ._.     ._.    


Changelog:

1.3b:
	Removed irrelevent conditions
	General code cleanup
	BUT STILL MESSY CODE HAHAHA

1.3:
	Added expiration time frame specification
	Fixed a bug in the error handler

1.2:
	Removed the need for a key file
	Added option to save all expiring posts
	Added Requests connection exception handler

1.1b:
	Added JSON exception handler
	Removed unique ID reuse handler

1.1a:
	Timestamp addition by s0ups

1.1:
	Fixed a duplication bug
	Changed filename syntax

1.0a:
	Added regex parsing
	Now strips non-printable chars
	Made it pretty

1.0:
	Initial release

"""


import requests
import json
import colorama
import time
import re

colorama.init()
print colorama.Style.BRIGHT


#
# Amount of content to fetch
#
paste_limit = 100              # Number of pastes to query for; max 500, default 50.
wait_time = 60                 # Number of seconds to wait between queries.
keep_expiring_pastes = False    # Whether or not to auto-save pastes with expiration times.
keep_within_time_frame = True  # Only save expiring pastes within the given time frame.
time_frame = "10m"             # 10m, 1h, 1d, 1w, 2w, or 1m; unused if keep_within_time_frame is False.


#
# Words that will cause the script to save the paste
#
# NOTE: Keywords must be lowercase.
#
keywords = [
	"put",
	"your",
	"keywords",
	"here"
]


#
# Regular expressions that will cause the script to save the paste
#
# NOTE: Regex must be lowercase.
#
regex = [
	r"[\w\d\._%+-]+@[\w\d\.-]+\.\w{2,8}[^\w\d\.-]"  # Regex for emails
	r"^[Aa]dditional regex goes here[\.!]$\n"
]


#
# Local file path options, relative to the current directory
#
save_dir = "pastebin"  # Directory to save files into.

total_matches = 0
seen_keys = []
expiration_intervals = {
	"10m" : 600,
	"1h" : 3600,
	"1d" : 86400,
	"1w" : 604800,
	"2w" : 1209600,
	"1m" : 2592000
}


# Strip out all bad characters from the string.
def strip_bad_chars(text):
	text = re.sub(r"[\x00-\x1f\\\/\:\*\?\"\<\>\|\x7f-\xff]", "", text)
	return text


# Save the paste to the directory specified in [save_dir].
def save_paste(prefix, suffix, title, timestamp, expiration=""):
	prefix = strip_bad_chars(prefix)
	save_file = "./%s/%s%s" % (save_dir, str(prefix), str(suffix))
	# Append the title of the paste to the key, if one exists.
	if title:
		title = str(title.encode("ascii", "ignore"))
		title = strip_bad_chars(title)
		save_file += " - %s" % title
	print "[%s] %s[MATCH] %s[%s.txt]%s" % (total_matches, colorama.Fore.GREEN, colorama.Fore.CYAN, save_file, colorama.Fore.RESET)
	save_file_ptr = open("%s.txt" % save_file, "w")
	save_data  = "Title: %s\n" % i["title"].encode("ascii", "ignore")
	save_data += "User: %s\n" % i["user"].encode("ascii", "ignore")
	save_data += "Retrieval Time: %s\n" % timestamp
	if expiration:
		save_data += "Expiration Time: %s\n" % expiration
	save_data += "Link: %s\n\n" % i["full_url"]
	save_data += "=========================\n\n\n%s" % paste.encode("ascii", "ignore")
	save_file_ptr.write(save_data)
	save_file_ptr.close()


while True:
	try:
		url = "http://pastebin.com/api_scraping.php?limit=%s" % str(paste_limit)
		keys = []

		# Grab the list of pastes from the API.
		paste_list = requests.get(url).text
		paste_list = json.loads(paste_list)

		# Detect which pastes contain any of the defined keywords.
		for i in paste_list:
			matched_keywords = []

			# Fill in the rest of the keys with old keys if duplicates.
			if i["key"] in seen_keys:
				end_index = paste_list.index(i)
				for x in range(0, (paste_limit - end_index)):
					keys.append(seen_keys[x])
				break

			else:
				keys.append(i["key"])
				prefix_string = ""
				paste = requests.get(i["scrape_url"]).text
				timestamp = time.ctime(int(i["date"]))

				# Grab the expiration timestamp and exit if catching all expiring pastes.
				if keep_expiring_pastes and int(i["expire"]) > 0:
					expiration = time.ctime(int(i["expire"]))

					# Only save the ones within a given time frame if configured to do so.
					if keep_within_time_frame:
						time_to_live = int(i["expire"]) - int(i["date"])
						if expiration_intervals[time_frame] == time_to_live:
							total_matches += 1
							save_paste("!expire - ", i["key"], i["title"], timestamp, expiration)
					else:
						total_matches += 1
						save_paste("!expire - ", i["key"], i["title"], timestamp, expiration)

				for keyword in keywords:
					if keyword in paste.lower():
						matched_keywords.append(keyword)
						break

				# Need to do something in that extra 55sec, right?
				for expression in regex:
					matches = re.search(expression, paste.lower())
					if matches:
						matched_keywords.append(matches.group(0))
						break

				# Combine all detected keywords/regex into one prefix string.
				if matched_keywords:
					for prefix_part in matched_keywords:
						prefix_string += "[%s] - " % prefix_part
						total_matches += 1
					save_paste(prefix_string, i["key"], i["title"], timestamp)

		# Repopulate the list of checked keys.
		seen_keys = keys
		print "Waiting %ssec..." % str(wait_time)
		time.sleep(wait_time)

	except KeyboardInterrupt:
		print "%s[BREAK] %sQuitting...%s\n" % (colorama.Fore.RED, colorama.Fore.YELLOW, colorama.Fore.RESET)
		exit()

	except ValueError:
		print "%s[ERROR] %sError encoding data via JSON! Retrying in %ssec...%s" % (colorama.Fore.RED, colorama.Fore.YELLOW, str(wait_time), colorama.Fore.RESET)
		time.sleep(wait_time)

	except IndexError:
		print "%s[ERROR] %sIterable index out of range! Wiping key list and retrying in %ssec...%s" % (colorama.Fore.RED, colorama.Fore.YELLOW, str(wait_time), colorama.Fore.RESET)
		seen_keys = []
		time.sleep(wait_time)

	except TypeError:
		print "%s[ERROR] %sAn error occurred while the error handler was handling a previous error." % (colorama.Fore.RED, colorama.Fore.YELLOW)
		print "Yes, you read that correctly. I made an error in the error handler."
		print "Please contact and tell me how much of a fucking moron I am if you enounter this.%s" % colorama.Fore.RESET
		exit()

	except requests.exceptions.ConnectionError:
		print "%s[ERROR] %sConnection error! Waiting %ssec...%s" % (colorama.Fore.RED, colorama.Fore.YELLOW, str(wait_time), colorama.Fore.RESET)
		time.sleep(wait_time)