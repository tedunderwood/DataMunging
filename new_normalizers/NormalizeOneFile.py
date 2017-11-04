# USAGE:
# from within this /workflow directory:
# python NormalizeOneFile.py file_to_crunch.txt > output.tsv

# The paths in NormalizeVolume only work if you do it from
# within this directory.

import FileCabinet
import NormalizeVolume
import sys

debug = False

pathdictionary = FileCabinet.loadpathdictionary('/Users/tunder/Dropbox/PythonScripts/workflow/PathDictionary.txt')

datapath = pathdictionary['datapath']
metadatapath = pathdictionary['metadatapath']
metaoutpath = pathdictionary['metaoutpath']
outpath = pathdictionary['outpath']

targetfile = sys.argv[1]

with open(targetfile, encoding='utf-8') as f:
    text = f.readlines()

tokens, pre_matched, pre_english, pagedata, headerlist = NormalizeVolume.as_stream([text], verbose=debug)

correct_tokens, pages, post_matched, post_english = NormalizeVolume.correct_stream(tokens, verbose = debug)

pagecounter = 0
masterdict = dict()
for page in pages:
    for item in page:
        if item in masterdict:
            masterdict[item] += page[item]
        else:
            masterdict[item] = page[item]


for key, value in masterdict.items():
    if not key.startswith('#'):
        print(key + '\t' + str(value))
