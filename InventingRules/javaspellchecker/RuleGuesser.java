package spellchecker;
import java.util.HashSet;
import java.util.Arrays;
import java.util.ArrayList;

public class RuleGuesser {
	String[] dictionary;
	boolean[] dictionaryTitlecase;
	int[] dictBigramCount;
	double[] freqCoefficients;
	Levenshtein matcher;
	HashSet<String> dictionarySet;
	static final String alphabet ="abcdefghijklmnopqrstuvwxyz'$";
	static final String punctuation = ".,():-—;\"!?$%#<>+=/[]*^\'{}_~\\|«»©~`£·";
	int[] alphaTranslationTable;
	ArrayList<ArrayList<HashSet<Integer>>> bigramIndex;
	// Yes, you got that right. A list of lists, of hashsets containing integers.
	
	public RuleGuesser(String[] dictionary, double[] freqCoefficients, boolean[] dictionaryTitlecase, Levenshtein matcher, String[] largerDictionary) {
		this.dictionary = dictionary;
		this.freqCoefficients = freqCoefficients;
		this.dictionaryTitlecase = dictionaryTitlecase;
		this.matcher = matcher;
		
		dictionarySet = new HashSet<String>();
		for (String word: largerDictionary) {
			dictionarySet.add(word);
		}
		// The Hashset dictionarySet is built from the larger (precision) dictionary.
		// But the bigram index below is built from the smaller (recall) dictionary.
		
		alphaTranslationTable = new int[256];
		// Initialize the translation table for k-gram indexing, using fixed alphabet.
		// The apostrophe, #26, is an all-purpose code for nonalphabetic characters.
		for (int i = 0; i < 256; ++i) {
			alphaTranslationTable[i] = 26;
		}
		// Now assign characters in the alphabet.
		for (int i = 0; i < alphabet.length(); ++i) {
			int ascii = (int) alphabet.charAt(i);
			alphaTranslationTable[ascii] = i;
			if (i < 26) {
				// Upper-case equivalent for alphabetic characters.
				int upper = ascii - 32;
				alphaTranslationTable[upper] = i;
			}
		}
		
		// Now we create a list of lists of hashsets, containing integers.
		bigramIndex = new ArrayList<ArrayList<HashSet<Integer>>>();
		for (int i = 0; i < 28; ++i) {
			ArrayList<HashSet<Integer>> aListOfSets = new ArrayList<HashSet<Integer>>();
			for (int j = 0; j < 28; ++j) {
				HashSet<Integer> wordsContainingBigramIJ = new HashSet<Integer>();
				aListOfSets.add(wordsContainingBigramIJ);
			}
			bigramIndex.add(aListOfSets);
		}
		
		dictBigramCount = new int[dictionary.length];
		for (int i = 0; i < dictionary.length; ++i) {
			String word = "$" + dictionary[i] + "$";
			HashSet<String> bigrams = new HashSet<String>();
			for (int j = 1; j < word.length(); ++ j) {
				String bigram = word.substring(j - 1, j + 1);
				bigrams.add(bigram);
				int gram1 = bigramcode(word.charAt(j - 1));
				int gram2 = bigramcode(word.charAt(j));
				ArrayList<HashSet<Integer>> listOfSets = bigramIndex.get(gram1);
				HashSet<Integer> setOfWords = listOfSets.get(gram2);
				setOfWords.add(i);
			}
			dictBigramCount[i] = bigrams.size();
		}	
	}
	
//	private static boolean isUpper(char toTest) {
//		int unicodeVal = (int) toTest;
//		boolean testCondition = false;
//		if (unicodeVal > 64 & unicodeVal < 91) testCondition = true;
//		return testCondition;
//	}
	
	private static boolean largelyNumeric(String toTest) {
		if (toTest.length() < 2) return false;
		int digits = 0;
		for (int i = 0; i < toTest.length(); ++i) {
			int ascii = (int) toTest.charAt(i);
			if (ascii >= 48 & ascii <= 57) ++ digits;
		}
		double percent = digits / (double) toTest.length();
		if (percent > 0.3) return true;
		else return false;
	}
	
//	private static boolean containsPunctuation(String toTest) {
//		if (toTest.length() < 2) return false;
//		for (int i = 0; i < punctuation.length(); ++i) {
//			String punctuationMark = Character.toString(punctuation.charAt(i));
//			if (toTest.contains(punctuationMark)) return true;
//		}
//		return false;
//	}
	
	private int bigramcode(char aChar) {
		int code = (int) aChar;
		if (code > 255) return 26;
		else return alphaTranslationTable[code];
	}
	
	private HashSet<Integer> wordsContaining(String bigram){
		int gram1 = bigramcode(bigram.charAt(0));
		int gram2 = bigramcode(bigram.charAt(1));
		ArrayList<HashSet<Integer>> aListOfSets = bigramIndex.get(gram1);
		return aListOfSets.get(gram2);
	}
	
