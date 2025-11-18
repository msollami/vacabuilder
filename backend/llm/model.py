from llama_cpp import Llama
import os
from typing import Optional

class LocalLLM:
    """Wrapper for llama.cpp model"""

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or os.getenv(
            "LLM_MODEL_PATH",
            "models/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
        )
        self.llm: Optional[Llama] = None
        self._load_model()

    def _load_model(self):
        """Load the GGUF model"""
        if not os.path.exists(self.model_path):
            print(f"Warning: Model not found at {self.model_path}")
            print("Please download a GGUF model and place it in the models/ directory")
            print("Recommended: Mistral-7B-Instruct or Llama-2-7B")
            print("Download from: https://huggingface.co/TheBloke")
            return

        try:
            print(f"Loading model from {self.model_path}...")
            self.llm = Llama(
                model_path=self.model_path,
                n_ctx=4096,  # Context window
                n_threads=4,  # CPU threads
                n_gpu_layers=0,  # Set to -1 for GPU acceleration if available
                verbose=False
            )
            print("Model loaded successfully!")
        except Exception as e:
            print(f"Error loading model: {e}")
            self.llm = None

    def is_ready(self) -> bool:
        """Check if model is loaded and ready"""
        return self.llm is not None

    def generate(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7) -> str:
        """Generate text from prompt"""
        if not self.is_ready():
            return "Error: LLM model not loaded. Please check model path."

        try:
            response = self.llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.95,
                repeat_penalty=1.1,
                stop=["</s>", "###"],
                echo=False
            )
            return response["choices"][0]["text"].strip()
        except Exception as e:
            return f"Error generating response: {e}"

    def create_prompt(self, system: str, user: str) -> str:
        """Create a formatted prompt for instruction-following models"""
        return f"""<s>[INST] <<SYS>>
{system}
<</SYS>>

{user} [/INST]"""
