## Hyphen RULEBUILDER

import codecs
import os

print('Begin')

TabChar = '\t'

Punctuation = {".", "?", "!", ":", ";", '"', "'", ",", "—", "$", "£",
'″', "′", '”', "´", '*', '(', ')', '¢', '_', '[', ']'}

def strip_punctuation(Token):
    """Strip punctuation marks from the beginning and end of a word"""

    TokLis = list(Token)
    
    WordBegun = False

    for Index, Char in enumerate(TokLis):
        if Char.isalnum():
            Token = Token[Index:]
            WordBegun = True
            break

    if not WordBegun:
        return ""

    # Now in reverse.

    LastPos = len(TokLis) - 1

    for Index in range(LastPos, 0, -1):
        if TokLis[Index].isalnum():
            Token = Token[:Index + 1]
            break

    return Token

## Open the MainDictionary, read it into Lexicon.

print('Loading dictionary.')

FileString = '/Users/tunderwood/Spellcheck/Rules/MainDictionary.txt'
F = codecs.open(FileString, 'r', 'utf-8')
FileLines = F.readlines()
F.close()

Lexicon = set()

for Line in FileLines:
   Line = Line.rstrip()
   LineParts = Line.split(TabChar)
   Word = LineParts[0].rstrip()
   Lexicon.add(Word)

Lexicon = frozenset(Lexicon)
del FileLines

OutPath = "/Users/tunderwood/Rules/HyphenRules/"

InPath = "/Users/tunderwood/Rules/FileSources/"

DirList = os.listdir(InPath)

SyncoFreq = {}
SyncoCorr = {}

HyphFreq = {}

Count = 0

DocLen = len(DirList)

Tenth = int(DocLen/10)
Tenths = frozenset(range(Tenth, DocLen+Tenth, Tenth))
TenthCount = 10

for FileName in DirList:

    if FileName[0] == '.' or FileName[-1] != 't':
        print('Skipping hidden file', FileName)
        continue

    Count += 1

    if Count in Tenths:
        print(TenthCount,'%', sep='')
        TenthCount += 10
    
    FileString = InPath + FileName
    F = codecs.open(FileString, 'r', 'utf-8')
    Document = F.readlines()
    F.close()

    DVector = []

    for Line in Document:
        Line = Line.rstrip()
        if Line == '' or Line.isdigit():
            continue

    ## Split each line into words after replacing certain problematic substrings.
        Line = Line.replace('äî', ' ')
        Line = Line.replace('Äî', ' ')
        Line = Line.replace('ñ™', ' ')
        Line = Line.replace(chr(8218), ' ')
        Line = Line.replace(chr(8212), ' ')
        Line = Line.replace(".", " ")
        Line = Line.replace(",", " ")
        Line = Line.replace("--", " ")
        Line = Line.replace("_", " ")
        Line = Line.replace('▪', ' ')
        Line = Line.replace(';', ' ')
        Line = Line.replace('"', ' ')
        Line = Line.replace('[', ' ')
        Line = Line.replace(']', ' ')
        Line = Line.replace('!', ' ')
        Line = Line.replace('?', ' ')
        Line = Line.replace('&', ' ')
        Line = Line.replace(':', ' ')
        Line = Line.replace('|', '')
        Line = Line.replace(chr(8739), '')
        Line = Line.replace('{', '')
        Line = Line.replace('}', '')
        Line = Line.replace('′', "'")
        Line = Line.replace('´', "'")
        WordList = Line.split()

        # Extend the doc vector by adding these words.

        DVector.extend(WordList)

    for Index, Word in enumerate(DVector):


        Word = Word.lower()
        Word = strip_punctuation(Word)

        if len(Word) < 2:
            continue

        if Word[-2:] == "'s":
            Word = Word[:-2]

        if Word[-2:] == "'d":
            ThreeWord = Word[:-3] + "ied"
            TwoWord = Word[:-2] + "ed"
            
            if TwoWord in Lexicon:
                CorrectWord = TwoWord
            elif ThreeWord in Lexicon:
                CorrectWord = ThreeWord
            else:
                CorrectWord = "n/a"

            if Word in SyncoCorr:
                SyncoFreq[Word] += 1
            else:
                SyncoCorr[Word] = CorrectWord
                SyncoFreq[Word] = 1
            
        if "-" in Word:
            if Word in HyphFreq:
                HyphFreq[Word] += 1
            else:
                HyphFreq[Word] = 1

print('Done initial read.')

WriteList = []

for Word, Freq in SyncoFreq.items():
    Line = Word + '\t' + SyncoCorr[Word] + '\t' + str(Freq) + '\n'
    WTuple = (Freq, Line)
    WriteList.append(WTuple)

WriteList = sorted(WriteList, key = lambda Pair: Pair[0], reverse = True)

FileString = OutPath + 'Syncopates.txt'
F = codecs.open(FileString, 'w', 'utf-8')
for WTuple in WriteList:
    Freq, Line = WTuple
    F.write(Line)
F.close()

del WriteList
del SyncoFreq
del SyncoCorr

WriteList = []

