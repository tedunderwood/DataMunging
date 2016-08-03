#!/usr/bin/env python3

# metadedup.py

# This is an aggressive version of deduplication.

# Our goal here is to deduplicate the post-1922
# part of the corpus, first by checking whether
# it's already in the existing corpus, and then
# also by checking for duplication within itself.

# We additionally discard volumes written
# by authors who died 20yrs before publication.

import csv, os, sys, math
from collections import Counter

# import utils
currentdir = os.path.dirname(__file__)
libpath = os.path.join(currentdir, '../lib')
sys.path.append(libpath)

import SonicScrewdriver as utils
from difflib import SequenceMatcher
import FileCabinet as cabinet

def standardize_name(weirdname):
    standardname = ''
    for character in weirdname:
        if character == ' ' or character == '-' or character.isalpha():
            standardname += character

    standardname = standardname.lower().replace('from old catalog', '')
    return standardname

inpath = '/Volumes/TARDIS/work/fullmeta/litenrichment.tsv'

newfic = []
oldfic = []

with open(inpath, encoding = 'utf-8') as f:
    reader = csv.DictReader(f, delimiter = '\t')
    fieldnames = reader.fieldnames
    for row in reader:
        genre = row['sampledas']
        if genre != 'bio':
            continue
            # right now we're running on biography

        authdate = row['authordate']
        birth, death = cabinet.parse_authordate(authdate)
        date = utils.date_row(row)
        if death > 0 and death < 1920:
            oldfic.append(row)
            continue
        elif death > 0 and death + 20 < date:
            oldfic.append(row)
            continue
        else:
            stdauthor = standardize_name(row['author'])
            row['stdauthor'] = stdauthor
            newfic.append(row)

def numeric_only(astring):
    numonly = ''
    for character in astring:
        if character.isdigit():
            numonly += character

    return numonly

def trim2equallen(stringA, stringB, minimum):
    minlen = min(len(stringA), len(stringB))
    if minlen > minimum:
        matchA = stringA[0: minlen]
        matchB = stringB[0: minlen]
    else:
        matchA = stringA
        matchB = stringB

    return matchA, matchB, minlen

def lengthfactor(anint):
    l = math.log(anint + 2)
    if l > 3:
        l = 3
    return l

def match_row(authorA, authorB, titleA, titleB):
    matchA, matchB, minauthlen = trim2equallen(authorA, authorB)
    m = SequenceMatcher(None, matchA, matchB)
    authormatch = m.ratio()

    if authormatch < 0.85:
        return 0

    matchA, matchB, mintitlelen = trim2equallen(titleA, titleB)
    m = SequenceMatcher(None, matchA, matchB)
    titlematch = m.ratio()

    if titlematch < 0.7:
        return 0

    return authormatch * titlematch * lengthfactor(mintitlelen)

def match_strings(authorA, authorB, minimum):
    matchA, matchB, minauthlen = trim2equallen(authorA, authorB, minimum)
    m = SequenceMatcher(None, matchA, matchB)
    authormatch = m.ratio()

    return authormatch

ctr = 0
fictionbyauth = dict()

with open('/Users/tunder/Dropbox/python/nonfic/deduplicatedbio.csv', encoding = 'utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        ctr += 1
        if ctr > 100000:
            break

        stdauthor = standardize_name(row['author'])
        row['stdauthor'] = stdauthor

        firstchar = ''
        if len(stdauthor) > 1:
            firstchar = stdauthor[0:2]

        if firstchar not in fictionbyauth:
            fictionbyauth[firstchar] = []

        fictionbyauth[firstchar].append(row)

print('Beginning to dedup.')

filtered = []
ctr = 0
for row in newfic:
    print(ctr)
    ctr += 1
    newauthor = row['stdauthor']
    newtitle = row['title']

    firstchar = ''
    if len(newauthor) > 1:
        firstchar = stdauthor[0:2]

    matched = False

    if firstchar in fictionbyauth:

        for oldrow in fictionbyauth[firstchar]:
            if matched:
                break

            match = match_strings(newauthor, oldrow['stdauthor'], 10)
            if match > 0.85:
                # too close for comfort
                if 'date' in oldrow:
                    olddate = int(oldrow['date'])
                else:
                    olddate = utils.date_row(oldrow)
                if olddate < 1900:
                    matched = True
                    continue
                    # probably a really old author
                else:
                    titlematch = match_strings(newtitle, oldrow['title'], 20)
                    if match > 0.8:
                        matched = True
                        continue
                        # author and title basically match

                # if you made it this far, it may be a work by an author who
                # published something else in the 20c
    else:
        fictionbyauth[firstchar] = []

    if not matched:
        fictionbyauth[firstchar].append(row)
        filtered.append(row)
    else:
        oldfic.append(row)

with open('/Volumes/TARDIS/work/post23/post1923dedupedbio.tsv', mode = 'w', encoding = 'utf-8') as f:
    writer = csv.DictWriter(f, fieldnames = fieldnames, extrasaction ='ignore', delimiter = '\t')
    writer.writeheader()
    for row in filtered:
        writer.writerow(row)

with open('/Volumes/TARDIS/work/post23/post1923redundantbio.tsv', mode = 'w', encoding = 'utf-8') as f:
    writer = csv.DictWriter(f, fieldnames = fieldnames, extrasaction ='ignore', delimiter = '\t')
    writer.writeheader()
    for row in oldfic:
        writer.writerow(row)




