'''Revised third-generation OCR normalizer.
    This was rewritten heavily in fall 2013 to ensure that it keeps
    punctuation. It was then adjusted in Spring 2014 to use the original
    HathiTrust zipfiles instead of text files as a source.

    This script loads volumes described in a "slice" of volume IDs, and corrects
    them using a set of rules both about OCR correction and about tokenization
    (e.g. any thing => anything).

    That work gets done in the Volume module.

    Then the script sends the stream of tokens to the Context modules, for
    contextual spellchecking (spellchecking that's aware of context, and
    can distinguish 'left' from 'lest' depending on the words that follow
    or precede it).

    Corrected clean text and a list of wordcounts *by page* are written to the original
    data directory. An errorlog and a record of metadata (e.g. word accuracy)
    are printed to the directory containing slices of volume IDs.

    This version of the OCR normalizer calls NormalizeVolume, a module based
    on the old "Volume" module, but now adjusted so that it does a better job
    of handling punctuation and more importantly so that it registers words whether
    or not they are in the English dictionary. It also aggregates certain *classes*
    of tokens under a class name like romannumeral, arabic2digit, personalname or
    propernoun. Finally it produces a collection of "pagedata" dictionaries that include
    structural_features like #lines, # of capitalized lines, # of repeated initial letters,
    etc. These structural features are distinguished from token counts with an initial
    hashtag.
'''

import FileCabinet
import NormalizeVolume
import Context
import os, sys
from zipfile import ZipFile

testrun = True
# Setting this flag to "true" allows me to run the script on a local machine instead of
# the campus cluster.

# DEFINE CONSTANTS.
delim = '\t'
debug = False
felecterrors = ['fee', 'fea', 'fay', 'fays', 'fame', 'fell', 'funk', 'fold', 'haft', 'fat', 'fix', 'chafe', 'loft']
selecttruths = ['see', 'sea', 'say', 'says', 'same', 'sell', 'sunk', 'sold', 'hast', 'sat', 'six', 'chase', 'lost']
# Of course, either set could be valid. But I expect the second to be more common.
# The comparison is used as a test.

# Define a useful function

def subtract_counts (token, adict, tosubtract):
    global errorlog, thisID
    if token in adict:
        adict[token] = adict[token] - tosubtract
        if adict[token] < 0:
            del adict[token]
        elif adict[token] < 1:
            del adict[token]
    return adict

def add_counts (token, adict, toadd):
    if token in adict:
        adict[token] = adict[token] + toadd
    else:
        adict[token] = toadd
    return adict

def clean_pairtree(htid):
    period = htid.find('.')
    prefix = htid[0:period]
    postfix = htid[(period+1): ]
    if ':' in postfix:
        postfix = postfix.replace(':','+')
        postfix = postfix.replace('/','=')
    cleanname = prefix + "." + postfix
    return cleanname

# LOAD PATHS.


## We assume the slice name has been passed in as an argument.
slicename = sys.argv[1]

# This is most important when running on the cluster, where files are stored in a pairtree
# structure and the only way to know which files we're processing is to list HTIDS in a
# "slice" file defining a slice of the collection.

# When we're running on a local machine, I usually just group files to be processed in a
# directory, and create a list of files to process by listing files in that directory.
# However, it's still necessary to have a slicename and slicepath, because these get
# used to generate a path for an errorlog and list of long S files.

if not testrun:
    pathdictionary = FileCabinet.loadpathdictionary('/home/tunder/python/normalize/PathDictionary.txt')
if testrun:
    pathdictionary = FileCabinet.loadpathdictionary('/Users/tunder/Dropbox/PythonScripts/workflow/PathDictionary.txt')

datapath = pathdictionary['datapath']
metadatapath = pathdictionary['metadatapath']
metaoutpath = pathdictionary['metaoutpath']
outpath = pathdictionary['outpath']
# only relevant if testrun == True

