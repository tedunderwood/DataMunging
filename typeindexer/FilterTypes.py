## MakeFilesToProcess
##
## Once typeindexer has managed to get the indexes sorted alphabetically, this
## script can divide them into 1) dictionary words and 2) unmatched words
## needing correction. In the process we get info about the frequency of
## the dictionary words.


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

def WeightedAverage(count1, acc1, count2, acc2):
    average = ((count1 * acc1) + (count2 * acc2)) / (count1 + count2)
    return average

datapath = "/Users/tunderwood/OCR/"

alphabet = '9abcdefghijklmnopqrstuvwxyz'
debug = True
delim = '\t'

maindictionary = set()

AllDictionaries = ['/Users/tunderwood/Dropbox/Hathi/Rules and dictionaries/MainDictionary.txt',
'/Users/tunderwood/Dictionaries/MassiveDictionary.txt',
'/Users/tunderwood/Dictionaries/all-latin-words-list.txt',
'/Users/tunderwood/Dictionaries/Top10kGerman.txt',
'/Users/tunderwood/Dictionaries/Top10kDutch.txt',
'/Users/tunderwood/Dictionaries/FrenchDictionaryUTF8.txt']

for filename in AllDictionaries:
    with open(filename, encoding='utf-8') as file:
        filelines = file.readlines()

    for line in filelines:
        line = line.rstrip()
        fields = line.split('\t')
        maindictionary.add(fields[0].lower())

dictlist = list()

for letter in alphabet:
    forms = dict()
    filename = datapath + letter + ".txt"
    index = TypeIndex.ReadIndex(filename, delim, debug)
    for word in index:
        lowerword = word.lower()
        count = index[word][0]
        vols = index[word][1]
        accuracy = index[word][2]
        if word[0].isupper() and word[-1].islower():
            titlecase = True
        else:
            titlecase = False
        if word.isupper() or word.islower():
            homogenouscase = True
        else:
            homogenouscase = False
        if (titlecase or homogenouscase) and (lowerword in forms):
            entry = forms[lowerword]
            if homogenouscase:
                entry[0] = entry[0] + count
            if titlecase:
                entry[4] = entry[4] + count
            entry[1] = entry[1] + vols
            entry[2] = WeightedAverage(entry[0], entry[2], count, accuracy)
            entry[3] = (entry[4] + 1) / (entry[0] + 1)
            ## odds of being titlecase
            forms[lowerword] = entry
            ## The four elements of this tuple are, first, the count of homogenouscased forms,
            ## then the total number of vols(all forms), then the accuracy(all forms), then
            ## the ratio titlecased/homogenouscased, then finally the count of titlecased forms.
            
        elif titlecase:
            forms[lowerword] = [0, vols, accuracy, count, count]
        elif homogenouscase:
            forms[lowerword] = [count, vols, accuracy, (1/count), 0]
            
        if (titlecase == False and homogenouscase == False):
            forms[word] = [count, vols, accuracy, 0, 0]

    outlist = list()
    for word in forms:
        if word in maindictionary:
            dictuple = (word, forms[word][1], forms[word][3])
            dictlist.append(dictuple)
            continue
            # for dictionary words we save the volume count, and odds of being titlecased
            
        fuseword = word.replace('-', '')
        fuseword = word.replace("'", '')
        fuseword = word.replace('.', '')
        if fuseword in maindictionary:
            continue
            # we ignore things that are easy to fix, by fusing
            
        if "-" in word:
            match = True
            splitwords = word.split("-")
            for token in splitwords:
                if token.lower() not in maindictionary:
                    match = False
            if match:
                continue
                # and things that are easy to match, by splitting

        outtuple = (word, forms[word][0], forms[word][1], forms[word][2], forms[word][3])
        outlist.append(outtuple)

    filename = datapath + 'filtered/' + letter + '.txt'
    
    outlist = sorted(outlist, key = lambda item: item[1], reverse = True)
    
    with open(filename, mode='w', encoding='utf-8') as file:
        for outtuple in outlist:
            if outtuple[1] < 5:
                continue
            outstrings = [str(x) for x in outtuple]
            outline = delim.join(outstrings) + '\n'
            file.write(outline)

print('Done with alphabet. Now printing dictionary.')

dictlist = sorted(dictlist, key = lambda item: item[1], reverse = True)
filename = datapath + 'filtered/maindict.txt'
with open(filename, mode='w', encoding='utf-8') as file:
    for outtuple in dictlist:
            outstrings = [str(x) for x in outtuple]
            outline = delim.join(outstrings) + '\n'
            file.write(outline)
                
            

    

    
            
            
            
            

print('Done.')
