package spellchecker;
import java.io.*;

public class LineWriter {
	File fileName;
	boolean append;
	
public LineWriter(String dirPath, boolean append) {
	this.fileName = new File(dirPath);
	this.append = append;
}

public void send(String[] lineArray) {
	try {
		BufferedWriter fileout = new BufferedWriter
				(new OutputStreamWriter(new FileOutputStream(fileName, append), "UTF-8"));
		// The boolean argument to FileOutputStream is whether to append.
		for(String line : lineArray) {
			fileout.write(line + "\n");
		}
		fileout.close();
	}
	catch (IOException e){
		System.out.println("Exception: " + e);
	}
	}
}

