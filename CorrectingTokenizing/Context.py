## CONTEXT.py

'''Contextual spellchecker. On being imported, it loads rulesets.
   The function as_stream reduces a file to a tokenstream and tests
   to see whether this is a long-s file needing correction. (Ideally
   you should only run it on pre-1830 files that might fall into that
   category.)
   Then the function "catch_ambiguities" can be called for a specific file.
'''

# IMPORTS.

import FileCabinet

pathdictionary = FileCabinet.loadpathdictionary()
rulepath = pathdictionary['contextrulepath']

# CONSTANTS.

delim = '\t'
punctuationset = {'.', ',', '?', '!', ';', ')'}
# There's a reason why we don't include left paren. See 'catch_ambiguities.'

flipslipper = ['flip', 'flips', 'flipped', 'flipping', 'flay', 'flays', 'flayed', "flay'd"]
# The triadic problems flip - slip - ship and flay - slay - stay require special treatment.                                          ')

felecterrors = ['fee', 'fea', 'fay', 'fays', 'fame', 'fell', 'funk', 'fold', 'haft', 'fat', 'fix', 'chafe', 'loft']
selecttruths = ['see', 'sea', 'say', 'says', 'same', 'sell', 'sunk', 'sold', 'hast', 'sat', 'six', 'chase', 'lost']
# Of course, either set could be valid. But I expect the second to be more common.
# The comparison is used as a test.

# RULESETS.
            
Context = {}
FileString = rulepath + 'DisambigTwograms.txt'
with open(FileString, encoding='utf=8') as file:
    filelines = file.readlines()

for line in filelines:
    line = line.rstrip()
    LineParts = line.split(delim)
    Context[LineParts[0]] = int(LineParts[1])

del filelines

AmbiguousPairs = []
AmbiguousTriggers = set()
FileString = rulepath + 'AmbiguousPairs.txt'

with open(FileString, mode='r', encoding='utf-8') as file:
    FileLines = file.readlines()

for Line in FileLines:
    Line = Line.rstrip()
    LineParts = Line.split(delim)
    LineTuple = (LineParts[0], LineParts[1])
    AmbiguousPairs.append(LineTuple)
    for i in range(0,2):
        if "f" in LineParts[i]:
            AmbiguousTriggers.add(LineParts[i])
        # We only add the words that contain "f" to the set that triggers
        # an investigation. Their "s" equivalents will be in AmbiguousPairs
        # but not the AmbiguousTriggers set. After all, we never correct
        # from the "s" version to the "f" version.

del FileLines
AmbiguousTriggers.add('fad')

# The word 'fad' doesn't exist before 1825, and I'm only running this script on early texts.

with open(rulepath + 'logvalues.tsv', encoding='utf-8') as file:
    filelines = file.readlines()

logvals = dict()
for line in filelines:
    line = line.rstrip()
    parts = line.split(delim)
    logvals[parts[0]] = float(parts[1])

# The purpose of the logvalues file is to give me some Bayesian guidance on the frequency of
# words.

# Functions

def add_or_inc (token, adict):
    if token in adict:
        adict[token] = adict[token] + 1
    else:
        adict[token] = 1
    return adict

