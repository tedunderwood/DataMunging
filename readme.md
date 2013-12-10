# DataMunging

This repo contains scripts (mostly in Python 3) for correcting OCR
and wrangling metadata drawn from HathiTrust. The scripts in /OCRnormalizer are packaged and ready to run (if you've got Python 3.2 or above).

###OCRnormalizer 0.1
OCRnormalizer corrects and normalizes OCR versions of English books published after 1700. It addresses the notorious "long S" problem, rejoins words broken across a linebreak, standarizes word division, and normalizes spelling to modern British practice. 

The name is "normalizer" rather than "corrector" because its goal is explicitly not to reproduce the original page image but to produce a standardized corpus that permits meaningful comparisons across time and across the Atlantic Ocean (e.g. "to day" and "to-day" turn into "today," "honor" turns into "honour", "fame" turns into "same" in 18c contexts where we can infer that it was originally "same").

To run the script, clone this repo and run OCRnormalizer/OCRnormalizer.py under Python 3. The rules it needs are in /rulesets, and the script should be able to find them if /rulesets and /OCRnormalizer are under the same parent directory.

The script will ask you where your files are located and what format they're in. It can take plain text files or zip files. You can provide the files in a flat folder, but the script will also (by default) recursively search subfolders. This means that you can use it to translate every file within (for instance) the kind of pairtree structure provided by HathiTrust Digital Library.

You can also select only certain files within a pairtree structure by providing pairtree identifiers.

The script writes a cleaned version of the text file (with the suffix clean.txt) to the original folder location. With very minimal editing, it could also write a wordcounts file (version 0.2 will probably include that feature).

### /HathiMetadata

If you've got metadata from Hathi as a bunch of separate .json files (one per volume) but would prefer to have that as a single .tsv table, the script in /HathiMetadata will do that.

/InventingRules contains scripts I used to produce rules, as does
/typeindexer

/rulesets contains the resulting rulesets (they're specialized for 18/19c English orthography, and aren't universally applicable)

/CorrectingTokenizing contains scripts I use to apply the rules to HathiTrust data. This includes a "contextual spellchecking" process that corrects phrases like "immortal foul," which cannot be corrected by 1gram rules.

/Unzip&RunningHeaders contains a process for tagging and separating the "running headers" at the tops of pages.

-- TU