'''
    This module reads in the dictionary files and stores them as sets.
    Current version will load multiple files (useful for keeping dictionaries
    modular, one for each language or each hyphenation or matching scheme) and
    compile them into a single dictionary.

    This module assumes that the dictionary is two fields per line.  I have
    not tested it with anything other than the two dictionaries packaged with
    the scripts, but it should work as along as the acceptable word is always
    the first on a line (regardless of how many fields are on a line).
'''

import glob

DictDirectory = "dictionaries/"

TabChar="\t"

MainDictionary = set()

## Currently reads in dictionary with frequencies, ignores frequencies

def BuildLexicon(dictionarypath, verbose=False):

    Dictionary = dictionarypath + "MainDictionary.txt"

    if verbose:
        print("Building Dictionary")       

    tempdict = set()
    with open(Dictionary, encoding='utf-8') as file:
        linelist = file.readlines()
        for workline in linelist:
            words = workline.split(TabChar)
            tempdict.add(words[0])
    MainDictionary.update(tempdict)

    if verbose:
        print(str(len(MainDictionary)) + " words added\n")

    return MainDictionary

## If executed independently, will just display the list in the console.

if __name__ == '__main__':
    BuildLexicon(True)
