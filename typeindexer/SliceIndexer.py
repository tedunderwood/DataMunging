import os
import sys
import TokenGen
import Dictionary
import TypeIndex
import FileCabinet

slicename = sys.argv[1]
## We assume the slice name has been passed in as an argument.

datapath = "/projects/ichass/usesofscale/nonserials/"
metadatapath = "/projects/ichass/usesofscale/hathimeta/slices/" + slicename + ".txt"
dictionarypath = "/projects/ichass/usesofscale/dictionaries/"
outputpath = "/projects/ichass/usesofscale/ocr/slices/"
       
HTIDfile = metadatapath
with open(HTIDfile, encoding="utf-8") as file:
    HTIDlist = file.readlines()

Lexicon = Dictionary.BuildLexicon(dictionarypath, debug)

writename = slicename + "IND.txt"

delim = '\t'

BigIndex = dict()

SortedIndex = list()

for IDtoprocess in HTIDlist:
    IDtoprocess = IDtoprocess.strip()
    filepath, postfix = FileCabinet.pairtreepath(IDtoprocess, datapath)
    filename = filepath + postfix + '/' + postfix + ".txt"

    try:
        with open(filename, encoding='utf-8') as file:
            lines = file.readlines()
            successflag = True
    except IOError as e:
        successflag = False

    if not successflag:
        print(IDtoprocess + " is missing.")
        continue
        
    tokens = TokenGen.keep_hyphens(lines,Lexicon,verbose=debug)

    if len(tokens) < 10:
        print(IDtoprocess, "has only tokencount", len(tokens))

    volacc = TypeIndex.GetAcc(tokens,Lexicon,debug)

    types = TypeIndex.GetTypes(tokens,verbose=debug)

    TypeIndex.UpdateIndex(BigIndex, types, volacc, debug)

### Deletes BigIndex after copying to list in order to save memory

SortedIndex = TypeIndex.SortIndex(BigIndex, debug)

del BigIndex

TypeIndex.WriteIndex(SortedIndex, outputpath + writename, delim, debug)

print("Volumes processed this session: ", len(HTIDlist))

