# written by Kenichi Furursawa (s3204146), Sho Cremers (s3135144), and Sukhleen Kaur (s3157423)
import requests
import sys
import re
import spacy
from yes_or_no import *

def print_answer(query):
	url = 'https://query.wikidata.org/sparql'
	data = requests.get(url, params={'query': query, 'format': 'json'}).json()
	flag = 0
	for item in data['results']['bindings']:
		flag = 1
		for var in item :
			print(item[var]['value'])
	return flag
	
def print_answer_count(query):
	answer = ''
	count = 0
	url = 'https://query.wikidata.org/sparql'
	data = requests.get(url, params={'query': query, 'format': 'json'}).json()
	flag = 0
	for item in data['results']['bindings']:
		flag = 1
		for var in item :
			count += 1
			answer = item[var]['value']
			#print(item[var]['value'])
	if count == 1 and answer.isdigit(): # If there is only one answer and it is a number, most likey the answer (like population)
		print(answer)
	elif answer: # print the count of answer if there is one.
		print(count)
	return flag



def create_query(prop, entity):
	query = 'SELECT DISTINCT ?answerLabel WHERE{ wd:%s wdt:%s ?answer. SERVICE wikibase:label{ bd:serviceParam wikibase:language "en".}}' % (entity, prop)
	return query 
	

def get_property_how(question, entity):
	area = ["big", "large", "small"]
	height = ["tall", "big", "high", "low", "short", "far"]
	length = ["long", "short"]
	depth = ["deep"]
	width = ["wide"]
	prop = []
	head = ''
	head_found = False

	# If the words are from the vocabulary, return the corresponding property
	for word in question:
		if word.lemma_ == "how":
			head = word.head
			if head.lemma_ in area:
				prop.append("area")
			elif head.lemma_ in height:
				prop.append("height")
			elif head.lemma_ in length:
				prop.append("length")
			elif head.lemma_ in depth:
				prop.append("vertical")
			elif head.lemma_ in width:
				prop.append("width")
			break
	
	#try with getting entity like state question 
	if not prop:
		prop = get_property_state(question, entity)
		
	#try words that comes before the verb
	if not prop:
		for word in question:
			if word == head:
				head_found = True
			if head_found == True:
				if word.pos_ == "VERB":
					head_found = False
					break
				else:
					prop.append(word.text)
			
	return prop
	
	

def get_property_W_prn(question, entity):
	prop = []
	possible_prop = []
	verb_found = False
	num_ent = len(entity)
	verb_count = 0
	last_verb = ''
	for word in question:
		if word.pos_ == "VERB":
			verb_count += 1
			last_verb = word.lemma_
		
	if verb_count == 1 and last_verb == "be": # questions like "when was ..." or "who is ..."
		for word in question:
			if verb_found == True:
				if num_ent > 0: # if the entity has not appeared in the question, check for it
					# if entity appears, remove so that it doesnt read it as a property by mistake
					if word.text == entity[0]:
						num_ent -= 1
						entity.pop()
						continue
				if word.tag_ == "WDT" or word.tag_ == "WP" or word.tag_ == "WP$": # if wh words are found, end loop
					verb_found = False
					break
				elif word.pos_ == "NOUN": # if noun is found, add the word and previous words that are possibly property to property
					# print("noun")
					while possible_prop:
						prop.append(possible_prop.pop(0))
					prop.append(word.lemma_)
				elif word.pos_ == "VERB" or word.pos_ == "ADJ" or word.pos_ == "ADV" or word.pos_ == "ADP":
					possible_prop.append(word.text)
				elif word.pos_ == "DET": # if the word is a determiner and it is not the first determiner of the property, then add it
					if prop or possible_prop:
						possible_prop.append(word.text)
			elif word.pos_ == "VERB":
				verb_found = True
	
	elif verb_count > 1:
		if last_verb == "found" or last_verb == "form":
			prop.append("inception")
		if last_verb == "locate" or last_verb == "situate":
			prop.append("located in the administrative territorial entity")
	
	if not prop:
		prop.append(last_verb)
	
	print(prop)
	return prop

def get_property_W_det(question, entity):
	prop = []
	possible_prop = []
	noun_found = False
	for word in question:
		if noun_found == True:
			if word.pos_ == "VERB": #only look at words before the verb
				noun_found = False
				break
			elif word.pos_ == "NOUN": # if noun is found, add the word and previous words that are possibly property to property
				while possible_prop:
					prop.append(possible_prop.pop(0))
				prop.append(word.lemma_)
			else:
				possible_prop.append(word.text)
				
		elif word.tag_ == "WDT":
			noun_found = True
				
		elif (word.tag_ == "WP" or word.tag_ == "WP$") and word.head.pos_ == "NOUN": # what ... is ... questions
			noun_found = True
	
	if not prop: #if it was not what ... is ... questions, then it is what is ... of ... question
		return get_property_W_prn(question, entity)
	else:
		return prop


def get_property_state(question, entity):
	prop = []
	last_word = ""
	possible_prop = []
	before_ent = []
	after_ent = []
	num_ent = len(entity)
	det_found = False
	# divide the sentence before and after entity
	for word in question:
		if num_ent == 0:
			after_ent.append(word)
		elif num_ent > 0:
			if word.text != entity[0]:
				before_ent.append(word)
			elif word.text == entity[0]:
				num_ent = num_ent - 1
				entity.pop(0)
	
	print (before_ent)
	print (after_ent)
	
	
	for word in before_ent:
		if det_found == True:
			if word.pos_ == "NOUN":
				while possible_prop:
					prop.append(possible_prop.pop(0))
				prop.append(word.text)
				last_word = word
			else:
				possible_prop.append(word.text)
		if word.pos_ == "DET":
			det_found = True
	
	if prop:
		if last_word.tag_ == "NNS":
			prop[-1] = last_word.lemma_
		return prop
	else:
		det_found = False
		for word in after_ent:
			if det_found == True:
				if word.pos_ == "NOUN":
					while possible_prop:
						prop.append(possible_prop.pop(0))
					prop.append(word.text)
					last_word = word
				else:
					possible_prop.append(word.text)
			if word.pos_ == "DET":
				det_found = True
		
		if not prop:
			return prop
		else:
			if last_word.tag_ == "NNS":
				prop[-1] = last_word.lemma_
			prop.append("of")
			return prop
	
