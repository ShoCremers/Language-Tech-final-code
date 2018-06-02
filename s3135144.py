import requests
import sys
import re
import spacy

def print_answer(query):
	url = 'https://query.wikidata.org/sparql'
	data = requests.get(url, params={'query': query, 'format': 'json'}).json()
	flag = 0
	for item in data['results']['bindings']:
		flag = 1
		for var in item :
			print(item[var]['value'])
	return flag

def print_ans_YesNO (query):
	url_spqrql = 'https://query.wikidata.org/sparql'
	data = requests.get(url_spqrql, params={'query': query,'format': 'json'}).json()
	return data['boolean']

def create_query(prop, entity):
	query = 'SELECT DISTINCT ?answerLabel WHERE{ wd:%s wdt:%s ?answer. SERVICE wikibase:label{ bd:serviceParam wikibase:language "en".}}' % (entity, prop)
	return query 
	
	
def create_query_YesNO(prop, entity):
	query = 'ASK { wd:%s wdt:P31 wd:%s . SERVICE wikibase:label{ bd:serviceParam wikibase:language "en".}}' % (prop, entity)
	return query 
	


def selectQuestion (parse):
	for token in parse:
		print("\t".join((token.text, token.lemma_, token.pos_, token.tag_, token.dep_, token.head.lemma_)))

	yesWords = ["can", "could", "would", "is", "does", "has", "was", "were", "had", "have", "did", "are", "will",'be']
	questionWords = ["who", "what", "where", "when", "why", "how", "whose", "which", "whom"]
	
	for token in parse:
		if token.lemma_ in yesWords: #check if this is a simple YesOrNo question 
			print('Yes or No question')
			return 1
		else:
			print('other type of question')
			return 2


def YesOrNoQuestion(parse):
	wordQ = "none"
	wordP = [] 

	for ent in parse.ents: 
		wordQ = ent.text
	
	for token in parse: 
		if token.tag_ =="NN": 
			wordP.append(token.text)
			print(token.text)
	
	url = 'https://www.wikidata.org/w/api.php'
	paramsQ = {'action': 'wbsearchentities', 'language': 'en',
               'format': 'json'}
 
	P = ' '.join(wordP) #make list into string 
	
	paramsQ['search'] =P
	jsonP = requests.get(url, paramsQ).json()
	
	for result in jsonP['search']:
		q_id = format(result['id'])
		break 
	paramsQ['search'] = wordQ
	jsonQ = requests.get(url, paramsQ).json()
		
	for result in jsonQ['search']:
		p_id = format(result['id'])
		query = create_query_YesNO(p_id,q_id)
		if print_ans_YesNO(query): 
			print('YES')
			break
		else:
			print('NO')
			break 



def get_property(question, entity):
	prop = []
	last_word = ""
	possible_prop = []
	before_ent = []
	after_ent = []
	num_ent = len(entity)
	det_found = False
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
	
	
	

def get_entity(question):
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
			else:
				possible_entity.append(word.text)
	return entity
			


def create_and_fire_query(question):
	url = 'https://www.wikidata.org/w/api.php'
	paramsQ = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json'}
	paramsP = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json', 'type': 'property',}
	
	
	entity = get_entity(question)
	if not entity: # if entity is empty, cannot find answer
		return 0
	paramsQ['search'] = " ".join(entity)
	json = requests.get(url, paramsQ).json()
	if not json['search']: # if the search of entity is empty, it cannot find answer
		return 0
	for result in json['search']:
		q_id = format(result['id'])
		prop = get_property(question, entity)
		if not prop: # if property is empty, cannot find answer
			return 0
		print(prop)
		paramsP['search'] = " ".join(prop)
		json = requests.get(url, paramsP).json()
		for result in json['search']:
			p_id = format(result['id'])
			query = create_query(p_id, q_id)
			return print_answer(query)
	

def QA(line): 
	ques_type = selectQuestion(line) # question type is selected, returns 1, 2 
	
	if ques_type == 1: #yes or no question 
		YesOrNoQuestion(line)
		return 1 
	else: 
		return create_and_fire_query(line) # what is the X of Y 
			

def main(argv):
	questions = []
	questions.append('Name the capital of Andaman and Nicobar Islands.')
	questions.append('What is the currency of France?')
	questions.append('State the population of Leeuwarden')
	questions.append('List the timezone of Syria')
	questions.append('What is the motto of South Africa?')
	questions.append('What is the internet domain of Antarctica?')
	questions.append('What is the area of Japan?')
	questions.append('What are the sister cities of Vancouver?')
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
