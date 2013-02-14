'''
    This module creates and manages a TypeIndex.  It does not have any hard depenencies,
    but its functions do require information that has been processed by the Dictionary
    and TokenGen modules.
'''

def GetAcc(Volume, Lexicon, verbose=False):
    '''
    This method performs a very simple accuracy calculation.  It has been defined apart
    from the other methods to leave open the option to use accuracy calculators from
    other modules.
    '''
    
    match = 0

    if verbose:
        print("Performing simple accuracy test")

    for token in Volume:
        if token.lower() in Lexicon:
            match = match + 1

    score = match / len(Volume)

    if verbose:
        print("\t" + str(match) + " matches found")
        print("\t" + str(score))

    return score

def GetTypes(Volume,discards=list(),verbose=False):
    '''
    This method produces a TypeIndex for a single volume, returning a dictionary
    where each key is a type and each value is that type's total number of occurrences
    in the volume.  Accepts processed list of tokens from TokenGen (Volume) and
    Dictionary (Lexicon) along with optional list of words to discard from TypeIndex
    and debug flag.  By default will process all tokens into a type index.
    '''

    if verbose:
        print("Creating type index for volume")

    types = dict()

### Ignore any types in discards, incremenet occurrences count (if already in index), or
### create a new dict() key if a new type.

    for x in Volume:
        if x in discards:
            continue
        elif x in types:
            types[x] = types[x] + 1
        else:
            types.update({x:1})

    if verbose:
        print(str(len(types)) + " unique types identified")

    return types

def SortIndex(Index,verbose=False,order='total'):
    '''
    Because a dict() is unordered, simply writing it to disk makes it hard to read at a
    glance.  This method turns it into a list and then orders it based on one of the
    three numbers associated with each type.  Accepts a batch-level TypeIndex and optional
    sorting and debug flags.  If no sorting flag is passed, defaults to total number of
    occurrences.
    '''

    if verbose:
        print("Sorting index before writing to disk")

    if order == 'vols':
        y = 1
    elif order == 'acc':
        y = 2
    else:
        y = 0

    indexlist = [x for x in Index.items()]

    return sorted(indexlist, key=lambda x:x[1][y], reverse=True)

def NewMean(old, count, acc):
    '''
    Calculates the new mean accurracy for types already in the batch-level TypeIndex when
    folding in new volumes.  Designed to be its own module in case the formula changes.
    '''
    num = (old[2] * old[0]) + (acc * count)
    den = old[0] + count
    return num / den

def UpdateIndex(Index, NewTypes, VolAcc, verbose=False):
    '''
    This method folds a new volume (NewTypes) into a batch-level TypeIndex (Index).
    It is very similar to the algorithm that produces a volume-level TypeIndex from a
    list of tokens, except that it also incremements volume occurrences (index 1) and
    re-calculates mean accuracy (index 2) for types already in Index.
    '''

    if verbose:
        print("Adding volume to master type index\n")

    for t in NewTypes:
        if t in Index:
            Index[t][0] = Index[t][0] + NewTypes[t]
            Index[t][1] = Index[t][1] + 1
            Index[t][2] = NewMean(Index[t], NewTypes[t],VolAcc)
        else:
            Index.update({t:[NewTypes[t],1,VolAcc]})

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

def WriteIndex(Index, filename, delim='\t', verbose=False):
    '''
    Writes a sorted batch-level TypeIndex to disk.  Requires that filename also be passed,
    but delimiter will default to tab if not specified.
    '''

    if verbose:
        print("Writing index to " + filename)

    with open(filename, mode='w', encoding='utf-8') as file:
        for x in Index:
            file.write(x[0] + delim)
            file.write(str(x[1][0]) + delim)
            file.write(str(x[1][1]) + delim)
            file.write(str(x[1][2]) + '\n')

def ReadIndex(filename, delim='\t', verbose=False):
    '''
    This method reconstructs a batch-level TypeIndex as a dict() with types as keys
    and list of total occurrences, volume occurrences, and mean accuracy as values.
    Running this before processing volumes in a data directory will allow you to use
    a batch-level TypeIndex from a past session.
    '''

    Index = dict()

    if verbose:
        print("Reading index from " + filename)

    with open(filename, encoding='utf-8') as file:
        lines = file.readlines()

    for x in lines:
        typedef = x.split(delim)
        Index.update({typedef[0] : [int(typedef[1]),int(typedef[2]),float(typedef[3])]})

    if verbose:
        print(str(len(Index)) + " types read from " + filename + '\n')

    return Index
