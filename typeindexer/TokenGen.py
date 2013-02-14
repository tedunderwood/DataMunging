'''
    This module reads in the specified text file and cleans it for use with
    accuracy and analytical modules.  It returns the "cleaned" file as a list.

    Current version has a Basic function that just strips punctuation and one
    that checks possible hyphenated end of line fusions against a dictionary
    and rules set (optionally).  The Hyphen function is buggy and probably not
    necessary for first pass eval.  I went ahead and included it here to show
    that this module can be structured to include multiple types of token
    generation depending on the level of scrutiny or cleaning desired.
'''

## Reads in file, stores as list, makes minimal corrections.

def Basic(Text, verbose=False):

    Punctuation = '.,():-—;"!?•$%@#<>+=/[]*^\'{}_■~\\|«»©&~`£·'

    if verbose:
        print("Generating tokens, ignoring end of line hyphens")

    words = list()
    discard = 0
              
    for line in Text:
        line = line.rstrip()
        line = line.replace(',',' ')
        words.extend(line.split())

## First checks to make sure that each word is not a formatting tag.  Then,
## strips punctuation from beginning/ending of words & sets all characters
## to lower-case to match lexicon.  Ignores digits, empty spots.
## NOTE: Commas removed above to account for numbers greater than 999.

## CONCERN: The check for XML/TEI tags won't work if the tag is touching
## a word.  For a first pass eval, this probably isn't a big deal.  In more
## precise processors/evals, will need to rewrite.

    cleanwords = list()

    for f in words:
        if f.endswith('>') and f.startswith('<'):
            discard = discard + 1
            continue
        f = f.strip(Punctuation)
        if len(f) < 1:
            discard = discard + 1
            continue
        if f.isdigit():
            discard = discard + 1
            continue
        cleanwords.append(f)

    if verbose:
        print("\t" + str(discard) + " items discarded")
        print("\t" + str(len(cleanwords)) + " tokens processed")

    return cleanwords


## This function is similar to the one above, but checks possible end of line
## hyphen splits against the dictionary.  If fusing produces a word, ignore
## fragments and add the new word to tokens.  If not, add both as tokens.

def Hyphen(Text,Lexicon,Rules={},verbose=False):

    Punctuation = '.,():-—;"!?•$%@#<>+=/[]*^\'{}_■~\\|«»©&~`£·'

    if verbose:
        print("Generating Tokens, checking end of line hyphens")

    words = list()
    cleanwords = list()
    corrections = 0
    discard = 0
    tryfuse = str()

    for line in Text:
        line = line.rstrip()
        line = line.replace(',',' ')
        
        checkwords = line.split()
        words = list()

## If XML/TEI tags, discard.  Then remove punctuation and discard anything that
## isn't a possible dictionary match.

        for w in checkwords:
            if w.startswith('<') and w.endswith('>'):
                discard = discard + 1
                continue
            w = w.strip(Punctuation)
            if w.isdigit():
                discard = discard + 1
                continue
            if len(w) < 1:
                discard = discard + 1
                continue
            words.append(w)            

## If the last loop detected a hyphen at the end of the line, then check to see
## if fusing with first token from current line produces a dictionary/rule match.
## If no match is found, then add to the beginning of the current line's list
## so that it will be added into the list of processed tokens at end of this loop
## Finally, reset fusion variable to an empty string.
                
        if tryfuse != str() and len(words) >= 1:

            if tryfuse + words[0] in Lexicon:                
                words[0] = tryfuse + words[0]
                corrections = corrections + 1

            elif len(Rules) >= 1 and tryfuse + words[0] in Rules:
                words[0] = tryfuse + words[0]
                corrections = corrections + 1

            else:
                words.insert(0, tryfuse)

            tryfuse = str()

## Before adding this line's processed tokens to list, check to see if the line
## ended with a hyphen.  If so, remove final token from this line's list and
## store in fusion variable for processing next loop.

        if (line.endswith('-') or line.endswith('—')) and len(words) > 0:
            tryfuse = words.pop()

        cleanwords.extend(words)

    if verbose:
        print("\t" + str(discard) + " items discarded")
        print("\t" + str(corrections) + " hyphenated line fragments fused")
        print("\t" + str(len(cleanwords)) + " tokens processed")

    return cleanwords

def break_hyphens(Text,Lexicon,Rules={},verbose=False):
    '''
    Tokenizes the Text passed in, breaking words at
    spaces, commas, quotes, dashes--and hyphens.
    Fuses words across linebreaks whenever doing so
    produces a valid word, whether or not there is an
    eol hyphen. TO BE USED FOR OCR-EVAL.
    '''

    Punctuation = '.,():-—;"!?•$%@#<>+=/[]*\'^{}_■~\\|«»©&~`£·'
    BreakablePunctuation = ',()-—;"!?'
    BreakDictionary = {}
    for character in BreakablePunctuation:
        BreakDictionary[character] = ' '
    BreakMap = BreakablePunctuation.maketrans(BreakDictionary)

    if verbose:
        print("Generating Tokens, breaking words at hyphens")

    words = list()
    cleanwords = list()
    corrections = 0
    discard = 0
    tryfuse = str()
    final_index = len(Text) - 1

    for index, line in enumerate(Text):
        line = line.rstrip()
        line = line.translate(BreakMap)
        
        checkwords = line.split()
        words = list()

