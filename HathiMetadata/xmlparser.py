## MetaParser.py
##
## This Python script is designed to parse the file of XML records provided by
## HathiTrust Digital Library to accompany their data.
##
## The general strategy is to read in the XML, one MARC record at a time, and parse
## the record for basic information which is then written in a tabular form, simpler
## to browse, and simpler for subsequent analytics to parse.
##
## Note that HathiTrust has two different layers of MARC records, one for volumes (items), and
## one for bibliographic "records" (manifestations). This script is designed to deal with
## volume-level MARC records Hathi tends to bundle in a meta.tar.gz file. But there is often more
## info available in the record-level MARCs that populate the leaves of a pairtree, and/or
## the MARCs contained in .jsons.
##
## See transcripts of e-mail by Tim Cole for a full account of these complexities.
##
## Large parts of this code are extracted from metamine.py, written by Mike Black (2012);
## it was subsequently adapted by Ted Underwood (2013). There are three main levels of
## changes:
##
## 1) Ingestion of source data is different, because we're dealing with xml rather than
## a folder of .jsons.
##
## 2) The HathiTrust volume ID and enumcron must be extracted from datafield 974.
##
## 3) I've added a function to parse the genre information in controlfield 008.
## I also move the genre terms from datafield 655 to this "genre" list rather than
## treating them as subject terms, as we did before. This means that the genre list
## will contain a combination of terms from two sources.
##
## A couple of notes about specific genre terms in that field.
##
## "Not fiction" ≠ nonfiction. It's based on one byte in controlfield 008, and
## includes a lot of poetry and drama, which are only rarely labeled by genre.
##
## "Biography" may not necessarily mean "nonfiction" either! I've seen some records
## labeled "Fiction;Biography."
##
## If the biography byte is ambiguous/missing, I add a term "biog?" to register that it has
## some Bayesian prior possibility of being Biography inasmuch as no one specifically
## said it wasn't. But it's not a very strong prior!


import xml.dom.minidom as xml

print("This script is designed to unpack the volume-level metadata in")
print("the meta.tar.gz file that HathiTrust tends to send with its data.")
print("Note that there's also usually record-level, or shall we say book-level")
print("metadata, available in jsons and/or in the individual mets files.")
print("This script will unpack records into a .tsv file with information")
print("on HTid, recordID, OCLC, author, title, date, pub info, vol number,")
print("subject headings and genre headings. Note that some fields may be")
print("<blank>, and there's no guarantee the date will always be four-digit &")
print("numeric. You get a lot of date ranges, estimated dates, etc.")
print("For detailed interpretation of the genre terms provided by this")
print("script, see the comments in the file. The important thing to note")
print("is that 'Not fiction' means what it says and != 'nonfiction'.")
print("Many works tagged as as 'not fiction' will actually be poetry and")
print("drama. Don't assume any category is tagged consistently or exhaustively;")
print("the tags were created by many different people over a period of years.")
print("")
print("I need the path to the unzipped meta.tar.gz file, including filename.")
print("You can just drag it to the Terminal window & paste for a shortcut.")
print('')
inpath = input('Input path? ')

print('')
print('Thanks! Now I need the path where you want me to put the extracted')
print("metadata table. This should end with a slash. You can paste the same")
print("string and just erase the previous filename, for a shortcut.")
print('')
outpath = input("Output path? ")
outpath = outpath + "ExtractedMetadata.tsv"

print("This will overwrite any file named", outpath)
user = input("Okay? Say 'no' to stop: ")
if user == "no":
    quit()

print("\nOkay, thanks. Will now proceed to unpack the metadata. I'll print")
print("the number of files I've unpacked every thousand or so.")
print('\n')

centuries = {'17','18','19'}
genredictionary = dict()

def numcount(string):
    count = 0
    for char in string:
        if char.isnumeric():
            count += 1
    return count

def startswithdate(string):
    length = len(string)
    digits = numcount(string)

    if length > 3:
        firstfour = numcount(string[0:4])
        if firstfour > 3:
            startsright = True
        else:
            startsright = False
    else:
        startsright = False

    if not startsright:
        return False
    elif digits / length > 0.5:
        # should also be mostly numeric
        return True
    else:
        return False