slicepath = pathdictionary['slicepath'] + slicename + '.txt'
errorpath = pathdictionary['slicepath'] + slicename + 'errorlog.txt'
longSpath = pathdictionary['slicepath'] + slicename + 'longS.txt'
headeroutpath = outpath + "headers.txt"

HTIDs = set()

if testrun:
    filelist = os.listdir(datapath)
    for afilename in filelist:
        if not (afilename.startswith(".") or afilename.startswith("_")):
            HTIDs.add(afilename)

else:
    with open(slicepath, encoding="utf-8") as file:
        HTIDlist = file.readlines()

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

# We define two different IO functions, for zip files and regular text files.
# The decision between them is defined by the extension on the filename;
# each function encapulates error-handling and returns a successflag that
# reports error status.

def read_zip(filepath):
    pagelist = list()
    try:
        with ZipFile(file = filepath, mode='r') as zf:
            for member in zf.infolist():
                pathparts = member.filename.split("/")
                suffix = pathparts[1]
                if "_" in suffix:
                    segments = suffix.split("_")
                    page = segments[-1][0:-4]
                else:
                    page = suffix[0:-4]

                if len(page) > 0 and page[0].isdigit():
                    numericpage = True
                else:
                    if len(page) > 0 and page!="notes" and page!="pagedata":
                        print("Non-numeric pagecode: " + page)
                    numericpage = False

                if not member.filename.endswith('/') and not member.filename.endswith("_Store") and not member.filename.startswith("_") and numericpage:
                    datafile = zf.open(member, mode='r')
                    linelist = [x.decode(encoding="UTF-8") for x in datafile.readlines()]
                    pagelist.append((page, linelist))

        pagelist.sort()
        pagecount = len(pagelist)
        if pagecount > 0:
            successflag = "success"
            pagelist = [x[1] for x in pagelist]
        else:
            successflag = "missing file"

    except IOError as e:
        successflag = "missing file"

    return pagelist, successflag

def read_txt(filepath):
    pagelist = list()
    try:
        with open(filepath, mode='r', encoding='utf-8') as f:
            filelines = f.readlines()

        page = list()
        for line in filelines:

            if line.startswith("<pb>"):
                pagelist.append(page)
                page = list()
            else:
                page.append(line)

        # You might assume that we would now need pagelist.append(page)
        # To catch the final page. But in practice the text files we are
        # likely to ingest have a <pb> at the bottom of *every* page,
        # even the last one. So no final append is needed.

        successflag = "success"

    except IOError as e:
        successflag = "missing file"

    return pagelist, successflag


processedmeta = list()
errorlog = list()
longSfiles = list()
totaladded = dict()
totaldeleted = dict()

# If the metadatafile doesn't exist yet,
# write header.

if not os.path.isfile(metaoutpath):
    with open(metaoutpath, 'w', encoding = 'utf-8') as f:
        f.write("volID\ttotalwords\tprematched\tpreenglish\tpostmatched\tpostenglish\n")
print(len(HTIDs))
progressctr = 0

