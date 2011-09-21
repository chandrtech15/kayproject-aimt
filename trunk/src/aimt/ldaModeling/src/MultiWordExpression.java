

public class MultiWordExpression {

	private String phrase = "";
	public static String fieldSep = "#";
	private String headFeatures = "";
	public int head;
	public MultiWordExpression(int head){
		this.head = head;
	}
	
	public MultiWordExpression(String word, int head){
		this.phrase = word;
		this.head = head;
	}
	
	public void addWord(String word){
		if (!this.phrase.equals("")){
			this.phrase+="!@!";
		}
		this.phrase += word;
	}
	
	public void setHeadFeatures(String features){
		this.headFeatures = features;
	}
	
	public String getExpression(){
		if (this.headFeatures!=""){
			if (this.phrase.equals("")){
				return this.headFeatures;
			}
			return this.phrase + this.fieldSep + this.headFeatures;
		}
		return this.phrase;
	}
}