def get_property_count(question, entity):
	prop = []
	possible_prop = []
	noun_found = False
	for word in question:
		if noun_found == True:
			if word.pos_ == "VERB":
				noun_found = False
				break
			elif word.pos_ == "NOUN":
				while possible_prop:
					prop.append(possible_prop.pop(0))
				prop.append(word.lemma_)
			else:
				possible_prop.append(word.text)
				
		elif word.lemma_ == "many":
			noun_found = True
			noun = word.head.pos_

	return prop	


def get_entity_backup(question):
	entity = []
	last_noun = ''
	for word in question:
		if word.pos_ == "NOUN":
			last_noun = word.text
		
	for word in question:
		if word.head.text == last_noun:
			if word.pos_ != "DET" or word.pos_ != "VERB":
				entity.append(word.text)
		elif word.text == last_noun:
			entity.append(word.text)
			break
		
	return entity


def get_entity(question): # find the pronoun from the sentence
	entity = []
	possible_entity = []
	NNP_found = False
	for word in question:
		if word.pos_ == "PROPN":
			NNP_found = True
		if NNP_found == True:
			if word.pos_ == "PROPN":
				while possible_entity:
					entity.append(possible_entity.pop(0))
				entity.append(word.text)
			elif word.head.pos_ == "PROPN":
				possible_entity.append(word.text)
			else:
				break
	if entity:
		return entity
	else:
		return get_entity_backup(question)


def create_and_fire_query(question, question_type):
	url = 'https://www.wikidata.org/w/api.php'
	paramsQ = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json'}
	paramsP = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json', 'type': 'property',}
	
	
	entity = get_entity(question)
	prop = []
	answer_found = 0
	print(entity)
	if not entity: # if entity is empty, cannot find answer
		return 0
	paramsQ['search'] = " ".join(entity)
	json = requests.get(url, paramsQ).json()
	if not json['search']: # if the search of entity is empty, it cannot find answer
		return 0
	for result in json['search']:
		q_id = format(result['id'])
		
		if question_type == 6:
			prop = get_property_how(question, entity)
		if question_type == 5:
			prop = get_property_count(question, entity)
		elif question_type == 4:
			prop = get_property_W_prn(question, entity)
		elif question_type == 3:
			prop = get_property_W_det(question, entity)
		elif question_type == 2:
			prop = get_property_state(question, entity) 
			
			
			
		if not prop: # if property is empty, cannot find answer
			return 0
		print(prop)
		paramsP['search'] = " ".join(prop)
		json = requests.get(url, paramsP).json()
		#print(json['search'])
		for result in json['search']:
			p_id = format(result['id'])
			query = create_query(p_id, q_id)
			if question_type == 5:
				answer_found = print_answer_count(query)
			else:
				answer_found = print_answer(query)
			if answer_found == 1:
				break
			if question_type == 3 and answer_found == 0:
				return create_and_fire_query(question, 4)
		return answer_found
	

def QA(line): 
	for token in line:
		print("\t".join((token.text, token.lemma_, token.pos_, token.tag_, token.dep_, token.head.lemma_)))

	yes_words = ["can","be", "do"]
	h_words = ["how"]
	state_words = ["state", "name", "list", "report"]
	wh_det_words = ["what","which"]
	wh_prn_words = ["who", "where", "when"]
	question_words = ["who", "what", "where", "when", "why", "how", "whose", "which", "whom"]
	
	
	if line[0].lemma_ in yes_words:
		print('Yes or No question')
		return YesOrNoQuestion(line) #yes or no question 
	else:
		for token in line:
			if token.lemma_ in state_words and token.pos_ != "PROPN":
				print('State question')
				return create_and_fire_query(line, 2) # state the X of Y
			elif token.lemma_ in wh_det_words:
				print('Wh determiner question')
				return create_and_fire_query(line, 3) # which city is the X of Y
			elif token.lemma_ in wh_prn_words:
				print('Wh pronoun question')
				return create_and_fire_query(line, 4) # where is the X of Y
			elif token.lemma_ in h_words:
				if token.head.lemma_ == "many":
					print('Count question')
					return create_and_fire_query(line, 5)
				else:
					print('How question')
					return create_and_fire_query(line, 6)
	
			

def main(argv):
	questions = []
	questions.append('Name the capital of Andaman and Nicobar Islands.')
	questions.append('How many countries does the Nile go through?')
	questions.append('State the population of Leeuwarden')
	questions.append('List the timezone of Syria')
	questions.append('What is the motto of South Africa?')
	questions.append('Is Australia a continent?')
	questions.append('How big is the surface of the Sahara Desert? ')
	questions.append('Is Yokohama a sister city of Vancouver?')
	questions.append('Which country is Berlin the capital of?')
	questions.append('Who is the head of state of the United States of America?')
	
	for x in range(0, 10):
		print(questions[x])
	
	for line in sys.stdin:
		line = line.rstrip()
		nlp = spacy.load('en')
		if QA(nlp(line)) == 0:
			print("We could not find the answer")
		print("Ask another question.")


if __name__ == "__main__":
	main(sys.argv)