for thisID in HTIDs:

    progressctr += 1
    if not testrun:
        filepath, postfix = FileCabinet.pairtreepath(thisID, datapath)
        filename = filepath + postfix + '/' + postfix + ".zip"
    else:
        filename = datapath + thisID

    if filename.endswith('.zip'):
        pagelist, successflag = read_zip(filename)
    else:
        pagelist, successflag = read_txt(filename)

    if successflag == "missing file":
        print(thisID + " is missing.")
        errorlog.append(thisID + '\t' + "missing")
        continue
    elif successflag == "pagination error":
        print(thisID + " has a pagination problem.")
        errorlog.append(thisID + '\t' + "paginationerror")
        continue

    tokens, pre_matched, pre_english, pagedata, headerlist = NormalizeVolume.as_stream(pagelist, verbose=debug)

    if pre_english < 0.6:
        print(thisID + " is suspicious.")

    with open(headeroutpath, mode="a", encoding="utf-8") as f:
        for astream in headerlist:
            if len(astream) > 0:
                outline = " ".join([x for x in astream])
                f.write(outline + '\n')
        f.write("------------------\n")

    tokencount = len(tokens)

    if len(tokens) < 10:
        print(thisID, "has only tokencount", len(tokens))
        errorlog.append(thisID + '\t' + 'short')

    correct_tokens, pages, post_matched, post_english = NormalizeVolume.correct_stream(tokens, verbose = debug)

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
        # okay, this is crazy and not efficient to run, but it's easy to write and there are a small number
        # of these files -- so I'm going to count the new contextually-corrected tokens by re-running them
        # through Volume.
        correct_tokens, pages, post_matched, post_english = NormalizeVolume.correct_stream(corrected, verbose = debug)

        corrected = correct_tokens

    # If we are upvoting tokens in the header, they need to be added here.

    for index, page in enumerate(pages):
        thispageheader = headerlist[index]
        header_tokens, header_pages, dummy1, dummy2 = NormalizeVolume.correct_stream(thispageheader, verbose = debug)
        headerdict = header_pages[0]
        for key, value in headerdict.items():
            if key == "romannumeral" or key.startswith("arabic"):
                continue
                # because we don't really want to upvote page numbers
            elif key in page:
                page[key] += 2
                # a fixed increment no matter how many times the word occurs in the
                # header

    # Write corrected file.
    cleanHTID = clean_pairtree(thisID)

    if testrun:
        if cleanHTID.endswith(".clean.txt"):
            outHTID = cleanHTID.replace(".clean.txt", "")
        elif cleanHTID.endswith("norm.txt"):
            outHTID = cleanHTID.replace("norm.txt", ".norm.txt")
        elif cleanHTID.endswith(".txt"):
            outHTID = cleanHTID.replace(".txt", "norm.txt")
        else:
            outHTID = cleanHTID + ".norm.txt"

        outfilename = outpath + "texts/" + outHTID
    else:
        outfilename = filepath + postfix + '/' + postfix + ".norm.txt"

    with open(outfilename, mode = 'w', encoding = 'utf-8') as file:
        for token in corrected:
            if token != '\n' and token != "“" and not (token.startswith('<') and token.endswith('>')):
                token = token + " "
            file.write(token)

    if len(pages) != len(pagedata):
        print("Discrepancy between page data and page metadata!")

    totalwordsinvol = 0

    if testrun:
        if cleanHTID.endswith(".clean.txt"):
            outHTID = cleanHTID.replace(".clean.txt", ".pg.tsv")
        elif cleanHTID.endswith("norm.txt"):
            outHTID = cleanHTID.replace("norm.txt", ".pg.tsv")
        elif cleanHTID.endswith(".txt"):
            outHTID = cleanHTID.replace(".txt", ".pg.tsv")
        else:
            outHTID = cleanHTID + ".pg.tsv"

        outfilename = outpath + "pagefeatures/" + outHTID
    else:
        outfilename = filepath + postfix + '/' + postfix + ".pg.tsv"

    with open(outfilename, mode = 'w', encoding = 'utf-8') as file:
        numberofpages = len(pages)
        for index, page in enumerate(pages):

            # This is a shameful hack that should be deleted later.
            if "estimated" in page and "percentage" in page and (index + 3) > numberofpages:
                continue
            if "untypical" in page and (index +2) > numberofpages:
                continue

            for feature, count in page.items():
                outline = str(index) + '\t' + feature + '\t' + str(count) + '\n'
                # pagenumber, featurename, featurecount
                file.write(outline)
                if not feature.startswith("#"):
                    totalwordsinvol += count
                # This is because there are structural features like #allcapswords
                # that should not be counted toward total token count.

            structural_features = pagedata[index]
            for feature, count in structural_features.items():
                if count > 0 or feature == "#textlines":
                    outline = str(index) + '\t' + feature + '\t' + str(count) + '\n'
                    file.write(outline)

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