def extract_subfields(node):

    if not node.hasChildNodes():
        if node.nodeValue == None:
            return list()
        else:
            return [node.nodeValue]
    else:
        first_child = node.firstChild
        valuelist = extract_subfields(first_child)
        if first_child.nextSibling == None:
            return valuelist
        else:
            moresibs = True
            prev = first_child
            while moresibs:
                nextsib = prev.nextSibling
                nextlist = extract_subfields(nextsib)
                valuelist.extend(nextlist)
                if nextsib.nextSibling == None:
                    moresibs = False
                else:
                    prev = nextsib

            return valuelist

def datefinder(subfields):
    date = '<blank>'

    ## If subfields has data in it, check each field for a date.
    if len(subfields) > 0:
        for entry in subfields:
            if type(entry) != type(str()):
                continue

            fixed = entry
            ## Correct OCR errors in the century
            if 'l7' in fixed:
                fixed = fixed.replace('l7','17')
            elif 'l8' in fixed:
                fixed = fixed.replace('l8','18')
            elif 'l9' in fixed:
                fixed = fixed.replace('l9','19')
            fixed = fixed.replace('-118','-18')
            fixed = fixed.strip('., ABCDEFGHIJKLMNOPQRSTUVWYZabcdefghijklmnopqrstuvwxyz<>-_?[]()&')
            fixed = fixed.replace('l','1')
            fixed = fixed.replace('[',' ')
            fixed = fixed.replace(']',' ')
            fixed = fixed.replace('(','')
            fixed = fixed.replace(')','')

            ## If there looks like a date but there are extra spaces, remove them
            if len(fixed) == 6 and fixed[:2] in centuries and fixed.replace(' ','').isnumeric():
                date = fixed.replace(' ','')
            elif len(fixed) == 5 and fixed[:2] in centuries and fixed.replace(' ','').isnumeric():
                date = fixed.replace(' ','')

            ## Check to see if there is a date in the string.  If so, make sure it's not a range.  If it's a range
            ## then send the range off to be checked.
            if len(fixed) >= 4 and fixed[:4].isnumeric() and fixed[:2] in centuries:
                date = fixed[:4]
                if len(fixed) >=5 and fixed[4] == '-':
                    date = cleanrange(fixed)
                break
            elif len(fixed) >= 4 and fixed[-4:].isnumeric():
                date = fixed[-4:]
                if len(fixed) >= 9 and fixed[-5] == '-':
                    date = cleanrange(fixed)
                break

        ## Check to see if date is an estimate before returning.  If it appears to be an estimate, return the
        ## date wrapped in an error code.  If date doesn't seem to at least have a partial date, then
        ## return it with an unparsed error code.
        fixed = entry.strip('. ')
        ##fixed = fixed.replace(' ','')
        if date == '1800' or date == '<blank>':
            numcount = 0
            for char in fixed:
                if char.isnumeric():
                    numcount += 1
            if numcount >= 2 and (fixed.endswith('?') or fixed.endswith(']') or fixed.endswith('-') or fixed.endswith('_')):
                fixed = fixed.strip('., ABCDEFGHIJKLMNOPQRSTUVWYZabcdefghijklmnopqrstuvwxyz')
                date = '<estimate="' + fixed + '">'
                return date
            elif len(fixed) < 4 and fixed.isnumeric() and date !='1800':
                date = '<estimate="' + fixed + '">'
                return date
            elif fixed[:2] in centuries and date != '1800':
                if len(fixed) == 4 and numcount == 3 and fixed.find('l') >= 0:
                    date = fixed.replace('l','1')
                    return date
                date = '<estimate="' + fixed + '">'
                return date
            elif date == '<blank>':
                date = '<unparsed="' + fixed + '">'
                return date
        ## If the date found isn't an estimate or partial, return it as normal.
        else:
            return date

    ## If subfields is empty, return default date value (blank code).  This will also catch any 1800s
    ## that are not found to be estimates.
    return date

