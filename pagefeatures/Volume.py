
## The following lines generate a translation map that zaps all
## non-alphanumeric characters in a token.

delchars = ''.join(c for c in map(chr, range(256)) if not c.isalpha())
alleraser = str.maketrans('', '', delchars)

## Translation map that only breaks selected punctuation marks
## likely to pose a problem. Does not break hyphens, does break dashes.

BreakablePunctuation = ',—;"_“”'
breakselected = str.maketrans(BreakablePunctuation, '       ')

## Translation map that erases most punctuation, including hyphens.
Punctuation = '.,():-—;"!?•$%@“”#<>+=/[]*^\'{}_■~\\|«»©&~`£·'
mosteraser = str.maketrans('', '', Punctuation)

punctuple = ('.', ',', '?', '!', ';')

delim = '\t'
foundcounter = 0
englishcounter = 0
pagedict = dict()

import FileCabinet

pathdictionary = FileCabinet.loadpathdictionary()

rulepath = pathdictionary['volumerulepath']

romannumerals = set()
with open(rulepath + 'romannumerals.txt', encoding = 'utf-8') as file:
    filelines = file.readlines()

for line in filelines:
    line = line.rstrip()
    romannumerals.add(line)

lexicon = dict()

with open(rulepath + 'MainDictionary.txt', encoding = 'utf-8') as file:
    filelines = file.readlines()

for line in filelines:
    line = line.rstrip()
    fields = line.split(delim)
    englflag = int(fields[1])
    lexicon[fields[0]] = englflag

correctionrules = dict()

with open(rulepath + 'CorrectionRules.txt', encoding = 'utf-8') as file:
    filelines = file.readlines()

for line in filelines:
    line = line.rstrip()
    fields = line.split(delim)
    correctionrules[fields[0]] = fields[1]

hyphenrules = dict()

with open(rulepath + 'HyphenRules.txt', encoding = 'utf-8') as file:
    filelines = file.readlines()
filelines.reverse()
# Doing this so that unhyphenated forms get read before hyphenated ones.

for line in filelines:
    line = line.rstrip()
    fields = line.split(delim)
    Word = fields[0].rstrip()
    Corr = fields[1].rstrip()
    hyphenrules[Word] = Corr
    if " " not in Corr:
        lexicon[Corr] = 1
    else:
        StripWord = Word.replace("-", "")
        hyphenrules[StripWord] = Corr
        ## That's so that we split "tigermoth" as well as "tiger-moth" into "tiger moth."
        
    if "-" in Word:
        StripWord = Word.replace("-", "")
        StripCorr = Corr.replace(" ", "")
        StripCorr = StripCorr.replace("-", "")
        if StripWord != StripCorr and StripWord not in hyphenrules:
            hyphenrules[StripWord] = Corr
            print(Word, 'produced two corrections.')
    ## The purpose of this is a bit obscure to me. It may be deletable.

fuserules = dict()
with open(rulepath + 'FusingRules.txt', encoding = 'utf-8') as file:
    filelines = file.readlines()
    
for Line in filelines:
    Line = Line.rstrip()
    LineParts = Line.split(delim)
    Word = LineParts[0].rstrip()
    Word = tuple(Word.split(' '))
    Corr = LineParts[1].rstrip()
    fuserules[Word] = Corr

syncoperules = dict()
with open(rulepath + 'SyncopeRules.txt', encoding = 'utf-8') as file:
    filelines = file.readlines()
    
for line in filelines:
    line = line.rstrip()
    fields = line.split(delim)
    syncoperules[fields[0]] = fields[1]

variants = dict()
with open(rulepath + 'VariantSpellings.txt', encoding = 'utf-8') as file:
    filelines = file.readlines()
    
for line in filelines:
    line = line.rstrip()
    fields = line.split(delim)
    variants[fields[0]] = fields[1]

personalnames = set()
with open(rulepath + 'PersonalNames.txt', encoding = 'utf-8') as file:
    filelines = file.readlines()

for line in filelines:
    line = line.rstrip()
    line = line.lower()
    personalnames.add(line)

