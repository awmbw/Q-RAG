"""
LLM Generator Module

Takes the selected documents and the original query, constructs a prompt,
and uses a local Small Language Model (SLM) to generate the final answer.
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

class LLMGenerator:
    """
    Wraps the HuggingFace Transformers library to generate answers.
    """
    
    def __init__(self, model_name="Qwen/Qwen2.5-1.5B-Instruct"):
        """
        Initializes the LLM and Tokenizer.
        """
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        
        # We will use CUDA if available, otherwise CPU
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def load_model(self):
        """
        Loads the model into GPU memory. 
        This takes a few seconds and requires ~3-4GB of VRAM.
        """
        print(f"Loading LLM ({self.model_name}) onto {self.device}...")
        
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        
        # Load in bfloat16 to save memory and speed up inference on RTX 5060
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.bfloat16,
            device_map=self.device
        )
        print("  ✅ LLM Loaded successfully.")

    def construct_prompt(self, question, selected_docs):
        """
        Builds the context-aware prompt for the LLM.
        """
        # Combine the text of all selected documents
        context = ""
        for idx, doc in enumerate(selected_docs):
            context += f"[Document {idx+1}: {doc['title']}]\n{doc['text']}\n\n"
            
        prompt = f"""You are an expert Question Answering system. 
Using ONLY the provided context documents, answer the user's question accurately and concisely.
If the answer is not contained in the context, say "I cannot answer based on the context."

CONTEXT:
{context}

QUESTION: {question}
ANSWER:"""
        
        return prompt

    def generate(self, question, selected_docs, max_new_tokens=50):
        """
        Generates the final answer.
        """
        if self.model is None:
            self.load_model()
            
        prompt = self.construct_prompt(question, selected_docs)
        
        # Convert text to tensor
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        # Generate!
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                pad_token_id=self.tokenizer.eos_token_id,
                do_sample=False  # Deterministic output
            )
            
        # The output includes the prompt, so we slice it off to get just the new text
        input_length = inputs.input_ids.shape[1]
        generated_tokens = outputs[0][input_length:]
        
        answer = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
        
        return answer.strip()
