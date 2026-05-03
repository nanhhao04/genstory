import yaml
from google import genai
import os
import asyncio
from huggingface_hub import AsyncInferenceClient
from dotenv import load_dotenv
from openai import AsyncOpenAI
import logging

load_dotenv()

curr_dir = os.path.dirname(__file__)
config_path = os.path.abspath(os.path.join(curr_dir, '../../config.yml'))

class UnifiedLLM:
    def __init__(self, model_name: str, gemini_keys: list, openai_key: str = None):
        self.model_name = model_name
        self.gemini_keys = [k for k in gemini_keys if k]
        self.openai_key = openai_key
        self.default_provider = os.getenv("DEFAULT_MODEL", "gemini").lower()
        
        self.openai_client = None
        if self.openai_key:
            self.openai_client = AsyncOpenAI(api_key=self.openai_key)
            
        self.current_gemini_key_idx = 0
        self.gemini_client = None
        self._configure_gemini()

    def _configure_gemini(self):
        if self.gemini_keys:
            key = self.gemini_keys[self.current_gemini_key_idx]
            # New SDK: client per key
            self.gemini_client = genai.Client(api_key=key)
            print(f"  [LLM] Gemini Client configured with key index {self.current_gemini_key_idx}")

    async def generate_content_async(self, prompt, **kwargs):
        """Unified interface for generating content with fallback logic."""
        providers_to_try = []
        if self.default_provider == "openai" and self.openai_client:
            providers_to_try.append("openai")
        providers_to_try.append("gemini")

        last_error = None
        
        for provider in providers_to_try:
            if provider == "openai":
                try:
                    print(f"  [LLM] 🚀 Attempting generation with OpenAI (Model: {os.getenv('OPENAI_MODEL', 'gpt-4o-mini')})...")
                    response = await self.openai_client.chat.completions.create(
                        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                        messages=[{"role": "user", "content": prompt}],
                        timeout=30,
                        **kwargs
                    )
                    print(f"  [LLM] ✅ OpenAI success.")
                    return type('obj', (object,), {'text': response.choices[0].message.content})
                except Exception as e:
                    print(f"  [LLM] ❌ OpenAI Failed: {e}. Falling back to Gemini...")
                    last_error = e
                    continue # Try Gemini
            
            if provider == "gemini":
                if not self.gemini_keys:
                    print("  [LLM] ⚠️ No Gemini keys available.")
                    continue

                # Try all available Gemini keys
                attempts = 0
                max_attempts = len(self.gemini_keys)
                
                while attempts < max_attempts:
                    try:
                        print(f"  [LLM] 🚀 Attempting Gemini (Key Index: {self.current_gemini_key_idx})...")
                        # New SDK async call
                        response = await self.gemini_client.aio.models.generate_content(
                            model=self.model_name,
                            contents=prompt
                        )
                        print(f"  [LLM] ✅ Gemini success (Key Index: {self.current_gemini_key_idx}).")
                        return response
                    except Exception as e:
                        attempts += 1
                        print(f"  [LLM] ❌ Gemini Failed (Key {self.current_gemini_key_idx}): {e}")
                        last_error = e
                        
                        # Rotate to next key
                        self.current_gemini_key_idx = (self.current_gemini_key_idx + 1) % len(self.gemini_keys)
                        self._configure_gemini()
                        
                        if attempts < max_attempts:
                            print(f"  [LLM] 🔄 Retrying with next Gemini key...")
                        else:
                            print(f"  [LLM] ⚠️ All Gemini keys exhausted.")
                
        print(f"  [LLM] 💀 ALL PROVIDERS FAILED.")
        raise last_error or RuntimeError("All LLM providers and keys failed.")

def connect_llm():
    cfg = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Could not read config.yml: {e}")

    # Primary Gemini Keys
    google_api_key = os.getenv("GOOGLE_API_KEY") or cfg.get('GOOGLE_API_KEY')
    google_api_key_1 = os.getenv("GOOGLE_API_KEY_1")
    google_api_key_2 = os.getenv("GOOGLE_API_KEY_2")
    
    gemini_keys = [google_api_key, google_api_key_1, google_api_key_2]
    
    # OpenAI Key
    openai_key = os.getenv("OPEN_API_KEY")
    
    # HF
    hf_token = os.getenv("HF_TOKEN") or cfg.get('HF_TOKEN')
    hf_model = os.getenv("HF_IMAGE_MODEL") or cfg.get('HF_IMAGE_MODEL', "black-forest-labs/FLUX.1-schnell")
    
    cfg['GOOGLE_API_KEY'] = google_api_key
    cfg['HF_TOKEN'] = hf_token
    cfg['HF_IMAGE_MODEL'] = hf_model

    model_name = os.getenv("GEMINI_MODEL") or "gemini-1.5-flash"
    
    llm = UnifiedLLM(model_name, gemini_keys, openai_key)
    hf_client = AsyncInferenceClient(token=hf_token)

    print(f"LLM initialized with fallback logic. Default provider: {llm.default_provider}")

    return llm, hf_client, cfg

llm, hf_client, cfg = connect_llm()