## placenames = set()
## with open(rulepath + 'PlaceNames.txt', encoding = 'utf-8') as file:
##     filelines = file.readlines()
##
## for line in filelines:
##     line = line.rstrip()
##     line = line.lower()
##     placenames.add(line)
## I have decided not to use this, because place names are not as arbitrary
## as personal names.
    

## End loading of rulesets.

def as_stream(linelist, verbose = False):
    '''converts a list of lines to a list of tokens'''
    global breakselected, lexicon, mosteraser
    
    listlength = len(linelist)

    # First, tag capitalized lines.
 
    caplist = ["amb"] * listlength
    previousCap = False
    previousLen = 0
    
    for index, line in enumerate(linelist):
        thisLen = len(line)
        initialcap = "amb"
        if line == "<pb>" or line == "<pb>\n":
            initialcap = "pb"
        elif thisLen < 1 or line == '\n':
            initialcap = "blank"
            previouslyLongAndCap = False
        else:
            for char in line:
                if char.isalpha() and char.isupper():
                    initialcap = "yes"
                    break
                if char.isalpha() and char.islower():
                    initialcap = "no"
                    break
                if char.isnumeric():
                    initialcap = "number"
                    break
                if char == "<" or char == "\n":
                    initialcap = "blank"
                    break

        if initialcap == "no":
            if previousCap and thisLen < 29 and (previousLen - thisLen) > 12:
                initialcap = "RunOnVerse?"
                
        caplist[index] = initialcap
        previousLen = len(line)
        
        if initialcap == "yes":
            previousCap = True
        else:
            previousCap = False

    # Then use the list of tags to count lines of text, and
    # initial-cap lines, for each page. Xml tags and blank
    # lines (whitespace, punctuation only) are not counted.
    
    remainder = caplist
    pages = list()
    while len(remainder) > 0:
        if "pb" in remainder:
            nextpage = remainder.index("pb") + 1
        else:
            nextpage = len(remainder)
        thispage = remainder [0: nextpage]
        linecount = len(thispage) - 1
        capcount = 0
        blankcount = 0
        for line in thispage:
            if line == "blank":
                blankcount = blankcount + 1
            if line == "yes":
                capcount = capcount + 1
        linecount = linecount - blankcount
        if linecount < 0:
            linecount == 0
        featuretuple = (linecount, capcount)
        pages.append(featuretuple)
        remainder = remainder[nextpage:]

    # Then figure out which lines count as "verse." I'm using "verse" here
    # not in the correct sense, but just as shorthand for any sequence of
    # lines with initial capital letters. This could be a table of contents
    # or an index, or dramatic dialogue. It's not really at this stage a
    # generic description; it's a purely formal or structural description.
        
    verselist = ["-1"] * listlength
    for index in range(0, listlength):

        ## There's a contorted logic here. We want to count as "verse" any line
        ## that is in a sequence of at least five initial-capitalized lines *and* is followed
        ## by at least one initial-capitalized line.
        
        ## To put that another way, we never count the last line as verse. It's usually
        ## the start of the next (prose) paragraph.

        ## A lot of things don't count as
        ## breaking a sequence. E.g., xml tags like <pb> or lines that contain only
        ## a page number don't count as capitalized, but also shouldn't break a sequence.
        ## Blank lines don't break a sequence, and short lines that might be "RunOnVerse"
        ## don't either. E.g.
        
        #  This is the forest primeval. The murmur-
        #  ing pines and the hemlocks,

        ## What we do, for each line, is search forward and backward until we hit a line
        ## that begins with a lowercase alphabetic character. Counting forward, we stop counting
        ## if we get to five. It's possible to be justified as "verse" just on the basis that you're
        ## followed by four capitalized lines. It's important to search forward and backward rather far,
        ## because verse sometimes comes in couplets separated by blank lines, so you can't assume
        ## that >50% of the lines will have text at all.

        ## Counting backward, we stop when we get to four. That means that being preceded by
        ## capitalized lines is never enough. You also need to be followed by at least one capitalized
        ## line in order to count as verse. (Because you will need a total of five in the sequence.)

        precedingVerse = 0
        for preceder in range(index, index - 9, -1):
            if preceder < 0:
                break
            if caplist[preceder] == "yes":
                precedingVerse = precedingVerse + 1
                if precedingVerse > 3:
                    break
            if caplist[preceder] == "no":
                break

        followingVerse = 0
        for follower in range(index, index + 9):
            if follower + 1 > listlength:
                break
            if caplist[follower] == "yes":
                followingVerse = followingVerse + 1
                if followingVerse > 4:
                    break
            if caplist[follower] == "no":
                break

        if precedingVerse + followingVerse > 4 and followingVerse > 0:
            verselist[index] = "-2"
        
    tokens = list()
    tokensverse = list()
    for index, line in enumerate(linelist):
        isthisverse = verselist[index]
        line = line.rstrip()
        if len(line) < 1:
            continue
        if line.startswith('<') and line.endswith('>'):
            tokens.append(line)
            tokens.append('\n')
            tokensverse.extend([isthisverse] * 2)
            continue

        line = line.translate(breakselected)
        line = line.replace('--', ' ')
        ## These do not zap all punctuation, but they turn commas, underscores,
        ## dashes, and quotation marks into spaces.
        
        lineparts = line.split()
        tokens.extend(lineparts)
        tokens.append('\n')
        tokensverse.extend([isthisverse] * (len(lineparts) + 1))

    assert len(tokens) == len(tokensverse)

    return tokens, tokensverse, pages

