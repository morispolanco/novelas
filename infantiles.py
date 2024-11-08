import os
import json
import requests
from dotenv import load_dotenv
import nltk
from nltk.corpus import wordnet
from wordcloud import WordCloud
import streamlit as st
from openai.api import Completion

# Load API key from environment variable
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Set up OpenRouter API client
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
}

model = "openai/gpt-4o-mini"

def generate_story(prompt, max_tokens=150):
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
    }
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

def generate_stories(num_stories, age_range):
    stories = []
    for _ in range(num_stories):
        theme = get_theme_for_age(age_range)
        prompt = f"Generate a children's story about {theme} suitable for {age_range} year olds."
        story = generate_story(prompt)
        stories.append(story)
    return stories

def get_theme_for_age(age_range):
    themes = {
        "2-4": ["animals", "colors", "numbers", "shapes"],
        "5-7": ["family", "friends", "adventure", "magic"],
        "8-10": ["mythical creatures", "discovery", "bravery", "friendship"],
        "11+": ["time travel", "space exploration", "inventions", "mystery"],
    }
    return random.choice(themes[age_range])

def save_stories_as_docx(stories, filename="children_stories.docx"):
    # This functionality requires additional libraries such as python-docx.
    # For the sake of simplicity, I won't include it here, but you can find it in the python-docx documentation:
    # https://python-docx.readthedocs.io/en/latest/user/documents.html
    pass

def main():
    st.set_page_config(page_title="Children's Stories Generator")
    st.header("Children's Stories Generator")

    age_range = st.selectbox(
        "Select age range",
        [
            "2-4",
            "5-7",
            "8-10",
            "11+",
        ],
    )
    num_stories = st.slider("Number of stories", min_value=1, max_value=15, value=3)

    if st.button("Generate Stories"):
        stories = generate_stories(num_stories, age_range)
        for i, story in enumerate(stories, start=1):
            st.markdown(f"### Story {i}\n\n{story}")

        # Save stories as DOCX
        st.download_button(
            label="Download as DOCX",
            data=None,  # Fill this with the data to be saved as DOCX
            file_name="children_stories.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

if __name__ == "__main__":
    main()