	private ArrayList<Integer> getCandidates(String word, boolean titlecase) {
		if (word.startsWith("av")) titlecase = false;
		word = "$" + word + "$";
		int[] sumMatchesPerWord = new int[dictionary.length];
		Arrays.fill(sumMatchesPerWord, 0);
		
		HashSet<String> bigrams = new HashSet<String>();
		for (int j = 1; j < word.length(); ++ j) {
			String bigram = word.substring(j - 1, j + 1);
			bigrams.add(bigram);
		}
		int wordBigramCount = bigrams.size();
		for (String bigram : bigrams) {
			HashSet<Integer> wordsMatchingThisBigram = wordsContaining(bigram);
			for (int match : wordsMatchingThisBigram) {
				++ sumMatchesPerWord[match];
			}
		}
		ArrayList<Integer> candidates = new ArrayList<Integer>();
		for (int i = 0; i < dictionary.length; ++i) {
			if (titlecase == true & dictionaryTitlecase[i] == false) continue;
			double dice = (2 * sumMatchesPerWord[i]) / (double) (wordBigramCount + dictBigramCount[i]);
			if (dice > 0.3) candidates.add(i);
		}
		return candidates;		
	}
	
	private ArrayList<String> matchtail(String word) {
		// Identifies dictionary words of which "word" is a possible
		// fragment, to disqualify it for usual spellchecking.
		int[] possibleMatches = new int[dictionary.length];
		Arrays.fill(possibleMatches, 0);
		String lastBigram = word.charAt(word.length() - 1) + "$";
		String nexttolastBigram = word.substring((word.length() -2 ), word.length());
		HashSet<Integer> wordsMatchingThisBigram = wordsContaining(lastBigram);
		for (int match : wordsMatchingThisBigram) {
			++ possibleMatches[match];
		}
		wordsMatchingThisBigram = wordsContaining(nexttolastBigram);
		for (int match : wordsMatchingThisBigram) {
			++ possibleMatches[match];
		}
		ArrayList<String> tailwords = new ArrayList<String>();
		for (int i = 0; i < dictionary.length; ++i) {
			if (possibleMatches[i] > 1 ) tailwords.add(dictionary[i]);
		}
		ArrayList<String> tailmatches = new ArrayList<String>();
		for (String candidate : tailwords) {
			// We don't want to consider candidates that are shorter than the word,
			// or the same length. We're looking for words *of which* this is a fragment.
			// Also, if the candidate is only one letter longer, that might be considered
			// a valid correction and will not be disqualified, unless the word is short.
			int allowable = 0;
			if (word.length() > 5) allowable = 1;
			if (candidate.length() <= (word.length() + allowable)) continue;
			String candidateChunk = candidate.substring(candidate.length() - word.length());
			if (candidateChunk.equals(word)) tailmatches.add(candidate);
		}
		return tailmatches;
	}
	
