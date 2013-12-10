# DataMunging

This repo contains scripts (mostly in Python) for wrangling data and metadata drawn from HathiTrust.

For instance, if you've got metadata from Hathi as a bunch of separate .json files (one per volume) but would prefer to have that as a single .tsv table, the script in /HathiMetadata will do that.

Most of the other folders are involved in an OCR correction process. Part of that process is described in the OCRflowchart in the main folder.

/InventingRules contains scripts I used to produce rules, as does
/typeindexer

/rulesets contains the resulting rulesets (they're specialized for 18/19c English orthography, and aren't universally applicable)

/CorrectingTokenizing contains scripts I use to apply the rules to HathiTrust data. This includes a "contextual spellchecking" process that corrects phrases like "immortal foul," which cannot be corrected by 1gram rules.

/Unzip&RunningHeaders contains a process for tagging and separating the "running headers" at the tops of pages.

-- TU