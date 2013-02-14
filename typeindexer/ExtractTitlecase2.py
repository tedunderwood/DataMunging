## Extract Titlecase 2
##
## Working with the list of forms extracted by ExtractTitlecase.py,
## produce a filtered list of ones that are
## not in PrecisionDictionary.txt
## but meet a list of probability criteria, including
## # of vols they appear in
## average OCR quality of those vols
## and proportion of time they're titlecased.

delim = '\t'

with open('/Users/tunderwood/Dictionaries/PrecisionDictionary.txt', encoding='utf-8') as file:
    filelines = file.readlines()

dictionary = set()
for line in filelines:
    fields = line.split(delim)
    dictionary.add(fields[0])

gazetteer = list()
for counter in range(0,4):
    with open('/Users/tunderwood/OCR/Titles' + str(counter) + '.txt', encoding='utf-8') as file:
        filelines = file.readlines()

    for line in filelines:
        line = line.rstrip()
        fields = line.split(delim)
        word = fields[0]
        if word.lower() in dictionary or word in dictionary:
            continue
        vols = int(fields[2])
        accuracy = float(fields[3])
        titleratio = float(fields[7])
        if titleratio < 3:
            continue
        if vols < 4000:
            continue
        if accuracy < 0.875:
            continue
        
        newtuple = (word, vols, titleratio)
        gazetteer.append(newtuple)

gazetteer = sorted(gazetteer, key = lambda item: item[1], reverse = True)

filename = '/Users/tunderwood/Dictionaries/Gazetteer.txt'
with open(filename, mode='w', encoding = 'utf=8') as file:
    for outtuple in gazetteer:
        outstrings = [str(x) for x in outtuple]
        outline = delim.join(outstrings) + '\n'
        file.write(outline)