## If XML/TEI tags, discard.  Then remove punctuation and discard anything that
## isn't a possible dictionary match.

        for w in checkwords:
            if w.startswith('<') and w.endswith('>'):
                discard = discard + 1
                continue
            w = w.strip(Punctuation)
            if w.isdigit():
                discard = discard + 1
                continue
            if len(w) < 1:
                discard = discard + 1
                continue
            words.append(w)            

## Always check last token from previous line to see whether
## fusing with first token from current line produces a dictionary/rule match.
## If no match is found, then add to the beginning of the current line's list
## so that it will be added into the list of processed tokens at end of this loop
                
        if tryfuse != str() and len(words) >= 1:

            if tryfuse + words[0] in Lexicon:                
                words[0] = tryfuse + words[0]
                corrections = corrections + 1

            elif len(Rules) >= 1 and tryfuse + words[0] in Rules:
                words[0] = tryfuse + words[0]
                corrections = corrections + 1

            else:
                words.insert(0, tryfuse)

## Before adding this line's processed tokens to list, remove final token from this
## line's list and store in fusion variable for processing next loop.
## Only exception is, if you're on the last line.

        if index < final_index and len(words) >= 1:
            tryfuse = words.pop()
        else:
            tryfuse = str()

        cleanwords.extend(words)

    if verbose:
        print("\t" + str(discard) + " items discarded")
        print("\t" + str(corrections) + " hyphenated line fragments fused")
        print("\t" + str(len(cleanwords)) + " tokens processed")

    return cleanwords

def keep_hyphens(Text,Lexicon,Rules={},verbose=False):
    '''
    Tokenizes the Text passed in, breaking words at
    spaces, commas, dashes--but not hyphens.
    Hyphenated words are preserved to be handled by a FormIndexer
    that will index *both* the hyphenated form and the parts.
    Fuse words across linebreaks whenever doing so creates
    dict/rule matches for previously unmatchable tokens. Where there is an
    eol hyphen but word won't fuse/match, turn word into hyphenated form.
    Does not strip kinds of punctuation that commonly
    serve as clues in correcting OCR.
    TO BE USED FOR The TypeIndexer.
    '''

    Punctuation = '.,():-—;"!?$%#<>+=/[]*^\'{}_~\\|«»©~`£·'
    BreakablePunctuation = ',—;"!?_'
    BreakDictionary = {}
    for character in BreakablePunctuation:
        BreakDictionary[character] = ' '
    BreakMap = BreakablePunctuation.maketrans(BreakDictionary)

    if verbose:
        print("Generating Tokens, keeping hyphens in words.")

    words = list()
    cleanwords = list()
    corrections = 0
    discard = 0
    tryfuse = str()
    final_index = len(Text) - 1
    eol_hyphen = False

    for index, line in enumerate(Text):
        line = line.rstrip()
        if line.startswith("<") and line.endswith(">"):
            continue
            ## because this is an xml tag!
        
        line = line.translate(BreakMap)
        line = line.replace('--', ' ')
        # Double-hyphens are probably dashes and should be split.
        
        if line.endswith('-'):
            eol_hyphen = True
        else:
            eol_hyphen = False
        
        checkwords = line.split()
        words = list()

## Remove punctuation and discard anything that
## isn't a possible dictionary match.

        for w in checkwords:
            if w.startswith('<') and w.endswith('>'):
                discard = discard + 1
                continue
            w = w.strip(Punctuation)
            if w.isdigit():
                discard = discard + 1
                continue
            if len(w) < 1:
                discard = discard + 1
                continue
            if len(w) > 29:
                discard = discard + 1
                continue
            words.append(w)            

## Always check last token from previous line to see whether
## fusing with first token from current line produces a dictionary/rule match.
## Fuse only if one of those tokens would otherwise not match.
## If there was a hyphen at the end of the line, but fusing does not
## produce a match, then treat the words as a hyphenated form; the FormIndexer
## will index both the parts and the compound.
            
## If no match is found, then add to the beginning of the current line's list
## so that it will be added into the list of processed tokens at end of this loop

                
        if tryfuse != str() and len(words) >= 1:

            if tryfuse + words[0] in Lexicon and (tryfuse not in Lexicon or words[0] not in Lexicon):                
                words[0] = tryfuse + words[0]
                corrections = corrections + 1

            elif tryfuse + words[0] in Rules and ((tryfuse not in Rules
            and tryfuse not in Lexicon) or (words[0] not in Rules and
            words[0] not in Lexicon)):
                words[0] = tryfuse + words[0]
                corrections = corrections + 1

            elif eol_hyphen:
                words[0] = tryfuse + "-" + words[0]
                corrections = corrections + 1

            else:
                words.insert(0, tryfuse)

## Before adding this line's processed tokens to list, remove final token from this
## line's list and store in fusion variable for processing next loop.
## Only exception is, if you're on the last line.

        if index < final_index and len(words) >= 1:
            tryfuse = words.pop()
        else:
            tryfuse = str()

        cleanwords.extend(words)

    if verbose:
        print("\t" + str(discard) + " items discarded")
        print("\t" + str(corrections) + " hyphenated line fragments fused")
        print("\t" + str(len(cleanwords)) + " tokens processed")

    return cleanwords
