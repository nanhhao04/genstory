import yaml
import google.generativeai as genai
import os
from huggingface_hub import AsyncInferenceClient
from dotenv import load_dotenv

load_dotenv()

curr_dir = os.path.dirname(__file__)
config_path = os.path.abspath(os.path.join(curr_dir, '../../config.yml'))

def connect_llm():
    cfg = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Could not read config.yml: {e}")

    # Override/fill from environment
    google_api_key = os.getenv("GOOGLE_API_KEY") or cfg.get('GOOGLE_API_KEY')
    hf_token = os.getenv("HF_TOKEN") or cfg.get('HF_TOKEN')
    hf_model = os.getenv("HF_IMAGE_MODEL") or cfg.get('HF_IMAGE_MODEL', "black-forest-labs/FLUX.1-schnell")
    
    # Merge back into cfg for export
    cfg['GOOGLE_API_KEY'] = google_api_key
    cfg['HF_TOKEN'] = hf_token
    cfg['HF_IMAGE_MODEL'] = hf_model

    if not google_api_key:
        print("Warning: GOOGLE_API_KEY not found in environment or config.yml")

    if google_api_key:
        genai.configure(api_key=google_api_key)
    else:
        print("  [Config] CẢNH BÁO: GOOGLE_API_KEY trống!")

    model_name = os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
    llm = genai.GenerativeModel(model_name)
    hf_client = AsyncInferenceClient(token=hf_token)

    print(f"LLM (model: {model_name}) + HF Client (Async) initialized")

    return llm, hf_client, cfg

llm, hf_client, cfg = connect_llm()