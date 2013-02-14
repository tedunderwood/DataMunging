## Extract Titlecases
##
## Goes through a bunch of standard-format indexes and extracts the titlecased terms,
## creating a new set of files cont


import TypeIndex

def MergeIndexes(IndexA, IndexB, verbose = False):
    '''
    This method merges two indexes that already have volacc figures associated with them,
    computing a weighted average of the volume accuracies and adding B to A.
    Okay, I know, the plural is indices. Whatever.
    '''

    for t in IndexB:
        
        if t in IndexA:
            IndexA[t][0] = IndexA[t][0] + IndexB[t][0]
            IndexA[t][1] = IndexA[t][1] + IndexB[t][1]
            IndexA[t][2] = ((IndexA[t][0] * IndexA[t][2]) + (IndexB[t][0] * IndexB[t][2])) / (IndexA[t][0] + IndexB[t][0])
        else:
            IndexA.update({t:[IndexB[t][0], IndexB[t][1], IndexB[t][2]]})

    return IndexA

datapath = "/Users/tunderwood/OCR/"

alphabet = 'abcdefghijklmnopqrstuvwxyz'
debug = True
delim = '\t'

filecounter = 0
linecounter = 0

for letter in alphabet:
    titles = dict()
    filename = datapath + letter + ".txt"
    index = TypeIndex.ReadIndex(filename, delim, debug)
    for word in index:
        if word[0].isupper() and word[-1].islower():
            titleword = word.capitalize()
            if titleword in titles and word != titleword:
                titles[titleword][0] = titles[titleword][0] + index[word][0]
                titles[titleword][1] = titles[titleword][1] + index[word][1]
                titles[titleword][2] = ((titles[titleword][0] * titles[titleword][2]) + (index[word][0] * index[word][2])) / (titles[titleword][0] + index[word][0])
            else:
                titles.update({titleword:[index[word][0], index[word][1], index[word][2]]})

    outlist = list()
    for word in titles:
        lowerword = word.lower()
        if lowerword in index:
            line = [word, titles[word][0], titles[word][1], titles[word][2], index[lowerword][0], index[lowerword][1], index[lowerword][2], (titles[word][0]/index[lowerword][0])]
        else:
            line = [word, titles[word][0], titles[word][1], titles[word][2], 0, 0, 0, titles[word][0]]
        outlist.append(line)

    outlist = sorted(outlist, key = lambda item: item[7], reverse = True)
    linecounter = linecounter + len(outlist)

    if linecounter > 5000000:
        linecounter = 0
        filecounter = filecounter + 1

    outfile = datapath + "Titles" + str(filecounter) + '.txt'
    with open(outfile, mode='a', encoding='utf-8') as file:
        for fieldset in outlist:
            line = ""
            fieldidx = 0
            for field in fieldset:
                line = line + str(field)
                fieldidx = fieldidx + 1
                if fieldidx < 8:
                    line = line + delim
                else:
                    line = line + '\n'
            file.write(line)
    
                
            

    

    
            
            
            
            

print('Done.')
