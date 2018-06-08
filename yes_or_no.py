# written by Kenichi Furursawa (s3204146), Sho Cremers (s3135144), and Sukhleen Kaur (s3157423)
import requests
import sys
import re
import spacy


def print_ans_YesNO (query):
    url_spqrql = 'https://query.wikidata.org/sparql'
    data = requests.get(url_spqrql, params={'query': query,'format': 'json'}).json()
    return data['boolean']


def create_query_YesNO(entity1, prop, entity2):
    query = 'ASK { wd:%s wdt:%s wd:%s . SERVICE wikibase:label{ bd:serviceParam wikibase:language "en".}}' % (entity1, prop, entity2)
    return query

def get_property_yesNo(parse, object):
    prop = []
    for t in parse:
        if (t.dep_ == "attr" or t.pos_ == "NOUN") and (t.dep_ != "dobj" and t.dep_ != "pobj") and t.text != object :
            for d in t.subtree:
                if (d.dep_ == "attr" or d.pos_ == "NOUN") and (d.dep_ != "dobj" and d.dep_ != "pobj"):
                    prop.append(d.text)
                    print("APPENDED PROPERTY LIST = ", d.text)
        if not prop :
            if t.dep_ == "prep":
                prop.append(t.text)

    if prop == object:
        prop = "instance of"

    return prop


def YesOrNoQuestion(parse):
    wordSubject = "none"
    wordObject = []
    url = 'https://www.wikidata.org/w/api.php'
    paramsQ = {'action': 'wbsearchentities', 'language': 'en',
               'format': 'json'}
    paramsP = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json', 'type': 'property',}

    for ent in parse.ents:
        wordSubject = ent.text

    wordProperty = get_property_yesNo(parse, wordSubject)
    for token in parse:
        if token.tag_== "NNP" and token.text != wordSubject and token.text!=wordProperty:
            wordObject.append(token.text)
        if token.tag_ =="NN" and token.text!= wordProperty and wordObject==[]:
            wordObject.append(token.text)


    Object = ' '.join(wordObject) #make list into string
    if wordProperty==wordObject:
        wordProperty = "instance of"

    paramsP['search'] = wordProperty
    jsonProperty = requests.get(url,paramsP).json()

    paramsQ['search'] = Object
    jsonObject = requests.get(url, paramsQ).json()

    for result in jsonObject['search']:
        subject_id = format(result['id'])
        break
    for result in jsonProperty['search']:
        property_id = format(result['id'])
        break

    print(wordProperty, wordSubject, wordObject)

    paramsQ['search'] = wordSubject
    jsonSubject = requests.get(url, paramsQ).json()

    for result in jsonSubject['search']:
        object_id = format(result['id'])
        query = create_query_YesNO(object_id,property_id, subject_id)
        if print_ans_YesNO(query):
            print('YES')
            break
        else:
            print('NO')
            break
