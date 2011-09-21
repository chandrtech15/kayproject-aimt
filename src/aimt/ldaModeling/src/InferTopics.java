

import java.io.File;
import java.io.FileInputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.util.ArrayList;
import java.util.regex.Pattern;

import cc.mallet.pipe.CharSequence2TokenSequence;
import cc.mallet.pipe.CharSequenceLowercase;
import cc.mallet.pipe.Pipe;
import cc.mallet.pipe.SerialPipes;
import cc.mallet.pipe.TokenSequence2FeatureSequence;
import cc.mallet.pipe.TokenSequenceRemoveStopwords;
import cc.mallet.pipe.iterator.CsvIterator;
import cc.mallet.topics.ParallelTopicModel;
import cc.mallet.topics.TopicInferencer;
import cc.mallet.types.Instance;
import cc.mallet.types.InstanceList;

public class InferTopics {

	
	/**
	 * @param args
	 * @throws Exception 
	 */
	/*arguments
	 sample-data\web\en\conllFormat.txt 1 
	 */
	
	public static void main(String[] args) throws Exception {
		if (args.length != 2){
			System.err.println("CORRECT USAGE:\n InferTopics <file_with_query> <usePhrases [0 or 1].");
			return;
		}
		int[] fields = {2};
		String queryFile = args[0];
		boolean usePhrases = (Integer.valueOf(args[1])!=0);
		String malletFile = "mallet.txt";
		File inputFd = new File(queryFile);
		File malletFd = new File(inputFd.getParent(),malletFile);
		//convert CONLL file to mallet file
		PreprocessForLDA.ConllToMallet(queryFile,malletFile, usePhrases, 11);
		
		
		//create pipe
		ArrayList<Pipe> pipeList = new ArrayList<Pipe>();
		// Pipes: lowercase, tokenize, remove stopwords, map to features
		pipeList.add( new CharSequenceLowercase() );
		pipeList.add( new CharSequence2TokenSequence(Pattern.compile("[\\p{L}\\p{Digit}][^\\p{Space}]+")) );
		pipeList.add( new TokenSequenceRemoveStopwords(new File("stoplists/en.txt"), "UTF-8", false, false, false) );
		pipeList.add( new TokenSequence2FeatureSequence() );
		//add query in pipe
		InstanceList query = new InstanceList (new SerialPipes(pipeList));
		Reader fileReader = new InputStreamReader(new FileInputStream(new File(malletFile)), "UTF-8");
		query.addThruPipe(new CsvIterator (fileReader, Pattern.compile("^(\\S*)[\\s,]*(\\S*)[\\s,]*(.*)$"),
											   3, 2, 1)); // data, label, name fields
		//load existing model
		//check if exists
		File LDAModel = new File("LDAModel");
		if (!LDAModel.exists()){
			System.err.println("Error: LDAModel file does not exist!!\n Try executing first FindTopics.java");
			return;
		}
		ParallelTopicModel model = ParallelTopicModel.read(LDAModel);
		//get inferencer
		TopicInferencer inferencer = model.getInferencer();
		int [][] topics = new int[query.size()][];
		//get the sampled topics for the query
		int i = 0;
		for (Instance q : query){
			inferencer.getSampledDistribution(q, 7, 1, 1);
			topics[i] = inferencer.topicsPerToken;
			//write back in a new file the topics of the query
			i++;
		}
		PreprocessForLDA.MalletToQueryConll(queryFile,query,topics);
		malletFd.delete();

	}

}
