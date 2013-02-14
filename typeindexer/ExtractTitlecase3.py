## Extract Titlecase 3
##
## delete hyphenated forms

delim = '\t'

with open('/Users/tunderwood/Dictionaries/PrecisionDictionary.txt', encoding='utf-8') as file:
    filelines = file.readlines()

dictionary = set()
for line in filelines:
    fields = line.split(delim)
    dictionary.add(fields[0])

with open('/Users/tunderwood/Dictionaries/Gazetteer.txt', encoding='utf-8') as file:
    filelines = file.readlines()

saved = list()

for line in filelines:
    fields = line.split(delim)
    word = fields[0].lower()
    if "-" in fields[0]:
        continue
    if word.endswith("'s") and word[:-2] in dictionary:
        continue
    if word.startswith('av'):
        continue
    for dictitem in dictionary:
        if dictitem.startswith(word) and (len(word) + 1) < len(dictitem):
            print(word)
            break
    else:
        saved.append(line)

filename = '/Users/tunderwood/Dictionaries/Gazetteer2.txt'
with open(filename, mode='w', encoding = 'utf=8') as file:
    for line in saved:
        file.write(line)
