# MultiNormalizeProcess
import NormalizeVolume
def processvolume(triplet):
    infile, outfile, integer = triplet
    print(integer)

    try:
        with open(infile, encoding='utf-8') as f:
            text = f.readlines()
    except:
        print("ERROR reading file " + infile)

    tokens, pre_matched, pre_english, pagedata, headerlist = NormalizeVolume.as_stream([text], verbose=False)

    correct_tokens, pages, post_matched, post_english = NormalizeVolume.correct_stream(tokens, verbose = False)

    pagecounter = 0
    masterdict = dict()
    for page in pages:
        for item in page:
            if item in masterdict:
                masterdict[item] += page[item]
            else:
                masterdict[item] = page[item]

    with open(outfile, mode = 'w', encoding = 'utf-8') as f:
        for key, value in masterdict.items():
            if not key.startswith('#'):
                f.write(key + '\t' + str(value) + '\n')

    print(str(integer) + ' complete.')

    return "null"
