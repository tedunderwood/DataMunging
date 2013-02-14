/**
 * 
 */
package spellchecker;

/**
 * @author tunderwood
 *
 */
public class Lexicon {
	String[] precisionLexicon;
	int[] numberOfVolumes;
	boolean[] titlecased;
	String[] recallLexicon;
	// The Lexicon divides into two parts -- a small "recall lexicon" where we attempt fuzzy matching
	// if a word is misspelled, and a larger "precision lexicon" that we use only for recognition, so
	// as *not* to "correct" a word that is correctly spelled.
	
public Lexicon(String[] precisionLex, int[] numVols, boolean[] title, String[] recallLex) {
	precisionLexicon = precisionLex;
	numberOfVolumes = numVols;
	titlecased = title;
	recallLexicon = recallLex;
}

}
