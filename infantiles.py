import streamlit as st
import requests
import json
from docx import Document
from io import BytesIO

# Set the page configuration
st.set_page_config(
    page_title="Children's Story Generator",
    layout="centered",
    initial_sidebar_state="auto",
)

# Title of the app
st.title("📚 Children's Story Generator")

# Description
st.markdown("""
Generate personalized children's stories in English tailored to different age groups. 
Specify the number of stories (up to 15), and let the app create engaging tales with varying themes and appropriate lengths.
""")

# Sidebar for user input
st.sidebar.header("Input Parameters")

# Number of stories input
num_stories = st.sidebar.number_input(
    "Number of Stories",
    min_value=1,
    max_value=15,
    value=1,
    step=1
)

# Age groups to choose from
age_groups = ["3-5 years", "6-8 years", "9-12 years"]
selected_age_group = st.sidebar.selectbox(
    "Select Age Group for the Stories",
    age_groups
)

# Button to generate stories
if st.sidebar.button("Generate Stories"):
    with st.spinner("Generating stories..."):
        # Function to generate a single story
        def generate_story(theme, age_group):
            api_url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}"
            }

            # Define the prompt based on age group
            if age_group == "3-5 years":
                prompt = f"Write a short and simple children's story suitable for {age_group}. The theme is {theme}. Keep the story engaging and easy to understand."
            elif age_group == "6-8 years":
                prompt = f"Write a children's story suitable for {age_group}. The theme is {theme}. Ensure the story has a clear plot and is appropriate for this age group."
            else:  # 9-12 years
                prompt = f"Write an engaging children's story suitable for {age_group}. The theme is {theme}. The story should have a more complex plot and appropriate vocabulary for this age group."

            data = {
                "model": "openai/gpt-4o-mini",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }

            try:
                response = requests.post(api_url, headers=headers, data=json.dumps(data))
                response.raise_for_status()
                result = response.json()
                story = result['choices'][0]['message']['content'].strip()
                return story
            except requests.exceptions.HTTPError as http_err:
                st.error(f"HTTP error occurred: {http_err}")
            except Exception as err:
                st.error(f"An error occurred: {err}")
            return "Sorry, an error occurred while generating the story."

        # Predefined list of themes
        themes = [
            "adventure in the forest",
            "a magical journey",
            "friendship and teamwork",
            "overcoming fears",
            "a day at the beach",
            "space exploration",
            "underwater mystery",
            "time travel",
            "a heroic quest",
            "learning to share",
            "the enchanted castle",
            "a detective story",
            "robot companions",
            "fantasy land",
            "animal kingdom"
        ]

        # Select themes for the number of stories
        import random
        selected_themes = random.sample(themes, num_stories) if num_stories <= len(themes) else random.choices(themes, k=num_stories)

        # Generate all stories
        stories = []
        for i in range(num_stories):
            theme = selected_themes[i]
            story = generate_story(theme, selected_age_group)
            stories.append({
                "title": f"Story {i+1}: {theme.title()}",
                "content": story
            })

        # Create a Word document
        doc = Document()
        doc.add_heading("Children's Stories", 0)

        for story in stories:
            doc.add_heading(story["title"], level=1)
            doc.add_paragraph(story["content"])

        # Save the document to a BytesIO stream
        doc_io = BytesIO()
        doc.save(doc_io)
        doc_io.seek(0)

        # Provide the download button
        st.success("Stories generated successfully!")
        st.download_button(
            label="📄 Download Stories as Word Document",
            data=doc_io,
            file_name="Children_Stories.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        # Optionally display the stories in the app
        with st.expander("View Generated Stories"):
            for story in stories:
                st.markdown(f"### {story['title']}")
                st.write(story['content'])

# Footer
st.markdown("---")
st.markdown("© 2024 Children's Story Generator. Powered by OpenRouter and Streamlit.")

