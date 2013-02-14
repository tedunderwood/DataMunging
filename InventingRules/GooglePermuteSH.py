## A routine that generates OCR-correction rules, for Google ngrams data
##
## After trying a number of different approaches, I found that the best
## approach to OCR correction in the Google dataset was to rely on pairs
## of known substitutions.
##
## This module accepts a list of ngrams drawn from Google data, and a
## dictionary (which should include period spellings). If an ngram doesn't
## match the dictionary, it sends it to the function find_matches,
## which takes a permutational approach to the problem. It goes through
## the list of substitution rules, and whenever it finds an applicable
## rule it permutes a list of possibilities by applying or not applying
## the rule to each possible "hit" in the string.
##
## So, for instance, if you give it "faflen' and the rule f->s,
## it will create the list [faflen, saflen, faslen, saslen]. Then it takes that
## list to the *next* rule and tries applying it to all the elements of the
## list. Say the rule fl->st. Now we have [faflen, fasten, saflen, sasten,
## faslen, saslen].
##
## When it's done considering all the rules, it goes through the list of
## possibilities and checks to see if there is one and only one
## dictionary word with a minimum edit distance. In this case, we get 'fasten.'
## If you get multiple matches with the same edit distance, the attempt
## to generate a correction rule will fail, and the ngram will be added
## to a list of ambiguous tokens.
##
## Matches also fail if the edit distance exceeds 1/3 the length of the string.
## Strings of three or fewer characters are not corrected; the number of
## short abbreviations and word parts creates too much possible ambiguity.
## I also haven't attempted to correct ngrams that are produced by the fusion
## of two words. Fusions do occur in the Google dataset, but the number is never
## huge, and without context, we would have to do too much guesswork.
##
## It would be different if we were correcting an individual document; there
## the problem of word division (and mistaken word-division) becomes
## important, and context would allow us to handle it better.
##
## The list of known OCR substitutions could be enlarged, but we should
## be careful how big we make it, because increasing
## the number of rules also increases possible ambiguity. The safest
## things to add would be rules for correcting uncommon symbols, like @;
## I haven't tried to catch all of those rules yet.
##
## The module can run in three different modes, #manual, #auto, or
## #assist. It defaults to manual, but the user can switch mode by
## replying '#auto' or '#assist' when prompted for input.
##
## Written in Python 3.2 for Mac OSX 10.6.6.
##
##

KnownSubstitutions = [('f', 's'), ('fl', 'ss'), ('fl', 'st'), ('&',
'ct'), ('ft', 'ct'), ('cl', 'ct'), ('dt', 'ct'),('dl', 'ct'), ('d',
'ct'), ('1', 'i'), ('1', 'l'), ('6', 'o'), ('6', 'e'), ('0', 'o'),
('c', 'e'), ('h', 'li'), ('H', 'li'), ('tb', 'th'), ('cb', 'ch'),
('ce', 'oe'), ('CE', 'OE'), ('U', 'll'), ('v', 'y'), ('jh', 'sh'),
('jb', 'sh'), ('m', 'sh'), ('fli', 'sh'), ('sb', 'sh')]

LimitedSubstitutions = [('f', 's'), ('fl', 'ss'), ('fl', 'st'), ('&',
'ct'), ('ft', 'ct'), ('cl', 'ct'), ('dt', 'ct'),('dl', 'ct'), ('1',
'i'), ('1', 'l'), ('6', 'o'), ('6', 'e'), ('0', 'o'), ('h', 'li'),
('tb', 'th'), ('cb', 'ch'), ('ce', 'oe'), ('CE', 'OE'), ('jh', 'sh'),
('jb', 'sh'), ('m', 'sh'), ('fli', 'sh'), ('sb', 'sh')]

