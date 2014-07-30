# Count phrases.

def addmatch(match, genre, matchdict):
	if genre not in matchdict:
		return

	if match in matchdict[genre]:
		matchdict[genre][match] += 1
	else:
		matchdict[genre][match] = 1

def normalize(phrase):
	stringphrase = " ".join(x.lower() for x in phrase)
	return strip_trailing_punctuation(stringphrase)

punctuple = ('.', ',', '?', '!', ';', '"', '“', '”', ':', '--', '—', ')', '(', "'", "`", "[", "]", "{", "}")

def strip_trailing_punctuation(astring):
    global punctuple
    keepclipping = True

    while keepclipping == True and len(astring) > 1:
        keepclipping = False
        if astring.endswith(punctuple):
            astring = astring[:-1]
            keepclipping = True

    return astring

def count_phrases(tokenstream, genremap, phraseset, genreset, cleanID):
	'''Counts specified phrases in a tokenstream and assigns them to
	the genre code associated with the appropriate page.
	'''

	# Create a dictionary that contains a key for each genre, with the
	# value of that key being another dictionary used to count phrases.
	matchdict = dict()
	for genre in genreset:
		matchdict[genre] = dict()

	page = 0
	lasttoken = ""
	nexttolasttoken = ""
	beforethat = ""

	for token in tokenstream:

		if token == "<pb>":
			page += 1
			continue

		if token == "\n":
			continue

		if page in genremap:
			genre = genremap[page]
		else:
			print("Pagination error in genremap " + cleanID + ": page " + str(page) + " but maplen " + str(len(genremap)))

		# Now we're going to consider possible phrases ending with this token,
		# and decide whether they need to be checked against our list of
		# (already lowercased) matching phrases. We're going to compare the
		# phrases with both sides lowercased so we catch a variety of forms,
		# but we do demand that the first letter of the first content word
		# be uppercased.

		oneword = [token]
		twoword = [lasttoken, token]
		threeword = [nexttolasttoken, lasttoken, token]
		fourword = [beforethat, nexttolasttoken, lasttoken, token]

		phrasestocheck = list()

		if len(token) > 0:
			phrasestocheck.append(oneword)
			if len(lasttoken) > 0:
				phrasestocheck.append(twoword)
				if len(nexttolasttoken) > 0:
					phrasestocheck.append(threeword)
					if len(beforethat) > 0:
						phrasestocheck.append(fourword)

		possiblematches = list()

		for phrase in phrasestocheck:
			# We demand that the first letter of the first content word be capitalized.
			# Otherwise we don't consider this a possible match.
			if phrase[0][0].isupper():
				possiblematches.append(normalize(phrase))
			elif len(phrase) > 1:
				if phrase[0] == "the" and phrase[1][0].isupper():
					possiblematches.append(normalize(phrase))

		for potentialmatch in possiblematches:
			if potentialmatch in phraseset:
				print(potentialmatch)
				addmatch(potentialmatch, genre, matchdict)
				break
				# Because we don't want to count more than one match at this position.

		beforethat = nexttolasttoken
		nexttolasttoken = lasttoken
		lasttoken = token

	return matchdict

def normalize_phraseset(phraselist):
	phraseset = set()
	for phrase in phraselist:
		phraseset.add(strip_trailing_punctuation(phrase.lower()))
	return phraseset


