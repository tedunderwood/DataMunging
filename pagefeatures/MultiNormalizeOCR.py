'''Revised third-generation OCR normalizer.
	This was rewritten heavily in fall 2013 to ensure that it keeps
	punctuation. It was then adjusted in Spring 2014 to use the original
	HathiTrust zipfiles instead of text files as a source.

	This script loads volumes described in a "slice" of volume IDs, and corrects
	them using a set of rules both about OCR correction and about tokenization
	(e.g. any thing => anything).

	That work gets done in the Volume module.

	Then the script sends the stream of tokens to the Context modules, for
	contextual spellchecking (spellchecking that's aware of context, and
	can distinguish 'left' from 'lest' depending on the words that follow
	or precede it).

	Corrected clean text and a list of wordcounts *by page* are written to the original
	data directory. An errorlog and a record of metadata (e.g. word accuracy)
	are printed to the directory containing slices of volume IDs.

	This version of the OCR normalizer calls NormalizeVolume, a module based
	on the old "Volume" module, but now adjusted so that it does a better job
	of handling punctuation and more importantly so that it registers words whether
	or not they are in the English dictionary. It also aggregates certain *classes*
	of tokens under a class name like romannumeral, arabic2digit, personalname or
	propernoun. Finally it produces a collection of "pagedata" dictionaries that include
	structural_features like #lines, # of capitalized lines, # of repeated initial letters,
	etc. These structural features are distinguished from token counts with an initial
	hashtag.
'''

import FileCabinet
import NormalizeVolume
import Context
import json
import os, sys, time
from zipfile import ZipFile
from multiprocessing import Pool
import SonicScrewdriver as utils

testrun = False
# Setting this flag to "true" allows me to run the script on a local machine instead of
# the campus cluster.

# DEFINE CONSTANTS.
delim = '\t'
debug = False
felecterrors = ['fee', 'fea', 'fay', 'fays', 'fame', 'fell', 'funk', 'fold', 'haft', 'fat', 'fix', 'chafe', 'loft']
selecttruths = ['see', 'sea', 'say', 'says', 'same', 'sell', 'sunk', 'sold', 'hast', 'sat', 'six', 'chase', 'lost']
# Of course, either set could be valid. But I expect the second to be more common.
# The comparison is used as a test.
meaningfulheaders = {"index", "introduction", "introductory", "preface", "contents", "glossary", "notes", "poems", "ode", "stanzas", "catalog", "books", "volumes", "tale", "chapter", "canto", "advertisement", "argument", "book", "scene", "act", "comedy", "tragedy", "plays"}

# LOAD PATHS.

## We assume the slice name has been passed in as an argument.
slicename = sys.argv[1]
current_working = os.getcwd()

# This is most important when running on the cluster, where files are stored in a pairtree
# structure and the only way to know which files we're processing is to list HTIDS in a
# "slice" file defining a slice of the collection.

# When we're running on a local machine, I usually just group files to be processed in a
# directory, and create a list of files to process by listing files in that directory.
# However, it's still necessary to have a slicename and slicepath, because these get
# used to generate a path for an errorlog and list of long S files.

if not testrun:
	pathdictionary = FileCabinet.loadpathdictionary('/home/tunder/python/normalize/PathDictionary.txt')
if testrun:
	pathdictionary = FileCabinet.loadpathdictionary('/Users/tunder/Dropbox/PythonScripts/workflow/PathDictionary.txt')

datapath = pathdictionary['datapath']
metadatapath = pathdictionary['metadatapath']
metaoutpath = pathdictionary['metaoutpath']
outpath = pathdictionary['outpath']
# only relevant if testrun == True

slicepath = pathdictionary['slicepath'] + slicename + '.txt'
errorpath = pathdictionary['slicepath'] + slicename + 'errorlog.txt'
longSpath = pathdictionary['slicepath'] + slicename + 'longS.txt'
headeroutpath = pathdictionary['slicepath'] + slicename + "headers.txt"

# read in special-purpose london phrase list