def strip_punctuation(astring):
    global punctuple
    keepclipping = True
    suffix = ""
    while keepclipping == True:
        keepclipping = False
        if astring.endswith(punctuple):
            suffix = suffix + astring[-1:]
            astring = astring[:-1]
            keepclipping = True
    return(astring, suffix)

def normalize_case(astring):
    if astring.islower():
        case = 'lower'
    elif astring.isupper():
        case = 'upper'
    elif astring.istitle():
        case = 'title'
    else:
        case = 'heterogenous'

    if case != "heterogenous":
        normalizedstring = astring.lower()
    else:
        normalizedstring = astring

    return normalizedstring, case

def mostly_numeric(astring):
    counter = 0
    for c in astring:
        if c.isdigit():
            counter += 1
    if len(astring) < 1:
        return False
    elif counter/len(astring) > .35:
        return True
    else:
        return False

def is_word(astring):
    global lexicon
    if astring in lexicon:
        return True
    elif astring.lower() in lexicon:
        return True
    elif (astring.lower() + "'s") in lexicon:
        return True
    else:
        return False

def logandreset(astring, thisverse, caseflag, possessive, suffix):
    ''' We normalize case at moments in the checking process, and
    also remove trailing apostrophe-s and punctuation. This routine ensures that
    both aspects of the token are restored to their original condition.
    Note that it does so only after logging the word, which means that
    possessive inflections are not registered in our wordcount.
    That's my only gesture toward lemmatization.'''
    
    global pagedict, lexicon, syncoperules, variants, foundcounter, englishcounter


    if astring in syncoperules:
        astring = syncoperules[astring]
    if astring in variants:
        astring = variants[astring]

    inDict = False

    if astring in lexicon:
        foundcounter += 1
        inDict = True
        if lexicon[astring] == 1:
            englishcounter += 1
    elif astring == "romannumeral" or astring == "arabicnumeral":
        foundcounter += 1
        englishcounter += 1

    if inDict or astring == "romannumeral" or astring == "arabicnumeral" or astring == "personalname":
        keytuple = (astring.lower(), thisverse)
        if keytuple in pagedict:
            pagedict[keytuple] += 1
        else:
            pagedict[keytuple] = 1
            
    elif caseflag == 'title':
        keytuple = ('titlecasenodict', thisverse)
        if keytuple in pagedict:
            pagedict[keytuple] += 1
        else:
            pagedict[keytuple] = 1       
    
    if caseflag == "lower":
        astring = astring.lower()
    elif caseflag == "upper":
        astring = astring.upper()
    elif caseflag == "title":
        astring = astring.title()
    else:
        astring = astring.lower()

    if possessive:
        astring = astring + "'s"

    if len(suffix) > 0:
        astring = astring + suffix

    return astring
        

