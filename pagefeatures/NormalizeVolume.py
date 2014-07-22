import re
import math
import HeaderFinder

## The following lines generate a translation map that zaps all
## non-alphanumeric characters in a token.

delchars = ''.join(c for c in map(chr, range(256)) if not c.isalpha())
alleraser = str.maketrans('', '', delchars)

## Translation map that only breaks selected punctuation marks
## likely to pose a problem. Does not break hyphens, does break dashes.

## Translation map that erases most punctuation, including hyphens.
Punctuation = '.,():-—;"!?•$%@“”#<>+=/[]*^\'{}_■~\\|«»©&~`£·'
mosteraser = str.maketrans('', '', Punctuation)

punctuple = ('.', ',', '?', '!', ';', '"', '“', '”', ':', '--', '—', ')', '(', "'", "`", "[", "]", "{", "}")
punctnohyphen = ['.', ',', '?', '!', ';', '"', '“', '”', ':', ')', '(', "'", "`", "[", "]", "{", "}"]
specialfeatures = {"arabicprice", "arabic1digit", "arabic2digit", "arabic3digit", "arabic4digit", "arabic5+digit", "romannumeral", "personalname"}
alphabet = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
honorifics = ["sir", "mr", "m", "miss", "mrs", "lord", "lady", "prince", "king", "queen"]

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

personalnames = set()
with open(rulepath + 'PersonalNames.txt', encoding = 'utf-8') as file:
    filelines = file.readlines()

for line in filelines:
    line = line.rstrip()
    line = line.lower()
    personalnames.add(line)

placenames = set()
with open(rulepath + 'PlaceNames.txt', encoding = 'utf-8') as file:
    filelines = file.readlines()

for line in filelines:
    line = line.rstrip()
    line = line.lower()
    placenames.add(line)

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

## End loading of rulesets.

def increment_dict(anitem, adictionary):
    if anitem in adictionary:
        adictionary[anitem] += 1
    else:
        adictionary[anitem] = 1

    return adictionary[anitem]

def commasplit(matchobj):
    '''Function that we're going to use below to process regexes.'''
    astring = matchobj.group(0)
    astring = astring.replace(',', ', ')
    return astring

def standarddev(alist):
    if len(alist) < 1:
        return 0

    mean = sum(alist) / len(alist)
    squareddifferences = 0
    for anitem in alist:
        squareddifferences += (anitem - mean) * (anitem - mean)
    variance = squareddifferences / len(alist)
    stdev = math.sqrt(variance)
    return stdev