# if testrun:
#     londonpath = current_working + "/london_places.txt"
# else:
#     londonpath = "/home/tunder/python/normalize/london_places.txt"
# with open(londonpath, encoding="utf-8") as f:
#     filelines = f.readlines()
# phraselist = [x.strip() for x in filelines]
# phraseset = PhraseCounter.normalize_phraseset(phraselist)

# Read the largest list of features we might use for page classification.

if testrun:
	mergedvocabpath = current_working + "/mergedvocabulary.txt"
else:
	mergedvocabpath = "/home/tunder/python/normalize/mergedvocabulary.txt"
with open(mergedvocabpath, encoding = "utf-8") as f:
	filelines = f.readlines()
pagevocabset = set([x.strip() for x in filelines])

##
## MAIN FUNCTION:
##

def main():
	global testrun, datapath, slicepath, metadatapath, current_working,  metaoutpath, errorpath, pagevocabset

	if testrun:
		filelist = os.listdir(datapath)
		HTIDs = set()
		for afilename in filelist:
			if not (afilename.startswith(".") or afilename.startswith("_")):
				HTIDs.add(afilename)

	else:
		with open(slicepath, encoding="utf-8") as file:
			HTIDlist = file.readlines()

		HTIDs = set([x.rstrip() for x in HTIDlist])
		del HTIDlist

	## discard bad volume IDs

	with open(metadatapath + "badIDs.txt", encoding = 'utf-8') as file:
		filelines = file.readlines()

	for line in filelines:
		line = line.rstrip()
		line = line.split(delim)
		if line[0] in HTIDs:
			HTIDs.discard(line[0])

	if not os.path.isfile(metaoutpath):
		with open(metaoutpath, 'w', encoding = 'utf-8') as f:
			f.write("volID\ttotalwords\tprematched\tpreenglish\tpostmatched\tpostenglish\n")

	print(len(HTIDs))

	# Let's get some metadata to create metadata features.

	if testrun:
		rowindices, columns, metadata = utils.readtsv("/Users/tunder/Dropbox/PythonScripts/hathimeta/ExtractedMetadata.tsv")
	else:
		rowindices, columns, metadata = utils.readtsv("/projects/ichass/usesofscale/hathimeta/ExtractedMetadata.tsv")

	metadata_clues = list()
	for aHTID in HTIDs:
		evidence = get_metadata_evidence(aHTID, rowindices, columns, metadata)
		metadata_clues.append(evidence)

	assert len(HTIDs) == len(metadata_clues)
	file_tuples = zip(HTIDs, metadata_clues)

	pool = Pool(processes = 12)
	res = pool.map_async(process_a_file, file_tuples)

	# After all files are processed, write metadata, errorlog, and counts of phrases.
	res.wait()
	resultlist = res.get()

	processedmeta = list()
	errorlog = list()
	phrasecount = dict()

	for file_dict in resultlist:
		processedmeta.append(file_dict["metadata"])
		errorlog.extend(file_dict["errors"])
		htid = file_dict["htid"]

	# Metadata.

	with open(metaoutpath, mode = 'a', encoding = 'utf-8') as file:
		for metatuple in processedmeta:
			outlist = [x for x in metatuple]
			outline = delim.join(outlist) + '\n'
			file.write(outline)

	# Write the errorlog.

	if len(errorlog) > 0:
		with open(errorpath, mode = 'w', encoding = 'utf-8') as file:
			for line in errorlog:
				file.write(line + '\n')

	# Write phrase counts.

	# with open(phrasecountpath, mode="w", encoding = "utf-8") as file:
	#     j = json.dumps(phrasecount)
	#     file.write(j)

	print("Done.")
	pool.close()
	pool.join()

	# Done.

# FUNCTIONS.

def subtract_counts (token, adict, tosubtract):
	if token in adict:
		adict[token] = adict[token] - tosubtract
		if adict[token] < 0:
			del adict[token]
		elif adict[token] < 1:
			del adict[token]
	return adict

def add_counts (token, adict, toadd):
	if token in adict:
		adict[token] = adict[token] + toadd
	else:
		adict[token] = toadd
	return adict

