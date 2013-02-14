ReadMe.txt

The scripts on this page take HathiTrust documents that I've already unpacked from .zip and put them through a process of OCR correction and tokenization. The master script is CombinedCorrect.py. It calls "Volume" for most of the correction and tokenization, and calls "Context" for special problems of contextual spellchecking when you can't tell just from spelling that a word is an error. E.g. six/fix, singer/finger, etc.

These scripts are designed to work with documents in a pairtree structure, and FileCabinet handles some of the clerical aspects of that.

The rulesets loaded by these scripts are in the rulesets folder.