## thirdmetamine.py
##
## Differs from newmetamine.py in parsing the 970 "original format" field to get
## clues about whether it's a biography. I also deleted the datedump utility.

import xml.dom.minidom
import json
import glob
import os

outfile = 'thirdmetatable.txt'
centuries = {'17','18','19'}

def numcount(string):
    count = 0
    for char in string:
        if char.isnumeric():
            count += 1
    return count

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

if len(glob.glob(outfile)) > 0:
    print("Partial table from previous session found.  Removing.")
    os.remove(outfile)
    
if len(glob.glob('errorlog.txt')) > 0:
    print("Error log from previous session found.  Removing.")
    os.remove('errorlog.txt')

if len(glob.glob('datedump.txt')) > 0:
    print("Date debug log from previous session found.  Removing.")
    os.remove('datedump.txt')

print("Getting list of JSON files to be processed...")
books = glob.glob('/Users/tunderwood/Dropbox/jsons/*/*.json')
##books = ['jsons/mdp.39015066692198.json','jsons/mdp.39015074635734.json','jsons/mdp.39015025882450.json','jsons/hvd.hxp5y7.json','jsons/wu.89038972626.json','jsons/nyp.33433076093255.json','jsons/uva.x030805679.json']
print("List complete.")

count = 0

for filename in books:
##    if filename[6:9] != 'nyp' and filename[6:9] != 'pst':
##       continue
 
    count += 1
    pathparts = filename.split('/')
    HTid = pathparts[-1]
    # that gets rid of the directory parts of the path
    HTid = HTid[:-5]
    # that cuts the .json off
    HTid = HTid.replace('-','/')
    if (count % 100) == 99:
        print(str(count) + ":", "Preparing",HTid,"for writing to",outfile)
    
    with open(filename,encoding='utf-8') as file:
        x = file.read()
    
    raw = json.loads(x.rstrip())
    items = raw['items']
    records = raw['records']
 
    if len(records) > 1:
        continue
    
    for key in records:
        marc = xml.dom.minidom.parseString(records[key]['marc-xml'])
        recordid = key
            
    author = '<blank>'
    title = '<blank>'
    date = '<blank>'
    LOCnum = '<blank>'
    imprint = '<blank>'
    enumcron = '<blank>'
    subjstr = '<blank>'
    if 'titles' in records[recordid]:
        longertitle = records[recordid]['titles'][0]
        longertitle = longertitle.rstrip('/ ')
    else:
        longertitle = ""
    subjset = set()
 
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
                    elif attribute.value == '974' and enumcron == '<blank>':
                        tempcron = extract_subfields(field)
                        if tempcron[1] == HTid:
                            enumcron = tempcron[0]
                            date = croncheck(enumcron,date)
                        del tempcron
                    elif attribute.value.isnumeric() and int(attribute.value) >= 600 and int(attribute.value) <= 699:
                        subjterms = extract_subfields(field)
                        for term in subjterms:
                            subjset.add(term.rstrip('.,'))
                    elif attribute.value == '970':
                        subjterms = extract_subfields(field)
                        if 'Biography' in subjterms:
                            subjset.add('IsBiography')
                        
    
    if len(subjset) > 0:
        subjstr = str()
        for term in subjset:
            subjstr += (term + ';')
        subjstr = subjstr.rstrip(';')
        
    if date.startswith('<'):
        with open('errorlog.txt',mode='a',encoding='utf-8') as file:
            file.write(HTid + '\t' + date + '\t***' + imprint + '\t###' + enumcron + '\n')

    if len(longertitle) > len(title):
        title = longertitle

    writestring = HTid + '\t' + recordid + '\t' + LOCnum + '\t' + author + '\t' + title + '\t' + imprint + '\t' + date + '\t' + enumcron + '\t'+ subjstr + '\n'

    with open(outfile,mode='a',encoding='utf-8') as file:
        file.write(writestring)
