WORKFLOW

This folder contains files used in the NEW WORKFLOW for cleaning texts in the genre project. Major difference here from earlier versions is that we do not trim running headers in the first pass, because they may be useful for page-level classification. We trim them only when we're aggregating features at the volume level.

Also, the translation of zip files now ditches the pages Michigan labels as "pagedata" and "notes." It previously included them.

As of Sept 6, 2014, the python scripts in the main /normalize folder are or ought ot be identical to the ones in taub/python/normalize.

This version of the normalization workflow produces page-level features, and many classes of features are compressed to aggregate features like "placename" or "personalname."

Subfolders

/slices - These 52 slices cover all the files in ExtractedMetadata.tsv as of May7, 2014. You may need to remove all the files in /hathimeta/2014badIDs.txt.

DIFFERENCES between pre20c and post20c workflow

sample script pre20c in /home/tunder/python/normalize

#!/bin/bash
#PBS -l walltime=10:00:00
#PBS -l nodes=1:ppn=12
#PBS -N mnew0
#PBS -q ichass
#PBS -m be
cd $PBS_O_WORKDIR
/projects/ichass/usesofscale/python3.4/bin/python3 MultiNormalizeOCR.py slice0

PathDictionary setup for pre20c in /home/tunder/python/normalize

datapath	/projects/ichass/usesofscale/nonserials/
metadatapath	/home/tunder/python/context/meta/
volumerulepath	/projects/ichass/usesofscale/rules/
slicepath	/home/tunder/python/normalize/slices/
contextrulepath	/projects/ichass/usesofscale/rules/contextual/
outpath	thispathisnotusedontaub
metaoutpath	/projects/ichass/usesofscale/hathimeta/NormalizingMetadata.txt

The metadatapath is only used for a list of badIDs, and can be kept the same for now.

Here's the PathDictionary setup I used for 20c:

datapath	/projects/ichass/usesofscale/20c/
metadatapath	/home/tunder/python/context/meta/
volumerulepath	/projects/ichass/usesofscale/rules/
slicepath	/projects/ichass/usesofscale/20cmeta/slices/
contextrulepath	/projects/ichass/usesofscale/rules/contextual/
outpath	thispathisnotusedontaub
metaoutpath	/projects/ichass/usesofscale/hathimeta/20cNormalizingMetadata.txt

Genre folds

ads, subsc -> ads

argum,pref -> pref

aut, bio -> bio

back

front

bookp

libra

bibli, gloss, index -> index

epi, fic -> fic

notes, errat -> notes

ora, let, trv, non -> non

lyr, nar, poe -> poe

vdr, pdr, dra, clo -> dra

title, impri -> title

toc