def as_stream(pagelist, verbose = False):
    '''Converts a list of pages to a list of tokens
    Linebreaks are represented as separate tokens.
    In the process we also collect data about each page,
    including the number of lines, the number of lines with
    text, the number that begin with a capital letter, the
    max number of repeats for a single letter (not case-sensitive),
    and the max number of repeats for an alphabetically-adjacent
    pair of letters (not case-sensitive).'''

    global lexicon, mosteraser, alphabet, punctnohyphen, personalnames, honorifics, romannumerals

    headerlist = HeaderFinder.find_headers(pagelist, romannumerals)

    linelist = list()
    firstpage = True
    pagedata = list()

    for page in pagelist:
        if firstpage:
            firstpage = False
        else:
            linelist.append('<pb>')

        linecounter = 0
        textlinecounter = 0
        capcounter = 0
        commas = 0
        periods = 0
        exclamationpoints = 0
        questionmarks = 0
        quotations = 0
        endwpunct = 0
        endwnumeral = 0
        startwname = 0
        startwrubric = 0
        sequentialcaps = 0
        thisalphabeticrun = 0
        lastcap = "|"
        initial_dict = dict()
        lengths = list()

        for line in page:
            strippedline = line.strip()
            if strippedline.startswith('<') and strippedline.endswith('>'):
                continue
                # with some exceptions, these lines represent xml encoding
                # in the file that we want to ignore
                # I'm willing to live with the exceptions.
            linelist.append(line)
            linecounter += 1

            if len(strippedline) > 0:
                lengths.append(len(strippedline))
                if len(strippedline) > 1:
                    textlinecounter += 1
                increment_dict(strippedline[0].lower(), initial_dict)
                commas += strippedline.count(",")
                periods += strippedline.count(".")
                quotations += strippedline.count('"')
                quotations += strippedline.count('”')
                quotations += strippedline.count('“')
                exclamationpoints += strippedline.count("!")
                questionmarks += strippedline.count("?")
                lastchar = strippedline[-1]

                if lastchar in punctnohyphen:
                    endwpunct += 1

                if lastchar.isdigit():
                    endwnumeral += 1
                elif len(strippedline) > 1:
                    nexttolastchar = strippedline[-2]
                    if nexttolastchar.isdigit():
                        endwnumeral += 1

                # Here what we're doing is counting the longest sequence
                # of line-initial uppercase letters that are in alphabetic
                # order
                if strippedline[0].isalpha() and strippedline[0].isupper():
                    capcounter += 1

                    if strippedline[0] >= lastcap:
                        thisalphabeticrun += 1
                        if thisalphabeticrun > sequentialcaps:
                            sequentialcaps = thisalphabeticrun
                    else:
                        thisalphabeticrun = 0

                    lastcap = strippedline[0]

                firstword = strippedline.split()[0]

                if len(firstword) > 0 and firstword[0].isupper():
                    prefix, strippedword, suffix = strip_punctuation(firstword)
                    firstwordlower = strippedword.lower()

                    if (firstwordlower not in lexicon) or (firstwordlower in personalnames) or (firstwordlower in honorifics):
                        startwname += 1

                    if firstword.endswith("."):
                        startwrubric += 1


        maxinitial = 0
        maxpair = 0
        lastcount = 0

        for letter in alphabet:
            if letter in initial_dict:
                thiscount = initial_dict[letter]
            else:
                thiscount = 0

            if thiscount > maxinitial:
                maxinitial = thiscount
            thispair = thiscount + lastcount
            if thispair > maxpair:
                maxpair = thispair
            lastcount = thiscount

        stdev = int(standarddev(lengths) * 100)
        structural_features = {"#lines": linecounter, "#textlines": textlinecounter, "#caplines": capcounter, "#maxinitial": maxinitial, "#maxpair": maxpair, "#commas": commas, "#periods": periods, "#exclamationpoints": exclamationpoints, "#questionmarks": questionmarks, "#quotations": quotations, "#endwpunct": endwpunct, "#endwnumeral": endwnumeral, "#startwrubric": startwrubric, "#startwname": startwname, "#sequentialcaps": sequentialcaps, "#stdev": stdev}
        pagedata.append(structural_features)

    tokens = list()
    for line in linelist:
        if len(line) < 1:
            continue
        if line == "\n":
            tokens.append(line)
            continue
        line = line.rstrip()
        if line == "<pb>":
            tokens.append(line)
            tokens.append('\n')
            continue

        line = line.replace('”', '” ')
        line = line.replace(':', ': ')
        line = line.replace(';', '; ')
        line = re.sub(',\D', commasplit, line)
        # That replaces all commas with comma + space unless they are followed by a digit.
        # Thus "300,000" isn't broken up but "my friend,Fred" is

        line = line.replace('—', ' — ')
        line = line.replace('--', ' -- ')
        ## Instead of zapping final punctuation, we make sure it's followed by a space.

        line = line.replace('_', ' ')
        # But we do zap underscores, which are rarely meaningful.

        # ## Quotes require special treatment, because their position relative to
        # ## the space can be significant.

        # if '"' in line:
        #     nextindex = line.find('"')
        #     while nextindex >= 0:
        #         if nextindex >= (len(line) - 1):
        #             followedbyspace = True
        #             nextindex = -1
        #         elif line[nextindex+1] == " ":
        #             followedbyspace = True
        #             nextindex = line.find('"', nextindex+1, len(line))
        #         else:
        #             if nextindex > 0 and line[nextindex - 1] == " ":
        #                 line = line[0:nextindex] + '“ ' + line[nextindex+1:]
        #                 nextindex = line.find('"', nextindex+2, len(line))
        #                 ## Okay, this is a teensy bit baroque. I know that correct_stream
        #                 ## doesn't handle prefixed punctuation very well. So I don't want
        #                 ## quotes to be prefixed to words. But I want to preserve the fact
        #                 ## that they were opening quotes. So I use the special open-quote
        #                 ## character if quote was prefixed to a word, and preceded by
        #                 ## a space.
        #             elif nextindex == 0:
        #                 line = '“' + line[nextindex+1:]
        #                 nextindex = line.find('"', nextindex+2, len(line))
        #             else:
        #                 line = line[0:nextindex] + '" ' + line[nextindex+1:]
        #                 nextindex = line.find('"', nextindex+2, len(line))
        #                 ## If not preceded by a space, this is ambiguous, and I leave
        #                 ## the character ambiguous.


        lineparts = line.split()
        tokens.extend(lineparts)
        tokens.append('\n')

    counter = 0
    englishcounter = 0
    allcounter = 0

    tokencount = len(tokens)

    for i in range(0, tokencount):
        token = tokens[i].lower()
        if token in lexicon:
            counter += 1
            allcounter += 1
            if lexicon[token] > 0:
                englishcounter += 1
        elif token == '\n' or token.startswith('<') or mostly_numeric(token):
            next
        elif i < (tokencount-1):
            token = token.translate(mosteraser)
            if token in lexicon:
                counter += 1
                allcounter += 1
                if lexicon[token] > 0:
                    englishcounter += 1
            else:
                nexttoken = tokens[i+1].lower()
                fused = token + nexttoken.translate(mosteraser)
                if fused in lexicon:
                    counter += 1
                    allcounter += 1
                    if lexicon[fused] > 0:
                        englishcounter += 1
                else:
                    allcounter += 1
        else:
            allcounter += 1

    if allcounter > 0:
        percentfound = counter / allcounter
        percentenglish = englishcounter / allcounter
    else:
        percentfound = 0
        percentenglish = 0

    return tokens, percentfound, percentenglish, pagedata, headerlist

