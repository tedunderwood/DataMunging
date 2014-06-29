## FileUtils

## currently only contains one function, a utility
## that reads my standard tab-separated metadata table,
## and returns three data objects: 1) a list of row indexes
## stored in the first column (e.g. volume ids).
## 2) a list of column names, and
## 3) a dictionary-of-dictionaries called table where
## table[columnname][rowindex] = the value of that cell.

def readtsv(filepath):
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
            
        
        

    
       
    
