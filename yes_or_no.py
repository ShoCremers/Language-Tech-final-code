# written by Kenichi Furursawa (s3204146), Sho Cremers (s3135144), and Sukhleen Kaur (s3157423)
import requests
import sys
import re
import spacy


def print_ans_YesNo (query):
	url_spqrql = 'https://query.wikidata.org/sparql'
	data = requests.get(url_spqrql, params={'query': query,'format': 'json'}).json()
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
	for t in parse: # find the last word that is not object nor subject
		if t.text not in subj and t.text not in obj:
			if t.pos_ == "NOUN" or t.pos_ == "ADJ" or t.pos_ == "ADV" or (t.pos_ == "VERB" and t != parse[0]):
				last_word = t.text
	
	for t in parse: # include the last word found and words that their head is the last word.
		if t.text not in subj and t.text not in obj:
			if t.head.pos_ == "NOUN" and t.head.text == last_word and t.pos_ != "DET": 
				prop.append(t.text)
			elif t.text == last_word:
				prop.append(t.text)
				break
	
	return ' '.join(prop)

def get_subject_yes_no(parse):
	subject = []
	for word in parse: # include the words that are identified as nsubj (subject)
		if word.head.dep_ == "nsubj" and word.pos_ != "DET":
			subject.append(word.text)
		elif word.dep_ == "nsubj":
			subject.append(word.text)
			break
	
	return ' '.join(subject)
	

def get_object_yes_no(parse, subject):
	obj = ''
	possible_obj = []
	for ent in parse.ents: # find entities that are not subject
		if ent.text != subject:
			obj = ent.text
			
	if not obj: # if object was not found from entities, find the last noun
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
	url = 'https://www.wikidata.org/w/api.php'
	paramsQ = {'action': 'wbsearchentities', 'language': 'en','format': 'json'}
	paramsP = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json', 'type': 'property',}
	
	wordSubject = get_subject_yes_no(parse)
	if wordSubject:	
		paramsQ['search'] = wordSubject
		jsonSubject = requests.get(url, paramsQ).json()
	else: # if subject cannot be found for some reason, answer No and end
		print ('NO')
		return 1
	
	for result in jsonSubject['search']:
		subject_id = format(result['id'])
		break
	
	wordObject = get_object_yes_no(parse, wordSubject)
	if wordObject:	
		paramsQ['search'] = wordObject
		jsonObject = requests.get(url, paramsQ).json()
	else: # if object cannot be found for some reason, answer No and end
		print ('NO')
		return 1
		
	wordProperty = get_property_yesNo(parse, wordSubject, wordObject)
	if wordProperty:
		paramsP['search'] = wordProperty
		jsonProperty = requests.get(url,paramsP).json()
		
	for result in jsonObject['search']:
		object_id = format(result['id'])
		if not wordProperty: # If there is no property, check if object occurs in the subject's page
			query = create_query_YesNO_no_property(subject_id, object_id)
			ans = print_ans_YesNo(query)
			if ans:
				print('YES')
				break
		else:
			for result in jsonProperty['search']:
				property_id = format(result['id'])
				query = create_query_YesNO(subject_id,property_id, object_id)
				ans = print_ans_YesNo(query)
				if not ans: # if anser is No, check with object as subject, and vice versa
					query = create_query_YesNO(object_id,property_id, subject_id)
					ans = print_ans_YesNo(query)
				if ans:
					print('YES')
					break
			if ans:
				break
			
	if not ans:
		print('NO')	
		
		
	return 1
