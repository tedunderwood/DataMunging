# DataMunging

This repo contains scripts (mostly in Python 3) for correcting OCR
and wrangling metadata drawn from HathiTrust. The scripts in /OCRnormalizer are packaged and ready to run (if you've got Python 3.2 or above).

### /OCRnormalizer 0.1
OCRnormalizer corrects and normalizes OCR versions of English books published after 1700. It addresses the notorious "long S" problem, rejoins words broken across a linebreak, standarizes word division, and normalizes spelling to modern British practice. 

The name is "normalizer" rather than "corrector" because its goal is explicitly not to reproduce the original page image but to produce a standardized corpus that permits meaningful comparisons across time and across the Atlantic Ocean (e.g. "to day" and "to-day" turn into "today," "honor" turns into "honour", "fame" turns into "same" in 18c contexts where we can infer that it was originally "same").

To run the script, clone this repo and run OCRnormalizer/OCRnormalizer.py under Python 3. The rules it needs are in /rulesets, and the script should be able to find them if /rulesets and /OCRnormalizer are under the same parent directory.

The script will ask you where your files are located and what format they're in. It can take plain text files or zip files. You can provide the files in a flat folder, but the script will also (by default) recursively search subfolders. This means that you can use it to translate every file within (for instance) the kind of pairtree structure provided by HathiTrust Digital Library.

You can also select only certain files within a pairtree structure by providing pairtree identifiers.

The script writes a cleaned version of the text file (with the suffix clean.txt) to the original folder location. If requested, it will also write a tab-separated file that contains wordcounts for each volume. On completion it writes three kinds of logs: a list of files not found or otherwise anomalous, a list of files thought to contain long-s, and a tab-separated table listing the percentage of words recognized before and after correction in each file.

### /pagefeatures

This folder contains a new-and-improved version of OCRnormalizer that I am currently only using locally. Whereas in OCRnormalizer I've made token efforts to generalize the scripts so that they could run on any machine, these scripts are very specifically adapted to my local work environment. They produce normalized versions of files that are a little cleaner than OCRnormalizer 0.1, specifically by preserving punctuation in places where OCRnormalizer will change or remove it. But they're also designed to output "page features" for a page-level classification workflow that is probably only relevant to me. TODO: merge this branch back into OCRnormalizer so the improvements I've made can be incorporated into a (slightly) more public-facing resource.

### /HathiMetadata

Contains scripts designed to extract tabular metadata from the file of xml MARC records that Hathi provides to accompany their data, or from .jsons extracted from the bibliographic API.

### /InventingRules contains scripts I used to produce rules, as does
/typeindexer

### /CorrectingTokenizing is mostly out-of-date right now.
