#!/usr/bin/env python3

# REPLICA 'CaTS' (Criteria and Terms Search) v0.1
# Last Updated: 2022-07-26

# DESCRIPTION :

# Provides functonality to search JSON files provided by the parsing component of REPLICA's Automated Document Analysis Tool. It accepts one or more JSON files provided by the parsing process, searching them for instances of terms which are associated with a set of criteria (provided by a JSON file during startup). The process outputs another set of JSON files which contain only the quotes where these matches occur, along with relevant meta-data (term, criteria, paper title).

# REQUIREMENTS:

# - criteria-and-terms.json - a json dictionary of 'criteria' holding an array of 'terms'.
# - json outputs of parsed PDFs

# HOW TO USE :

# 1. Place this Python file, along with the json of 'criteria-and-terms', into a new folder.
# 2. Inside the new folder, create two more sub-folders - 'inputs' and 'outputs'.
# 3. Place one or more JSON files from the PDF parser into the folder you named 'inputs'.
# 4. *deep breath* Run the Python file.
# 5. Depending on how many JSON files you are working with, make a cup of tea/coffee.
# 6. You will find shiny new JSON files in 'outputs'- listing matching sentences within respective criteria and terms.

# - - - #

# IMPORTS :

# Import the Python 'csv' module.

print("Importing 'csv'.")
import csv
print("Finished importing 'csv'." + "\n")

# Import the Python 'json' module.

print("Importing 'json'.")
import json
print("Finished importing 'json'." + "\n")

# Import the Python 'os' module.

print("Importing 'os'.")
import os
print("Finished importing 'os'." + "\n")

# Import the Python 're' module.

print("Importing 're'.")
import re
print("Finished importing 're'." + "\n")

# Import the Python 'time' module.

print("Importing 'time'.")
import time
print("Finished importing 'time'." + "\n")

# - - - #

# CLASSES AND METHODS :

# Class definition that holds neccesary meta-data on each match that is found.

#class Match():
#	def __init__(self, paper_title: str, json_input: str, criteria: str, term: str, quote: str):
#		self.paper_title = paper_title
#		self.json_input = json_input
#		self.criteria = criteria
#		self.term = term
#		self.quote = quote
		
#testMatch = Match("T-Title", "T-JSON", "T-Criteria", "T-Term", "T-Quote")
#print("Paper Title: " + testMatch.paper_title)
#print("JSON Input: " + testMatch.json_input)
#print("Criteria: " + testMatch.criteria)
#print("Term: " + testMatch.term)
#print("Quote: " + testMatch.quote)

# - - - #

# FUNCTIONS :
		
# FUNCTION: append_match()
# - expects a criteria (str), path to the file (str), sentence to add (str), and term to add it within (str)
# - returns None
		
def append_match(criteria: str, path: str, sentence: str, term: str):
	
	output_file = "outputs/output-" + path
	json_obj = {}
	
	try:
		with open(output_file, "r") as f:
			json_obj = json.load(f)
	except IOError:
		pass
		
	if criteria in json_obj:
		if term in json_obj[criteria]:
			json_obj[criteria][term].append(sentence)
		else:
			json_obj[criteria][term] = [sentence]
	else:
		json_obj[criteria] = { term : [sentence] }
		
	if os.path.exists("outputs") is False:
		os.makedirs("outputs")
		
	with open(output_file, "w") as f:
		json.dump(json_obj, f)
	
	return None

# FUNCTION: get_title(path: str):
# - expects the path of a json input (str)
# - returns 'title' (str)

def get_title(path: str):
	with open("inputs/" + path, 'r') as f:
		data = json.load(f)
	title = data["content"][0]["sentences"][0]["content"]
	return title

# FUNCTION: match_criteria()
# - Expects a dictionary consisting of criteria (keys) associated with lists of terms (values) and two string variables (paper title and file name of the json input).
# - The value of each key/criteria is a list of terms. 'match_term()' with every item (terms).
# - returns None

def match_criteria(criteria_and_terms: dict, current_title: str, current_file: str):
	dict_keys = criteria_and_terms.keys()
	print("dict_keys (list):" + str(dict_keys))
	for k in dict_keys :
		current_criteria = k
		print(str("Searching for criteria '" + current_criteria + "'..."))
		current_terms = criteria_and_terms[k]
		match_terms(current_criteria, criteria_and_terms, current_title, current_file)
		print("Finished searching for criteria '" + current_criteria + "'.")
	return None
			
# FUNCTION: match_terms()
# - Using the term included in the call, it looks for substring matches in each string of the current JSON input.
# - If a match is found, it calls 'append_match()' to update (or create) a JSON output.
# - returns None
			
def match_terms(current_criteria: str, criteria_and_terms: dict, current_title: str, current_file: str):
	terms = criteria_and_terms[current_criteria]
	terms.append(current_criteria)
	for t in terms:
		print("    Searching for term '" + t + "'...")
		with open("inputs/" + current_file, "r") as f:
			data = json.load(f)
			for each_obj in data["content"]:
				for each_sen in each_obj["sentences"]:
					#print(each_sen["content"])
					regex = r"\b" + t + r"\b"
					if re.search(regex, each_sen["content"], re.IGNORECASE):
					#if t in each_sen["content"]:
						print("        Match found for \'" + t + "\' in string \"" + each_sen["content"] + "\"")
						append_match(current_criteria, current_file, each_sen["content"], t)
		print(str("    Finished searching for term '" + t + "'."))
	return None

# - - - #

# SCRIPT :
		
# Import files to be processed (JSON files in '*/inputs').

print("Importing JSON input(s)...")

json_inputs = []
for file in os.listdir("inputs/"):
	if file.endswith(".json"):
		json_inputs.append(file)

# print("json_inputs (list): " + str(json_inputs))
		
print("Finished importing JSON input(s)." + "\n")

# Import criteria and search terms to be used ('criteria-and-terms.json').

print("Importing criteria and search terms...")

with open("criteria-and-terms.json", "r") as f:
	criteria_and_terms = json.load(f)
	
#print("criteria_and_terms (dict): " + str(criteria_and_terms))

print("Finished importing criteria and search terms." + "\n")

# Start working through the populated list of JSON inputs using criteria, terms...

for j in json_inputs:
	j_path = j
	match_criteria(criteria_and_terms, get_title(j_path), j_path)