ReadMe.txt for /HathiMetadata

metamine.py is a script we used to mine metadata from the .jsons provided by Hathi. This was originally written by Mike Black, rather than Ted Underwood.

For version two, Ted fixed problem where metamine only got the short version of a title if there's a colon or semicolon. (My hack was to also scoop the title from outer levels of the .json rather than the MARC xml, and accept whichever was longer.)

For version three of metamine.py, Ted added a couple of lines of code to get info from tag 970 of the MARC record. Biographies are tagged more reliably there than they are in the "subjects" field.

I also got rid of a few features that were slowing down the script (e.g. printing every file it processed to screen and keeping a datedump list).