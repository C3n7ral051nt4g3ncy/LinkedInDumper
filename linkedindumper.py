import requests
import json
import re
import argparse
from argparse import RawTextHelpFormatter
import sys
import time
import unidecode
from datetime import datetime
import urllib.parse
import textwrap

# mandatory authenticated session cookie
li_at = "AQEDAScD8v8Fe0dPAAABhHXoAdQAAAGGekee1E0AC7B-2_ReeI7-2kktI86_on_PE0FrKQDrbm3A_KlSkYJdzMkiRgEb0JB__2SoXOpPFIADecEva2hnyk7Yf2KIgVZTpUJuzKETnKZ0mp6zIpPx79TU"

# converting german umlauts
special_char_map = {ord('ä'):'ae', ord('ü'):'ue', ord('ö'):'oe', ord('ß'):'ss'}

format_examples = '''
 [1] john.doe@example.com > '{0}.{1}@example.com'
 [2] j.doe@example.com > '{0[0]}.{1}@example.com'
 [3] jdoe@example.com > '{0[0]}{1}@example.com'
 [4] doe@example.com > '{1}@example.com'
 [5] john@example.com > '{0}@example.com'
 [6] jd@example.com > '{0[0]}{1[0]}@example.com'
'''

parser = argparse.ArgumentParser("linkedindumper.py", formatter_class=RawTextHelpFormatter)
parser.add_argument("--url", metavar='<linkedin-url>', help="A LinkedIn company url - https://www.linkedin.com/company/<company>", type=str, required=True)
parser.add_argument("--cookie", metavar='<cookie>', help="LinkedIn 'li_at' session cookie", type=str, required=False,)
parser.add_argument("--quiet", help="Show employee results only", required=False, action='store_true')
parser.add_argument("--include-private-profiles", help="Show private accounts too", required=False, action='store_true')
parser.add_argument("--email-format", help="Python string format for emails; for example:"+format_examples, required=False, type=str)

args = parser.parse_args()
url = args.url

# optional CSRF token, not needed for GET requests but still defined to be sure
JSESSIONID = "ajax:1337133713371337"

# overwrite varibales if set via CLI
if (args.cookie):
	li_at = args.cookie

if (args.email_format):
	mailformat = args.email_format
else:
	mailformat = False

headers = {'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)', 'Content-type': 'application/json', 'Csrf-Token': JSESSIONID}
cookies_dict = {"li_at": li_at, "JSESSIONID": JSESSIONID} 