def find_matches(ToBeMatched):
   """Use known substitutions to find a dictionary match."""

   Variants = {ToBeMatched: 0}
   VarCopy = {}
   if ToBeMatched[0].isupper() and len(ToBeMatched) < 6:
      Substitutions = LimitedSubstitutions
   else:
      Substitutions = KnownSubstitutions

   ## We start by looping through substitution rules.

   for RuleTuple in Substitutions:
      Target, Replacement = RuleTuple
      Tlen = len(Target)

      ## This is not elegant, but I make a copy of the list of
      ## variants (technically, a "dictionary" of variants)
      ## so that I can iterate through the copy while adding to
      ## the original dictionary.
      
      for Token, Distance in Variants.items():
         if Token not in VarCopy:
            VarCopy[Token] = Distance

      ## Another dictionary as a temporary holding place for added
      ## variants.

      AddedForTarget = {}
      
      for Variant, EditDistance in VarCopy.items():
         Hits = Variant.count(Target)
         
         if Hits < 1:
            continue

         StartSearch = 0
         Locations = []
         
         for i in range(Hits):
            NextHit = Variant.find(Target,StartSearch)
            StartSearch = NextHit + Tlen
            Locations.append(NextHit)

         Permutations = [Variant]
         
         for i in range(Hits):
            AddForLocation = []
            Loc = Locations[i]
            for Instance in Permutations:
               Replaced = Instance[0:Loc] + Replacement + Instance[Loc+Tlen:]
               AddForLocation.append(Replaced)
               
            Permutations.extend(AddForLocation)

         for i in range(1,len(Permutations)):
            AddedForTarget[Permutations[i]] = EditDistance + 1

      for Token, Distance in AddedForTarget.items():
         if Token not in Variants:
            Variants[Token] = Distance

   ##  Now we have the list of variants. We need to check to
   ##  find the best and second-best match, which are defined
   ##  as those with the smallest edit distance.

   BestV = ""
   SecBestV = ""
   SmallestD = len(ToBeMatched)
   SecSmallestD = len(ToBeMatched)

   for Variant, Distance in Variants.items():
      
      Variant = Variant.lower()
      
      if Variant not in CorLexicon:
         continue

      ## It's important that this be Variant.lower(); otherwise you won't match
      ## words containing capital letters unless the capital is in Substitutions.
   
      
      if Distance >= SecSmallestD:
         continue
      elif Distance <= SmallestD:
         SecBestV = BestV
         SecSmallestD = SmallestD
         BestV = Variant
         SmallestD = Distance
      elif Distance < SecSmallestD:
         SecBestV = Variant
         SecSmallestD = Distance
      else:
         print("Error in comparison.")

   return BestV, SmallestD, SecBestV, SecSmallestD


def spell_check(TWord):
   """Assess reliability of top two fuzzy matches, depending on UserMode."""

   ## MaxEdDist is a parameter establishing an edit distance above which
   ## we discard all matches. Right now I'm
   ## setting it to be 1/3 of the word length.
   
   MaxEdDist = len(TWord)/3
   BestMatch, EdDist, SecondBestMatch, SecondEdDist = find_matches(TWord)
   global UserMode

   ## What we do with the match depends on whether we're in user-assisted or
   ## autonomous mode. In autonomous mode, the module accepts all matches
   ## where the edit distance is not more than 1/3 the length of the string,
   ## and where there is only *one* match with a minimum edit distance.
   ## I.e., the second-best-edit-distance cannot = the best distance.
   ## I print the matches so we can see the results.

   if UserMode == "#auto":

      if (EdDist <= MaxEdDist) and (SecondEdDist > EdDist):
         print(TWord, BestMatch)
         return BestMatch

      ## Different failures are handled differently. If the match
      ## fails because the "best" and "second-best" matches
      ## had the same edit distance, we want to add the string to
      ## a list of ambiguous ngrams.
      
      elif EdDist <= MaxEdDist:
         return "#ambiguous"

      else:
         return ""

   elif UserMode == "#manual":

      ## In manual mode the matches we have found are purely informational.

      print(TWord, " ==> ", BestMatch, " at edit distance: ", EdDist)
      print(TWord, " ==> ", SecondBestMatch, " at edit distance: ", SecondEdDist)
      
      if EdDist > MaxEdDist:
         print('No match found.')

      Reply = (input("Actual match? "))
      Reply = Reply.lower()

      ## The next if statement is a clumsy patch that allows me to avoid
      ## "string index out of range" errors when the answer is "".

      if len(Reply) == 0:
         Reply="++"

      ## The number sign is an escape character that allows the user to switch modes.

      if Reply[0] =="#":
         UserMode = Reply
         Reply = (input("Actual match? "))
         Reply = Reply.lower() 
         if len(Reply) == 0:
            Reply="++"

      if Reply == "++":
         return ""
      else:
         return Reply

   else:

      ## In "assist mode," the computer automatically corrects clear matches, but queries
      ## the user for help if EdDist is not sufficiently below the cut-off and/or
      ## the second-best match.

      if (EdDist < MaxEdDist) and (SecondEdDist > EdDist):
         print(TWord, BestMatch)
         return BestMatch
      
      elif EdDist > MaxEdDist:
         return ""
      
      else:
         print(TWord, " ==> ", BestMatch, " at edit distance: ", EdDist)
         print(TWord, " ==> ", SecondBestMatch, " at edit distance: ", SecondEdDist)
      
         Reply = (input("Actual match? "))
         Reply = Reply.lower()

         if len(Reply) == 0:
            Reply="++"

         ## The number sign is an escape character that allows the user to switch modes.

         if Reply[0] =="#":
            UserMode = Reply
            Reply = (input("Actual match? "))
            Reply = Reply.lower()
            if len(Reply) == 0:
               Reply="++"

         if Reply == "++":
            return ""
         else:
            return Reply

## BEGIN MAIN ROUTINE.
##
## Set the mode to user-assisted. Once the script is correcting words
## reliably, the user can switch it to "autonomous."

import codecs
UserMode = "#auto"
Space = ' '
TabChar = '\t'

Number = str(input('Partition number? '))
FileSuffix = Number + '.txt'

## Open dictionary, read it into Lexicon, then
## strip newline and whitespace.

