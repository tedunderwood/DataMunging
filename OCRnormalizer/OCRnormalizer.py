#!/usr/bin/env python
'''
OCRnormalizer 0.1

This script does OCR correction and normalization on text files submitted to it,
using a set of rules contained in the 'rulesets' folder. The goal is
not to fix all possible errors, but to address major variations, especially
problems like s/f substitution that are likely to produce distortion
because they are unequally distributed across the lexicon and across
the time axis.

The script corrects OCR a) using straightforward replacement rules for
single tokens known to be likely errors, and also b) using contextual rules to
guide replacement in cases like "damned fouls for" where context
makes clear that "fouls" is an error for "souls." It also c) rejoins words div-
ided across a linebreak, and d) normalizes word division and hyphenation to
a modern standard (e.g. "any where" or "any-where" become "anywhere.") It
removes hyphens from rare compound words so they can be treated as individual
elements. (E.g. "sixty-three-year-old" will be broken into components.)
It also e) normalises spelling to a modern British standard and 
f) unpacks syncope in eighteenth-century verbs like "remember'd."

All these decisions involve judgment calls that could be made differently,
so use this at your own risk. There is no warranty explicit or implicit,
etc. Try running it on a sample set of files and see if you like the
translation. If you would do things differently, feel free to fork the code
and rules and change them.

The script will accept files in several different ways. It can work on
text files of any kind, but it has special adaptations that let it
handle HathiTrust files in a pairtree structure if that's what you've got.
When it encounters zip files it assumes they are concatenations of individual .txt
files, one per page (this is the HathiTrust format). It concatenates them to produce
a single connected text file with <pb> tags that represent pagebreaks.

You can give files to this script in three ways.

1. Give it a flat folder full of text files (or zipped files from HathiTrust.)
2. Give it a file listing HathiTrust volume IDs that specify the location of
HT zip files in a pairtree structure.
3.  Just give it the root directory of a pairtree structure and let it
recursively walk the directory, correcting .txt files or .zip files.

In every case it produces a file with the suffix .clean.txt as output, and leaves it
in the folder where the original file was located.

Most of the actual correction gets done in the Volume2 module (for basic problems)
and the Context module (for tricky contextual OCR correction).

An errorlog is printed to the directory where files were stored, along with a list
of files that had the eighteenth-century 'long S' and needed contextual correction.

Written by Ted Underwood, 2011-2013, in Python 3.2.
CC-BY 3.0. Dec 2013.
'''

