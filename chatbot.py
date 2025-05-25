import os
import torch
import random
from dotenv import load_dotenv
from transformers import AutoModelForCausalLM, AutoTokenizer
from serpapi import GoogleSearch
from pymongo import MongoClient
import openai

# ✅ Predefined responses
responses = {
    "hi": ["Hello!", "Hey there!", "Hi! How can I assist?"],
    "hello": ["Hey! How's your day going?", "Hello there!"],
    "how are you": ["I'm just a bot, but I'm here to help!"],
    "bye": ["Goodbye!", "Take care!"]
}

# ✅ Load environment variables
load_dotenv(dotenv_path="config/.env")
SERP_API_KEY = os.getenv("SERP_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# ✅ MongoDB connection
client = MongoClient(MONGO_URI)
db = client["EVO_AI_DB"]
collection = db["chat_history"]

# ✅ Device selection
use_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ✅ Load GPT-Neo model
def load_model():
    model_name = "EleutherAI/gpt-neo-125M"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name).to(use_device)
    return tokenizer, model

tokenizer, model = load_model()

# ✅ Google Search
def search_google(query):
    params = {"q": query, "hl": "en", "gl": "us", "api_key": SERP_API_KEY}
    search = GoogleSearch(params)
    results = search.get_dict()
    if "organic_results" in results and results["organic_results"]:
        return results["organic_results"][0].get("snippet", "Couldn't find an answer.")
    return "Sorry, I couldn't find anything on Google."

# ✅ Factual detection
def needs_google_search(user_input):
    keywords = ["what is", "who is", "define", "explain", "how", "when", "where"]
    return any(word in user_input.lower() for word in keywords)

# ✅ GPT-Neo response
def generate_gpt_neo_response(user_input):
    try:
        input_ids = tokenizer.encode(user_input, return_tensors="pt").to(use_device)
        with torch.no_grad():
            output = model.generate(
                input_ids,
                max_length=60,
                do_sample=True,
                temperature=0.9,
                top_k=50,
                top_p=0.95
            )
        decoded = tokenizer.decode(output[0], skip_special_tokens=True)
        reply = decoded.replace(user_input, "").strip()
        return reply if reply else None
    except Exception as e:
        print(f"GPT-Neo error: {e}")
        return None

# ✅ OpenAI GPT fallback
def ask_openai(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print(f"OpenAI error: {e}")
        return "Sorry, I couldn't generate a response right now."

# ✅ MongoDB history save
def save_conversation(user_id, user_input, bot_response):
    collection.insert_one({"user_id": user_id, "user_input": user_input, "bot_response": bot_response})

def get_previous_messages(user_id):
    conversations = collection.find({"user_id": user_id}).sort("_id", -1).limit(5)
    unique_lines = []
    seen = set()
    for c in conversations:
        line = f"User: {c['user_input']}\nAI: {c['bot_response']}"
        if line not in seen:
            unique_lines.append(line)
            seen.add(line)
    return "\n".join(reversed(unique_lines))

# ✅ Main chat logic
def get_chat_response(user_input, user_id="default"):
    user_input = user_input.lower().strip()

    if needs_google_search(user_input):
        response = search_google(user_input)

    elif any(key in user_input for key in responses):
        for key in responses:
            if key in user_input:
                response = random.choice(responses[key])
                break

    else:
        # First try GPT-Neo
        response = generate_gpt_neo_response(user_input)
        if not response:
            print("GPT-Neo failed or empty, switching to OpenAI.")
            response = ask_openai(user_input)

    save_conversation(user_id, user_input, response)
    return response
