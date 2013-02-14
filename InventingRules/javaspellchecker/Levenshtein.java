package spellchecker;

import java.util.HashMap;
// import java.util.Arrays;

public class Levenshtein {
	double[][] confusionMatrix;
	static final String dictionaryCharacters = "abcdefghijklmnopqrstuvwxyz0123456789ßàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ'-÷";
	HashMap<Character, Integer> dictionaryMap;
	boolean[][] textInsertable;
	boolean[][] dictInsertable;
	final static String[] textInsertions = {
		"h-li", "m-in", "d-cl", "u-ii", "n-ii", "w-Av", "w-iv", "w-v/", "w-V/"
	};
	final static String[] dictInsertions = {
		"li-h", "li-H", "in-m", "ct-d", "ct-&", "ll-U", "li-U", "li-u", "rn-m", "ri-n", "ct-6", "sh-m"
	};
	int[][] substitutionsCounted;
	HashMap<String, Integer> insertionsCounted;
	
public Levenshtein(double[][] confusionMatrix) {
	this.confusionMatrix = confusionMatrix;
	
	dictionaryMap = new HashMap<Character, Integer>();
	
	for (int i = 0; i < dictionaryCharacters.length(); i++) {
		char aCharacter = dictionaryCharacters.charAt(i);
		dictionaryMap.put(aCharacter, i);
	}
	for (int i = 0; i < 256; i ++) {
		char aCharacter = (char) i;
		Integer inYet = dictionaryMap.get(aCharacter);
		if (inYet == null) dictionaryMap.put(aCharacter, 70);
		if (i > 64 & i < 91) dictionaryMap.put(aCharacter, i - 65);
	}
	
	textInsertable = new boolean[256][71];
	dictInsertable = new boolean[256][71];
	for (int t = 0; t < 256; ++t) {
		for (int d = 0; d < 71; ++d) {
			textInsertable[t][d] = false;
			dictInsertable[t][d] = false;
		}
	}
	for (String insertion : textInsertions) {
		int t = (int) insertion.charAt(3);
		int d = dictcharToCode(insertion.charAt(0));
		textInsertable[t][d] = true;
	}
	for (String insertion : dictInsertions) {
		int t = (int) insertion.charAt(3);
		int d = dictcharToCode(insertion.charAt(1));
		dictInsertable[t][d] = true;
	}
	
	substitutionsCounted = new int[256][71];
	insertionsCounted = new HashMap<String, Integer>();
}

// private char codeToDictchar(int code) {
//	char toReturn = '÷';
//	if (code >= 0 & code <= 70) toReturn = dictionaryCharacters.charAt(code);
//	return toReturn;
//}

private int dictcharToCode(char dictchar) {
	Integer code = dictionaryMap.get(dictchar);
	if (code == null) code = 70;
	return code;
}

public void unpackMatrix() {
	String[] csvfile = new String[26]; 
	for (int i = 0; i < 26; ++ i) {
		String line = "";
		int text = i + 97;
		for (int j = 0; j < 26; ++ j) {
			line = line + Double.toString(confusionMatrix[text][j]);
			if (j < 25) line = line + ",";
		}
	    csvfile[i] = line;
	}
	String outPath = "/Users/tunderwood/javaspellcheck/outfiles/";
	LineWriter outFile = new LineWriter(outPath + "alphabetSoup.csv", false);
	outFile.send(csvfile);
}

private static double minimum(double a, double b, double c) {
    return Math.min(Math.min(a, b), c);
}
 
public Tuple[] findMatches(String word, String[] possMatches, double[] freqCoefficients){
	int numMatches = possMatches.length;
	double cutoff = .15 + (word.length() / (double) 6);
	String closest = "";
	double closestConf = 10.0;
	String nextclosest = "";
	double nextConf = 10.0;
	
	for (int i = 0; i < numMatches; ++i) {
		String match = possMatches[i];
		double distance = editDistance(word, match);
		double confidence = distance - (distance * freqCoefficients[i]);
		
		if (confidence < closestConf) {
			nextclosest = closest;
			closest = match;
			nextConf = closestConf;
			closestConf = confidence;
		}
		else if (confidence < nextConf) {
			nextclosest = match;
			nextConf = confidence;
		}
	}
	
	if (closestConf < cutoff) {
		Tuple best = new Tuple(closest, closestConf);
		Tuple nextbest = new Tuple(nextclosest, nextConf);
		Tuple[] tuplePair = new Tuple[2];
		tuplePair[0] = best;
		tuplePair[1] = nextbest;
		return tuplePair;
	}
	else {
		Tuple[] tuplePair = new Tuple[2];
		Tuple dummy = new Tuple("no match", 0.0);
		tuplePair[0] = dummy;
		tuplePair[1] = dummy;
		return tuplePair;
	}
}

public double editDistance(CharSequence textWord, CharSequence dictWord) {
	double[][] distance = new double[textWord.length() + 1][dictWord.length() + 1];
	int twLen = textWord.length();
	int dwLen = dictWord.length();
	int[] textIntegers = new int[twLen];
	int[] dictIntegers = new int[dwLen];
	
    for (int i = 0; i <= twLen; i++){
    	distance[i][0] = i;
    	if (i > 0) {
    		int textAscii = (int) textWord.charAt(i-1);
    		if (textAscii > 255 | textAscii < 0) {
    			textAscii = 255;
    		}
    		textIntegers[i-1] = textAscii;
    	}
    }
    for (int j = 0; j <= dwLen; j++){
        distance[0][j] = j;
        if (j > 0) {
        	dictIntegers[j-1] = dictcharToCode(dictWord.charAt(j-1));
        }
    }   

    for (int t = 1; t <= textWord.length(); t++) {
            for (int d = 1; d <= dictWord.length(); d++) {
            	char textChar = textWord.charAt(t - 1);
            	char dictChar = dictWord.charAt(d - 1);
            	
            	int tIndex = textIntegers[t-1];
            	int dIndex = dictIntegers[d-1];
            	
            	double increment = confusionMatrix[tIndex][dIndex];
            	if (Character.toLowerCase(textChar) == dictChar) {
            		increment = 0;
            	}
            	// Insertions and deletions should never be cost-free, even
            	// when you're repeating the same character. Also, they
            	// should cost slightly more than substitutions.
            	double insertIncrement = increment + 0.3;
            	if (insertIncrement < .75 ) insertIncrement = 0.65;
            	
            	double diagonalCost = distance[t - 1][d - 1] + increment;
            	
            	double textInsertCost = distance[t - 1][d] + insertIncrement;
            	// First we check to see whether this text/dict combo is recognized
            	// as part of a multi-character substitution. If so, we get the previous
            	// text character and see whether the combination of two text chars with
            	// this dict char is in our list.
            	if (t >= 2 & textInsertable[tIndex][dIndex] == true) {
            		String charCombo = dictWord.charAt(d-1) + "-" +
            				textWord.charAt(t-2) + textWord.charAt(t-1);
            		for (int i = 0; i < textInsertions.length; ++i) {
            			if (charCombo.equals(textInsertions[i])) {
            				// If we're dealing with a known multi-character substitution
            				// both edit-distance increments (for the previous text char and
            				// this text char) are reduced.
            				int prevIndex = textIntegers[t - 2];
            				double takeBack = (confusionMatrix[prevIndex][dIndex] / 2);
            				distance[t - 1][d] = distance[t -1][d] - takeBack;
            				textInsertCost = distance[t - 1][d] + (insertIncrement / 4);
            				// that 4 is a finger in the scales
            			}
            		}
            	}
            	
            	double dictInsertCost = distance[t][d - 1] + insertIncrement;
            	// Could this be a fusion of two characters in a real (dictionary) word?
             	if (d >= 2 & dictInsertable[tIndex][dIndex] == true) {
            		String charCombo = Character.toString(dictWord.charAt(d-2)) + dictWord.charAt(d-1) + "-" +
            				textWord.charAt(t-1);
            		for (int i = 0; i < dictInsertions.length; ++i) {
            			// If we're dealing with a fusion (aka insertion in the dictionary word)
            			// reduce both edit-distance increments by half.
            			if (charCombo.equals(dictInsertions[i])) {
            				int prevIndex = dictIntegers[d - 2];
            				double takeBack = (confusionMatrix[tIndex][prevIndex] / 2);
            				distance[t][d - 1] = distance[t][d - 1] - takeBack;
            				dictInsertCost = distance[t][d - 1] + (insertIncrement / 3);
            			}
            		}
            	}
                
            	distance[t][d] = minimum(diagonalCost, textInsertCost, dictInsertCost);
            }
    }
    return distance[twLen][dwLen];
}

private void addOrIncrement(String insertion) {
	Integer currentCount = insertionsCounted.get(insertion);
	if (currentCount == null) insertionsCounted.put(insertion, 1);
	else insertionsCounted.put(insertion, currentCount + 1);
}

public void traceSubstitutions(CharSequence textWord, CharSequence dictWord) {
	double[][] distance = new double[textWord.length() + 1][dictWord.length() + 1];
	int twLen = textWord.length();
	int dwLen = dictWord.length();
	int[] textIntegers = new int[twLen];
	int[] dictIntegers = new int[dwLen];
	
    for (int i = 0; i <= twLen; i++){
    	distance[i][0] = i;
    	if (i > 0) {
    		int textAscii = (int) textWord.charAt(i-1);
    		if (textAscii > 255 | textAscii < 0) {
    			textAscii = 255;
    		}
    		textIntegers[i-1] = textAscii;
    	}
    }
    for (int j = 0; j <= dwLen; j++){
        distance[0][j] = j;
        if (j > 0) {
        	dictIntegers[j-1] = dictcharToCode(dictWord.charAt(j-1));
        }
    }   

    for (int t = 1; t <= textWord.length(); t++) {
            for (int d = 1; d <= dictWord.length(); d++) {
            	char textChar = textWord.charAt(t - 1);
            	char dictChar = dictWord.charAt(d - 1);
            	
            	int tIndex = textIntegers[t-1];
            	int dIndex = dictIntegers[d-1];
            	
            	double increment = confusionMatrix[tIndex][dIndex];
            	if (Character.toLowerCase(textChar) == dictChar) {
            		increment = 0;
            	}
            	// Insertions and deletions should never be cost-free, even
            	// when you're repeating the same character. Also, they
            	// should cost slightly more than substitutions.
            	double insertIncrement = increment + 0.3;
            	if (insertIncrement < .75 ) insertIncrement = 0.65;
            	
            	double diagonalCost = distance[t - 1][d - 1] + increment;
            	
            	double textInsertCost = distance[t - 1][d] + insertIncrement;
            	// First we check to see whether this text/dict combo is recognized
            	// as part of a multi-character substitution. If so, we get the previous
            	// text character and see whether the combination of two text chars with
            	// this dict char is in our list.
            	if (t >= 2 & textInsertable[tIndex][dIndex] == true) {
            		String charCombo = dictWord.charAt(d-1) + "-" +
            				textWord.charAt(t-2) + textWord.charAt(t-1);
            		for (int i = 0; i < textInsertions.length; ++i) {
            			if (charCombo.equals(textInsertions[i])) {
            				// If we're dealing with a known multi-character substitution
            				// both edit-distance increments (for the previous text char and
            				// this text char) are reduced by half.
            				int prevIndex = textIntegers[t - 2];
            				double takeBack = (confusionMatrix[prevIndex][dIndex] / 2);
            				distance[t - 1][d] = distance[t -1][d] - takeBack;
            				textInsertCost = distance[t - 1][d] + (insertIncrement / 4);
            			}
            		}
            	}
            	
            	double dictInsertCost = distance[t][d - 1] + insertIncrement;
            	// Could this be a fusion of two characters in a real (dictionary) word?
             	if (d >= 2 & dictInsertable[tIndex][dIndex] == true) {
            		String charCombo = Character.toString(dictWord.charAt(d-2)) + dictWord.charAt(d-1) + "-" +
            				textWord.charAt(t-1);
            		for (int i = 0; i < dictInsertions.length; ++i) {
            			// If we're dealing with a fusion (aka insertion in the dictionary word)
            			// reduce both edit-distance increments by half.
            			if (charCombo.equals(dictInsertions[i])) {
            				int prevIndex = dictIntegers[d - 2];
            				double takeBack = (confusionMatrix[tIndex][prevIndex] / 2);
            				distance[t][d - 1] = distance[t][d - 1] - takeBack;
            				dictInsertCost = distance[t][d - 1] + (insertIncrement / 3);
            			}
            		}
            	}
                
            	distance[t][d] = minimum(diagonalCost, textInsertCost, dictInsertCost);
            }
    }
    // Now augment the count of substitutions and record insertions.
    int t = twLen;
    int d = dwLen;
    while (t > 0 & d > 0) {
    	++ substitutionsCounted[textIntegers[t - 1]][dictIntegers[d - 1]];
    	
    	double diagonal = distance[t - 1][d - 1];
    	double dictInsert = distance[t][d - 1];
    	double textInsert = distance[t - 1][d];
    	
    	if (textInsert < diagonal & textInsert < dictInsert) {
    		if (t > 1) {
    			String textBigram = Character.toString(textWord.charAt(t - 2)) + Character.toString(textWord.charAt(t - 1));
    			String Insertion = Character.toString(dictWord.charAt(d - 1)) + "-" + textBigram;
    			addOrIncrement(Insertion);
    		}
    		t = t - 1;
    	}
    	else if (dictInsert < diagonal & dictInsert < textInsert) {
    		if (d > 1) {
    			String dictBigram = Character.toString(dictWord.charAt(d - 2)) + Character.toString(dictWord.charAt(d - 1));
    			String Insertion = dictBigram + "-" + Character.toString(textWord.charAt(t - 1));
    			addOrIncrement(Insertion);
    		}
    		d = d - 1;
    	}
    	else {
    		t = t - 1;
    		d = d - 1;
    	}
    	
    }
}
public void listInsertions() {
	for (String insertion : insertionsCounted.keySet()) {
		int occurrences = insertionsCounted.get(insertion);
		System.out.println(insertion + ": " + occurrences);
	}
}

public int[][] getSubstitutions() {
	return substitutionsCounted;
}

}
