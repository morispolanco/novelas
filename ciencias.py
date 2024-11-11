# app.py

import streamlit as st
import requests
import time
from docx import Document
from docx.shared import Inches
import base64
from io import BytesIO
import re

# Function to generate chapter content using OpenRouter API
def generate_chapter(topic):
    api_url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}"
    }
    prompt = (
        f"Write a chapter for a children's book about the scientific discipline '{topic}', suitable for kids aged 9 to 12. "
        f"The chapter should be both educational and engaging, presenting scientific concepts in an entertaining and informative manner. "
        f"It should aim to spark curiosity and interest in '{topic}' while being accessible and enjoyable for the target age group.\n\n"
        f"Blend storytelling with educational content, using creative and engaging language to explain scientific principles and concepts. "
        f"Incorporate interactive elements, such as experiments or activities, to make learning fun and hands-on for the young readers.\n\n"
        f"Ensure the chapter is age-appropriate, presenting scientific ideas in a way that is understandable and captivating for children aged 9 to 12. "
        f"Use storytelling, illustrations, and interactive elements to create an immersive and educational experience while maintaining a balance between instruction and entertainment.\n\n"
        f"Additionally, cover the following aspects:\n"
        f"1. Introduction to '{topic}': its definition and purpose.\n"
        f"2. Scope of '{topic}': what areas it covers.\n"
        f"3. Methods used in '{topic}': how scientists conduct research in this field.\n"
        f"4. Achievements in '{topic}': significant discoveries and advancements.\n"
        f"5. Current state of '{topic}': latest trends and developments.\n"
        f"6. Include numerous examples to illustrate concepts."
    )
    data = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    response = requests.post(api_url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        st.error(f"Error generating chapter: {response.text}")
        return None

# Function to generate an illustration using Together API
def generate_image(topic, chapter_number, img_num):
    api_url = "https://api.together.xyz/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {st.secrets['TOGETHER_API_KEY']}",
        "Content-Type": "application/json"
    }
    prompt = (
        f"Create an engaging and colorful illustration for a children's science book chapter about {topic}. "
        f"Illustration {img_num} for Chapter {chapter_number}. "
        f"The illustration should complement the storytelling and educational content, making it appealing and understandable for children aged 9 to 12."
    )
    data = {
        "model": "black-forest-labs/FLUX.1.1-pro",
        "prompt": prompt,
        "width": 1024,
        "height": 768,
        "steps": 50,  # Increased to improve image quality
        "n": 1,
        "response_format": "b64_json"
    }

    response = requests.post(api_url, headers=headers, json=data)
    if response.status_code == 200:
        image_b64 = response.json()['data'][0]['b64_json']
        image_bytes = base64.b64decode(image_b64)
        return image_bytes
    else:
        st.error(f"Error generating image: {response.text}")
        return None

# Function to process Markdown-formatted content and apply it to the Word document
def add_formatted_content(doc, content):
    lines = content.split('\n')
    for line in lines:
        # Level 1 Headings (equivalent to #)
        if line.startswith('# '):
            doc.add_heading(line[2:].strip(), level=1)
        # Level 2 Headings (equivalent to ##)
        elif line.startswith('## '):
            doc.add_heading(line[3:].strip(), level=2)
        # Level 3 Headings (equivalent to ###)
        elif line.startswith('### '):
            doc.add_heading(line[4:].strip(), level=3)
        else:
            # Process bold text **text**
            bold_pattern = re.compile(r'\*\*(.*?)\*\*')
            parts = bold_pattern.split(line)
            paragraph = doc.add_paragraph()
            for idx, part in enumerate(parts):
                if idx % 2 == 1:
                    # Bold text
                    run = paragraph.add_run(part)
                    run.bold = True
                else:
                    # Normal text
                    paragraph.add_run(part)

# Function to create the Word document
def create_word_document(book_title, chapters):
    doc = Document()
    doc.add_heading(book_title, 0)

    for idx, chapter in enumerate(chapters, 1):
        # Add chapter title as Heading 1
        chapter_title = f"Chapter {idx}: {chapter['topic'].capitalize()}"
        doc.add_heading(chapter_title, level=1)

        # Insert the first illustration after the title
        if len(chapter['images']) >= 1:
            doc.add_paragraph(f"Figure 1: Illustration for {chapter['topic']}")
            image_stream = BytesIO(chapter['images'][0])
            doc.add_picture(image_stream, width=Inches(6))

        # Add chapter content with formatting
        add_formatted_content(doc, chapter['content'])

    return doc

# Streamlit App Layout
st.title("Children's Science Book Generator")
st.write("Generate a personalized science book for children aged 9 to 12 with automatically generated chapters and illustrations.")

# User Inputs
book_title = st.text_input("Book Title", "Amazing Scientific Adventures")
num_chapters = st.number_input("Number of Chapters", min_value=1, max_value=20, value=5, step=1)

# Define the list of 20 topics
topics_list = [
    "Astronomy",
    "Biology",
    "Geology",
    "Botany",
    "Physics",
    "Chemistry",
    "Environmental Science",
    "Marine Biology",
    "Technology",
    "Space Exploration",
    "Meteorology",
    "Ecology",
    "Genetics",
    "Anatomy",
    "Paleontology",
    "Neuroscience",
    "Robotics",
    "Forensic Science",
    "Renewable Energy",
    "Biomedical Science"
]

# Allow user to select topics from the predefined list
selected_topics = st.multiselect(
    "Select Topics for Chapters (Each chapter will have a unique topic):",
    options=topics_list,
    default=topics_list[:num_chapters],
    help="Select up to 20 unique scientific topics for the chapters."
)

# Ensure the number of selected topics matches the number of chapters
if len(selected_topics) < num_chapters:
    st.warning("Not enough unique topics selected. Some topics will be reused.")
elif len(selected_topics) > num_chapters:
    selected_topics = selected_topics[:num_chapters]

# Button to start book generation
if st.button("Generate Book"):
    chapters = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i in range(num_chapters):
        # Select topic for the current chapter
        topic = selected_topics[i % len(selected_topics)]

        status_text.text(f"Generating Chapter {i+1} on {topic}...")
        # Generate chapter content
        content = generate_chapter(topic)
        if not content:
            st.error("Failed to generate chapter content. Stopping generation.")
            break

        # Generate illustration
        image = generate_image(topic, i+1, 1)  # Only one illustration per chapter
        if not image:
            st.error("Failed to generate illustration. Stopping generation.")
            break

        chapters.append({
            "topic": topic,
            "content": content,
            "images": [image]  # List containing one image
        })

        # Update progress bar
        progress = (i + 1) / num_chapters
        progress_bar.progress(progress)
        time.sleep(0.5)  # Simulate progress

    if len(chapters) == num_chapters:
        status_text.text("Generating Word document...")
        doc = create_word_document(book_title, chapters)

        # Save the document to a BytesIO stream
        doc_stream = BytesIO()
        doc.save(doc_stream)
        doc_bytes = doc_stream.getvalue()

        # Encode the document in base64 for download
        b64 = base64.b64encode(doc_bytes).decode()

        # Create download link
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="{book_title.replace(" ", "_")}.docx">📄 Download Book as Word Document</a>'
        st.markdown(href, unsafe_allow_html=True)
        st.success("Book generation completed successfully!")
    else:
        st.error("Not all chapters were generated successfully.")
