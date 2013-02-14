## TOKENIZING First Pass: Identifies common words and words not yet in the lexicon.

import codecs
import os
from operator import itemgetter

print('Begin')

TabChar = '\t'
SpaceChar = " "

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
    TokLis = list(Token)
    
    # Now in reverse.
    LastPos = len(TokLis) - 1
    WordBegun = False
    
    for Index in range(LastPos, 0, -1):
        if TokLis[Index].isalnum():
            Token = Token[:Index + 1]
            WordBegun = True
            break

    if not WordBegun:
        return ""
    else:
        return Token

## Open the MainDictionary, read it into Lexicon. In this program Lexicon
## is a universal mapper covering dictionary words (which map to themselves)
## as well as variant-spellings and syncopates (which map to corrections).
    

print('Loading dictionary.')

FileString = '/Users/tunderwood/Rules/Dictionaries/TokenDictionary.txt'
F = codecs.open(FileString, 'r', 'utf-8')
FileLines = F.readlines()
F.close()

Lexicon = {}

for Line in FileLines:
    Line = Line.rstrip()
    LineParts = Line.split(TabChar)
    Word = LineParts[0].rstrip()
    Word = Word.lower()
    Lexicon[Word] = Word

OutPath = "/Users/tunderwood/Rules/HyphenRules/"

InPath = "/Users/tunderwood/Rules/FileSources/"

SyncRules = {}
SyncCount = {}

FileString = "/Users/tunderwood/Rules/Dictionaries/SyncRules.txt"
F = codecs.open(FileString, 'r', 'utf-8')
FileLines = F.readlines()
F.close()

for Line in FileLines:
    Line = Line.rstrip()
    LineParts = Line.split(TabChar)
    Word = LineParts[0].rstrip()
    Corr = LineParts[1].rstrip()
    SyncRules[Word] = Corr
    SyncCount[Word] = 0

DirList = os.listdir(InPath)

Count = 0

NewSync = {}

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
        Line = Line.replace("--", " ")
        Line = Line.replace("_", " ")
        Line = Line.replace('▪', ' ')
        Line = Line.replace(';', ' ')
        Line = Line.replace('"', ' ')
        Line = Line.replace('[', ' ')
        Line = Line.replace(']', ' ')
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

    MaxLen = len(DVector)
    SkipWords = 0
    
    for Index, Word in enumerate(DVector):

        if SkipWords > 0:
            SkipWords = SkipWords - 1
            continue

        Word = Word.lower()
        
        Word = strip_punctuation(Word)

        if len(Word) > 2 and Word[-2:] == "'s":
            Word = Word[:-2]

        if Word in SyncCount:
            SyncCount[Word] +=1
        elif "'" in Word:
            if Word in NewSync:
                NewSync[Word] += 1
            else:
                NewSync[Word] = 1           

print('Done gathering words, now sorting.')

SyncSort = sorted(SyncCount.items(), key = itemgetter(1), reverse = True)
NewSort = sorted(NewSync.items(), key = itemgetter(1), reverse = True)

FileString = "/Users/tunderwood/Rules/Output/SyncRulesbyFreq.txt"
F = codecs.open(FileString, 'w', 'utf-8')
for Entry in SyncSort:
    Word, Freq = Entry
    Corr = SyncRules[Word]
    Line = Word + '\t' + Corr + '\t' + str(Freq) + '\n'
    F.write(Line)
F.close()

FileString = "/Users/tunderwood/Rules/Output/NewSyncRules.txt"
F = codecs.open(FileString, 'w', 'utf-8')
for Entry in NewSort:
    Line = Entry[0] + '\t' + str(Entry[1]) + '\n'
    F.write(Line)
F.close()

print('Done.')
