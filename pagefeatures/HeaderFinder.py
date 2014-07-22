# HeaderFinder.py
#
# Scans a list of pages for running headers, which we understand as lines, near
# the top of a page, that are repeated within the space of two pages,
# in either direction. The two-page window is necessary because headers
# are sometimes restricted to recto or verso. A very common pattern
# involves different, alternating recto and verso headers. We also use
# fuzzy matching to allow for OCR errors and other minor variation (e.g.
# page numbers that may be roman numerals).
#
# Once headers are identified, they can be treated in a range of different
# ways. Here we are not concerned to *separate* the header from the original
# text but only to identify it so that it can be given extra weight in
# page classification.

from difflib import SequenceMatcher

def find_headers(pagelist, romannumerals):
	'''Identifies repeated page headers and returns them as a list keyed to
	original page locations.'''

	# For very short documents, this is not a meaningful task.

	if len(pagelist) < 5:
		return []

	firsttwos = list()
	# We construct a list of the first two substantial lines on
	# each page. We ignore short lines and lines that are just numbers,
	# and don't go deeper than five lines in any event.

	# We transform lines in this process -- e.g, by removing digits.
	# If we were attempting to *remove* lines from the original text,
	# we would probably need to construct objects that package the transformed
	# line with information about its original location, so we could also
	# remove the original.

	for page in pagelist:
		thesetwo = list()
		linesaccepted = 0

		for idx, line in enumerate(page):
			if idx > 4:
				break

			line = line.strip()
			if line.startswith('<') and line.endswith('>'):
				continue

			line = "".join([x for x in line if not x.isdigit()])
			# We strip all numeric chars before the length check.

			if line in romannumerals:
				continue

			# That may not get all roman numerals, because of OCR junk, so let's
			# attempt to get them by shrinking them below the length limit. This
			# will also have the collateral benefit of reducing the edit distance
			# for headers that contain roman numerals.
			line = line.replace("iii", "")
			line = line.replace("ii", "")
			line = line.replace("xx", "")

			if len(line) < 5:
				continue

			linesaccepted += 1
			thesetwo.append(line)

			if linesaccepted >= 2:
				break

		firsttwos.append(thesetwo)

	# Now our task is to iterate through the firsttwos, identifying lines that
	# repeat within a window, which we define as "this page and the two previous
	# pages."

	# We're going to do this with a list of sets. That way we can add things
	# without risk of duplication. Otherwise, when we add headers to previous
	# pages, we're always going to be checking whether they were already added.

	repeated = list()
	for i in range(len(firsttwos)):
		newset = set()
		repeated.append(newset)

	for index in range(2, len(firsttwos)):
		# We can be sure the 2 index is legal because we have previously filtered
		# short documents.

		indexedlines = firsttwos[index]

		for j in range (index - 2, index):

			previouslines = firsttwos[j]

			for lineA in indexedlines:
				for lineB in previouslines:
					s = SequenceMatcher(None, lineA, lineB)
					similarity = s.ratio()
					if similarity > .8:
						repeated[index].add(lineA)
						repeated[j].add(lineB)

	# Now we have a list of sets that contain digit-stripped strings
	# representing headers, in original page order, with empty sets where no headers
	# were found. We want to convert this to a list of lists of individual tokens.

	listoftokenstreams = list()

	for thispageheaders in repeated:
		thisstream = []
		for header in thispageheaders:
			thisstream.extend(header.split())
		listoftokenstreams.append(thisstream)

	return listoftokenstreams








