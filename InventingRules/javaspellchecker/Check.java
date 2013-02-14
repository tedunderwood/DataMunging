package spellchecker;
// import java.util.*;
import java.util.ArrayList;

public class Check {

	static final String alphabet = "abcdefghijklmnopqrstuvwxyz";
	
	public static void main(String[] args) {
		String outPath = "/Users/tunderwood/javaspellcheck/";
		FileCabinet cabinet = new FileCabinet(outPath);
		double[][] confusionMatrix = cabinet.getMatrix();
		Levenshtein matcher = new Levenshtein(confusionMatrix);
		matcher.unpackMatrix();
		
		Lexicon mainLex = cabinet.getMainDictionary(40000);
		String[] recallDictionary = mainLex.recallLexicon;
		int[] volsPerWord = mainLex.numberOfVolumes;
		boolean[] titlecased = mainLex.titlecased;
		String[] precisionDictionary = mainLex.precisionLexicon;
		double[] freqCoefficients = new double[volsPerWord.length];
		for (int i = 0; i < volsPerWord.length; ++i) {
			freqCoefficients[i] = Math.log(volsPerWord[i]) / (double) 60;
		}
		
		for (int charposition = 0; charposition < 26; ++charposition) {
			String letter = alphabet.substring(charposition, charposition + 1);
			String inputPath = "/Users/tunderwood/OCR/filtered/" + letter + ".txt"; 
			ChunkOfTypes typesToProcess = cabinet.wordsToProcess(inputPath);
			String[] rawTokens = typesToProcess.getWords();
			boolean[] rawTitles = typesToProcess.getTitlecased();
			System.out.println(rawTokens.length);
			
			// Scanner keyboard = new Scanner(System.in, "UTF8");
			
			RuleGuesser guessBot = new RuleGuesser(recallDictionary, freqCoefficients, titlecased, matcher, precisionDictionary);
			int chunklength = 50000;
			String[] assignment = new String[chunklength];
			
			for (int i = 0; i < chunklength; ++i) {
				assignment[i] = rawTokens[i];
			}
			
			String[] matches = guessBot.mineMatches(assignment, rawTitles);
			int matchlength = matches.length;
			assert (matchlength == chunklength);
			ArrayList<String> failedWords = new ArrayList<String>(matchlength);
			ArrayList<String> ruleSet = new ArrayList<String>(matchlength);
			ArrayList<String> tailWords = new ArrayList<String>(matchlength);
			ArrayList<String> addToDict = new ArrayList<String>(matchlength);
			int[] numVols = typesToProcess.getNumVols();
			
			for (int i = 0; i < matchlength; ++i) {
				String originalword = assignment[i].toLowerCase();
				if (matches[i].equals(assignment[i])) {
					// this word was in dictionary
					System.out.println(matches[i] + " already in dictionary.");
					if (originalword.endsWith("eth") | originalword.endsWith("est")) {
						addToDict.add(originalword + "\t" + Integer.toString(numVols[i]) + "\t0");
					}
					continue;
				}
				else if (matches[i].equals("")) {
					// we failed to match this
					String failedLine = typesToProcess.getSpecificLine(i);
					failedWords.add(failedLine);
			        continue;
				}
				else if (matches[i].startsWith("#tail ")) {
					// this word looks a lot like a tail fragment of a longer word
					String tailLine = assignment[i] + "\t" + matches[i].substring(6) + "\t" + Integer.toString(numVols[i]);
					tailWords.add(tailLine);
				}
				else {
					// we have a new correction rule
					String ruleLine = assignment[i] + "\t" + matches[i] + "\t" + Integer.toString(numVols[i]);
					ruleSet.add(ruleLine);
				}
			}
			
			if (failedWords.size() > 0) {
				LineWriter outFile = new LineWriter(outPath + "outfiles/failedWords.txt", true);
				String[] outLines = new String[failedWords.size()];
				failedWords.toArray(outLines);
				outFile.send(outLines);
			}
			if (tailWords.size() > 0) {
				LineWriter outFile = new LineWriter(outPath + "outfiles/tailWords.txt", true);
				String[] outLines = new String[tailWords.size()];
				tailWords.toArray(outLines);
				outFile.send(outLines);
			}
			if (ruleSet.size() > 0) {
				LineWriter outFile = new LineWriter(outPath + "outfiles/ruleSet.txt", true);
				String[] outLines = new String[ruleSet.size()];
				ruleSet.toArray(outLines);
				outFile.send(outLines);
			}
			if (addToDict.size() > 0) {
				LineWriter outFile = new LineWriter(outPath + "outfiles/addToDictionary.txt", true);
				String[] outLines = new String[addToDict.size()];
				addToDict.toArray(outLines);
				outFile.send(outLines);
			}
		}
		matcher.listInsertions();
		int[][] newMatrix = matcher.getSubstitutions();
		cabinet.addMatrix(newMatrix);
	}

}