def cleanrange(date):
    ## Sometimes removing brackets creates an extra space after the hyphen that causes
    ## the date to be unparsed.  This corrects that error.
    date = date.strip()
    baddash = {'-0-','-1-','-2-','-3-','-4-','-5-','-6-','-7-','-8-','-9-'}
    fix = str()

    date = date.replace(',',' ')

    dashcount = 0

    for char in date:
        if char == '-':
            dashcount += 1

    if dashcount > 1:
        for error in baddash:
            if error in date:
                fix = error
        if fix != str():
            date = date.replace(fix,'-')

    if len(date) >= 9 and date[:4].isnumeric() and date[-4:].isnumeric() and date[4] == '-' and date[5] == ' ':
        date = date[:5] + date[-4:]
    elif len(date) >= 9 and date[:4].isnumeric() and date[-4:].isnumeric() and date[4] == ' ' and date[5] == '-':
        date = date[:4] + date[-5:]


    ## If there are 5 digits in the first set, then there might have been an OCR error.
    ## First, try removing the first digit in case the date got pressed into another number
    ## (which often happens in enumcron dates).  If it's just a case of a repeated digit
    ## inside the starting date, there's no way to tell for sure which digit is repeated
    ## since 18822, for example, could be 1882 or 1822.
    if len(date) >= 5 and date[:5].isnumeric() and date[0] != '1':
        date = date[1:]
    elif len(date) >= 5 and date[:5].isnumeric():
        date = '<estimate="' + date + '">'
        return date

    ## If there's more than one character with a blank character, its probably an estimate
    if '--' in date or '__' in date or dashcount > 1:
        if len(date) >= 9 and date[:4].isnumeric() and date[4] == '-' and date[5:7] in centuries and date.find(' ') > 8:
            temp = date.split()
            date = cleanrange(temp[0])
        elif len(date) >= 9 and date[:4].isnumeric() and date[4] == '-' and date[5:7] in centuries and date[5:9].isnumeric:
            date = cleanrange(date[:9])
        elif len(date) >= 7 and date[:4].isnumeric() and date[4] == '-' and date[5:7].isnumeric():
            date = cleanrange(date[:7])
        elif len(date) >= 8 and date[:4].isnumeric() and date[4] == '-' and date[5] == ' ' and date[6:8].isnumeric():
            date = cleanrange(date[:5] + date[6:])
        elif len(date) >= 4 and (not date[4].isnumeric()) and date[-4:].isnumeric() and date[-5] == '-' and date[-4:-2] in centuries:
            date = date[-4:]
        else:
            date = '<estimate="' + date + '">'

    ## If date is at or below expected date, check for OCR error and known abbreviations
    elif len(date) <= 9:
        ## Sometimes the last date appears as [84], remove non-numerics for correction
        date = date.replace('[','')
        date = date.replace(']','')
        ## Determine why length of date range string is less than 9
        if len(date) < 7:
            ## If hyphen isn't the 5th value, digits are missing from the leading year
            if len(date) >4 and date[4] != '-':
                if date[-4:].isnumeric() and date[-4:-2] in centuries:
                    date = date[-4:]
                else:
                    date = '<unparsed="' + date + '">'
            ## Range is within the same decade, so end date is only represented by 1 digit
            elif len(date) == 6 and int(date[3]) < int(date[5]):
                date = date[:5] + date[:3] + date[5]
            ## If date is not a range but a valid date, then end this check and return the date!
            elif len(date) == 4 and date.isnumeric():
                return date
            ## Doesn't fit expected errors, so assign error code and return
            else:
                date = '<unparsed="' + date + '">'
        elif date[:2] in centuries:
            ## 17 is sometimes incorrectly OCR'd as 11
            if date[:2] == '17' and date[5:7] == '11' and len(date) == 9:
                date = date[:6] + '7' + date[7:]
            ## Sometimes the century is not included in the end-date
            elif not date[5:7] in centuries:
                ## If the century is missing, the years should still be greater
                ## than the begin-date
                if date[2:4].isnumeric() and date[5:7].isnumeric() and int(date[2:4]) < int(date[5:7]):
                    date = date[:5] + date[:2] + date[5:]
                elif date[:4].isnumeric():
                    date = date[:4]
                ## Otherwise its probably an error, return unparsed code
                else:
                    date = '<unparsed="' + date + '">'

    ## If date is longer than expected, determine whether its a bad range
    ## or just has some non-numeric characters embedded in it.
    else:
        ## If there are trailing characters, crop date!
        if (not date[9].isnumeric()) and date[8].isnumeric() and (date.find(' ') >= 9 or date.find(' ') == -1):
            date = date[:9]
        ## If not, there are probably some bad characters in play. Remove
        ## and then restart this cleaner function with all characters
        ## preceding the first space (to catch & fix dates less than 9)
        else:
            remove = set()
            for char in date:
                if char.isnumeric():
                    continue
                elif char != '-' and char != ' ':
                    remove.add(char)
            for char in remove:
                date = date.replace(char,'')
            x = date.find(' ')
            former = numcount(date[:x])
            latter = numcount(date[x:])
            if x != -1:
                if latter > former:
                    date = cleanrange(date[x+1:])
                else:
                    date = cleanrange(date[:x])
            else:
                date = cleanrange(date)

