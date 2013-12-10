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