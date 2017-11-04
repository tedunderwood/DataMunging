# USAGE:
# from within this /workflow directory:
# python NormalizeOneFolder.py folderoftexts outputfolder

# The paths in NormalizeVolume only work if you do it from
# within this directory.

def main():
    import FileCabinet
    import NormalizeVolume
    import sys, os
    from multiprocessing import Pool
    import MultiNormalizeProcess
    args = sys.argv

    inputfolder = args[1]
    outputfolder = args[2]

    if not os.path.isdir(inputfolder):
        print("Input folder " + inputfolder + " is not a directory.")
        sys.exit(0)

    if not os.path.isdir(outputfolder):
        print("Output folder " + outputfolder + " is not a directory.")
        sys.exit(0)

    infiles = os.listdir(inputfolder)

    already_converted = [x.replace('.tsv', '.txt') for x in os.listdir(outputfolder) if x.endswith('.tsv')]

    not_yet_converted = set(infiles) - set(already_converted)

    print("There are " + str(len(not_yet_converted)) + " files still to convert.")
    inpaths = [os.path.join(inputfolder, x) for x in not_yet_converted if x.endswith('.txt')]

    outpaths = [os.path.join(outputfolder, x).replace('.txt', '.tsv') for x in not_yet_converted if x.endswith('.txt')]

    debug = False

    pathdictionary = FileCabinet.loadpathdictionary('/Users/tunder/Dropbox/PythonScripts/workflow/PathDictionary.txt')

    datapath = pathdictionary['datapath']
    metadatapath = pathdictionary['metadatapath']
    metaoutpath = pathdictionary['metaoutpath']
    outpath = pathdictionary['outpath']

    pathpairs = list(zip(inpaths, outpaths, list(range(len(inpaths)))))

    pool = Pool(processes = 12)
    res = pool.map_async(MultiNormalizeProcess.processvolume, pathpairs)
    res.wait()
    resultlist = res.get()

    pool.close()
    pool.join()

    os.system('say "your program has finished"')

if __name__ == "__main__":
    main()