## Return date with corrections.  If no errors were found, return original date
    return date

def croncheck(enumcron,date):
    ## If the enumcron is not long enough to possibly contain a date,
    ## then return the original date
    if len(enumcron) < 4:
        return date
    ## Otherwise loop through the enumcrom, checking to see if a set of
    ## four continguous characters is numeric.  If so, check to see if
    ## it looks like a date within expected range. Return if a new date is
    ## found.  Otherwise, just return the old one.
    else:
        ## Spaces around volume numbers trip up recursion loops.  So scan through
        ## the enumcron string to find the first set of characters that looks
        ## like a date and slice to remove leading volume numbers
        temp = str()
        enumcron = enumcron.replace('(',' ')
        enumcron = enumcron.replace(')',' ')
        enumcron = enumcron.replace(',',' ')
        enumcron = enumcron.rstrip()
        for i,n in enumerate(enumcron):
            if i + 4 < len(enumcron):
                if enumcron[i:i+4].isnumeric():
                    temp = enumcron[i:]
                    break

        ## Check to see if one of the valid century strings is in enumcron before
        ## proceeding.  If not, then just return the original date.
        for num in centuries:
            if num in enumcron and not ('1' + num) in enumcron:
                valid = True
                break
            else:
                valid = False

        if not valid:
            return date

        temp = datefinder([enumcron])
        ## If the date resolver returns an errorcode, return the original date
        if temp.startswith('<'):
            return date
        ## If date is a range but date in numcron isn't, return the date resolved
        ## from the enumcron
        elif len(date) > len(temp):
            return temp
        ## If they're both ranges, return the one with the smallest
        elif len(date) == 9 and len(temp) == 9:
            x = int(date[-4:]) - int(date[:4])
            y = int(temp[-4:]) - int(temp[:4])
            if y < x:
                return temp
            else:
                return date
        ## If all else fails, just return the original date!
        else:
            return date

def subfield_dictionary(field):
    '''Returns a dictionary of codes and code values for the subfields of a datafield.
    Specifically used right now to distinguish subfields a and c of datafield 974.'''
    subfields = field.getElementsByTagName('subfield')
    codedictionary = dict()

    for subfield in subfields:
        subsublist = extract_subfields(subfield)
        atrilist = subfield.attributes
        atrilen = atrilist.length
        for i in range(0, atrilen):
            attribute = atrilist.item(i)
            codedictionary[attribute.value] = subsublist[i]

    return codedictionary