F = codecs.open('/Users/tunderwood/Spellcheck/Rules/MainDictionary.txt', 'r', 'utf-8')
FileLines = F.readlines()
Lexicon = set()
CorLexicon = set()
for Line in FileLines:
   Line = Line.rstrip()
   LineParts = Line.split(TabChar)
   Token = LineParts[0].rstrip()
   Freq = float(LineParts[1].rstrip())
   TokenLength = len(Token)
   if TokenLength > 2:
      Lexicon.add(Token)
   if TokenLength > 2 and Freq > 0.09 and 'sh' in Token:
      CorLexicon.add(Token)

F.close()


Punctuation = ".,?\"\'!:;"
StopWords = {"", "â€¢", "i", "v", "ii", "iii", "iv", "(", ")", "-"}
PunctuationSet = {".", "?", "!", ":", ";", '"', "'", ",", "—", "$", "£",
'″', "′", '”', "´", '*', '(', ')', '¢', '_', '[', ']'}

## Open Google data, and read it as a list of utf-8 tokens.


F = codecs.open('/Users/tunderwood/Databases/GoogleData/Raw'+Number+'Names.txt', 'r','utf-8')
FileLines = F.readlines()
F.close()
NgramList = []
Frequency = {}
for Line in FileLines:
   Line = Line.rstrip()
   LineParts = Line.split(TabChar)
   Token = LineParts[0].rstrip()
   TokenLength = len(Token)
   if TokenLength > 2:
      NgramList.append(Token)
      Frequency[Token] = int(LineParts[1].rstrip())
   
print('ngrams loaded')
del FileLines, LineParts

CorrectionRules = {}
UnCorrectable = []

for Ngram in NgramList:

   ## Since I don't assume that the dictionary is going to contain possessive versions of
   ## every noun, I truncate apostrophe-s and correct the truncated Word rather than the
   ## original Ngram

   if Ngram[-2:] == "'s":
      Word = Ngram[0:len(Ngram) - 2]
   else:
      Word = Ngram
      
   ## If a word is in the lexicon, or is simply a number, we skip over it.
   ## I'm working with a slimmed-down version of the Google dataset where
   ## ngrams that *begin* with non-alphabetic characters have already been
   ## deleted. But this script could also be used on a list of ngrams
   ## where numbers have been allowed to remain. That would be better,
   ## because it would allow us to catch tokens like "1isten."
   ##
   ## If you wanted to use this script on completely unfiltered Google data, 
   ## you would need to define a function
   ## that identifies all non-"word" ngrams so they could be ignored.
   ## For instance, you might want to ignore
   ## all ngrams that begin with a dollar sign, and most other kinds of punctuation.
   ## You could also use the resources of extended utf-8 character set, which
   ## I believe are present in the Google data, but are largely ignored in this script.
   ## I doubt that the extended character set makes much difference, but ...
      
   if (Word.lower() in Lexicon) or Word.isdigit() or Word[0] == '$' or Word[0] == '£':
      continue

   ## I've built in an ability to ignore certain stopwords, although this is a patch that
   ## it's probably best not to use.

   if Word.lower() in StopWords:
      continue
   
   ## Words that only have 1-3 characters are almost impossible to
   ## reliably correct; there's too great a probability that many of
   ## the occurrences represent random noise, or an abbreviation, etc.

   if len(Word) < 4:
      continue

   Letters = len(Word)
   Repeat = False
   if Letters > 3:
      for i in range(0, Letters-3):
         if Word[i] == Word[i+1] and Word[i+1] == Word[i+2]:
            Repeat = True

   if Repeat == True:
      continue     

   ## Words that don't match Lexicon get spell-checking. At the moment, I'm ignoring
   ## the possibility that a word might need to be divided into two valid dictionary
   ## words. The numbers of those occurrences are low in the Google dataset, and it
   ## enormously complicates the spell-checking task.

   Correction = spell_check(Word)

   ## The spell_check function returns a string of length zero if it fails to find
   ## a suitable match. We either append the Ngram to a list of uncorrectable Ngrams,
   ## or add Ngram, Correction as an entry in the dictionary of CorrectionRules.

   if Correction == "#ambiguous":
      UnCorrectable.append(Ngram)
   elif Correction == "":
      continue
   else:
      CorrectionRules[Ngram] = Correction

print('Done.')

## Write the list of ambiguous tokens, and the correction rules.

F = codecs.open('/Users/tunderwood/Databases/SHrules/Uncorrectable' + FileSuffix,'w', 'utf-8')
for Token in UnCorrectable:
   WriteString = Token + '\r'
   F.write(WriteString)
F.close()

print('Uncorrectable tokens saved as uncorrectable.txt.')

F = codecs.open('/Users/tunderwood/Databases/SHrules/Corrections' + FileSuffix,'w', 'utf-8')
for Ngram, Correction in CorrectionRules.items():
   WriteString = Ngram + '\t' + Correction + '\t' + str(Frequency[Ngram]) + '\r'
   F.write(WriteString)
F.close()

print('Correction rules saved as CorrectionRules.txt. Script complete.')