def strip_punctuation(astring):
    global punctuple
    keepclipping = True
    suffix = ""
    while keepclipping == True and len(astring) > 1:
        keepclipping = False
        if astring.endswith(punctuple):
            suffix = astring[-1:] + suffix
            astring = astring[:-1]
            keepclipping = True
    keepclipping = True
    prefix = ""
    while keepclipping == True and len(astring) > 1:
        keepclipping = False
        if astring.startswith(punctuple):
            prefix = prefix + astring[:1]
            astring = astring[1:]
            keepclipping = True
    return(prefix, astring, suffix)

def normalize_case(astring):
    if astring.islower():
        case = 'lower'
    elif astring.replace("'", "").isupper():
        case = 'upper'
    elif astring.istitle():
        case = 'title'
    elif astring.replace("'", "").istitle():
        case = "title"
    # The replace part is important lest all possessive words get interpreted
    # as heterogenous-case.
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

def arabic_digits(astring):
    pricecodes = ["$", "£", "¢"]
    counter = 0
    for c in astring:
        if c.isdigit():
            counter += 1

    priceflag = False
    for code in pricecodes:
        if astring.count(code) > 0:
            priceflag = True
    if astring.endswith("s") or astring.endswith("d"):
        priceflag = True

    if len(astring) < 1 or counter/len(astring) < .4:
        return "none"
    elif priceflag == True:
        return "arabicprice"
    elif counter < 2:
        return "arabic1digit"
    elif counter < 3:
        return "arabic2digit"
    elif counter < 4:
        return "arabic3digit"
    elif counter < 5:
        return "arabic4digit"
    else:
        return "arabic5+digit"

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

