
metadatapath = "/projects/ichass/usesofscale/hathimeta/"
outputpath = "/projects/ichass/usesofscale/ocr/slices/"
scriptpath = "/home/tunder/python/typeindexer/"


HTIDfile = metadatapath + "htids.txt"
with open(HTIDfile, encoding="utf-8") as file:
    HTIDlist = file.readlines()

totalfiles = len(HTIDlist)

start = 0
end = 20000
counter = 0

while start < totalfiles:
    slicename = metadatapath +"slices/slice" + str(counter) + ".txt"
    scriptname = scriptpath + "slicejob" + str(counter) + ".pbs"
    sliceargument = "slice" + str(counter)
    
    with open(slicename, mode = 'w', encoding='utf-8') as file:
        for i in range(start, end):
            file.write(HTIDlist[i])
            
    with open(scriptname, mode = 'w', encoding = 'utf=8') as file:
        file.write("#!/bin/bash\n")
        file.write("#PBS -l walltime=08:00:00\n")
        file.write("#PBS -l nodes=1:ppn=12\n")
        file.write("#PBS -N " + sliceargument + "\n")
        file.write("#PBS -q ichass\n")
        file.write("#PBS -m be\n")
        file.write("cd $PBS_O_WORKDIR\n")
        file.write("/usr/local/bin/python3.2 SliceIndexer.py " + sliceargument + "\n")

    counter = counter + 1
    start = end
    end = end + 20000
    if end > totalfiles:
        end = totalfiles

print("Created", counter, "slices of the dataset.")
        
