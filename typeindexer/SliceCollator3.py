import TypeIndex
import os

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

datapath = "/projects/ichass/usesofscale/ocr/slices/"
outputpath = "/projects/ichass/usesofscale/ocr/index/"

alphabet = 'abcdefghijklmnopqrstuvwxyz'
debug = True
delim = '\t'
NewPieces = dict()

filelist = ["slice0IND.txt", "slice10IND.txt"]
counter = 0

for counter in range(0, 10):
    indexname = datapath + "slice" + str(counter) + "IND.txt"
    with open(indexname, mode='r', encoding='utf-8') as slicefile:
        filelines = slicefile.readlines()
    SliceIndex = list()
    for line in filelines:
        line = line.rstrip()
        words = line.split(delim)
        SliceIndex.append((words[0], int(words[1]), int(words[2]), float(words[3])))

    del filelines
    SliceIndex = sorted(SliceIndex, key = lambda row: row[0].lower())
    print("Sort complete.")

    for letter in alphabet:
        NewPieces[letter] = dict()
                          
    currentletter = 'a'
    for row in SliceIndex:
        if currentletter < row[0][0].lower() and currentletter != 'z':
            for letter in alphabet:
                if row[0][0].lower() <= letter:
                    print(letter)
                    break
            currentletter = letter
        NewPieces[currentletter][row[0]] = row[1:4]

    del SliceIndex

    for letter in alphabet:
        existingfile = outputpath + letter + ".txt"
        if os.path.isfile(existingfile):
            AlphabeticSegment = TypeIndex.ReadIndex(existingfile, delim, debug)
        else:
            AlphabeticSegment = dict()
            
        collated = MergeIndexes(AlphabeticSegment, NewPieces[letter], debug)
        del AlphabeticSegment

        with open(existingfile, mode = 'w', encoding = 'utf-8') as outfile:
            for x in collated:
                outfile.write(x + delim)
                outfile.write(str(collated[x][0]) + delim)
                outfile.write(str(collated[x][1]) + delim)
                outfile.write(str(collated[x][2]) + '\n')               
        
        print("Merged index# ", counter, " letter ", letter)

print("Done.")