def correct_stream(tokens, aretokensverse, verbose = False):
    global lexicon, hyphenrules, fuserules, syncoperules, correctionrules, romannumerals, pagedict, foundcounter, englishcounter, placenames, personalnames

    corrected = list()
    streamlen = len(tokens)
    skipflag = False
    wordsfused = 0
    pagecounter = 0
    pagedict = dict()
    pages = list()
    foundcounter = 0
    englishcounter = 0
    paratext = 0

    for i in range(0, streamlen):
        
        thisword = tokens[i]
        thisverse = aretokensverse[i]
        if len(thisword) < 1:
            continue

        originalword = thisword

        if thisword == "<pb>":
            pages.append(pagedict)
            pagedict = dict()
            # log the old page dictionary and start a new one
            corrected.append(thisword)
            paratext +=1
            continue

        if (thisword.startswith('<') and thisword.endswith('>')) or thisword == '\n':
            corrected.append(thisword)
            paratext += 1
            continue

        ## Notice the sequence here. We don't reset skipflag if we're just skipping newlines or
        ## xml markup.

        if skipflag:
            skipflag = False
            continue

        # get the next word, ignoring newlines and xml markup
        for j in range(1, 4):
            if i < (streamlen-j):
                nextword = tokens[i+j]
                if nextword.startswith('<') or nextword=='\n':
                    continue
                else:
                    break
            else:
                nextword = "#EOFile"
                break

        thisword, thiscase = normalize_case(thisword)
        nextword, nextcase = normalize_case(nextword)
        ## All words in homogenouscase (upper/lower) or titlecase go to lowercase
        ## HeterOGENous words retain existing case.

        thisword, thissuffix = strip_punctuation(thisword)
        nextword, nextsuffix = strip_punctuation(nextword)

        ## We also strip and record apostrophe-s to simplify checks.

        thispossessive = False
        nextpossessive = False

        if (thisword.endswith("'s") or thisword.endswith("'S")) and len(thisword) > 2:
            thispossessive = True
            thisword = thisword[0:-2]

        if (nextword.endswith("'s") or nextword.endswith("'S")) and len(nextword) > 2:
            nextpossessive = True
            nextword = nextword[0:-2]

        thislower = thisword.lower()
        nextlower = nextword.lower()

        # Is this a number?

        if thislower in romannumerals:
            numeral = logandreset("romannumeral", thisverse, thiscase, False, thissuffix)
            corrected.append(thisword)
            continue

        if mostly_numeric(thisword):
            numeral = logandreset("arabicnumeral", thisverse, thiscase, False, thissuffix)
            corrected.append(thisword)
            continue

        # Is this a placename or a personal name?

