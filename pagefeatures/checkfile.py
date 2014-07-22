with open("/Users/tunderwood/Dropbox/GenreProject/PythonUtilities/CreateLabelWork/volumes/njp.32101067676559.txt", encoding ='utf-8') as f:
	filelines = f.readlines()

counter = 0
othercounter = 0
for line in filelines:
	if line =="<pb>\n":
		counter += 1
	if "<pb" in line:
		othercounter += 1

print(counter)
print(othercounter)