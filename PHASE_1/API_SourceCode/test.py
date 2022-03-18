import json
from nltk import sent_tokenize


def UniqueDisease(data,sentence, word):
  DiseaseList = []
  for disease in data: 
    if disease["name"].lower() in sentence.lower() and disease["name"].lower() != word.lower():
      DiseaseList.append(disease["name"])
  return DiseaseList


def HowManyReports(text):
  sentences = sent_tokenize(text)
  print(sentences)
  DiseaseList = {}
  Uncertainty = ["or", "to be confirmed", "uncertain", "possibly",]
  ExclusionList = ["similar to", "same as", "identical", "parallel", "the same as", "resembling"]
  ProcessedDiseases = []
  f = open("disease_list.json","r") 
  data = json.load(f)
  for word in data:
    if word in ProcessedDiseases:
        continue
    for sentence in sentences:
      for similarity in ExclusionList:
        sentence = sentence.lower()
        if similarity in sentence:
          safe, ignore = sentence.split(similarity)
          if word["name"].lower() in ignore:
            continue
          elif word["name"] in safe and word['name'] not in ProcessedDiseases:
            DiseaseList[word["name"]] = [word['name']]
            ProcessedDiseases.append(word["name"])
            break
            
      if word['name'].lower() in sentence.lower() and word['name'] not in ProcessedDiseases:  
        if len(UniqueDisease(data, sentence, word['name'])) == 0:
            DiseaseList[word["name"]] = [word["name"]]
            ProcessedDiseases.append(word["name"])
            print(word["name"])
            break
        else: 
          for disease in UniqueDisease(data, sentence, word['name']):
            if disease in ProcessedDiseases and disease in DiseaseList.keys() and word["name"] not in DiseaseList[disease]:
              DiseaseList[disease].append(word['name'])
              ProcessedDiseases.append(word['name'])
              print(word["name"])
              break
            
          if any(word in sentence.lower() for word in Uncertainty):
            DiseaseList[word["name"]] = UniqueDisease(data, sentence, word['name'])
            DiseaseList[word["name"]].append(word["name"])
            for disease in DiseaseList[word["name"]]:
                ProcessedDiseases.append(disease)
            break
          else:
            print(word["name"])
            DiseaseList[word["name"]] = [word['name']]
            ProcessedDiseases.append(word["name"])
            break
  print(DiseaseList)
  return DiseaseList
text = "This is COVID-19 and this is SARS."
HowManyReports(text)