"""
LLM Processor - Ollama Llama-2 7B Integration
Conexion directa a Ollama local en puerto 11434
"""

import requests
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)


class OllamaLLMProcessor:
    """Interfaz con Ollama Llama-2 7B local"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama2:7b",
        temperature: float = 0.3,
        timeout: int = 60
    ):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self._verify_connection()
    
    def _verify_connection(self):
        """Verify Ollama is running and model is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            
            models = [m['name'] for m in response.json().get('models', [])]
            
            if self.model not in models and f"{self.model}:latest" not in models:
                logger.warning(f"Model {self.model} not found. Available: {models}")
                raise ValueError(f"Model {self.model} not found in Ollama")
            
            logger.info(f"Ollama connected. Model: {self.model}")
            
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Make sure it's running: ollama serve"
            )
        except Exception as e:
            logger.error(f"Ollama verification failed: {e}")
            raise
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 512,
        stream: bool = False
    ) -> str:
        """Generate text using Ollama"""
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        try:
            start_time = time.time()
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "temperature": self.temperature,
                    "top_p": 0.9,
                    "num_predict": max_tokens
                },
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            generated_text = result.get("response", "").strip()
            
            elapsed_time = time.time() - start_time
            logger.info(f"Generated response in {elapsed_time:.2f}s")
            
            return generated_text
            
        except requests.exceptions.Timeout:
            logger.error(f"Ollama request timed out after {self.timeout}s")
            raise
        except requests.exceptions.ConnectionError:
            logger.error("Connection to Ollama failed")
            raise
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise
    
    def test(self):
        """Test LLM with simple prompt in Spanish"""
        test_prompt = "Que es la diabetes mellitus? Responde en maximo 50 palabras."
        
        logger.info("Testing Ollama with Spanish prompt...")
        try:
            response = self.generate(test_prompt, max_tokens=100)
            logger.info(f"Test response: {response[:100]}...")
            return True
        except Exception as e:
            logger.error(f"Test failed: {e}")
            return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    llm = OllamaLLMProcessor()
    llm.test()
