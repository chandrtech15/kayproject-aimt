

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PrintStream;
import java.io.UnsupportedEncodingException;
import java.util.ArrayList;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import cc.mallet.topics.TopicAssignment;
import cc.mallet.types.FeatureSequence;
import cc.mallet.types.Instance;
import cc.mallet.types.InstanceList;

public class PreprocessForLDA {
	
	public static String fieldSep = "#";
	
	public PreprocessForLDA(){
		
	}
	
	public static void ConllToMallet(String fileName, String malletFilename, boolean usePhrases, int fieldForPhrase) throws Exception, FileNotFoundException{
		System.err.println("Here in conlltomallet");
		BufferedReader fileReader = null;
		File mFile = new File(malletFilename);
		PrintStream out = new PrintStream(new File(malletFilename));
		//split line in groups 1-5 and rest of the line is group 6
		Pattern pattern = Pattern.compile("^(\\S*)[\\s]+(\\S*)[\\s]+(\\S*)[\\s]+(\\S*)[\\s]+(\\S*)(.*)+$");
		Pattern patternForName = Pattern.compile("^\\.I[\\s]+([0-9]+)");
		Pattern patternForHeadOfPhrase = Pattern.compile("(\\S*)");
		String target = "X";
		System.err.println("Printing file"+mFile.getAbsolutePath());
		//for **the** file of Conll format
		fileReader = new BufferedReader(new InputStreamReader(new FileInputStream(new File(fileName)), "UTF-8"));
		String data = "";
		String line = null;
		String name = "";
		String token="";
		
		ArrayList<MultiWordExpression> expressions = new ArrayList<MultiWordExpression>();
		
		while( (line =  fileReader.readLine())!=null) {
			if (line.startsWith(".I")){ //new file
				//write back old file
				if (!data.equals("")){
					for(MultiWordExpression exp: expressions){
						data += exp.getExpression()+ " ";
					}
					expressions = new ArrayList<MultiWordExpression>();	
					out.print(name);
					out.print(" " + target);
					out.println(" " + data);
				}
				//start buffering new file
				data = "";
				Matcher m = patternForName.matcher(line) ;
				m.find();
				name = m.group(1);
				continue;
			}
			if(line.equals(""))
				continue;  
			Matcher m = pattern.matcher(line);
			m.find();
			token = "";
			//beggining of new sentence
			
			if (Integer.valueOf(m.group(1)) == 1){
				
				//write previous sentence
				if (!expressions.isEmpty()){
					for(MultiWordExpression exp: expressions){
						data += exp.getExpression()+ " ";
					}
					expressions = new ArrayList<MultiWordExpression>();	
				}
					
			}
			//add current token in the expression list
			//don't use phrases
			token = "";
			Matcher m2 = patternForHeadOfPhrase.matcher(m.group(6));
			m2.find();
			int curHead;
			
			if (usePhrases == false){
				curHead = 0;
			}
			else{
				curHead = Integer.valueOf(m2.group(1));
			}
			
			if ( m.group(3).equals("<unknown>")){
				token += m.group(2);
			}
			else{
				token += m.group(3);
			}
			if (usePhrases == false || curHead == 0){
				MultiWordExpression newExp = new MultiWordExpression(0);
				newExp.setHeadFeatures(token);
				expressions.add(newExp);
			}
			else{ 
				if (expressions.isEmpty()   //new expression
								||curHead != expressions.get(expressions.size()-1).head ) {
					MultiWordExpression newExp = new MultiWordExpression(m.group(2),curHead);
					if (curHead == Integer.valueOf(m.group(1))){
						newExp.setHeadFeatures(token);
					}	
					expressions.add(newExp);	
				}
				else{   
					expressions.get(expressions.size()-1).addWord(m.group(2));
					if (curHead == Integer.valueOf(m.group(1))){
						expressions.get(expressions.size()-1).setHeadFeatures(token);
					}
				}
				
			}
		}
		//for last sentence of last file
		for(MultiWordExpression exp: expressions){
			data += exp.getExpression()+ " ";
		}
		//write back last Senrence
		out.print(name);
		out.print(" " + target);
		out.println(" " + data);
		fileReader.close();
		System.err.println("Writing in file"+malletFilename);
		out.close();
	}
	
