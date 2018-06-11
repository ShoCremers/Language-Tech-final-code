# written by Kenichi Furursawa (s3204146), Sho Cremers (s3135144), and Sukhleen Kaur (s3157423)
import requests
import sys
import re
import spacy


def print_ans_YesNO (query):
	url_spqrql = 'https://query.wikidata.org/sparql'
	data = requests.get(url_spqrql, params={'query': query,'format': 'json'}).json()
	return data['boolean']
	
def print_answer_no_property(query):
	url = 'https://query.wikidata.org/sparql'
	data = requests.get(url, params={'query': query, 'format': 'json'}).json()
	return data['boolean']

def create_query_YesNO(entity1, prop, entity2):
	query = 'ASK { wd:%s wdt:%s wd:%s . SERVICE wikibase:label{ bd:serviceParam wikibase:language "en".}}' % (entity1, prop, entity2)
	return query
	
def create_query_YesNO_no_property(entity1, entity2):
	query = 'ASK { wd:%s ?property wd:%s . SERVICE wikibase:label{ bd:serviceParam wikibase:language "en".}}' % (entity1, entity2)
	return query
	
	

	
def get_property_yesNo(parse, subj, obj):
	prop = []
	last_word = ''
	for t in parse:
		if t.text not in subj and t.text not in obj:
			if t.pos_ == "NOUN" or t.pos_ == "ADJ" or t.pos_ == "ADV" or (t.pos_ == "VERB" and t != parse[0]):
				last_word = t.text
	
	for t in parse:
		if t.text not in subj and t.text not in obj:
			if t.head.pos_ == "NOUN" and t.head.text == last_word and t.pos_ != "DET": 
				prop.append(t.text)
			elif t.text == last_word:
				prop.append(t.text)
				break
	
	return ' '.join(prop)

def get_subject_yes_no(parse):
	subject = []
	for word in parse:
		if word.head.dep_ == "nsubj" and word.pos_ != "DET":
			subject.append(word.text)
		elif word.dep_ == "nsubj":
			subject.append(word.text)
			break
	
	return ' '.join(subject)
	

def get_object_yes_no(parse, subject):
	obj = ''
	possible_obj = []
	for ent in parse.ents:
		if ent.text != subject:
			obj = ent.text
			
	if not obj:
		for word in parse:
			if word.pos_ == "NOUN":
				last_noun = word.text
		
		for word in parse:
			if word.head.text == last_noun and word.pos_ != "DET":
				possible_obj.append(word.text)
			elif word.text == last_noun:
				possible_obj.append(word.text)
				break
				
		obj = ' '.join(possible_obj)
	
	return obj
	
def YesOrNoQuestion(parse):
	ans = None
	wordSubject = "none"
	wordObject = []
	url = 'https://www.wikidata.org/w/api.php'
	paramsQ = {'action': 'wbsearchentities', 'language': 'en','format': 'json'}
	paramsP = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json', 'type': 'property',}
	
	wordSubject = get_subject_yes_no(parse)
	if wordSubject:	
		paramsQ['search'] = wordSubject
		jsonSubject = requests.get(url, paramsQ).json()
	else:
		print ('NO')
		return 1
	
	for result in jsonSubject['search']:
		subject_id = format(result['id'])
		break
	
	wordObject = get_object_yes_no(parse, wordSubject)
	paramsQ['search'] = wordObject
	jsonObject = requests.get(url, paramsQ).json()
		
	wordProperty = get_property_yesNo(parse, wordSubject, wordObject)
	if wordProperty:
		paramsP['search'] = wordProperty
		jsonProperty = requests.get(url,paramsP).json()

	#print("subject and property and object: ", wordSubject, wordProperty, wordObject)
		
	for result in jsonObject['search']:
		object_id = format(result['id'])
		if not wordProperty:
			query = create_query_YesNO_no_property(subject_id, object_id)
			ans = print_answer_no_property(query)
			if ans:
				print('YES')
				break
		else:
			for result in jsonProperty['search']:
				property_id = format(result['id'])
				#print("subject, property, object: ", subject_id, property_id, object_id)
				query = create_query_YesNO(subject_id,property_id, object_id)
				ans = print_ans_YesNO(query)
				if not ans:
					query = create_query_YesNO(object_id,property_id, subject_id)
					ans = print_ans_YesNO(query)
				if ans:
					print('YES')
					break
			if ans:
				break
			
	if not ans:
		print('NO')	
		
		
	return 1