def main():
    import FileCabinet
    import FileUtils
    import Volume2
    import Context
    import sys
    import os

    print(sys.version)

    # DEFINE CONSTANTS.
    delim = '\t'
    debug = False
    felecterrors = ['fee', 'fea', 'fay', 'fays', 'fame', 'fell', 'funk', 'fold', 'haft', 'fat', 'fix', 'chafe', 'loft']
    selecttruths = ['see', 'sea', 'say', 'says', 'same', 'sell', 'sunk', 'sold', 'hast', 'sat', 'six', 'chase', 'lost']

    # Locate ourselves in the directory structure.

    cwd = os.getcwd()
    cwdparent = os.path.abspath(os.path.join(cwd, os.pardir))

    # We need to find a directory called 'rulesets,' which we expect to be located
    # either within the working directory or adjacent to it.

    if os.path.isdir(os.path.join(cwd, "rulesets")):
        rulepath = os.path.join(cwd, "rulesets")
    elif os.path.isdir(os.path.join(cwdparent, "rulesets")):
        rulepath = os.path.join(cwdparent, "rulesets")
    else:
        user = input("Please specify a path to the ruleset directory: ")
        if os.path.isdir(user):
            rulepath = user
        else:
            print("Invalid path.")
            sys.exit()

    # Use rulepath to load relevant rules inside modules.

    Volume2.importrules(rulepath)
    Context.importrules(rulepath)

    # Now we enter dialogue with the user. This is all a little 1982,
    # but what can I say? Wetware upgrades are expensive.

    def prompt(promptstring, options):
        user = input(promptstring)
        if user not in options:
            user = prompt(promptstring, options)
        return user

    # Ask the user to tell us how to find files to process.
    print("****************** CorrectOCR 0.1 ******************")
    print()
    print("Do you want the full spiel (explanations, caveats, etc.)")
    user = prompt("y/n : ", ["y", "n"])
    
    if user.lower() == "y":
        spielpath = os.path.join(cwd, "spiel.txt")
        with open(spielpath, encoding = 'utf-8') as file:
            filelines = file.readlines()
        for line in filelines:
            print(line, end='')

    print("\nThis script will correct .txt files, or extract text")
    print("from zipped archives containing one txt file for each page.")
    print("In either case it writes the cleaned files back to their")
    print("original locations with the new suffix '.clean.txt'.")
    print("\nDo you want to unpack .zip files or .txt files?")
    user = prompt("zip or txt: ", ["zip", "txt"])
    suffix = "." + user
    suffixlen = len(suffix)
    
    print("\nThere are two ways to identify the location of the")
    print("files to be corrected.")
    print("\n1. Provide the path to a folder that contains them. I'll")
    print("recursively search subdirectories of that folder as well. Or,")
    print("\n2. Provide a file holding a list of pairtree file identifiers,")
    print("e.g. HathiTrust Volume IDs. I can use those identifiers to infer")
    print("the paths to the files themselves.\n")

    user = prompt("Which option do you prefer (1 or 2)? ", ["1", "2"])
    
    if user == "1":
        print('\n')
        rootpath = input("Path to the folder that contains source files: ")
        filelist = FileUtils.recursivefilegetter(rootpath, suffix)
 
    else:
        print('\n')
        print("I expect the pairtree identifiers to be listed one per line,")
        print("and to be the only item on a line.")  
        filepath = input("Path to the file that contains pairtree identifiers: ")
        filelist = list()
        with open(filepath, encoding = 'utf-8') as file:
            filelines = file.readlines()

        print("Now I need a path to the folder that contains the pairtree structure.")
        print("If you have multiple folders for different libraries, this should be")
        print("the folder above them all. It should end with a slash.")
        rootpath = input("Path to the folder that contains pairtree: ")
        for line in filelines:
            line = line.rstrip()
            filepath, postfix = FileCabinet.pairtreepath(line, rootpath)
            filename = filepath + postfix + '/' + postfix + suffix
            filelist.append(filename)

    print("\nI identified", len(filelist), "files in that location.")
    print("Now proceeding to process them.\n")

    # Here's where we BEGIN THE ACTUAL CORRECTION OF FILES.
    
    processedmeta = list()
    errorlog = list()
    longSfiles = list()

    count = 0

    for filename in filelist:

        try:
            if suffix == ".zip":
                lines = FileUtils.readzip(filename)
                successflag = True
            else:
                with open(filename, encoding='utf-8') as file:
                    lines = file.readlines()
                    successflag = True
        except IOError as e:
            successflag = False

        if not successflag:
            print(filename + " is missing.")
            errorlog.append(filename + '\t' + "missing")
            continue
            
        tokens, pre_matched, pre_english = Volume2.as_stream(lines, verbose=debug)

        tokencount = len(tokens)
        
        if len(tokens) < 10:
            print(filename, "has only tokencount", len(tokens))
            errorlog.append(filename + '\t' + 'short')

        correct_tokens, pages, post_matched, post_english = Volume2.correct_stream(tokens, verbose = debug)

        # Combine page dictionaries into a master dictionary.
        # If you ask, why didn't you just produce one in the first place? ...
        # answer has to do with flexibility of the Volume module for other purposes.

        pagecounter = 0
        masterdict = dict()
        for page in pages:
            for item in page:
                if item in masterdict:
                    masterdict[item] += page[item]
                else:
                    masterdict[item] = page[item]

        # Now that we have a master dictionary, consider whether there are long-s problems.
        # This algorithm works adequately.

        errors = 1
        truths = 1
        # Initialized to 1 as a Laplacian correction.
        
        for word in felecterrors:
            errors = errors + masterdict.get(word, 0)
        for word in selecttruths:
            truths = truths + masterdict.get(word, 0)

        if truths > errors:
            LongSproblem = False
        else:
            LongSproblem = True

        if LongSproblem == False:
            corrected = correct_tokens
        else:
            longSfiles.append(filename)
            deleted, added, corrected, changedphrases, unchanged = Context.catch_ambiguities(correct_tokens, debug)
            # "deleted" and "added" are not used in this script

        # Write corrected file.
 
        outfilename = filename[:-suffixlen] + ".clean.txt"
        
        with open(outfilename, mode = 'w', encoding = 'utf-8') as file:
            lasttoken = ""
            for token in corrected:
                if lasttoken == '\n' and (token == '"' or token == "'"):
                    token = token
                elif token != '\n' and token != "“" and not (token.startswith('<') and token.endswith('>')):
                    token = token + " "
                    
                file.write(token)
                lasttoken = token

        print(outfilename)
        count += 1
        if count > 10:
            break
                
    # END ITERATION ACROSS FILES.
    
    # Write the errorlog and list of long S files.
    errorpath = os.path.join(rootpath, "processingerrors.txt")
    longSpath = os.path.join(rootpath, "longSfiles.txt")
    
    if len(errorlog) > 0:
        with open(errorpath, mode = 'w', encoding = 'utf-8') as file:
            for line in errorlog:
                file.write(line + '\n')

    if len(longSfiles) > 0:
        with open(longSpath, mode = 'w', encoding = 'utf-8') as file:
            for line in longSfiles:
                file.write(line + '\n')

    # Done.

if __name__ == "__main__":
    main()


