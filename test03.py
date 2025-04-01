import streamlit as st
import requests
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from googleapiclient.discovery import build #pip install google-api-python-client
import os

st.set_page_config(page_title="Link and Text Checker", layout="centered")

@st.cache_resource
def load_model_and_tokenizer():
    model_name = "gpt2"
    try:
        model = GPT2LMHeadModel.from_pretrained(model_name)
        tokenizer = GPT2Tokenizer.from_pretrained(model_name)
        return model, tokenizer
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None, None

def check_link(url):
    # Check if the link is reachable
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return False, "The link is not reachable."
    except requests.exceptions.RequestException:
        return False, "The link is not reachable."

    # Check if the link is flagged as malicious using Google Safe Browsing API
    api_key = os.getenv("GOOGLE_API_KEY")  # Read API key from environment variable
    if not api_key:
        return False, "API key is not set in the environment variables."
    service = build("safebrowsing", "v4", developerKey=api_key)
    body = {
        "client": {
            "clientId": "yourcompanyname",
            "clientVersion": "1.5.2"
        },
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [
                {"url": url}
            ]
        }
    }
    response = service.threatMatches().find(body=body).execute()
    if "matches" in response:
        return False, "The link is flagged as malicious."
    return True, "The link is genuine."

def calculate_perplexity(text, model, tokenizer):
    encodings = tokenizer(text, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**encodings, labels=encodings["input_ids"])
    loss = outputs.loss
    perplexity = torch.exp(loss).item()
    return perplexity

if __name__ == "__main__":
    st.title("Authentication Checker")

    option = st.selectbox("Choose an option", ("Check Link Genuineness", "Check Text Review"))

    if option == "Check Link Genuineness":
        url = st.text_input("Enter the URL to check:")
        if st.button("Check"):
            is_genuine, message = check_link(url)
            if is_genuine:
                st.success(message)
            else:
                st.error(message)

    elif option == "Check Text Review":
        text = st.text_area("Enter Review to check its Genuineness:")
        if st.button("Analyze"):
            if text:
                model, tokenizer = load_model_and_tokenizer()
                if model and tokenizer:
                    perplexity = calculate_perplexity(text, model, tokenizer)
                    if perplexity > 50:
                        st.balloons()
                        st.success("🎉 The text appears to be human-written! 🎉")
                        st.write("Perplexity Score:", perplexity)
                        #st.image("https://media.giphy.com/media/3o7aD2saalBwwftBIY/giphy.gif", width=300)
                    else:
                        st.warning("🤖 The text appears to be AI-generated. 🤖")
                        st.write("Perplexity Score:", perplexity)
                        #st.image("https://media.giphy.com/media/3o6Zt481isNVuQI1l6/giphy.gif", width=300)
                else:
                    st.error("Failed to load model and tokenizer.")