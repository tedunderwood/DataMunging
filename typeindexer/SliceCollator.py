import TypeIndex

def MergeIndexes(IndexA, IndexB, verbose=False):
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
outputpath = "/projects/ichass/usesofscale/ocr/"

collated = dict()
debug = True
delim = '\t'

for counter in range(0, 23):
    indexname = datapath + "slice" + str(counter) + "IND.txt"
    NewIndex = TypeIndex.ReadIndex(indexname, delim, debug)
    collated = MergeIndexes(collated, NewIndex, debug)
    print("Merged index# ", counter)

SortedIndex = list()
SortedIndex = TypeIndex.SortIndex(collated, debug)

TypeIndex.WriteIndex(SortedIndex, outputpath + "MasterIndex.txt", delim, debug)

print("Done.")