def all_nonalphanumeric(astring):
    nonalphanum = True
    for character in astring:
        if character.isalpha() or character.isdigit():
            nonalphanum = False
    return nonalphanum

def logandreset(astring, caseflag, possessive, prefix, suffix):
    ''' We normalize case at moments in the checking process, and
    also remove trailing apostrophe-s and punctuation. This routine ensures that
    both aspects of the token are restored to their original condition.
    Note that it does so only after logging the word, which means that
    possessive inflections are not registered in our wordcount.
    That's my only gesture toward lemmatization.'''

    global pagedict, lexicon, syncoperules, variants, foundcounter, englishcounter, personalnames, placenames

    # In this version of logandreset, tokens that belong to certain special classes are represented
    # with class names to make classification easier. These names include romannumeral, arabic1digit,
    # arabic2digit, arabic3digit, arabic4digit, arabic5+digit (which will have been changed before
    # this function is invoked). But we also log certain titlecased words as "personalname" or
    # "propernoun", and that change gets made in this function.

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
    elif astring in specialfeatures:
        foundcounter += 1

    logstring = astring.lower()
    if (caseflag == "upper" or caseflag == "title") and astring in personalnames:
        logstring = "personalname"
        if astring not in lexicon:
            # count personal names as things found but not english.
            # do this only id not in lexicon to avoid doublecounting with
            # with if statement above
            foundcounter += 1
    elif (caseflag == "upper" or caseflag == "title") and astring in placenames:
        logstring = "placename"
        if astring not in lexicon:
            # count personal names as things found but not english.
            # do this only id not in lexicon to avoid doublecounting with
            # with if statement above
            foundcounter += 1
    elif caseflag == "title" and len(astring) > 4 and astring not in lexicon:
        logstring = "propernoun"
        # This is a long titlecased word not present
        # in our lexicon. Probably a proper noun.

    if logstring in pagedict:
        pagedict[logstring] += 1
    else:
        pagedict[logstring] = 1

    if caseflag == "lower":
        astring = astring.lower()
    elif caseflag == "upper":
        astring = astring.upper()
        increment_dict("#allcapswords", pagedict)
        # This is a special feature that counts the number of words
        # on each page in ALLCAPS. It has a # in front to distinguish
        # it from features that represent actual token counts. You
        # would not include features with a # when counting the total
        # number of words on a page.
    elif caseflag == "title":
        astring = astring.title()
    else:
        astring = astring.lower()

    if possessive:
        astring = astring + "'s"

    if len(suffix) > 0:
        astring = astring + suffix
    if len(prefix) > 0:
        astring = prefix + astring

    return astring


