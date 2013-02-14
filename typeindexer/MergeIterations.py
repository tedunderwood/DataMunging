## MergeIterations.
##
## This is highly kludgy. Basically, I couldn't index my whole 500,000-volume dataset at once go, because
## the index doesn't fit in memory. So I improvised, by a) dividing the volumes into groups and indexing
## each group, then b) splitting the results into alphabetical segments. I needed alphabetical order
## because I want to pair upper- and lower-case forms to compare that ratio. But I still couldn't fit
## all of each letter segment into one iteration (eight hour wallclock limit) soooo ... I've got three
## different sets of alphabetically coded files out there! Need to merge those.


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

datapath = "/projects/ichass/usesofscale/ocr/index/"
outputpath = "/projects/ichass/usesofscale/ocr/abbrevindex/"

alphabet = '9abcdefghijklmnopqrstuvwxyz'
debug = True
delim = '\t'

for letter in alphabet:
    index = dict()
    for i in range(0,3):
        if i == 0:
            suffix = ""
        else:
            suffix = str(i)
        print(letter + suffix)
        filename = datapath + letter + suffix + ".txt"
        newindex = TypeIndex.ReadIndex(filename, delim, debug)
        index = MergeIndexes(index, newindex, debug)

    outfile = outputpath + letter + ".txt"
    with open(outfile, mode='w', encoding = 'utf-8') as file:
        
        for word in index:
            fields = index[word]
            if fields[0] < 3:
                continue
            else:
                file.write(word + delim)
                file.write(str(fields[0]) + delim)
                file.write(str(fields[1]) + delim)
                file.write(str(fields[2]) + '\n')

print('Done.')
