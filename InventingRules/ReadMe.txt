ReadMe for OCRrules

The process of actually generating OCR rules and variant-spelling rules is messy.

With OCR, I've found that it works best to rely on pairs of known substitutions. The best model here may be the script GooglePermuteSH.py. I used it to produce many of the correction rules I now use, working with the Google ngrams dataset.

I've tried a number of other things, and an idealized version of my new data flow is included in this folder. I switched to Java instead of Python because I wanted to make the process run faster, and I used a weighted substitution matrix that learned as it went along instead of a pre-set list of rules.

As part of this process I also created a list of proper nouns not in the dictionary, through the crude technique of identifying forms that are not in the dictionary & usually appear in titlecase. I knew I didn't want to correct these. See /ForJavaProcess/gazetteer.txt

But while the Java version did produce a more complete list of correction rules, it also produced a lot of unreliable rules. I accepted some of these in my most recent (enlarged) ruleset. But if I ever take this further and generate an even better set of rules, I actually want to move back toward the GooglePermute approach where I rely on known subsitutions.

I also stuck in a couple of scripts that I used to build rules for syncope (e.g. "star-spangl'd") and hyphenation. Not sure these are very illuminating; they're not well commented. In reality there was also a lot of manual editing involved in these processes.