def clean_pairtree(htid):
	period = htid.find('.')
	prefix = htid[0:period]
	postfix = htid[(period+1): ]
	if ':' in postfix:
		postfix = postfix.replace(':','+')
		postfix = postfix.replace('/','=')
	cleanname = prefix + "." + postfix
	return cleanname

def dirty_pairtree(htid):
	period = htid.find('.')
	prefix = htid[0:period]
	postfix = htid[(period+1): ]
	if '=' in postfix:
		postfix = postfix.replace('+',':')
		postfix = postfix.replace('=','/')
	dirtyname = prefix + "." + postfix
	return dirtyname

# We define two different IO functions, for zip files and regular text files.
# The decision between them is defined by the extension on the filename;
# each function encapulates error-handling and returns a successflag that
# reports error status.

def read_zip(filepath):
	pagelist = list()
	try:
		with ZipFile(file = filepath, mode='r') as zf:
			for member in zf.infolist():
				pathparts = member.filename.split("/")
				suffix = pathparts[1]
				if "_" in suffix:
					segments = suffix.split("_")
					page = segments[-1][0:-4]
				else:
					page = suffix[0:-4]

				if len(page) > 0 and page[0].isdigit():
					numericpage = True
				else:
					if len(page) > 0 and page!="notes" and page!="pagedata":
						print("Non-numeric pagecode: " + page)
					numericpage = False

				if not member.filename.endswith('/') and not member.filename.endswith("_Store") and not member.filename.startswith("_") and numericpage:
					datafile = zf.open(member, mode='r')
					linelist = [x.decode(encoding="UTF-8") for x in datafile.readlines()]
					pagelist.append((page, linelist))

		pagelist.sort()
		pagecount = len(pagelist)
		if pagecount > 0:
			successflag = "success"
			pagelist = [x[1] for x in pagelist]
		else:
			successflag = "missing file"

	except IOError as e:
		successflag = "missing file"

	return pagelist, successflag

def read_txt(filepath):
	pagelist = list()
	try:
		with open(filepath, mode='r', encoding='utf-8') as f:
			filelines = f.readlines()

		page = list()
		for line in filelines:

			if line.startswith("<pb>"):
				pagelist.append(page)
				page = list()
			else:
				page.append(line)

		pagelist.append(page)

		# This turned out to be false:
				# You might assume that we would now need pagelist.append(page)
				# To catch the final page. But in practice the text files we are
				# likely to ingest have a <pb> at the bottom of *every* page,
				# even the last one. So no final append is needed.

		successflag = "success"

	except IOError as e:
		successflag = "missing file"

	return pagelist, successflag

# DEPRECATED.
# def get_map(thisID, genremappath):
#     errormsg = ""
#     genremap = dict()

#     try:
#         with open(genremappath, encoding="utf-8") as f:
#             filelines = f.readlines()
#         ctr = 0
#         for line in filelines:
#             fields = line.split('\t')
#             genre = fields[2]
#             pageid = fields[0]
#             pagenum = int(pageid.rpartition(',')[2])
#             # That takes the part after the last comma in page id.
#             # For instance "yale.39002098631915,85" => 85.
#             genremap[pagenum] = genre
#             if pagenum != ctr:
#                 print("Anomalous sequence in " + genremappath)
#             ctr += 1
#     except:
#         print("Failure to read genremap in " + genremappath)
#         errormsg = thisID + '\t' + " genre map failure."

#     return genremap, errormsg

def keywithmaxval(dictionary):
	maxval = 0
	maxkey = ""

	for key, value in dictionary.items():
		if value > maxval:
			maxval = value
			maxkey = key

	return maxkey

def get_metadata_evidence(htid, rowindices, columns, metadata):
	'''Reads metadata about this volume and uses it to decide what metadata-level features should be assigned.'''

	metadata_evidence = dict()

	metadata_evidence["drama"] = False
	metadata_evidence["poetry"] = False
	metadata_evidence["biography"] = False
	metadata_evidence["fiction"] = False

	htid = utils.pairtreelabel(htid)
	# convert the clean pairtree filename into a dirty pairtree label for metadata matching

	if htid not in rowindices:
		# We have no metadata for this volume.
		return metadata_evidence

	else:
		genrestring = metadata["genres"][htid]
		genreinfo = genrestring.split(";")
		# It's a semicolon-delimited list of items.

		for info in genreinfo:

			if info == "Biography" or info == "Autobiography":
				metadata_evidence["biography"] = True

			if info == "Fiction" or info == "Novel":
				metadata_evidence["fiction"] = True

			if (info == "Poetry" or info == "Poems"):
				metadata_evidence["poetry"] = True

			if (info == "Drama" or info == "Tragedies" or info == "Comedies"):
				metadata_evidence["drama"] = True

	return metadata_evidence

