## FileUtils
##
## Just a bunch of simple Python functions for interacting with files.
## 
## Ted Underwood
## Version 3
## Python 3.2.2
## Dec 8, 2013

import os
from zipfile import ZipFile

def clearpath(rootpath, suffix):
    '''Joins two parts to create a filepath and then checks
    to make sure it doesn't yet exist.'''

    firstpath = os.path.join(rootpath, suffix)
    
    if os.path.exists(firstpath):
        for i in range(2, 20):
            newpath = firstpath + "_" + str(i)
            if not os.path.exists(newpath):
                firstpath = newpath
                break

    return firstpath

def recursivefilegetter(filepath, suffix):
    '''
    Recursively walks a directory and all its subdirectories
    to extract paths to files that end with suffix.
    '''
    suffixlen = len(suffix)
    
    filelist = list()
    for root, dirs, files in os.walk(filepath):
        for file in files:
            if len(file) > suffixlen and file[-suffixlen:] == suffix:
                filepath = os.path.join(root, file)
                if len(filepath) > 10 and filepath[-10:] == ".clean.txt":
                    continue
                    # Because we don't want to reprocess files that are already clean.
                else:
                    filelist.append(filepath)
                    
    return filelist

def readzip(filepath):
    '''
    Reads a zipfile of numbered pages and returns a list of lines, separated
    by <pb> tags between pages. I tacitly assume I'm working with HathiTrust
    data.
    '''
    
    pagelist = []
    
    with ZipFile(filepath, mode='r') as zipvol:
        zippages = zipvol.namelist()
        zippages.sort()
        del zippages[0]
        count = 0
        for f in zippages:
            count += 1
            pagecode = zipvol.read(f)
            pagetxt = pagecode.decode('utf-8','replace').splitlines(True)
            pagelist.append(pagetxt)
            
    linelist = list()
    
    first = True
    # The goal of the first flag is to ensure that we get a <pb> between
    # pages but not before the first page or after the last. AKA, the
    # Head-Tail pattern.
    
    for page in pagelist:
        if first:
            first = False
        else:
            linelist.append("<pb>\n")
            
        for line in page:
            linelist.append(line)

    return linelist                                         

def readtsv2(filepath):
    '''
    reads my standard tab-separated metadata table,
    and returns three data objects: 1) a list of row indexes
    stored in the first column (e.g. volume ids).
    2) a list of column names, and
    3) a dictionary-of-dictionaries called table where
    table[columnname][rowindex] = the value of that cell.
    the difference here is thatthe first column, containing
    row indexes, is also returned as a column of the table.
    In the original version, it stupidly wasn't.
    '''
    
    with open(filepath, encoding='utf-8') as file:
        filelines = file.readlines()

    header = filelines[0].rstrip()
    fieldnames = header.split('\t')
    numcolumns = len(fieldnames)
    indexfieldname = fieldnames[0]

    table = dict()
    indices = list()
    
    for i in range(0, numcolumns):
        table[fieldnames[i]] = dict()

    for line in filelines[1:]:
        line = line.rstrip()
        fields = line.split('\t')
        rowindex = fields[0]
        indices.append(rowindex)
        for thisfield in range(0, numcolumns):
            thiscolumn = fieldnames[thisfield]
            thisentry = fields[thisfield]
            table[thiscolumn][rowindex] = thisentry

    return indices, fieldnames, table           

def writetsv(columns, rowindices, table, filepath):

    headerstring = ""
    numcols = len(columns)
    filebuffer = list()

    ## Only create a header if the file does not yet exist.
    
    if not os.path.exists(filepath):

        headerstring = ""
        for index, column in enumerate(columns):
            headerstring = headerstring + column
            if index < (numcols -1):
                headerstring += '\t'
            else:
                headerstring += '\n'

        filebuffer.append(headerstring)

    for rowindex in rowindices:
        rowstring = ""
        for idx, column in enumerate(columns):
            rowstring += table[column][rowindex]
            if idx < (numcols -1):
                rowstring += '\t'
            else:
                rowstring += '\n'

        filebuffer.append(rowstring)

    with open(filepath, mode='a', encoding = 'utf-8') as file:
        for line in filebuffer:
            file.write(line)

    return len(filebuffer)

def easywritetsv(columns, rowindices, table, filepath):
    '''This version does not assume the table contains a dict for rowindices'''
    firstcolumn = columns[0]
    table[firstcolumn] = dict()
    for idx in rowindices:
        table[firstcolumn][idx] = idx

    headerstring = ""
    numcols = len(columns)
    filebuffer = list()

    ## Only create a header if the file does not yet exist.
    
    if not os.path.exists(filepath):

        headerstring = ""
        for index, column in enumerate(columns):
            headerstring = headerstring + column
            if index < (numcols -1):
                headerstring += '\t'
            else:
                headerstring += '\n'

        filebuffer.append(headerstring)

    for rowindex in rowindices:
        rowstring = ""
        for idx, column in enumerate(columns):
            rowstring += table[column][rowindex]
            if idx < (numcols -1):
                rowstring += '\t'
            else:
                rowstring += '\n'

        filebuffer.append(rowstring)

    with open(filepath, mode='a', encoding = 'utf-8') as file:
        for line in filebuffer:
            file.write(line)

    return len(filebuffer)
       
def readtsv(filepath):
    '''
    reads my standard tab-separated metadata table,
    and returns three data objects: 1) a list of row indexes
    stored in the first column (e.g. volume ids).
    2) a list of column names, and
    3) a dictionary-of-dictionaries called table where
    table[columnname][rowindex] = the value of that cell.
    '''
    
    with open(filepath, encoding='utf-8') as file:
        filelines = file.readlines()

    header = filelines[0].rstrip()
    fieldnames = header.split('\t')
    numcolumns = len(fieldnames)
    indexfieldname = fieldnames[0]

    table = dict()
    indices = list()
    
    for i in range(1, numcolumns):
        table[fieldnames[i]] = dict()

    for line in filelines[1:]:
        line = line.rstrip()
        fields = line.split('\t')
        rowindex = fields[0]
        indices.append(rowindex)
        for thisfield in range(1, numcolumns):
            thiscolumn = fieldnames[thisfield]
            thisentry = fields[thisfield]
            table[thiscolumn][rowindex] = thisentry

    return indices, fieldnames, table   


    
def clean_pairtree(htid):
    period = htid.find('.')
    prefix = htid[0:period]
    postfix = htid[(period+1): ]
    if ':' in postfix:
        postfix = postfix.replace(':','+')
        postfix = postfix.replace('/','=')
    cleanname = prefix + "." + postfix
    return cleanname
