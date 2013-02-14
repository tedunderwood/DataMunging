package spellchecker;
import java.util.HashMap;
import java.lang.Math;
import static java.util.Arrays.fill;

public class FileCabinet {
	
	String inPath;
	String outPath;
	static final CharSequence dictionaryCharacters = "abcdefghijklmnopqrstuvwxyz0123456789ßàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ'-÷";
	HashMap<Character, Integer> dictionaryMap;
	
	public FileCabinet(String rootPath) {
		inPath = rootPath + "infiles/";
		outPath = rootPath + "outfiles/";
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
	}
	
//	private char codeToDictchar(int code) {
//		char toReturn = '÷';
//		if (code >= 0 & code <= 70) toReturn = dictionaryCharacters.charAt(code);
//		return toReturn;
//	}
	
	private int dictcharToCode(char dictchar) {
		Integer code = dictionaryMap.get(dictchar);
		if (code == null) code = 70;
		return code;
	}
	
	private static double stringToDouble(String aString) {
		try {
	         double d = Double.valueOf(aString.trim()).doubleValue();
	         return d;
	      } catch (NumberFormatException nfe) {
	         System.out.println("NumberFormatException: " + nfe.getMessage());
	         return 0.01;
	      }
	}
	
	public double[][] getMatrix() {
		LineReader inFile = new LineReader(inPath + "CharMatrix.txt");
		String[] fileLines = inFile.readlines();
		
		int[][] substitutionCounts = new int[256][71];
		
		for (int i = 0; i < 256; ++i) {
			String line = fileLines[i];
			String[] commaSepValues = line.split(",");
			int j = 0;
			
			for (String aValue : commaSepValues) {
				int substitutions = Integer.parseInt(aValue);
				substitutionCounts[i][j] = substitutions;
				++ j;
			}	
		}
		
		int[] substitutionSums = new int[256];
		fill(substitutionSums, 1);
		
		for (int i = 0; i < 256; ++ i) {
			for (int j = 0; j < 71; ++ j) {
				substitutionSums[i] += substitutionCounts[i][j];
			}
		}
		
		double[][] confusionMatrix = new double[256][71];
		
		for (int i = 0; i < 256; ++ i) {
			for (int j = 0; j < 71; ++ j) {
				confusionMatrix[i][j] = Math.pow(1 - (substitutionCounts[i][j] / (double) substitutionSums[i]), 3);
				// The cost of substitution is (1 - probabilityOfSubstitution)^3.
			}
		}
		// The confusion distance of a character to itself is defined as always zero.
		// We don't do this for dictionary character 70, because it's a catch-all.
		for (int i = 0; i < 256; ++i) {
			int dictionaryEquivalent = dictcharToCode((char) i);
			if (dictionaryEquivalent < 70) confusionMatrix[i][dictionaryEquivalent] = 0;
		}
		// We define the confusion distance from a diacritic to its normal equivalent as 0.1.
		CharSequence diacriticString = "èéêë";
		for (int i = 0; i < diacriticString.length(); ++i) {
			int diacriticDict = dictcharToCode(diacriticString.charAt(i));
			int diacriticText = (int) diacriticString.charAt(i);
			int normalText = (int) 'e';
			int normalDict = dictcharToCode('e');
			confusionMatrix[normalText][diacriticDict] = 0.1;
			confusionMatrix[diacriticText][normalDict] = 0.1;
		}
		diacriticString = "àáâãäå";
		for (int i = 0; i < diacriticString.length(); ++i) {
			int diacriticDict = dictcharToCode(diacriticString.charAt(i));
			int diacriticText = (int) diacriticString.charAt(i);
			int normalText = (int) 'a';
			int normalDict = dictcharToCode('a');
			confusionMatrix[normalText][diacriticDict] = 0.1;
			confusionMatrix[diacriticText][normalDict] = 0.1;
		}
		diacriticString = "ìíîï";
		for (int i = 0; i < diacriticString.length(); ++i) {
			int diacriticDict = dictcharToCode(diacriticString.charAt(i));
			int diacriticText = (int) diacriticString.charAt(i);
			int normalText = (int) 'i';
			int normalDict = dictcharToCode('i');
			confusionMatrix[normalText][diacriticDict] = 0.1;
			confusionMatrix[diacriticText][normalDict] = 0.1;
		}
		diacriticString = "òóôõöø";
		for (int i = 0; i < diacriticString.length(); ++i) {
			int diacriticDict = dictcharToCode(diacriticString.charAt(i));
			int diacriticText = (int) diacriticString.charAt(i);
			int normalText = (int) 'o';
			int normalDict = dictcharToCode('o');
			confusionMatrix[normalText][diacriticDict] = 0.1;
			confusionMatrix[diacriticText][normalDict] = 0.1;
		}
		diacriticString = "ùúûü";
		for (int i = 0; i < diacriticString.length(); ++i) {
			int diacriticDict = dictcharToCode(diacriticString.charAt(i));
			int diacriticText = (int) diacriticString.charAt(i);
			int normalText = (int) 'u';
			int normalDict = dictcharToCode('u');
			confusionMatrix[normalText][diacriticDict] = 0.1;
			confusionMatrix[diacriticText][normalDict] = 0.1;
		}
		return confusionMatrix;
	}
	