def parse008(field):
    '''Parses the information in fixed-width control field 008,
    extracting a date that may or may not correspond with the date
    drawn from the rest of the record, as well as a set of genre
    descriptors.

    I'm using information here to do it:
    http://www.loc.gov/marc/bibliographic/bd008b.html
    '''

    genres = set()
    datetype = field[6]
    date1 = field[7:11]
    date2 = field[11:15]
    place = field[15:18]

    audience = field[22]
    if audience == 'b' or audience == 'c' or audience == 'd' or audience == 'j':
        genres.add('Juvenile audience')
    ## I define "juvenile" broadly as anything from primary school to 'adolescent.'


    contents = field[24:28]
    if 'b' in contents:
        genres.add('Bibliographies')
    if 'c' in contents:
        genres.add('Catalog')
    if 'd' in contents:
        genres.add('Dictionary')
    if 'e' in contents:
        genres.add('Encyclopedia')
    if 'f' in contents:
        genres.add('Handbooks')
    if 'g' in contents:
        genres.add('Legal articles')
    if 'i' in contents:
        genres.add('Indexes')
    if 'l' in contents:
        genres.add('Legislation')
    if 'r' in contents:
        genres.add('Directories')
    if 's' in contents:
        genres.add('Statistics')
    if 'v' in contents:
        genres.add('Legal cases')
    if '5' in contents:
        genres.add('Calendars')

    form = field[33]
    if form == '0':
        genres.add('NotFiction')
    elif form == '1':
        genres.add('Fiction')
    elif form == 'd':
        genres.add('Drama')
    elif form == 'e':
        genres.add('Essays')
    elif form == 'f':
        genres.add('Novel')
    elif form == 'h':
        genres.add('Humor')
    elif form == 'i':
        genres.add('Letters')
    elif form == 'j':
        genres.add('Short stories')
    elif form == 'm':
        genres.add('Mixed')
    elif form == 'p':
        genres.add('Poetry')
    elif form == 's':
        genres.add('Speeches')
    else:
        genres.add('UnknownGenre')

    biog = field[34]
    if biog == "b" or biog == "c":
        genres.add("Biography")
    elif biog == "a":
        genres.add("Autobiography")
    elif biog == "#":
        genres.add("NotBiographical")
    elif biog == "d":
        genres.add("ContainsBiogMaterial")

    return datetype, date1, date2, place, genres

def get_materialtype(leaderstring):
    ctrlchar = leaderstring[7]
    materialtype = '<blank>'

    if ctrlchar == 'a' or ctrlchar == 'c' or ctrlchar == 'd':
        materialtype = "monograph part(s)"
    if ctrlchar == 'b':
        materialtype = "serial part"
    if ctrlchar == 'i':
        materialtype = "serial integration"
    if ctrlchar == 'm':
        materialtype = "monograph"
        if leaderstring[19] == "a":
            materialtype = "monograph set"
        if leaderstring[19] == "b" or leaderstring[19] == "c":
            materialtype = "monograph part"
    if ctrlchar == 's':
        materialtype = "serial"

    return materialtype

def parsemarc(marc):
    HTid = '<blank>'
    recordid = '<blank>'
    author = '<blank>'
    title = '<blank>'
    date = '<blank>'
    LOCnum = '<blank>'
    imprint = '<blank>'
    enumcron = '<blank>'
    OCLC = '<blank>'
    materialtype = '<blank>'
    subjset = set()
    genreset = set()
    alternatedate = ""

    leaderfields = marc.getElementsByTagName('leader')
    leaderfield = leaderfields[0]
    # There should only be one leader.
    leader = extract_subfields(leaderfield)[0]
    materialtype = get_materialtype(leader)

    controlfields = marc.getElementsByTagName('controlfield')
    for field in controlfields:
        value = extract_subfields(field)[0]
        fieldnumber = ""
        if field.hasAttributes():
            attrilist = field.attributes
            attrilen = attrilist.length
            for i in range(0,attrilen):
                attribute = attrilist.item(i)
                if attribute.name == 'tag':
                    fieldnumber = attribute.value

        if fieldnumber == "001":
            recordid = value.replace("MIU01-", "")

        if fieldnumber == "008":
            datetype, date1, date2, place, genreset = parse008(value)

    datafields = marc.getElementsByTagName('datafield')
    for field in datafields:
        if field.hasAttributes():
            attrilist = field.attributes
            attrilen = attrilist.length
            for i in range(0,attrilen):
                attribute = attrilist.item(i)
                if attribute.name == 'tag':
                    if attribute.value == '245':
                        title = extract_subfields(field)[0]
                        title = title.rstrip(' /:.,')
                    elif attribute.value =='050':
                        nums = extract_subfields(field)
                        LOCnum = str()
                        for chunk in nums:
                            LOCnum += chunk
                        LOCnum = LOCnum.strip('[]')
                    elif attribute.value == '260':
                        pubinfo = extract_subfields(field)
                        date = datefinder(pubinfo)
                        for subfield in pubinfo:
                            if not len(subfield) > 0:
                                continue
                            if imprint == '<blank>':
                                imprint = str()
                            imprint += subfield.strip(' :,[];') + ';'
                        imprint = imprint.rstrip(';')
                    elif attribute.value == '100':
                        author = extract_subfields(field)[0]
                    elif attribute.value == '974':
                        subfields = subfield_dictionary(field)
                        if 'a' in subfields:
                            HTid = subfields['a']
                        if 'c' in subfields:
                            enumcron = subfields['c']
                    elif attribute.value == "655" or attribute.value == "155":
                        genreterms = extract_subfields(field)
                        for term in genreterms:
                            if term[0].isupper():
                                genreset.add(term.rstrip('.,;'))
                    elif attribute.value.isnumeric() and int(attribute.value) >= 600 and int(attribute.value) <= 699:
                        subjterms = extract_subfields(field)
                        for term in subjterms:
                            subjset.add(term.rstrip('.,'))
                    elif attribute.value == '970':
                        subjterms = extract_subfields(field)
                        if 'Biography' in subjterms:
                            subjset.add('IsBiographical')
                    elif attribute.value == '035':
                        controlcode = extract_subfields(field)[0]
                        if '(OCoLC)' in controlcode:
                            controlcode = controlcode.replace('(OCoLC)', '')
                            controlcode = controlcode.replace('ocn', '')
                            controlcode = controlcode.replace('ocm', '')
                            OCLC = controlcode

    if materialtype.startswith("ser") and numcount(date) < 4 and numcount(enumcron) > 4:
        enumparts = enumcron.split(" ")
        if len(enumparts) > 1:
            lastpart = enumparts[-1]
            lastpart = lastpart.replace("(", "")
            lastpart = lastpart.replace(")", "")

            if startswithdate(lastpart):
                date = lastpart

    return HTid, recordid, author, title, date, LOCnum, imprint, enumcron, OCLC, subjset, genreset, materialtype, datetype, date1, date2, place