for Word, Freq in HyphFreq.items():
    Line = (Word, Freq)
    WriteList.append(Line)

WriteList = sorted(WriteList, key = lambda Pair: Pair[1], reverse = True)

FileString = OutPath + 'HyphFreq.txt'
F = codecs.open(FileString, 'w', 'utf-8')
for WTuple in WriteList:
    Word, Freq = WTuple
    Line = Word + '\t' + str(Freq) + '\n'
    F.write(Line)
F.close()

del WriteList

print('Exported HyphFreq.')

# Generate a dictionary containing all first elements in the list of hyphenated terms,
# another dictionary containing tuples of the separate elements,
# and a third containing the elements fused as a word.

FirstParts = {}
TupleFreq = {}
FusedFreq = {}

for Word, Freq in HyphFreq.items():
    
    First, Sep, Second = Word.partition("-")
    if First in FirstParts:
        FirstParts[First] += 1
    elif Second != "" and First.isalnum():
        FirstParts[First] = 1
        
    ## There are some hidden consequences of that elif, because we only check tuple
    ## versions in cases where the first element is in FirstParts.
        
    if Freq < 5:
        continue

    Unhyphed = Word.replace('-', ' ')
    WordTuple = tuple(Unhyphed.split())
    TupleFreq[WordTuple] = 0
    
    Fused = Word.replace('-', '')
    FusedFreq[Fused] = 0


## Count the fused and tuple versions.
Count = 0
Total = 0

for FileName in DirList:

    if FileName[0] == '.' or FileName[0] == 'K' or FileName[-1] != 't':
        continue
    print(FileName)
    FileString = InPath + FileName
    F = codecs.open(FileString, 'r', 'utf-8')
    Document = F.readlines()
    F.close()

    DVector = []

    for Line in Document:
        Line = Line.rstrip()
        if Line == '' or Line.isdigit():
            continue

    ## Split each line into words after replacing certain problematic substrings.
        Line = Line.replace('äî', ' ')
        Line = Line.replace('Äî', ' ')
        Line = Line.replace('ñ™', ' ')
        Line = Line.replace(chr(8218), ' ')
        Line = Line.replace(chr(8212), ' ')
        Line = Line.replace(".", " ")
        Line = Line.replace(",", " ")
        Line = Line.replace("--", " ")
        Line = Line.replace("_", " ")
        Line = Line.replace('▪', ' ')
        Line = Line.replace(';', ' ')
        Line = Line.replace('"', ' ')
        Line = Line.replace('[', ' ')
        Line = Line.replace(']', ' ')
        Line = Line.replace('!', ' ')
        Line = Line.replace('?', ' ')
        Line = Line.replace('&', ' ')
        Line = Line.replace(':', ' ')
        Line = Line.replace('|', '')
        Line = Line.replace(chr(8739), '')
        Line = Line.replace('{', '')
        Line = Line.replace('}', '')
        Line = Line.replace('′', "'")
        Line = Line.replace('´', "'")
        WordList = Line.split()

        # Extend the doc vector by adding these words.

        DVector.extend(WordList)

    Total += len(DVector)
    Count += 1
    
    for Index, Word in enumerate(DVector):

        Word = Word.lower()
        Word = strip_punctuation(Word)

        if len(Word) < 1:
            continue

        if Word in FusedFreq:
            FusedFreq[Word] += 1

        if Word not in FirstParts:
            continue

        TwoWord = tuple(DVector[Index: Index+2])
        if TwoWord in TupleFreq:
            TupleFreq[TwoWord] += 1
            continue

        ThreeWord = tuple(DVector[Index: Index+3])
        if ThreeWord in TupleFreq:
            TupleFreq[ThreeWord] += 1

# Write the frequencies of hyphenated, fused, and split versions.

Average = int(Total/Count)
print('Average word length', Average)

WriteList = []

for Word, Freq in HyphFreq.items():
    
    Unhyphed = Word.replace('-', ' ')
    WordTuple = tuple(Unhyphed.split())
    
    Fused = Word.replace('-', '')

    Fuse = FusedFreq.get(Fused, 0) * 10
    Tup = TupleFreq.get(WordTuple, 0) * 10

    # Does the word mostly occur hyphenated, fused, split, or is it ambiguous?

    if Freq > Fuse and Freq > Tup:
        Most = "H"
    elif Fuse > Freq and Fuse > Tup:
        Most = "F"
    elif Tup > Freq and Tup > Fuse:
        Most = "S"
    else:
        Most = "A"

    if Fused in Lexicon:
        Most = "D"
    
    Line = Word + '\t' + str(Freq)  + '\t' + str(Fuse) + '\t' + str(Tup)  + '\t' + Most + '\n'
    WTuple = Most, Freq, Line
    WriteList.append(WTuple)

WriteList = sorted(WriteList, key = lambda Element: Element[1], reverse = True)
WriteList = sorted(WriteList, key = lambda Element: Element[0])

FileString = OutPath + 'Hyphenates.txt'
F = codecs.open(FileString, 'w', 'utf-8')
for WTuple in WriteList:
    Most, Freq, Line = WTuple
    F.write(Line)
F.close()

del WriteList
            

        