def disambiguate(preceded, token, followed, pair):
    """Determine which of two candidates better fits context."""
    global Context, flipslipper, logvals
    
    Jekyll, Hyde = pair
    # unpack the tuple into an ambiguous (indeed sinister) pair

    # The triadic problems flip - slip - ship and flay - slay - stay
    # require special treatment, because ship and stay are actually most common,
    # but we also need to check the other two alternatives.
    # I do this by putting the common, surprising forms (ship and stay, etc)
    # in AmbiguousPairs, and forcing the program to make up the obvious
    # f/s substitutions (slip and slay) on its own.
    
    # E.g., in AmbiguousPairs, flip, flips, flipped, and flipping all map to
    # the ship- alternative. But we should also check the slip- alternative.
    # This can be done recursively. I assume that "flip," "flay," etc. will come in the
    # Jekyll position because I know that's true in the 2013 version of AmbiguousPairs.txt.
    # If you use a different file you'll want to code with less sloppy assumptions.

    # Technically, similar situations occur with flit-slit-shit and flat-slat-shat.
    # But fine-tuning the distribution of shit and shat is just a bit too Swiftian
    # an enterprise for me to contemplate. I leave it as an exercise ...
     
    if Jekyll in flipslipper:
        slipversion = Jekyll.replace('f', 's')
        newpair = (slipversion, Hyde)
        otheroption, otherprob = disambiguate(preceded, token, followed, newpair)
    else:
        otherprob = 0
        otheroption = ""
    
    # The threes in the code that follows are default values for
    # the frequency of anything not in our dataset. Consider this
    # a Laplacian correction of a slightly more generous kind.
    # Any word combination is at least slightly likely. More likely
    # if the word involved is common: that's the function of
    # the logvals dictionary. The log-frequency function I'm using
    # here is not rigorously Bayesian, but it'll do.

    if Jekyll in logvals:
        DefaultJekyll = 3 + logvals[Jekyll]
    else:
        DefaultJekyll = 3
    if Hyde in logvals:       
        DefaultHyde = 3 + logvals[Hyde]
    else:
        DefaultHyde = 3
    
    if preceded == "#nought":
        BeforeJ = DefaultJekyll
        BeforeH = DefaultHyde
    else:
        BeforeJ = Context.get(preceded + " " + Jekyll, DefaultJekyll)
        BeforeH = Context.get(preceded + " " + Hyde, DefaultHyde)

    # Context.get is a nice Pythonic trick that gets the value if
    # there is one, but otherwise returns the default arg of 3.

    if followed == "#nought":
        AfterJ = DefaultJekyll
        AfterH = DefaultHyde
    else:
        AfterJ = Context.get(Jekyll + " " + followed, DefaultJekyll)
        AfterH = Context.get(Hyde + " " + followed, DefaultHyde)

    # Here's the magnificently complex algorithm for evaluating the probability of
    # two different three-word sequences.
    # Compare: P('he flunk') * P('flunk into')
    # To: P('he slunk') * P('slunk into')
    # Which of the two products is bigger?

    JProb = BeforeJ * AfterJ
    HProb = BeforeH * AfterH

    if otherprob > JProb and otherprob > HProb:
        return otheroption, otherprob
    elif JProb > HProb:
        return Jekyll, JProb
    elif HProb > JProb:
        return Hyde, HProb
    else:
        return "", HProb


def as_stream(linelist, verbose = False):
    '''converts a list of lines to a list of tokens
    this is considerably simpler than the version of this function
    in Volume.py. It also tests to see whether this file needs long-s correction.
    '''
    
    global breakselected, felecterrors, selecttruths
    
    tokens = list()
    for line in linelist:
        line = line.rstrip()
        if len(line) < 1:
            continue
        if line.startswith('<') and line.endswith('>'):
            tokens.append(line)
            tokens.append('\n')
            continue
        
        # We adopt a solution to punctuation that would be
        # inappropriate in other contexts: we actually want
        # to treat common punctuation marks as free-standing words.
        # I.e. "full ftop." is three tokens 1) full 2) ftop 3) .
        
        # Punctuation is treated this way in the Google database
        # where I got my bigram list,
        # and since punctuation marks a syntactic break, it's
        # arguably just as relevant contextually as anything
        # on the other side of the break.

        # You could do this with commas as well, but I haven't,
        # because commas got zapped at an earlier stage of file-
        # cleaning (they so often fuse words that it seemed easier
        # to change them globally to whitespace). I preserve
        # original formatting when I can, but only IF it's easy
        # to do so in a way that doesn't interfere with my
        # real goal, which is accurate tokenization & wordcounting.
        
        line = line.replace('.', ' . ')
        line = line.replace('(', ' ( ')
        line = line.replace(')', ' ) ')
        line = line.replace(';', ' ; ')
        line = line.replace(':', ' : ')
        line = line.replace('--', ' - ')
        line = line.replace('!', ' ! ')
        line = line.replace('?', ' ? ')
        line = line.replace('ﬅ', 'st')
        line = line.replace('ſ', 's')
        
        lineparts = line.split()
        tokens.extend(lineparts)
        tokens.append('\n')

    # Now we have a list of tokens. Let's see if it needs long-s correction.
    errors = 1
    truths = 1
    # 1 = Laplacian correction.
    for word in felecterrors:
        errors = errors + tokens.count(word)
    for word in selecttruths:
        truths = truths + tokens.count(word)

    print(truths/errors)

    if truths > errors:
        LongSproblem = False
    else:
        LongSproblem = True

    return tokens, LongSproblem