## HERE IS WHERE THE MAIN ROUTINE BEGINS.

writestring = 'HTid\trecordid\tOCLC\tLOCnum\tauthor\timprint\tdatetype\tstartdate\tenddate\ttextdate\tplace\tenumcron\tmaterialtype\tsubjects\tgenres\ttitle\n'

with open(outpath, mode='w',encoding='utf-8') as outfile:
    outfile.write(writestring)

with open(inpath, encoding='utf-8') as file:
    recordstring = ""
    beginflag = False
    counter = 0

    for newline in file:

        if newline == "<record>\n":
            beginflag = True

        if beginflag:
            recordstring = recordstring + newline.strip()
            # Remove whitespace!

        if newline == "</record>\n":
            counter += 1

            marc = xml.parseString(recordstring)
            HTid, recordid, author, title, textdate, LOCnum, imprint, enumcron, OCLC, subjset, genreset, materialtype, datetype, date1, date2, place = parsemarc(marc)

            if HTid == '<blank>':
                print("Blank HTID: " + title)
                continue

            subjstr = '<blank>'
            if len(subjset) > 0:
                subjstr = str()
                for term in subjset:
                    subjstr += (term + ';')
                subjstr = subjstr.rstrip(';')

            genrestr = '<blank>'
            if len(genreset) > 0:
                genrestr = str()
                for term in genreset:
                    genrestr += (term + ';')
                    if term in genredictionary:
                        genredictionary[term] += 1
                    else:
                        genredictionary[term] = 1

                genrestr = genrestr.rstrip(';')

            writestring = HTid + '\t' + recordid + '\t' + OCLC + '\t' + LOCnum + '\t' + author + '\t' + imprint + '\t' + datetype + '\t' + date1 + '\t' + date2  + '\t' + textdate + '\t' + place + '\t' + enumcron + '\t' + materialtype + '\t'+ subjstr + '\t' + genrestr  +'\t' + title
            writestring = writestring.replace('\n', '') + '\n'

            with open(outpath, mode='a',encoding='utf-8') as outfile:
                outfile.write(writestring)

            recordstring = ""
            if counter % 1000 == 1:
                print(counter)

print('Metadata file successfully created. Now I can review the genre terms')
print("I encountered. This is useful just to get a sense of the range of info")
print("available and should not be taken as an accurate map of the collection,")
print("because genre is severely undercoded in MARC records. Further classification")
print("will be necessary. Note that I skip terms with frequency < 3.")
dummyvar = input("Are you ready ?")

alltuples = []
for genre, count in genredictionary.items():
    if count > 2:
        alltuples.append((count, genre))

alltuples.sort()
for tuple in alltuples:
    count, genre = tuple
    print(genre, '\t', count)
