'''This script loads volumes described in a "slice" of volume IDs, and corrects
    them using a set of rules both about OCR correction and about tokenization
    (e.g. any thing => anything).

    That work gets done in the Volume module.

    Then the script sends the stream of tokens to the Context modules, for
    contextual spellchecking (spellchecking that's aware of context, and
    can distinguish 'left' from 'lest' depending on the words that follow
    or precede it).

    Corrected clean text and a list of wordcounts are written to the original
    data directory. An errorlog and a record of metadata (e.g. word accuracy)
    are printed to the directory containing slices of volume IDs.
'''

import FileCabinet
import Volume
import Context

# DEFINE CONSTANTS.
delim = '\t'
debug = False
felecterrors = ['fee', 'fea', 'fay', 'fays', 'fame', 'fell', 'funk', 'fold', 'haft', 'fat', 'fix', 'chafe', 'loft']
selecttruths = ['see', 'sea', 'say', 'says', 'same', 'sell', 'sunk', 'sold', 'hast', 'sat', 'six', 'chase', 'lost']
# Of course, either set could be valid. But I expect the second to be more common.
# The comparison is used as a test.

# LOAD PATHS.
slicename = sys.argv[1]

## We assume the slice name has been passed in as an argument.

pathdictionary = FileCabinet.loadpathdictionary('/home/tunder/python/combined/')

datapath = pathdictionary['datapath']
slicepath = pathdictionary['slicepath'] + slicename + '.txt'
metadatapath = pathdictionary['metadatapath']
metaoutpath = pathdictionary['slicepath'] + slicename + 'acc.txt'
errorpath = pathdictionary['slicepath'] + slicename + 'errorlog.txt'
longSpath = pathdictionary['slicepath'] + slicename + 'longS.txt'
       
with open(slicepath, encoding="utf-8") as file:
    HTIDlist = file.readlines()

HTIDs = set()

for thisID in HTIDlist:
    thisID = thisID.rstrip()
    HTIDs.add(thisID)

del HTIDlist

## discard bad volume IDs

with open(metadatapath + "badIDs.txt", encoding = 'utf-8') as file:
    filelines = file.readlines()

for line in filelines:
    line = line.rstrip()
    line = line.split(delim)
    if line[0] in HTIDs:
        HTIDs.discard(line[0])

processedmeta = list()
errorlog = list()
longSfiles = list()
totaladded = dict()
totaldeleted = dict()

for thisID in HTIDs:
    
    filepath, postfix = FileCabinet.pairtreepath(thisID, datapath)
    filename = filepath + postfix + '/' + postfix + ".txt"

    try:
        with open(filename, encoding='utf-8') as file:
            lines = file.readlines()
            successflag = True
    except IOError as e:
        successflag = False

    if not successflag:
        print(thisID + " is missing.")
        errorlog.append(thisID + '\t' + "missing")
        continue
        
    tokens, pre_matched, pre_english = Volume.as_stream(lines, verbose=debug)

    tokencount = len(tokens)
    
    if len(tokens) < 10:
        print(thisID, "has only tokencount", len(tokens))
        errorlog.append(thisID + '\t' + 'short')

    correct_tokens, pages, post_matched, post_english = Volume.correct_stream(tokens, verbose = debug)

    # Combine page dictionaries into a master dictionary.
    # If you ask, why didn't you just produce one in the first place? ...
    # answer has to do with flexibility of the Volume module for other purposes.

    pagecounter = 0
    masterdict = dict()
    for page in pages:
        for item in page:
            if item in masterdict:
                masterdict[item] += page[item]
            else:
                masterdict[item] = page[item]

    # Now that we have a master dictionary, consider whether there are long-s problems.
    # This algorithm works adequately.

    errors = 1
    truths = 1
    # Initialized to 1 as a Laplacian correction.
    
    for word in felecterrors:
        errors = errors + masterdict.get(word, 0)
    for word in selecttruths:
        truths = truths + masterdict.get(word, 0)

    if truths > errors:
        LongSproblem = False
    else:
        LongSproblem = True

    if LongSproblem == False:
        corrected = correct_tokens
        deleted = dict()
        added = dict()
    else:
        longSfiles.append(thisID)
        deleted, added, corrected, changedphrases, unchanged = Context.catch_ambiguities(correct_tokens, debug)

    # Write corrected file.
    outfilename = filepath + postfix + '/' + postfix + ".clean.txt"
    
    with open(outfilename, mode = 'w', encoding = 'utf-8') as file:
        for token in corrected:
            if token != '\n' and not (token.startswith('<') and token.endswith('>')):
                token = token + " "
            file.write(token)

    for word, count in deleted.items():
        masterdict = subtract_counts(word, masterdict, count)
        totaldeleted = add_counts(word, totaldeleted, count)

    for word, count in added.items():
        masterdict = add_counts(word, masterdict, count)
        totaladded = add_counts(word, totaladded, count)
                
    outlist = sorted(masterdict.items(), key = lambda x: x[1], reverse = True)
    
    outfilename = filepath + postfix + '/' + postfix + ".vol.tsv"
    totalwordsinvol = 0
    
    with open(outfilename, mode = 'w', encoding = 'utf-8') as file:
        for item in outlist:
            outline = item[0] + delim + str(item[1]) + '\n'
            file.write(outline)
            totalwordsinvol += item[1]

    metatuple = (thisID, str(totalwordsinvol), str(pre_matched), str(pre_english), str(post_matched), str(post_english))
    processedmeta.append(metatuple)

    if len(processedmeta) > 99:
        with open(metaoutpath, mode = 'a', encoding = 'utf-8') as file:
            for metatuple in processedmeta:
                outlist = [x for x in metatuple]
                outline = delim.join(outlist) + '\n'
                file.write(outline)
        processedmeta = list()

# After all iterations, write anything left in processedmeta.

with open(metaoutpath, mode = 'a', encoding = 'utf-8') as file:
    for metatuple in processedmeta:
        outlist = [x for x in metatuple]
        outline = delim.join(outlist) + '\n'
        file.write(outline)

# Write the errorlog and list of long S files.

if len(errorlog) > 0:
    with open(errorpath, mode = 'w', encoding = 'utf-8') as file:
        for line in errorlog:
            file.write(line + '\n')

if len(longSfiles) > 0:
    with open(longSpath, mode = 'w', encoding = 'utf-8') as file:
        for line in longSfiles:
            file.write(line + '\n')

# Done.