def correct_stream(tokens, verbose = False):
    global lexicon, hyphenrules, fuserules, syncoperules, variants, correctionrules, romannumerals, pagedict, foundcounter, englishcounter, personalnames, placenames

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

        if all_nonalphanumeric(thisword):
            corrected.append(thisword)
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

        thisprefix, thisword, thissuffix = strip_punctuation(thisword)
        nextprefix, nextword, nextsuffix = strip_punctuation(nextword)

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
            numeral = logandreset("romannumeral", thiscase, False, thisprefix, thissuffix)
            corrected.append(originalword)
            continue

        arabic = arabic_digits(thisword)
        if arabic != "none":
            numeral = logandreset(arabic, thiscase, False, thisprefix, thissuffix)
            corrected.append(originalword)
            continue

        if (thiscase=="title" or thiscase=="upper") and (thisword in personalnames or thisword in placenames):
            newtoken = logandreset(thisword, thiscase, thispossessive, thisprefix, thissuffix)
            corrected.append(newtoken)
            continue

        # Is this part of a phrase that needs fusing?

        if is_word(thisword) and is_word(nextword):
            fusetuple = (thislower, nextlower)
            if fusetuple in fuserules:
                newtoken = fuserules[fusetuple]
                newtoken = logandreset(newtoken, thiscase, nextpossessive, thisprefix, nextsuffix)
                corrected.append(newtoken)
                wordsfused += 1
                skipflag = True
                continue

            else:
                thisword = logandreset(thisword, thiscase, thispossessive, thisprefix, thissuffix)
                corrected.append(thisword)
                continue

        if is_word(thisword):
            thisword = logandreset(thisword, thiscase, thispossessive, thisprefix, thissuffix)
            corrected.append(thisword)
            continue

        ## At this point we know that thisword doesn't match lexicon.
        ## Maybe it's a word fragment
        ## that needs to be joined to nextword, after erasure of hyphens, etc.

        thistrim = thisword.translate(mosteraser)
        nexttrim = nextword.translate(mosteraser)
        possiblefusion = thistrim + nexttrim

        if is_word(possiblefusion):
            newtoken = logandreset(possiblefusion, thiscase, nextpossessive, thisprefix, nextsuffix)
            corrected.append(newtoken)
            wordsfused += 1
            skipflag = True
            continue

        #maybe both parts need to be corrected
        if possiblefusion.lower() in correctionrules:
            thiscorr = correctionrules[possiblefusion.lower()]
            newtoken = logandreset(thiscorr, thiscase, nextpossessive, thisprefix, nextsuffix)
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
            newtoken = logandreset(newtoken, thiscase, nextpossessive, thisprefix, nextsuffix)
            corrected.append(newtoken)
            wordsfused += 1
            skipflag = True
            continue

        ## But otherwise, if the correction worked, move on.

        if is_word(thiscorr):
            thiscorr = logandreset(thiscorr, thiscase, thispossessive, thisprefix, thissuffix)
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

                newtoken = logandreset(part, partcase, False, "", "")
                if j == (len(theseparts) - 1):
                    newtoken = newtoken + thissuffix
                if j == 0:
                    newtoken = thisprefix + newtoken
                corrected.append(newtoken)
            continue

        ## Ordinary correction rules didn't work. Now we try syncope.

        if thiscorr in syncoperules:
            thiscorr = syncoperules[thiscorr]

        if is_word(thiscorr):
            thiscorr = logandreset(thiscorr, thiscase, thispossessive, thisprefix, thissuffix)
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

                newtoken = logandreset(part, partcase, False, "", "")

                if j == (len(theseparts) - 1):
                    newtoken = newtoken + thissuffix
                if j == 0:
                    newtoken = thisprefix + newtoken
                corrected.append(newtoken)
            continue

        #last-ditch move. zap all nonalphabetic characters

        thispurged = thiscorr.translate(alleraser)

        if is_word(thispurged):
            thiscorr = logandreset(thispurged, thiscase, thispossessive, thisprefix, thissuffix)
            corrected.append(thiscorr)
            continue
        else:
            if thiscorr in syncoperules:
                thiscorr = syncoperules[thiscorr]
                thiscorr = logandreset(thiscorr, thiscase, thispossessive, thisprefix, thissuffix)
                corrected.append(thiscorr)
            elif thiscorr in variants:
                thiscorr = variants[thiscorr]
                thiscorr = logandreset(thiscorr, thiscase, thispossessive, thisprefix, thissuffix)
                corrected.append(thiscorr)
            else:
                dummy = logandreset(thiscorr, thiscase, thispossessive, thisprefix, thissuffix)
                corrected.append(originalword)
            ## The word will in fact only be logged in the page dictionary if it
            ## matches the dictionary. Variant spellings will be normalized in the
            ## logandreset function.
            continue

    pages.append(pagedict)
    # Because the last page also needs to be appended.

    if verbose:
        print('There were', wordsfused, 'fused words.')

    totaltokens = len(corrected) - paratext
    if totaltokens > 0:
        percentmatched = foundcounter / totaltokens
        percentenglish = englishcounter / totaltokens
    else:
        percentmatched = 0
        percentenglish = 0
    return corrected, pages, percentmatched, percentenglish

    # The method returns a vector of all tokens, including xml tags and linebreaks,
    # plus a list of page dictionaries, plus a count of words that matched, and the
    # number of those words that were english.