if (url.startswith('https://www.linkedin.com/company/')):
	try:
		# extract company slug from given LinkedIn URL
		before_keyword, keyword, after_keyword = url.partition('company/')
		company = after_keyword.split('/')[0]
		
		# url encode potential special chars that will brick the api lookup
		company = urllib.parse.quote(company)
		
		api1 = "https://www.linkedin.com/voyager/api/voyagerOrganizationDashCompanies?decorationId=com.linkedin.voyager.dash.deco.organization.MiniCompany-10&q=universalName&universalName=" + str(company)
		# request to query a company's urn ID
		r = requests.get(api1, headers=headers, cookies=cookies_dict)
		response1 = r.json()

		# retrieve company urn from the api; e.g. "urn:li:fsd_company:42848399"
		companyID = response1["elements"][0]["entityUrn"].split(":")[-1]

		# we'll use paging count 10 since it seems to work best
		paging_count = 10

		api2 = "https://www.linkedin.com/voyager/api/search/dash/clusters?decorationId=com.linkedin.voyager.dash.deco.search.SearchClusterCollection-165&origin=COMPANY_PAGE_CANNED_SEARCH&q=all&query=(flagshipSearchIntent:SEARCH_SRP,queryParameters:(currentCompany:List(" + str(companyID) + "),resultType:List(PEOPLE)),includeFiltersInResponse:false)&count=" + str(paging_count)+ "&start=0"
		# retrieve employee information from the api based on previously obtained company id
		r2 = requests.get(api2, headers=headers, cookies=cookies_dict)
		response2 = r2.json()

		paging_total = response2["paging"]["total"]
		required_pagings = -(-paging_total // paging_count)

		if not args.quiet:

			print("""\

 ██▓     ██▓ ███▄    █  ██ ▄█▀▓█████ ▓█████▄  ██▓ ███▄    █ ▓█████▄  █    ██  ███▄ ▄███▓ ██▓███  ▓█████  ██▀███  
▓██▒    ▓██▒ ██ ▀█   █  ██▄█▒ ▓█   ▀ ▒██▀ ██▌▓██▒ ██ ▀█   █ ▒██▀ ██▌ ██  ▓██▒▓██▒▀█▀ ██▒▓██░  ██▒▓█   ▀ ▓██ ▒ ██▒
▒██░    ▒██▒▓██  ▀█ ██▒▓███▄░ ▒███   ░██   █▌▒██▒▓██  ▀█ ██▒░██   █▌▓██  ▒██░▓██    ▓██░▓██░ ██▓▒▒███   ▓██ ░▄█ ▒
▒██░    ░██░▓██▒  ▐▌██▒▓██ █▄ ▒▓█  ▄ ░▓█▄   ▌░██░▓██▒  ▐▌██▒░▓█▄   ▌▓▓█  ░██░▒██    ▒██ ▒██▄█▓▒ ▒▒▓█  ▄ ▒██▀▀█▄  
░██████▒░██░▒██░   ▓██░▒██▒ █▄░▒████▒░▒████▓ ░██░▒██░   ▓██░░▒████▓ ▒▒█████▓ ▒██▒   ░██▒▒██▒ ░  ░░▒████▒░██▓ ▒██▒
░ ▒░▓  ░░▓  ░ ▒░   ▒ ▒ ▒ ▒▒ ▓▒░░ ▒░ ░ ▒▒▓  ▒ ░▓  ░ ▒░   ▒ ▒  ▒▒▓  ▒ ░▒▓▒ ▒ ▒ ░ ▒░   ░  ░▒▓▒░ ░  ░░░ ▒░ ░░ ▒▓ ░▒▓░
░ ░ ▒  ░ ▒ ░░ ░░   ░ ▒░░ ░▒ ▒░ ░ ░  ░ ░ ▒  ▒  ▒ ░░ ░░   ░ ▒░ ░ ▒  ▒ ░░▒░ ░ ░ ░  ░      ░░▒ ░      ░ ░  ░  ░▒ ░ ▒░
  ░ ░    ▒ ░   ░   ░ ░ ░ ░░ ░    ░    ░ ░  ░  ▒ ░   ░   ░ ░  ░ ░  ░  ░░░ ░ ░ ░      ░   ░░          ░     ░░   ░ 
    ░  ░ ░           ░ ░  ░      ░  ░   ░     ░           ░    ░       ░            ░               ░  ░   ░     
                                      ░                      ░                                         ░ by LRVT      
			""")

			print("[i] Company Name: " + company)
			print("[i] Company X-ID: " + companyID)
			print("[i] LN Employees: " + str(paging_total) + " employees found")
			print("[i] Dumping Date: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
			if mailformat:
				print("[i] Email Format: " + mailformat)
			print()

		dump_count = 0

		def clean_data(data):
			emoj = re.compile("["
						u"\U0001F600-\U0001F64F"  # emoticons
						u"\U0001F300-\U0001F5FF"  # symbols & pictographs
						u"\U0001F680-\U0001F6FF"  # transport & map symbols
						u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
						u"\U00002500-\U00002BEF"  # chinese char
						u"\U00002702-\U000027B0"
						u"\U00002702-\U000027B0"
						u"\U000024C2-\U0001F251"
						u"\U0001f926-\U0001f937"
						u"\U00010000-\U0010ffff"
						u"\u2640-\u2642" 
						u"\u2600-\u2B55"
						u"\u200d"
						u"\u23cf"
						u"\u23e9"
						u"\u231a"
						u"\ufe0f"  # dingbats
						u"\u3030"
													"]+", re.UNICODE)
			
			# remove emojis
			cleaned = re.sub(emoj, '', data).strip()
			# convert german umlauts before removing diacritics
			cleaned = cleaned.replace('Ü','Ue').replace('Ä','Ae').replace('Ö', 'Oe').replace('ü', 'ue').replace('ä', 'ae').replace('ö', 'oe')
			# convert semicolon to colon to prevent CSV breaking
			cleaned = cleaned.replace(',', '')
			cleaned = cleaned.replace(';', ',')
			# remove diacritics
			cleaned = unidecode.unidecode(cleaned)
			return cleaned.strip()

		def progressbar(it, prefix="", size=60, out=sys.stdout): # Python3.3+
				count = len(it)
				def show(j):
						x = int(size*j/count)
						print("{}[{}{}] {}/{}".format(prefix, "#"*x, "."*(size-x), j, count),
										end='\r', file=out, flush=True)
				show(0)
				for i, item in enumerate(it):
						yield item
						show(i+1)
				print("\n", flush=True, file=out)

		employee_dict = []
		# paginate API results
		for page in progressbar(range(required_pagings), "Progress: ", 40):
			api2 = "https://www.linkedin.com/voyager/api/search/dash/clusters?decorationId=com.linkedin.voyager.dash.deco.search.SearchClusterCollection-165&origin=COMPANY_PAGE_CANNED_SEARCH&q=all&query=(flagshipSearchIntent:SEARCH_SRP,queryParameters:(currentCompany:List(" + str(companyID) + "),resultType:List(PEOPLE)),includeFiltersInResponse:false)&count=" + str(paging_count)+ "&start=" + str(page*10)
			# retrieve employee information from the api based on previously obtained company id
			r2 = requests.get(api2, headers=headers, cookies=cookies_dict)
			response2 = r2.json()
			try:
				test = response2["elements"][0]["results"][0]["title"]["text"]
				results = response2["elements"][0]["results"]
			except:
				pass

			try:
				test = response2["elements"][1]["results"][0]["title"]["text"]
				results = response2["elements"][1]["results"]
			except:
				pass

			try:
				test = response2["elements"][2]["results"][0]["title"]["text"]
				results = response2["elements"][2]["results"]
			except:
				pass

			for employee in results:
				# get a user's full account name and remove some known abbreviations and salutations
				account_name = clean_data(employee["title"]["text"]).split(" ")
				badwords = ['Prof.', 'Dr.', 'M.A.', ',', 'LL.M.']
				for word in list(account_name):
					if word in badwords:
						account_name.remove(word)

				# if the account name consists of 2 strings, assume firstname and lastname
				if len(account_name) == 2:
					firstname = account_name[0]
					lastname = account_name[1]
				# otherwise it is some unknown format with saluation, or middle name or random abbreviations
				else:
					# combine everything up to last string into firstname
					firstname = ' '.join(map(str,account_name[0:(len(account_name)-1)]))
					# use the last string as lastname
					lastname = account_name[-1]
				
				try:
					position = clean_data(employee["primarySubtitle"]["text"])
				except:
					position = "N/A"
				gender = "N/A"
				
				# an account's location is sometimes unaccessible
				try:
					location = employee["secondarySubtitle"]["text"]
				except:
					location = "N/A"
				
				profile_link = employee["navigationUrl"].split("?")[0]

				if args.include_private_profiles:
					employee_dict.append({"firstname":firstname, "lastname":lastname, "position":position, "gender":gender, "location":location, "profile_link":profile_link})
					dump_count += 1
				else:
					if (firstname != "LinkedIn" and lastname != "Member"):
						employee_dict.append({"firstname":firstname, "lastname":lastname, "position":position, "gender":gender, "location":location, "profile_link":profile_link})
						dump_count += 1

		# remove duplicates from list in dict
		l = employee_dict
		seen = set()
		new_l = []
		for d in l:
			t = tuple(sorted(d.items()))
			if t not in seen:
				seen.add(t)
				new_l.append(d)

			# this is the new dict with unique employees
			employee_dict = new_l

		if mailformat:
			legende = "Firstname;Lastname;Email;Position;Gender;Location;Profile"
		else:
			legende = "Firstname;Lastname;Position;Gender;Location;Profile"
		
		print(legende)

		# dump all crawled employees
		for person in employee_dict:
			if mailformat:
				print(person["firstname"]+";"+person["lastname"]+";"+mailformat.format(person["firstname"].replace(".","").lower().translate(special_char_map),person["lastname"].replace(".","").lower().translate(special_char_map))+";"+person["position"]+";"+person["gender"]+";"+person["location"]+";"+person["profile_link"])
			else:
				print(";".join(person.values()))

		if not args.quiet:
			print()
			print("[i] Successfully crawled " + str(len(employee_dict)) + " unique " + str(company) + " employee(s). Hurray ^_-")
	
	except Exception as e:
		# likely authorization error due to incorrect 'login' cookie
		# otherwise the script is broken or the api has been changed
		print("[!] Authenticated session cookie required.")
		print("    > Set variable permanently in script or use the '--session-cookie' CLI flag!")
		print("[debug] " + str(e))
else:
	print()
	print("[!] Invalid URL provided.")
	print("[i] Example URL: 'https://www.linkedin.com/company/apple'")