##        if thisword in placenames and (thiscase == "title" or thiscase == "upper"):
##            placeholder = logandreset("placename", thisverse, thiscase, False, thissuffix)
##            corrected.append(originalword)
##            continue

        if thisword in personalnames and (thiscase == "title" or thiscase == "upper"):
            placeholder = logandreset("personalname", thisverse, thiscase, False, thissuffix)
            corrected.append(originalword)
            continue

        # Is this part of a phrase that needs fusing?
            
        if is_word(thisword) and is_word(nextword):
            fusetuple = (thislower, nextlower)
            if fusetuple in fuserules:
                newtoken = fuserules[fusetuple]
                newtoken = logandreset(newtoken, thisverse, thiscase, nextpossessive, nextsuffix)
                corrected.append(newtoken)
                wordsfused += 1
                skipflag = True
                continue

            else:
                thisword = logandreset(thisword, thisverse, thiscase, thispossessive, thissuffix)
                corrected.append(thisword)
                continue

        if is_word(thisword):
            thisword = logandreset(thisword, thisverse, thiscase, thispossessive, thissuffix)
            corrected.append(thisword)
            continue

        ## At this point we know that thisword doesn't match lexicon. Maybe it's a word fragment
        ## that needs to be joined to nextword, after erasure of hyphens, etc.

        thistrim = thisword.translate(mosteraser)
        nexttrim = nextword.translate(mosteraser)
        possiblefusion = thistrim + nexttrim

        if is_word(possiblefusion):
            newtoken = logandreset(possiblefusion, thisverse, thiscase, nextpossessive, nextsuffix)
            corrected.append(newtoken)
            wordsfused += 1
            skipflag = True
            continue

        #maybe both parts need to be corrected
        if possiblefusion.lower() in correctionrules:
            thiscorr = correctionrules[possiblefusion.lower()]
            newtoken = logandreset(thiscorr, thisverse, thiscase, nextpossessive, nextsuffix)
            corrected.append(newtoken)
            wordsfused += 1
            skipflag = True
            continue

        if thisword in correctionrules:
            thiscorr = correctionrules[thisword]
        elif thistrim in correctionrules:
            thiscorr = correctionrules[thistrim]
        else:
            thiscorr = thisword.lower()

        if nextword in correctionrules:
            nextcorr = correctionrules[nextword]
        elif nexttrim in correctionrules:
            nextcorr = correctionrules[nexttrim]
        else:
            nextcorr = nextword.lower()

        ## Since we're past the correction rules, there's no reason any longer to
        ## retain words in Heter-Ogenous case.

        ## Now we have to check one last time for possible fusing.

        fusetuple = (thiscorr, nextcorr)
        if fusetuple in fuserules:
            newtoken = fuserules[fusetuple]
            newtoken = logandreset(newtoken, thisverse, thiscase, nextpossessive, nextsuffix)
            corrected.append(newtoken)
            wordsfused += 1
            skipflag = True
            continue

        ## But otherwise, if the correction worked, move on.

        if is_word(thiscorr):
            thiscorr = logandreset(thiscorr, thisverse, thiscase, thispossessive, thissuffix)
            corrected.append(thiscorr)
            continue

        if thiscorr in hyphenrules:
            thiscorr = hyphenrules[thiscorr]
            
        ## Maybe the correction is multiple words. That's a split that could have happened as a result
        ## of correctionrules or hyphenrules.
            
        if " " in thiscorr:
            theseparts = thiscorr.split()
            for j in range(0, len(theseparts)):
                part = theseparts[j]
                if j == 0:
                    partcase = thiscase
                else:
                    partcase = "lower"
                    
                newtoken = logandreset(part, thisverse, partcase, False, "")
                if j == (len(theseparts) - 1):
                    newtoken = newtoken + thissuffix
                corrected.append(newtoken)
            continue

        ## Ordinary correction rules didn't work. Now we try syncope.

        if thiscorr in syncoperules:
            thiscorr = syncoperules[thiscorr]

        if is_word(thiscorr):
            thiscorr = logandreset(thiscorr, thisverse, thiscase, thispossessive, thissuffix)
            corrected.append(thiscorr)
            continue

        ## If we still have a hyphen, try splitting there.

        if "-" in thiscorr:
            splitcorr = thiscorr.replace("-", " ")
            theseparts = splitcorr.split()
            for j in range(0, len(theseparts)):
                part = theseparts[j]
                if j == 0:
                    partcase = thiscase
                else:
                    partcase = "lower"
                    
                newtoken = logandreset(part, thisverse, partcase, False, "")
                if j == (len(theseparts) - 1):
                    newtoken = newtoken + thissuffix
                corrected.append(newtoken)
            continue

        #last-ditch move. zap all nonalphabetic characters

        thispurged = thiscorr.translate(alleraser)

        if is_word(thispurged):
            thiscorr = logandreset(thispurged, thisverse, thiscase, thispossessive, thissuffix)
            corrected.append(thiscorr)
            continue
        else:
            originalword = logandreset(thiscorr, thisverse, thiscase, thispossessive, thissuffix)
            corrected.append(originalword)
            ## The word will in fact only be logged in the page dictionary if it
            ## matches the dictionary. Variant spellings will be normalized in the
            ## logandreset function.
            continue
            
    if verbose:
        print('There were', wordsfused, 'fused words.')

    totaltokens = len(corrected) - paratext
##    if totaltokens > 0:
##        percentmatched = foundcounter / totaltokens
##        percentenglish = englishcounter / totaltokens
##    else:
##        percentmatched = 0
##        percentenglish = 0
    
    return corrected, pages

    # The method returns a vector of all tokens, including xml tags and linebreaks,
    # plus a list of page dictionaries.

        

            
                
                
            
            
    