	public Lexicon getMainDictionary(int recallLimit) {
		LineReader inFile = new LineReader(inPath + "maindict.txt");
		String[] fileLines = inFile.readlines();
		int numLines = fileLines.length;
		// The recallLimit controls how much of the dictionary we actually use for matching purposes.
		String[] firstLex = new String[numLines];
		String[] recallLex = new String[recallLimit];
		boolean[] title = new boolean[recallLimit];
		int[] numberVols = new int[recallLimit];
		
		for (int i = 0; i < numLines; ++i) {
			String line = fileLines[i];
			String[] lineParts = line.split("[\t]");
			String word = lineParts[0];
			firstLex[i] = word;
			if (i < recallLimit) {
				recallLex[i] = word;
				numberVols[i] = Integer.parseInt(lineParts[1]);
			    double titleodds = stringToDouble(lineParts[2]);
			    title[i] = false;
			    if (titleodds > 2.5) title[i] = true; 
			}
		}
		// now we add a gazetteer of proper nouns to firstLex, and
		// archaic -est and -eth forms
		LineReader getProperNouns = new LineReader(inPath + "gazetteer.txt");
		fileLines = getProperNouns.readlines();
		LineReader getArchaic = new LineReader(inPath + "addToDictionary.txt");
		String[] moreLines = getArchaic.readlines();
		int totalLength = numLines + fileLines.length + moreLines.length;
		int twothirds = numLines + fileLines.length;
		String[] precisionLex = new String[totalLength];
		for (int i = 0; i < totalLength; ++ i) {
			if (i < numLines) {
				precisionLex[i] = firstLex[i];
			}
			else if (i < twothirds){
				String line = fileLines[i - numLines];
				String[] lineParts = line.split("[\t]");
				precisionLex[i] = lineParts[0].toLowerCase();
			}
			else {
				String line = moreLines[i - twothirds];
				String[] lineParts = line.split("[\t]");
				precisionLex[i] = lineParts[0].toLowerCase();
			}
		}
		Lexicon mainLex = new Lexicon(precisionLex, numberVols, title, recallLex);
		return mainLex;
	}
	
	public ChunkOfTypes wordsToProcess(String inPath) {
		LineReader inFile = new LineReader(inPath);
		String[] fileLines = inFile.readlines();
		int numLines = fileLines.length;
		String[] words = new String[numLines];
		int[] vols = new int[numLines];
		boolean[] titlecased = new boolean[numLines];
		
		for (int i = 0; i < numLines; ++i) {
			String line = fileLines[i];
			String[] lineParts = line.split("[\t]");
			words[i] = lineParts[0];
			vols[i] = Integer.parseInt(lineParts[2]);
			double titleodds = stringToDouble(lineParts[4]);
			titlecased[i] = false;
			if (titleodds > 2.5) titlecased[i] = true;
		}
		ChunkOfTypes chunk = new ChunkOfTypes(fileLines, words, vols, titlecased);
		return chunk;
	}
    
	public void addMatrix(int[][] newMatrix) {
		LineReader inFile = new LineReader(inPath + "CharMatrix.txt");
		String[] fileLines = inFile.readlines();
		
		int[][] substitutionCounts = new int[256][71];
		
		for (int i = 0; i < 256; ++i) {
			String line = fileLines[i];
			String[] commaSepValues = line.split(",");
			int j = 0;
			
			for (String aValue : commaSepValues) {
				int substitutions = Integer.parseInt(aValue);
				substitutionCounts[i][j] = substitutions;
				++ j;
			}	
		}
		
		String[] outlines = new String[256];
		for (int i = 0; i < 256; ++i) {
			String thisLine = "";
			for (int j = 0; j < 71; ++j) {
				substitutionCounts[i][j] += newMatrix[i][j];
				thisLine = thisLine + Integer.toString(substitutionCounts[i][j]);
				if (j < 70) thisLine = thisLine + ",";
			}
			outlines[i] = thisLine;
		}
		
		LineWriter outFile = new LineWriter(outPath + "CharMatrix.txt", false);
		outFile.send(outlines);
	}
}