	public String[] mineMatches(String[] wordsToMatch, boolean[] titlecased) {
		int chunklength = wordsToMatch.length;
		String[] matches = new String[chunklength];
		// The basic drill here is that we get a list of words and return a list of matches.
		// If the word is easy to match by simple fusing or splitting at hyphens, we send
		// back the same form we got, to say "make no rule here" -- it can be handled later.
		// If the word is impossible to match, we send back "", to say "we failed here."
		// Otherwise, if the rule requires fuzzy matching/spell checking, we send back
		// the match we identified, to say "make a rule that will abbreviate this later."
		
		for (int worditerate = 0; worditerate < chunklength; ++ worditerate) {
			String word = wordsToMatch[worditerate];
			boolean title = titlecased[worditerate];
			String lowerWord = word.toLowerCase();
			// Reasons not to bother with this word.

			if (dictionarySet.contains(lowerWord)) {
				matches[worditerate] = word;
				continue;
			}
			if (dictionarySet.contains(word)) {
				matches[worditerate] = word;
				continue;
			}
			if (word.length() < 3) {
				matches[worditerate] = "";
				continue;
			}
			if (largelyNumeric(word)) {
				matches[worditerate] = "";
				continue;
			}
			
			// regularize the word by replacing special characters
			String regWord = word.replaceAll("ſ", "s");
			regWord = regWord.replaceAll("ﬁ", "fi");
			regWord = regWord.replaceAll("ﬅ", "st");
			regWord = regWord.replaceAll("æ", "ae");
			
			if (regWord.endsWith("'s") | (regWord.endsWith("ly") & regWord.length() > 6)) {
				int wordLen = regWord.length();
				String stem = regWord.substring(0, (wordLen - 2));
				if (dictionarySet.contains(stem)) {
					matches[worditerate] = regWord;
					continue;
				}	
			}
			
			//try fusing the word by removing all nonword characters
			String fuseWord = regWord.replaceAll("\\W", "");
			if (dictionarySet.contains(fuseWord.toLowerCase())) {
				matches[worditerate] = fuseWord;
				continue;
			}
			
			//try fuzzy matching on fuseword if there were nonword chars
			//for cases like appre-henfion
			if (fuseWord.length() < regWord.length()) {
				String possible = findClosest(fuseWord, title);
				// checking for length > 0 would exclude the reply "" (no match)
				// but I also want to exclude cases like .^a*-n where the letters
				// make a word pretty much by accident, so I require length > 3
				if (possible.length() > 3) {
					matches[worditerate] = possible;
					continue;
				}
			}

			if (regWord.contains("-")) {
				String[] tokens = regWord.split("[-]+");
				// split at any sequence of hyphens
				int tokencount = tokens.length;
				int correct = 0;
				String corrected = "";
				boolean madeChanges = false;
				int counter = 0;
				for (String token: tokens) {
					counter += 1;
					if (dictionarySet.contains(token)) {
						correct += 1;
						corrected = corrected + token;
					}
					else {
						boolean firstOneTitlecased = false;
						if (counter < 2 & title == true) firstOneTitlecased = true;
						String match = findClosest(token, firstOneTitlecased);
						if (match.equals("")) {
							corrected = corrected + token;
						}
						else {
							corrected = corrected + match;
							correct += 1;
							madeChanges = true;
						}	
					}
					if (counter < tokencount) corrected = corrected + " ";
				}
				if ((correct/(double) tokencount) > 0.6 & madeChanges) {
					matches[worditerate] = corrected;
					continue;
				}
				if ( (correct/ (double) tokencount) > 0.6) {
					matches[worditerate] = regWord;
					continue;
					// Splitting hyphens produced matches in a banal, replicable way. No rule.
				}
			}
			
			// Is this token a likely tail-fragment? If so, don't create a rule. We'll try to fuse, in context.
			ArrayList<String> tailmatches = matchtail(regWord);
			if (tailmatches.size() > 0 & title == false) {
				matches[worditerate] = "#tail " + tailmatches.get(0);
				continue;
			}
			
			if ((regWord.endsWith("eth") | regWord.endsWith("est")) & regWord.length() > 5) {
				int wordLen = regWord.length();
				String stem = regWord.substring(0, (wordLen - 2));
				if (dictionarySet.contains(stem)) {
					matches[worditerate] = regWord;
					continue;
				}
				stem = regWord.substring(0, (wordLen - 3));
				if (dictionarySet.contains(stem)) {
					matches[worditerate] = regWord;
					continue;
				}	
			}
			
			if (regWord.endsWith("llest")) {
				int wordLen = regWord.length();
				String stem = regWord.substring(0, (wordLen - 4));
				if (dictionarySet.contains(stem)) {
					matches[worditerate] = regWord;
					continue;
				}
			}
			
		    // All the obvious things having failed, we need to attempt fuzzy matching now.
			matches[worditerate] = findClosest(regWord, title);
			
		}
		return matches;
	}
			
	private String findClosest(String word, boolean titlecase) {
		
		ArrayList<Integer> candidates = getCandidates(word.toLowerCase(), titlecase);
		String[] wordsToCheck = new String[candidates.size()];
		double[] wordCoefficients = new double[candidates.size()];
		int idx = 0;
		for (int candidate : candidates) {
			wordsToCheck[idx] = dictionary[candidate];
			wordCoefficients[idx] = freqCoefficients[candidate];
			++ idx;
		}
		
		if (titlecase) {
			String initialChar = word.substring(0,1);
			word = initialChar.toUpperCase() + word.substring(1);
		}
		
		Tuple[] results = matcher.findMatches(word, wordsToCheck, wordCoefficients);
		Tuple first = results[0];
		String resultword = first.getFirst();
		if (!resultword.equals("no match")) {
			matcher.traceSubstitutions(word, resultword);
			return resultword;
		}
		else {
			if (word.length() > 6 & titlecase == false) {
				return splitword(word.toLowerCase());
			}
			else return "";
		}
	}
	
	private String splitword(String word) {
		// start by getting matches to the tail of the word
		ArrayList<String> matches = new ArrayList<String>();
		ArrayList<Double> probabilities = new ArrayList<Double>();
		for (int i = 0; i < 10000; ++ i) {
			String head = dictionary[i];
			if (!word.startsWith(head)) continue;
			if (head.length() > (word.length() + 2)) continue;
			if (head.length() < 2) continue;
			for (int j = 0; j < 10000; ++ j) {
				String tail = dictionary[j];
				if (!word.endsWith(tail)) continue;
				if (tail.length() + head.length() != word.length()) continue;
				if (tail.length() < 2) continue;
				matches.add(head + " " + tail);
				probabilities.add(freqCoefficients[i] * freqCoefficients[j]);
			}
		}
		int numMatches = probabilities.size();
		String returnword = "";
		if (numMatches < 1) {
			return returnword;
		}
		else {
			double max = 0;
			for (int i = 0; i < numMatches; ++i) {
				double cutoff = 0.051 - (0.00006 * word.length());
				if (probabilities.get(i) > cutoff & probabilities.get(i) > max) {
					max = probabilities.get(i);
					returnword = matches.get(i);
					System.out.println(returnword + " " + Double.toString(max));
				}
			}
		return returnword;
		}
	}
}
