import sys
import requests as req
import spacy

def print_questions(questions):
    for string in questions:
        print (string)
        

        
def print_result(query):
    url_spqrql = 'https://query.wikidata.org/sparql'
    response = req.get(url_spqrql, params={'query': query,'format': 'json'}).json()
    for item in response['results']['bindings']:
        for var in item:
                print (item[var]['value'])
        return True
    return False

def build_query(prop, entity):
    query = 'SELECT DISTINCT ?countryLabel WHERE{ wd:%s wdt:%s ?country. SERVICE wikibase:label{ bd:serviceParam wikibase:language "en".}}' % (entity, prop)
    return query 


def find_X(sentence):
  X = []
  nnFound = False
  nnCount = 0
  for word in sentence:
    if ((word.tag_ == "NN"  or word.tag_ == "NNS" or  word.tag_ == "VBG" or word.tag_ == "JJ"  or word.tag_ == "JJS") and (word.dep_ != "ROOT")):
      X.append(word.text)
      if(word.tag_ == "NN"):
        nnCount += 1
    if(nnCount ==1 and word.tag_ == "IN"):
         X.append(word.text)
  #remove last element if it is of:
  if(X[len(X)-1] == "of"):
    X.pop()
  return " ".join(X)

def find_Y(sentence):
  Y = []
  for word in sentence:
    if (word.tag_ == "NNP"):
      Y.append(word.text)
  return " ".join(Y)
  

def build_and_run_query(line):
    url = 'https://www.wikidata.org/w/api.php'
    paramsQ = {'action': 'wbsearchentities', 'language': 'en',
               'format': 'json'}
    paramsP = {
        'action': 'wbsearchentities',
        'language': 'en',
        'format': 'json',
        'type': 'property',
        }
    en_nlp = spacy.load('en_core_web_md')

    X = find_X(en_nlp(line))
    Y = find_Y(en_nlp(line))
    paramsP['search'] = X 
    paramsQ['search'] = Y

    jsonP = req.get(url, paramsP).json()
    jsonQ = req.get(url, paramsQ).json()

    for result in jsonP['search']:
        prop = format(result['id'])
        paramsQ['search'] = Y
        for result in jsonQ['search']:
            entity = format(result['id'])
            query = build_query(prop, entity)
            if print_result(query) == True:
                return True 
    return False

def main(argv):

    questions = [
        "Name the capital of Denmark.",
        "List the tributary of Jhelum River.",
        "What is the height of Azure Window?",
        "Who is the head of state of USA?",
        "Name the national anthem of Spain.",
        "State the capital of Karnataka.",
        "What is the internet domain of Antarctica?",
        "What is the driving side of South Africa?",
        "State the currency of Greenland.",
        "What is the marriageable age of Colombia?"]
    print_questions(questions)
    
    for question in sys.stdin:
        #remove duplicate spaces if any
        question = " ".join(question.split())
        found = build_and_run_query(question)
        if found == False:
            print ("No answer found")
        print ('Next Question')

if __name__ == '__main__':
    main(sys.argv)