# Workhorse function.

def process_a_file(file_tuple):
	global testrun, pairtreepath, datapath, genremapdir, felecterrors, selecttruths, debug, phraseset, pagevocabset, meaningfulheaders

	thisID, metadata_evidence = file_tuple

	perfileerrorlog = list()
	return_dict = dict()
	return_dict["htid"] = thisID
	return_dict["metadata"] = (thisID, "0", "0", "0", "0", "0")
	return_dict["errors"] = []
	return_dict["phrasecounts"] = dict()

	if testrun:
		cleanID = clean_pairtree(thisID.replace("norm.txt", ""))
	else:
		cleanID = clean_pairtree(thisID)

	if not testrun:
		filepath, postfix = FileCabinet.pairtreepath(thisID, datapath)
		filename = filepath + postfix + '/' + postfix + ".zip"
	else:
		filename = datapath + thisID

	# ACTUALLY READ THE FILE.

	if filename.endswith('.zip'):
		pagelist, successflag = read_zip(filename)
	else:
		pagelist, successflag = read_txt(filename)

	if successflag == "missing file":
		print(thisID + " is missing.")
		perfileerrorlog.append(thisID + '\t' + "missing")
		return_dict["errors"] = perfileerrorlog
		return return_dict

	elif successflag == "pagination error":
		print(thisID + " has a pagination problem.")
		perfileerrorlog.append(thisID + '\t' + "paginationerror")
		return_dict["errors"] = perfileerrorlog
		return return_dict

	tokens, pre_matched, pre_english, pagedata, headerlist = NormalizeVolume.as_stream(pagelist, verbose=debug)

	if pre_english < 0.6:
		perfileerrorlog.append(thisID + '\t' + "not english")

	tokencount = len(tokens)

	if len(tokens) < 10:
		print(thisID, "has only tokencount", len(tokens))
		perfileerrorlog.append(thisID + '\t' + 'short')

	correct_tokens, pages, post_matched, post_english = NormalizeVolume.correct_stream(tokens, verbose = debug)

	# Combine page dictionaries into a master dictionary.
	# If you ask, why didn't you just produce one in the first place? ...
	# answer has to do with flexibility of the Volume module for other purposes.

	pagecounter = 0
	masterdict = dict()
	for page in pages:
		for item in page:
			if item in masterdict:
				masterdict[item] += page[item]
			else:
				masterdict[item] = page[item]

	# Now that we have a master dictionary, consider whether there are long-s problems.
	# This algorithm works adequately.

	errors = 1
	truths = 1
	# Initialized to 1 as a Laplacian correction.

	for word in felecterrors:
		errors = errors + masterdict.get(word, 0)
	for word in selecttruths:
		truths = truths + masterdict.get(word, 0)

	if truths > errors:
		LongSproblem = False
	else:
		LongSproblem = True

	if LongSproblem == False:
		corrected = correct_tokens
		deleted = dict()
		added = dict()
	else:
		deleted, added, corrected, changedphrases, unchanged = Context.catch_ambiguities(correct_tokens, debug)
		# okay, this is crazy and not efficient to run, but it's easy to write and there are a small number
		# of these files -- so I'm going to count the new contextually-corrected tokens by re-running them
		# through Volume.
		correct_tokens, pages, post_matched, post_english = NormalizeVolume.correct_stream(corrected, verbose = debug)

		corrected = correct_tokens

	# If we are upvoting tokens in the header, they need to be added here.

	for index, page in enumerate(pages):
		thispageheader = headerlist[index]
		header_tokens, header_pages, dummy1, dummy2 = NormalizeVolume.correct_stream(thispageheader, verbose = debug)
		headerdict = header_pages[0]
		for key, value in headerdict.items():
			if key in meaningfulheaders:
				if key in page:
					page[key] += 2
					# a fixed increment no matter how many times the word occurs in the
					# header
				else:
					page[key] = 2
					print("Word " + key + " in headerdict for " + thisID + " at " + str(index) + " but not main page.")

	# Write corrected file.
	cleanHTID = clean_pairtree(thisID)

	if testrun:
		if cleanHTID.endswith(".clean.txt"):
			outHTID = cleanHTID.replace(".clean.txt", "")
		elif cleanHTID.endswith("norm.txt"):
			outHTID = cleanHTID.replace("norm.txt", ".norm.txt")
		elif cleanHTID.endswith(".txt"):
			outHTID = cleanHTID.replace(".txt", "norm.txt")
		else:
			outHTID = cleanHTID + ".norm.txt"

		outfilename = outpath + "texts/" + outHTID
	else:
		outfilename = filepath + postfix + '/' + postfix + ".norm.txt"

	with open(outfilename, mode = 'w', encoding = 'utf-8') as file:
		for token in corrected:
			if token != '\n' and token != "“" and not (token.startswith('<') and token.endswith('>')):
				token = token + " "
			file.write(token)

	if len(pages) != len(pagedata):
		perfileerrorlog.append("Discrepancy between page data and page metadata in \t" + thisID)

	totalwordsinvol = 0

	if testrun:
		if cleanHTID.endswith(".clean.txt"):
			outHTID = cleanHTID.replace(".clean.txt", ".pg.tsv")
		elif cleanHTID.endswith("norm.txt"):
			outHTID = cleanHTID.replace("norm.txt", ".pg.tsv")
		elif cleanHTID.endswith(".txt"):
			outHTID = cleanHTID.replace(".txt", ".pg.tsv")
		else:
			outHTID = cleanHTID + ".pg.tsv"

		outfilename = outpath + "pagefeatures/" + outHTID
	else:
		outfilename = filepath + postfix + '/' + postfix + ".pg.tsv"

	with open(outfilename, mode = 'w', encoding = 'utf-8') as file:

		if metadata_evidence["biography"]:
			file.write("-1\t#metaBiography\t0\n")

		if metadata_evidence["drama"]:
			file.write("-1\t#metaDrama\t0\n")

		if metadata_evidence["fiction"]:
			file.write("-1\t#metaFiction\t0\n")

		if metadata_evidence["poetry"]:
			file.write("-1\t#metaPoetry\t0\n")

		numberofpages = len(pages)
		for index, page in enumerate(pages):

			# This is a shameful hack that should be deleted later.
			if testrun and "estimated" in page and "percentage" in page and (index + 3) > numberofpages:
				continue
			if testrun and "untypical" in page and (index +2) > numberofpages:
				continue

			otherfeatures = 0

			for feature, count in page.items():
				if feature in pagevocabset or feature.startswith("#"):
					outline = str(index) + '\t' + feature + '\t' + str(count) + '\n'
					# pagenumber, featurename, featurecount
					file.write(outline)
				else:
					otherfeatures += count

				if not feature.startswith("#"):
					totalwordsinvol += count
				# This is because there are structural features like #allcapswords
				# that should not be counted toward total token count.

			structural_features = pagedata[index]
			for feature, count in structural_features.items():
				if count > 0 or feature == "#textlines":
					outline = str(index) + '\t' + feature + '\t' + str(count) + '\n'
					file.write(outline)

			if otherfeatures > 0:
				outline = str(index) + '\t' + "wordNotInVocab" + '\t' + str(otherfeatures) + '\n'
				file.write(outline)

	metatuple = (thisID, str(totalwordsinvol), str(pre_matched), str(pre_english), str(post_matched), str(post_english))

	return_dict["metadata"] = metatuple
	return_dict["errors"] = perfileerrorlog

	return return_dict

if __name__ == "__main__":
	start_time = time.time()
	main()
	print("Time elapsed: " + str(time.time() - start_time))