def catch_ambiguities(tokenlist, verbose = False):
    global AmbiguousPairs, AmbiguousTriggers, punctuationset
    
    deletions = {}
    additions = {}
    corrected = []
    changedphrases = []
    unchanged = {}

    # pre-processing is necessary in this version of Context, because the incoming
    # tokenstream still fuses punctuation marks with words, but the body of
    # catch_ambiguities assumes they are separate list elements

    separatedlist = list()

    for token in tokenlist:
        if len(token) < 1:
            continue
        
        if token[-1] in punctuationset and len(token) > 1:
            separatedlist.append(token[:-1])
            separatedlist.append(token[-1])
            # basically, we add the word and its trailing punctuation as two separate items.
            continue
        else:
            separatedlist.append(token)

    del tokenlist

    for indexnum, origtoken in enumerate(separatedlist):
        # TEI markup and single characters, including newline characters, should
        # pass through unchanged, except for punctuation characters, which get magnetically
        # attracted to the previous word.
        
        if origtoken.startswith('<') and origtoken.endswith('>'):
            corrected.append(origtoken)
            continue

        if origtoken in punctuationset and len(corrected) > 1:
            corrected[-1] = corrected[-1] + origtoken
            continue
        
        if len(origtoken) < 2:
            corrected.append(origtoken)
            continue

        if "-" in origtoken and verbose:
            wordparts = origtoken.split("-")
            for part in wordparts:
                if part in AmbiguousTriggers:
                    correctionphrase = " ".join(["UNCHANGED HYPHEN:", origtoken])
                    changedphrases.append(correctionphrase)
        # Right now I'm not attempting to correct the parts of hyphenated words.
        # This "verbose" option is included for the debug run just to see what
        # kinds of problems I may be ignoring.
        
        token = origtoken.lower()
        if origtoken.istitle():
            Titlecased = True
        else:
            Titlecased = False
            
        if origtoken.isupper():
            Uppercased = True
        else:
            Uppercased = False
            
        if token in AmbiguousTriggers:
            if token == "fad":
                additions = add_or_inc('sad', additions)
                deletions = add_or_inc('fad', deletions)
                token = "sad"
                continue
            
            # The word 'fad' doesn't exist before 1825, and I'm only running this script on early texts.
            # So I globally convert 'fad' to 'sad' without question.

            # Now we need to get the "previous" word and the "next" word -- a task complicated
            # by the fact that the previous or next tokens could be TEI or a newline character.
            
            preceded = '#nought'
            followed = '#nought'

            if indexnum > 4:
                for j in range(1, 3):
                    if (not tokenlist[indexnum - j].startswith('<')) and tokenlist[indexnum - j] !='\n':
                        preceded = tokenlist[indexnum - j].lower()
                        break
                
            if indexnum < (len(tokenlist)- 4):
                for j in range(1, 3):
                    if (not tokenlist[indexnum + j].startswith('<')) and tokenlist[indexnum + j] !='\n':
                        followed = tokenlist[indexnum + j].lower()
                        break
                
            for Pair in AmbiguousPairs:
                Tweedledee, Tweedledum = Pair
                if token == Tweedledee or token == Tweedledum:
                    RealMcCoy, prob = disambiguate(preceded, token, followed, Pair)
                    # we get a probability back that we don't use in this context

                    if RealMcCoy != token and RealMcCoy != "":
                        if verbose:
                            correctionphrase = " ".join([preceded, token, followed, "=>", preceded, RealMcCoy, followed])
                            changedphrases.append(correctionphrase)
                            
                        additions = add_or_inc(RealMcCoy, additions)
                        deletions = add_or_inc(token, deletions)
                        token = RealMcCoy
                    else:
                        if verbose:
                            correctionphrase = " ".join([preceded, token, followed, "<= KEPT"])
                            changedphrases.append(correctionphrase)
                        unchanged = add_or_inc(token, unchanged)
                       
                    break

                # "Break" because we assume that a token can only match
                # one ambiguous pair. The only exception I know of is
                # flip - slip - ship, and that's handled recursively in the
                # disambiguate function
                
            if Titlecased:
                origtoken = token.title()
            elif Uppercased:
                origtoken = token.upper()
            else:
                origtoken = token
                
            # If we considered any ambiguity, we pass the (possibly corrected)
            # token back to "origtoken," while restoring the original case of the token.
            
        corrected.append(origtoken)
                
    return deletions, additions, corrected, changedphrases, unchanged
