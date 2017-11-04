# USAGE:
# from within this /workflow directory:
# python NormalizeOneFolder.py folderoftexts outputfolder

# The paths in NormalizeVolume only work if you do it from
# within this directory.

import FileCabinet
import NormalizeVolume
import sys, os

args = sys.argv

inputfolder = args[1]
outputfolder = args[2]

if not os.path.isdir(inputfolder):
    print("Input folder " + inputfolder + " is not a directory.")
    sys.exit(0)

if not os.path.isdir(outputfolder):
    print("Output folder " + outputfolder + " is not a directory.")
    sys.exit(0)

infiles = os.listdir(inputfolder)

already_converted = [x.replace('.tsv', '.txt') for x in os.listdir(outputfolder) if x.endswith('.tsv')]

not_yet_converted = set(infiles) - set(already_converted)

print("There are " + str(len(not_yet_converted)) + " files still to convert.")
inpaths = [os.path.join(inputfolder, x) for x in not_yet_converted if x.endswith('.txt')]

outpaths = [os.path.join(outputfolder, x).replace('.txt', '.fic.tsv') for x in not_yet_converted if x.endswith('.txt')]

debug = False

pathdictionary = FileCabinet.loadpathdictionary('/Users/tunder/Dropbox/PythonScripts/workflow/PathDictionary.txt')

datapath = pathdictionary['datapath']
metadatapath = pathdictionary['metadatapath']
metaoutpath = pathdictionary['metaoutpath']
outpath = pathdictionary['outpath']

for targetfile, outfile in zip(inpaths, outpaths):

    outfile = outfile.replace('.txt', '.fic.tsv')

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

    with open(outfile, mode = 'w', encoding = 'utf-8') as f:
        for key, value in masterdict.items():
            if not key.startswith('#'):
                f.write(key + '\t' + str(value) + '\n')

os.system('say "your program has finished"')
