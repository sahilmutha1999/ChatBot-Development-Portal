import os
from huggingface_hub import InferenceClient
from PIL import Image
import dotenv
dotenv.load_dotenv()

class SimpleSwimlaneAnalyzer:
    """
    Using HuggingFace's InferenceClient - the modern way to use their API
    """
    
    def __init__(self):
        # Get token from environment
        self.token = os.getenv("HUGGINGFACE_HUB_TOKEN")
        if not self.token:
            raise ValueError("Please set HUGGINGFACE_HUB_TOKEN environment variable")
        
        # Initialize the InferenceClient
        self.client = InferenceClient(token=self.token)
    
    def analyze_image_simple(self, image_path: str, model: str = "Salesforce/blip-image-captioning-base"):
        """
        Analyze image with simple caption
        """
        print(f"\n🔍 Analyzing: {image_path}")
        print(f"🤖 Using model: {model}")
        
        try:
            # Use the image_to_text method
            result = self.client.image_to_text(
                image_path,
                model=model
            )
            
            return {
                "success": True,
                "model": model,
                "caption": result,
                "type": "simple_caption"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model": model
            }
    
    def analyze_with_question(self, image_path: str, question: str, model: str = "dandelin/vilt-b32-finetuned-vqa"):
        """
        Visual Question Answering - ask specific questions about the image
        """
        print(f"\n❓ Question: {question}")
        
        try:
            # Use visual_question_answering
            result = self.client.visual_question_answering(
                image=image_path,
                question=question,
                model=model
            )
            
            return {
                "success": True,
                "model": model,
                "question": question,
                "answer": result,
                "type": "vqa"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model": model
            }
    
    def comprehensive_swimlane_analysis(self, image_path: str):
        """
        Comprehensive analysis using multiple approaches
        """
        print("\n🏊 COMPREHENSIVE SWIMLANE ANALYSIS")
        print("="*60)
        
        results = {}
        
        # 1. Try different caption models
        caption_models = [
            "Salesforce/blip-image-captioning-base",
            "Salesforce/blip-image-captioning-large",
            "nlpconnect/vit-gpt2-image-captioning"
        ]
        
        print("\n1️⃣ Testing Caption Models:")
        for model in caption_models:
            result = self.analyze_image_simple(image_path, model)
            results[f"caption_{model.split('/')[-1]}"] = result
            
            if result["success"]:
                print(f"✅ {model}: {result['caption']}")
            else:
                print(f"❌ {model}: {result['error']}")
        
        # 2. Try Visual Question Answering
        print("\n2️⃣ Visual Question Answering:")
        questions = [
            "What type of diagram is this?",
            "How many swimlanes are in this diagram?",
            "What departments are shown?",
            "Describe the process flow."
        ]
        
        vqa_model = "dandelin/vilt-b32-finetuned-vqa"
        for question in questions:
            result = self.analyze_with_question(image_path, question, vqa_model)
            results[f"vqa_{questions.index(question)}"] = result
            
            if result["success"]:
                print(f"✅ Q: {question}")
                print(f"   A: {result['answer']}")
            else:
                print(f"❌ Failed: {result['error']}")
        
        return results
    
    def get_best_caption(self, image_path: str):
        """
        Get the best available caption from working models
        """
        # Try models in order of preference
        models = [
            "Salesforce/blip-image-captioning-large",
            "Salesforce/blip-image-captioning-base",
            "nlpconnect/vit-gpt2-image-captioning",
            "microsoft/git-base"
        ]
        
        for model in models:
            result = self.analyze_image_simple(image_path, model)
            if result["success"]:
                return result
        
        return {"success": False, "error": "No models worked"}


def main():
    """Test the analyzer"""
    
    # Initialize
    analyzer = SimpleSwimlaneAnalyzer()
    
    # Your image path
    image_path = "media/swim_lane.png"  # Change to your path
    
    print("🚀 HUGGINGFACE INFERENCE CLIENT TEST")
    print("="*60)
    
    # Option 1: Simple analysis
    print("\n📝 SIMPLE CAPTION TEST")
    result = analyzer.get_best_caption(image_path)
    
    if result.get("success"):
        print(f"\n✅ Best Caption Result:")
        print(f"Model: {result['model']}")
        print(f"Caption: {result['caption']}")
    else:
        print(f"\n❌ Error: {result['error']}")
    
    # Option 2: Full analysis
    print("\n" + "="*60)
    user_input = input("\nRun comprehensive analysis? (y/n): ")
    
    if user_input.lower() == 'y':
        results = analyzer.comprehensive_swimlane_analysis(image_path)
        
        # Prepare for vector DB
        print("\n💾 VECTOR DB PREPARATION:")
        print("-"*40)
        
        successful_results = [r for r in results.values() if r.get("success")]
        
        if successful_results:
            # Create chunks for vector DB
            chunks = []
            
            # Add captions
            for result in successful_results:
                if result["type"] == "simple_caption":
                    chunks.append({
                        "content": f"Swimlane diagram description: {result['caption']}",
                        "metadata": {"type": "caption", "model": result["model"]}
                    })
                elif result["type"] == "vqa":
                    chunks.append({
                        "content": f"Q: {result['question']} A: {result['answer']}",
                        "metadata": {"type": "vqa", "question": result["question"]}
                    })
            
            print(f"\n✅ Created {len(chunks)} chunks for vector DB:")
            for i, chunk in enumerate(chunks[:3]):  # Show first 3
                print(f"\nChunk {i+1}:")
                print(f"Content: {chunk['content'][:100]}...")
                print(f"Type: {chunk['metadata']['type']}")


if __name__ == "__main__":
    main()