

import cc.mallet.util.*;
import cc.mallet.types.*;
import cc.mallet.pipe.*;
import cc.mallet.pipe.iterator.*;
import cc.mallet.topics.*;

import java.util.*;
import java.util.regex.*;
import java.io.*;

public class FindTopics {

	/* arguments
	 * sample-data\web\en\conllFormat.txt 1 3 1 0.02 0.01 2
	 */
	public static void main(String[] args) throws Exception {

		if (args.length != 8){
			System.err.println("CORRECT USAGE:\n FindTopics <inputFileWithDocuments> <printTopKWords[0 or 1]>" +
					"<K> <position Of use_phrases feature> <parameter a for LDA> <parameter b for LDA> <numOfTopics>");
			return;
		}
		String inputFile = args[0];
		System.err.println(inputFile);
		int showTopWords = Integer.valueOf(args[1]);
		int topK = Integer.valueOf(args[2]);
		boolean usePhrases = (Integer.valueOf(args[3])!=0);
		float a = Float.valueOf(args[4]);
		float b = Float.valueOf(args[5]);
		int numTopics = Integer.valueOf(args[6]);
		int iter = Integer.valueOf(args[7]);
		String malletFile = "mallet.txt";
		File inputFd = new File(inputFile);
		File malletFd = new File(inputFd.getParent(),malletFile);
		
		
		System.err.println("Print mallet file"+inputFd.getParent());
		//convert from Conll type to mallet type
		PreprocessForLDA.ConllToMallet(inputFile,malletFile,usePhrases, 11);
		
		// Begin by importing documents from text to feature sequences
		ArrayList<Pipe> pipeList = new ArrayList<Pipe>();

		// Pipes: lowercase, tokenize, remove stopwords, map to features
		pipeList.add( new CharSequenceLowercase() );
		//pipeList.add( new CharSequence2TokenSequence(Pattern.compile("[\\p{L}\\p{XDigit}]+[\\p{L}\\p{P}\\p{XDigit}]+\\p{L}")) );
		pipeList.add( new CharSequence2TokenSequence(Pattern.compile("[\\p{L}\\p{Digit}][^\\p{Space}]+")) );
		pipeList.add( new TokenSequenceRemoveStopwords(new File("stoplists/en.txt"), "UTF-8", false, false, false) );
		pipeList.add( new TokenSequence2FeatureSequence() );

		InstanceList instances = new InstanceList (new SerialPipes(pipeList));
		

		Reader fileReader = new InputStreamReader(new FileInputStream(malletFile), "UTF-8");
		instances.addThruPipe(new CsvIterator (fileReader, Pattern.compile("^(\\S*)[\\s,]*(\\S*)[\\s,]*(.*)$"),
											   3, 2, 1)); // data, label, name fields
		
		// Create a model with 2 topics, alpha_t = 0.01, beta_w = 0.01
		//  Note that the first parameter is passed as the sum over topics, while
		//  the second is 
		ParallelTopicModel model = new ParallelTopicModel(numTopics, numTopics*a, b);
		model.addInstances(instances);

		// Use two parallel samplers, which each look at one half the corpus and combine
		//  statistics after every iteration.
		model.setNumThreads(10);

		// Run the model for 50 iterations and stop (this is for testing only, 
		//  for real applications, use 1000 to 2000 iterations)
		model.setNumIterations(iter);
		model.estimate();
		
		
		// Serialize the model in the file LDAModel
		File LDAModelFile = new File("LDAModel");
		model.write(LDAModelFile);

		//write back topics of tokens in conll format
		PreprocessForLDA.MalletToConll(inputFile,model.data);
		//malletFd.delete();
		if (showTopWords == 1){
			File topWords = new File(inputFd.getParent(),"top"+topK+"Words");
			model.printTopWords(topWords, topK, false);
		}

	}

}