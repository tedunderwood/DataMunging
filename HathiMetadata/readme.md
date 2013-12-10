### munging HathiTrust metadata

The scripts in this directory extract tabular metadata from the file of xml records that HathiTrust Digital Library provides to accompany their data.

The most up-to-date script here is xmlparser.py. This is based on a script called metamine.py originally written by Mike Black (also included here). Metamine worked with jsons extracted from the bibliographic API; xmlparser works with MARC records in xml format.

The general strategy is to read in the XML, one MARC record at a time, and parse
the record for basic information which is then written in a tabular form, simpler
to browse, and simpler for subsequent analytics to parse.

Note that HathiTrust has two different layers of MARC records, one for volumes (items), and
one for bibliographic "records" (manifestations). This script is designed to deal with
the volume-level MARC records that Hathi tends to bundle in a meta.tar.gz file. But there is sometimes more
info available in the record-level MARCs that populate the leaves of a pairtree, and/or
the MARCs contained in .jsons. This script does not get at all of those sources.

Large parts of this code are extracted from metamine.py, written by Mike Black (2012);
it was subsequently adapted by Ted Underwood (2013). Ted was guided by e-mailed advice from Tim Cole.

There are three main levels of changes between metamine and xmlparser:

1) Ingestion of source data is different, because we're dealing with xml rather than
a folder of .jsons.

2) The HathiTrust volume ID and enumcron must be extracted from datafield 974.

3) I've added a function to parse the genre information in controlfield 008.
I also move the genre terms from datafield 655 to this "genre" list rather than
treating them as subject terms, as we did before. This means that the genre list
will contain a combination of terms from two sources.

A couple of notes about specific genre terms in that field.

"Not fiction" ≠ nonfiction. It's based on one byte in controlfield 008, and
includes a lot of poetry and drama, which are only rarely labeled by genre.

"Biography" may not necessarily mean "nonfiction" either! I've seen some records
labeled "Fiction;Biography."

If the biography byte is ambiguous/missing, I add a term "biog?" to register that it has
some Bayesian prior possibility of being Biography inasmuch as no one specifically
said it wasn't. But it's not a very strong prior!
