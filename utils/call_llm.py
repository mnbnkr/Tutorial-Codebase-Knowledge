from google import genai
import os
import logging
import json
from datetime import datetime

# Configure logging
log_directory = os.getenv("LOG_DIR", "logs")
os.makedirs(log_directory, exist_ok=True)
log_file = os.path.join(log_directory, f"llm_calls_{datetime.now().strftime('%Y%m%d')}.log")

# Set up logger
logger = logging.getLogger("llm_logger")
logger.setLevel(logging.INFO)
logger.propagate = False  # Prevent propagation to root logger

file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Simple cache configuration
cache_file = "llm_cache.json"

# # By default, we Google Gemini 2.5 pro, as it shows great performance for code understanding
def call_llm(prompt: str, use_cache: bool = True) -> str:
    # Log the prompt
    # Wrap logging in try-except to prevent logging errors from crashing the main process
    try:
        logger.info(f"PROMPT: {prompt}")
    except Exception as log_err:
        print(f"Warning: Failed to log prompt - {log_err}") # Print warning instead of crashing

    # Check cache if enabled
    if use_cache:
        # Load cache from disk
        cache = {}
        if os.path.exists(cache_file):
            try:
                # --- Specify UTF-8 encoding for reading cache ---
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
            except Exception as cache_load_err: # Catch broader exceptions during load
                logger.warning(f"Failed to load cache: {cache_load_err}, starting with empty cache")
                cache = {} # Ensure cache is an empty dict on failure

        # Return from cache if exists
        if prompt in cache:
            response_text = cache[prompt]
            # Wrap logging in try-except
            try:
                logger.info(f"RESPONSE (cached): {response_text}")
            except Exception as log_err:
                print(f"Warning: Failed to log cached response - {log_err}")
            return response_text

    # Call the LLM if not in cache or cache disabled
    try:
        client = genai.Client(
        #     vertexai=True,
        #     # TODO: change to your own project id and location
        #     project=os.getenv("GEMINI_PROJECT_ID", "your-project-id"),
        #     location=os.getenv("GEMINI_LOCATION", "europe-north1")

        # You can comment the previous lines and use the AI Studio key instead:

            api_key=os.getenv("GEMINI_API_KEY", "your-api-key"),
        )

        model = os.getenv("GEMINI_MODEL", "models/gemini-2.5-pro-preview-03-25")
        response = client.models.generate_content(
            model=model,
            contents=[prompt]
        )
        response_text = response.text if response.text is not None else ""

    except Exception as llm_err:
        logger.error(f"Error calling LLM API: {llm_err}")
        # Consider how to handle LLM errors, maybe raise an exception or return an error string
        # For now, returning an error string to avoid crashing the flow
        return f"Error calling LLM: {llm_err}"

    # Log the response
    # Wrap logging in try-except
    try:
        logger.info(f"RESPONSE (API): {response_text}")
    except Exception as log_err:
        print(f"Warning: Failed to log API response - {log_err}")

    # Update cache if enabled
    if use_cache:
        # Load cache again to avoid overwrites from concurrent runs (less likely here but good practice)
        cache = {}
        if os.path.exists(cache_file):
            try:
                # --- FIX: Specify UTF-8 encoding for reading cache ---
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
            except Exception as cache_reload_err:
                logger.warning(f"Failed to reload cache before saving: {cache_reload_err}")
                # Decide if you want to proceed with overwriting or skip saving
                # For simplicity, we'll proceed, potentially overwriting if reload failed

        # Add to cache and save
        cache[prompt] = response_text
        try:
            # --- Specify UTF-8 encoding for writing cache ---
            with open(cache_file, 'w', encoding='utf-8') as f:
                # Use ensure_ascii=False to allow non-ASCII chars directly in JSON
                json.dump(cache, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    return response_text

# # Use Anthropic Claude 3.7 Sonnet Extended Thinking
# def call_llm(prompt, use_cache: bool = True):
#     from anthropic import Anthropic
#     client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", "your-api-key"))
#     response = client.messages.create(
#         model="claude-3-7-sonnet-20250219",
#         max_tokens=21000,
#         thinking={
#             "type": "enabled",
#             "budget_tokens": 20000
#         },
#         messages=[
#             {"role": "user", "content": prompt}
#         ]
#     )
#     return response.content[1].text

# # Use OpenAI o4-mini
# def call_llm(prompt, use_cache: bool = True):
#     # Log the prompt (Optional: keep logging if desired)
#     logger.info(f"PROMPT: {prompt}")

#     # Check cache if enabled (Optional: keep caching if desired)
#     if use_cache:
#         # Load cache from disk
#         cache = {}
#         if os.path.exists(cache_file):
#             try:
#                 with open(cache_file, 'r') as f:
#                     cache = json.load(f)
#             except Exception as e:
#                 logger.warning(f"Failed to load cache: {e}, starting with empty cache")

#         # Return from cache if exists
#         if prompt in cache:
#             logger.info(f"Using cached RESPONSE: {cache[prompt]}")
#             return cache[prompt]

#     # Call the LLM if not in cache or cache disabled
#     from openai import OpenAI
#     client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "your-api-key"))
#     try:
#         r = client.chat.completions.create(
#             model="o4-mini",
#             messages=[{"role": "user", "content": prompt}],
#             response_format={
#                 "type": "text"
#             },
#             reasoning_effort="medium",
#             store=False
#         )
#         response_text = r.choices[0].message.content if r.choices and r.choices[0].message else ""

#         # Log the response (Optional: keep logging if desired)
#         logger.info(f"RESPONSE: {response_text}")

#         # Update cache if enabled (Optional: keep caching if desired)
#         if use_cache:
#             # Load cache again to avoid overwrites
#             cache = {}
#             if os.path.exists(cache_file):
#                 try:
#                     with open(cache_file, 'r') as f:
#                         cache = json.load(f)
#                 except Exception as e:
#                     logger.warning(f"Failed to reload cache before saving: {e}")

#             # Add to cache and save
#             cache[prompt] = response_text
#             try:
#                 with open(cache_file, 'w') as f:
#                     json.dump(cache, f, indent=4) # Added indent for readability
#             except Exception as e:
#                 logger.error(f"Failed to save cache: {e}")

#         return response_text

#     except Exception as e:
#         logger.error(f"Error calling OpenAI API: {e}")
#         return f"Error: {e}" # Return error message

if __name__ == "__main__":
    test_prompt = "Hello, how are you? 你好吗？😊" # For non-ASCII testing

    # First call - should hit the API (unless cached from previous runs)
    print("Making call...")
    # Using cache=False for demonstration to ensure API call if not cached
    response1 = call_llm(test_prompt, use_cache=True)
    print(f"Response 1: {response1}")

    # Second call - should hit the cache if use_cache=True was used above and successful
    print("\nMaking second call (should use cache if enabled)...")
    response2 = call_llm(test_prompt, use_cache=True)
    print(f"Response 2: {response2}")

    print(f"\nCheck log file: {log_file}")
    print(f"Check cache file: {cache_file}")
