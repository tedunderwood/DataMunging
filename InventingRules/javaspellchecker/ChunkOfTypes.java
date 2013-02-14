package spellchecker;

public class ChunkOfTypes {
	private String[] originalLines;
	private String[] wordsThemselves;
	private int[] numberVolumes;
	private boolean[] titlecased;
	private int numberOfLines;
	
public ChunkOfTypes(String[] originalLines, String[]wordsThemselves, int[] numberVolumes, boolean[] titlecased) {
	this.numberOfLines = originalLines.length;
	this.originalLines = originalLines;
	this.wordsThemselves = wordsThemselves;
	this.numberVolumes = numberVolumes;
	this.titlecased = titlecased;
}

public String[] getLines() {
	return originalLines;
}

public String[] getWords() {
	return wordsThemselves;
}

public int[] getNumVols() {
	return numberVolumes;
}

public boolean[] getTitlecased() {
	return titlecased;
}

public int getChunkSize() {
	return numberOfLines;
}

public String getSpecificLine(int linenum) {
	return originalLines[linenum];
}
	

}
