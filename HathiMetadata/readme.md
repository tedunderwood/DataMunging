### munging HathiTrust metadata

The scripts in this directory extract tabular metadata from the file of xml records that HathiTrust Digital Library provides to accompany their data. A lot of the scripts here have a lot of work by Michael L. Black somewhere in their genetic history, although it's now somewhat scrambled and fused with other code.

### scrape_json.py
The most up-to-date script here is scrape_json.py. But this is designed to work with a file that contains the MARC records as jsons, which may not be what you've got.

Improvements over earlier versions include, especially, better handling of the various parts of a title string.

### scrape_marc.py
is a slightly older version that actually scrapes from Hathi's bibliographic API.

### older versions
xmlparser.py is based on a script called metamine.py originally written by Mike Black (also included here). Metamine worked with jsons extracted from the bibliographic API; xmlparser works with MARC records in xml format.

The general strategy is to read in the XML, one MARC record at a time, and parse
the record for basic information which is then written in a tabular form, simpler
to browse, and simpler for subsequent analytics to parse.

Note that HathiTrust has two different layers of MARC records, one for volumes (items), and one for bibliographic "records" (manifestations). All the scripts above are designed to deal with the volume-level records.

### some weird shit you will encounter

MARC is a format with a long history, and it has some weird corners. Things like genres and dates are encoded in multiple confusing places. They are also often encoded *badly*, not to mince words. 

For instance, there is a flag in the header field that's supposed to indicate whether something is fiction. About 60% of the time this has some relation to what you might think it would mean. The rest of the time, it's unreliable. Poetry gets encoded as "fiction"; novels sometimes don't get encoded as fiction.

My agenda is to get all this information out in a csv where I can scan it visually and figure out what to do with it. Often this means translating binary flags into a phrase like "NotFiction." Place no trust in these genre designations -- at least not until you have traced them back to their source in the 008 header field, and/or surveyed a csv to see how reliable they are in practice. Generally, they aren't.

A couple of notes about specific genre terms in that field.

"Not fiction" ≠ nonfiction. It's based on one byte in controlfield 008, and
includes a lot of poetry and drama, which are only rarely labeled by genre.

"Biography" may not necessarily mean "nonfiction" either! I've seen some records
labeled "Fiction;Biography."

If the biography byte is ambiguous/missing, I add a term "biog?" to register that it has
some Bayesian prior possibility of being Biography inasmuch as no one specifically
said it wasn't. But it's not a very strong prior!
