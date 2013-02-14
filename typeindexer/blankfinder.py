import glob

datapath = "/Users/tunderwood/Dropbox/PythonScripts/"

FileList = glob.glob(datapath + "doslice*")

blankids = list()
counter = 0

for file in FileList:
    with open(file, mode='r', encoding = 'utf-8') as sourcefile:
        filelines = sourcefile.readlines()
    for line in filelines:
        words = line.split()
        if words[0] != "Volume" and words[0] != "Volumes":
            blankids.append(words[0])
            counter = counter + 1

with open(datapath + "BlankIDs.txt", mode='w', encoding='utf-8') as outfile:
    for htid in blankids:
        outfile.write(htid + '\n')

print(counter, 'volumes.')
    