	public static void MalletToConll(String  fileName, ArrayList<TopicAssignment> data ) throws Exception, FileNotFoundException{
		BufferedReader fileReader = null;
		PrintStream out = null;
		//split line in groups 1-5 and rest of the line is group 6
		Pattern pattern = Pattern.compile("^(\\S*)[\\s]+(\\S*)[\\s]+(\\S*)[\\s]+(\\S*)[\\s]+(\\S*)(.*)$");
		String token="";
		String tokenInstance = "";
		String newLine = "";
		String newFile="";
		 //for **the** file
		
		fileReader = new BufferedReader(new InputStreamReader(new FileInputStream(new File(fileName)), "UTF-8"));

		
		newFile = fileName.split("\\.")[0]+ "_topics"+fileName.split("\\.")[1];
		out = new PrintStream(new File(newFile));
		int topic = -2;
		String line = null;
		Matcher m = null;
		for(int inst=0; inst<data.size(); inst++){
			for (int pos = 0;pos<((FeatureSequence)data.get(inst).instance.getData()).size(); pos++){
				
				tokenInstance = ((FeatureSequence)data.get(inst).instance.getData()).get(pos).toString();
				
				String[] newWords = tokenInstance.split("!@!");
				for (String word : newWords){
					while( (line =  fileReader.readLine())!=null) {
						if(line.equals("") || line.startsWith(".I")){
							out.println(line);
							continue;  
						}
						m = pattern.matcher(line);
						m.find();
						token = "";
						if (m.group(3).equals("<unknown>")){
							token+=m.group(2).toLowerCase();  //to lowercase
							
						}
						else{
							token+=m.group(3).toLowerCase();
						}
						
						//System.err.println("Word is: "+word);
						//System.err.println("Line is: "+line);
						//if (word.equals("resistant")){
						//	Thread.sleep(100);
						//}
						if (token.startsWith(word) || token.endsWith(word)){
							topic = Integer.valueOf(data.get(inst).topicSequence.getLabelAtPosition(pos).toString().split("topic")[1]);
							break;
						}
						else{
							//if tokenInstace not equal with token then token was a stopWord
							topic = -1;
							newLine = "";
							for(int i=1; i<6; i++){
								newLine+=m.group(i)+"\t";
							}
							newLine +=  topic+"\t";
							newLine += m.group(6);
							if (!newLine.contains("\n")){
								newLine += "\n";
							}
							out.print(newLine);
						}
						
					}
					newLine = "";
					for(int i=1; i<6; i++){
						newLine+=m.group(i)+"\t";
					}
					newLine += topic +"\t";
					newLine += m.group(6);
					if (!newLine.contains("\n")){
						newLine += "\n";
					}
					out.print(newLine);
				}
			}
		}
		while( (line =  fileReader.readLine())!=null) {
			if(line.equals("") || line.startsWith(".I")){
				out.println(line);
				continue;  
			}
			topic = -1;
			m = pattern.matcher(line);
			m.find();
			newLine = "";
			for(int i=1; i<6; i++){
				newLine+=m.group(i)+"\t";
			}
			newLine +=  topic+"\t";
			newLine += m.group(6);
			if (!newLine.contains("\n")){
				newLine += "\n";
			}
			out.print(newLine);
		}
		fileReader.close();
		out.close();
		
	}
	
	public static void MalletToQueryConll(String queryFile, InstanceList query, int[][] topics) throws IOException{
		BufferedReader fileReader = null;
		PrintStream out = null;
		//split line in groups 1-5 and rest of the line is group 6
		Pattern pattern = Pattern.compile("^(\\S*)[\\s]+(\\S*)[\\s]+(\\S*)[\\s]+(\\S*)[\\s]+(\\S*)(.*)$");
		String token="";
		String tokenInstance = "";
		String newLine = "";
		String newFile="";
		 //for **the** file
		
		fileReader = new BufferedReader(new InputStreamReader(new FileInputStream(new File(queryFile)), "UTF-8"));
		newFile = queryFile.split("\\.")[0]+ "_Inftopics"+queryFile.split("\\.")[1];
		out = new PrintStream(new File(newFile));
		int topic = -2;
		String line = null;
		Matcher m = null;
		//for every  query instance 
		for (int q = 0; q < query.size(); q++)
		{
			
			for (int pos = 0;pos<((FeatureSequence)query.get(q).getData()).size(); pos++){
				tokenInstance = ((FeatureSequence)query.get(q).getData()).get(pos).toString();
				String[] newWords = tokenInstance.split("!@!");
				for (String word : newWords){
					while( (line =  fileReader.readLine())!=null) {
						if(line.equals("") || line.startsWith(".I")){
							out.println(line);
							continue;  
						}
						m = pattern.matcher(line);
						m.find();
						
						token = "";
						if (m.group(3).equals("<unknown>")){
							token += m.group(2).toLowerCase();
							
						}
						else{
							token += m.group(3).toLowerCase();
						}
						if (token.startsWith(word) || token.endsWith(word)){
							topic = topics[q][pos];
							//System.err.println(word+ "   "+topic);
							break;
						}
						else{
							//if tokenInstace not equal with token then token was a stopWord
							topic = -1;
							newLine = "";
							for(int i=1; i<6; i++){
								newLine+=m.group(i)+"\t";
							}
							newLine +=  topic+"\t";
							newLine += m.group(6);
							if (!newLine.contains("\n")){
								newLine += "\n";
							}
							out.print(newLine);
						}
							
					}
					newLine = "";
					for(int i=1; i<6; i++){
						newLine+=m.group(i)+"\t";
					}
					newLine += topic +"\t";
					newLine += m.group(6);
					if (!newLine.contains("\n")){
						newLine += "\n";
					}
					out.print(newLine);
	
				}
			}
		}
		while( (line =  fileReader.readLine())!=null) {
			if(line.equals("") || line.startsWith(".I")){
				out.println(line);
				continue;  
			}
			topic = -1;
			m = pattern.matcher(line);
			m.find();
			newLine = "";
			for(int i=1; i<6; i++){
				newLine+=m.group(i)+"\t";
			}
			newLine +=  topic+"\t";
			newLine += m.group(6);
			if (!newLine.contains("\n")){
				newLine += "\n";
			}
			out.print(newLine);
		}
		fileReader.close();
		out.close();
	}
}