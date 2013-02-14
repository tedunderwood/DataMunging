import glob
import os
import TokenGen
import Dictionary
import TypeIndex
import FileCabinet

debug = False
batchcount = 100

pathdictionary = FileCabinet.loadpathdictionary()

datapath = pathdictionary["datapath"]
metadatapath = pathdictionary["metadatapath"]
dictionarypath = pathdictionary["dictionarypath"]
outputpath = pathdictionary["outputpath"]

if os.path.isfile(outputpath + "processed.txt"):
    with open(outputpath + "processed.txt", encoding="utf-8") as file:
        lines = file.readlines()
    startindex = int(lines[-1]) + 1
else:
    startindex = 0
       
HTIDfile = metadatapath + "htids.txt"
with open(HTIDfile, encoding="utf-8") as file:
    HTIDlist = file.readlines()

if startindex >= len(HTIDlist):
    print("Finished processing the whole list of volume IDs.")
    quit()
elif startindex + batchcount > len(HTIDlist):
    endindex = len(HTIDlist)
else:
    endindex = startindex + batchcount

Lexicon = Dictionary.BuildLexicon(dictionarypath, debug)

writename = 'typeindex.txt'

delim = '\t'

if startindex == 0:
    BigIndex = dict()
else:
    BigIndex = TypeIndex.ReadIndex(writename, delim, debug)

SortedIndex = list()

for index in range(startindex, endindex):
    IDtoprocess = HTIDlist[index].strip()
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

    volacc = TypeIndex.GetAcc(tokens,Lexicon,debug)

    types = TypeIndex.GetTypes(tokens,verbose=debug)

    TypeIndex.UpdateIndex(BigIndex, types, volacc, debug)

### Deletes BigIndex after copying to list in order to save memory

SortedIndex = TypeIndex.SortIndex(BigIndex, debug)

del BigIndex

TypeIndex.WriteIndex(SortedIndex, outputpath + writename, delim, debug)

print("Volumes processed this session: ", endindex - startindex)

with open(outputpath + "processed.txt", mode = 'a', encoding = 'utf-8') as file:
    file.write(str(index) + '\n')

