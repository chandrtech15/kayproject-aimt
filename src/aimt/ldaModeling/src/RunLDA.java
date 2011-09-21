

import java.util.Arrays;

public class RunLDA {

	/**
	 * @param args
	 * @throws Exception 
	 */
	public static void main(String[] args) throws Exception {
		if (args.length==0){
			System.err.println("CORRECT USAGE:\n RunLDA <[F]indTopics or [I]nferTopics> <list of arguments>");		
			return;
		}
		//F sample-data\train.tg 1 3 0 0.01 0.01 10 30
		if (args[0].equals("F")){
			FindTopics.main(Arrays.copyOfRange(args, 1, args.length));
		}
		///I sample-data\web\en\conllFormat.txt 0
		else if (args[0].equals("I")){
			InferTopics.main(Arrays.copyOfRange(args, 1, args.length));
		}
		else{
			System.err.println("CORRECT USAGE:\n RunLDA <[F]indTopics or [I]nferTopics> <list of arguments>");		
			return;
		}
		

	}

}
