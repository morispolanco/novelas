import streamlit as st
import requests
from docx import Document
from io import BytesIO
import backoff
import re
from difflib import SequenceMatcher

# Define constants
MAX_RETRIES = 3  # Maximum number of retry attempts for API calls
MAX_STORIES = 30  # Maximum number of stories to prevent API overload
MIN_STORIES = 1   # Minimum number of stories

# Configure the Streamlit page
st.set_page_config(
    page_title="📝 Kids' Adventure Story Generator",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📝 Kids' Adventure Story Generator (Ages 9-12)")
st.write("""
    This application automatically generates adventure stories for children aged 9 to 12 in English. 
    You can specify the number of stories you want to generate and download them all in a Word document.
""")

# Initialize session state
if 'stories' not in st.session_state:
    st.session_state.stories = []
if 'process_completed' not in st.session_state:
    st.session_state.process_completed = False
if 'used_themes' not in st.session_state:
    st.session_state.used_themes = []

# Function to measure similarity between two texts
def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

# Customized prompt refined without illustrations and adapted for multiple chapters
PROMPT_BASE = """
Write an adventure story intended for {age_range} years old. The story should be exciting and age-appropriate, including elements such as challenges, brave characters, and imaginative settings. Ensure the content is entertaining, but also safe and suitable for children. Include an interesting conflict and a resolution that leaves a positive message.

# Requirements and Suggestions
- The story should be between 500 and 700 words, using accessible and understandable language for readers in this age group.
- Introduce lovable characters that readers can empathize with, such as curious children, magical animals, or fantastical beings.
- There should be at least one obstacle or challenge that the characters must overcome, with a positive message about teamwork, bravery, or creativity at the end.
- Use visual descriptions to create vibrant scenes, but avoid using overly complex terms or situations.

# Suggested Structure
1. **Introduction**: Present the protagonist and the initial setting where a calm situation is experienced before the adventure begins.
2. **Conflict**: An event that changes the protagonist's routine and leads them to an unexpected mission.
3. **Development**: Moments of action where the protagonist faces challenges and obstacles. There can be a companion who helps the protagonist.
4. **Resolution**: The conclusion of the adventure with a creative solution and a happy ending that offers reflection or a positive message.

# Tone and Style
- **Tone**: Adventurous, motivating, fun.
- **Narrative Style**: Third person or first person.

# Output Format
The output should include:
1. **CHAPTER {chapter_number}: {{Title}}**
2. **Summary:** A brief summary of the chapter.
3. **Theme:** The main theme of the chapter.
4. **Story Content:** The full story, between 500-700 words.

Each time a speaking character changes, use a line break for clarity.

# Unique Theme Instruction
Each story must have a unique theme that has not been used in previous stories. Refer to the list of used themes below and choose a new, distinct theme for this story. Avoid using similar phrases or titles such as "The Quest for...", "The Mystery of...", or "The Adventure of...".
"""

# Function to extract the title using regular expressions
def extract_title(response, chapter_number):
    pattern = fr'CHAPTER\s*{chapter_number}:\s*(.*)'
    match = re.search(pattern, response, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return f"Untitled Chapter {chapter_number}"

# Function to extract the summary of the story
def extract_summary(response):
    pattern = r'Summary:\s*(.*)'
    match = re.search(pattern, response, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "No summary available."

# Function to extract the main theme of the story
def extract_theme(response):
    pattern = r'Theme:\s*(.*)'
    match = re.search(pattern, response, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "No theme identified."

# Function to extract the content of the story
def extract_content(response):
    pattern = r'Story Content:\s*((?:.|\n)*)'
    match = re.search(pattern, response, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "No content available."

# Backoff decorator for retrying API calls on exceptions
@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=MAX_RETRIES)
def generate_story(age_range, chapter_number):
    """
    Generates a complete story including title, summary, theme, and content.

    Args:
        age_range (str): Selected age range.
        chapter_number (int): Chapter number.

    Returns:
        dict: Dictionary with 'title', 'summary', 'theme', 'content'.
    """
    # OpenAI API endpoint
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {st.secrets['OPENAI_API_KEY']}"
    }

    # Format the prompt with the age range and chapter number
    formatted_prompt = PROMPT_BASE.format(
        age_range=age_range,
        chapter_number=chapter_number
    )

    # Replace the unique theme instruction with used themes
    if st.session_state.used_themes:
        used_themes_formatted = "; ".join(st.session_state.used_themes)
        formatted_prompt = formatted_prompt.replace(
            "Refer to the list of used themes below and choose a new, distinct theme for this story.",
            f"Refer to the list of used themes below and choose a new, distinct theme for this story.\n\nUsed Themes: {used_themes_formatted}"
        )
    else:
        formatted_prompt = formatted_prompt.replace(
            "Refer to the list of used themes below and choose a new, distinct theme for this story.",
            "Refer to the list of used themes below and choose a new, distinct theme for this story.\n\nUsed Themes: None"
        )

    data = {
        "model": "openai/gpt-4o-mini",  # Specify the required model
        "messages": [
            {
                "role": "user",
                "content": formatted_prompt
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        response_json = response.json()
        
        # Debugging: Show the complete API response
        st.write(f"**API Response for CHAPTER {chapter_number}:**")
        st.json(response_json)
        
        if 'choices' in response_json and len(response_json['choices']) > 0:
            complete_content = response_json['choices'][0]['message']['content']
            st.write(f"**Generated Content for CHAPTER {chapter_number}:**")
            st.text(complete_content)
            
            title_generated = extract_title(complete_content, chapter_number)
            summary_generated = extract_summary(complete_content)
            theme_generated = extract_theme(complete_content)
            content_generated = extract_content(complete_content)
            
            return {
                "title": title_generated,
                "summary": summary_generated,
                "theme": theme_generated,
                "content": content_generated
            }
        else:
            st.error(f"**Error:** OpenAI API did not return expected choices for CHAPTER {chapter_number}.")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"**Error generating CHAPTER {chapter_number}:** {e}")
        return None

# Function to create a Word document with all generated stories
def create_document(work_title, stories):
    """
    Creates a Word document that includes all generated stories.

    Args:
        work_title (str): Title of the work.
        stories (list): List of dictionaries with 'title', 'summary', 'theme', 'content'.

    Returns:
        BytesIO: Buffer of the generated Word document.
    """
    doc = Document()
    doc.add_heading(work_title, 0)

    # Create Table of Contents
    doc.add_heading("Table of Contents", level=1)
    for idx, story in enumerate(stories, 1):
        toc_entry = f"CHAPTER {idx}: {story['title']}"
        toc_summary = f"Summary: {story['summary']}"
        doc.add_paragraph(toc_entry, style='List Number')
        doc.add_paragraph(toc_summary, style='List Bullet')
    
    doc.add_page_break()

    # Add each story
    for idx, story in enumerate(stories, 1):
        doc.add_heading(f"CHAPTER {idx}: {story['title']}", level=1)
        doc.add_paragraph(story['content'])
        doc.add_page_break()

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# User interface for generating stories
if not st.session_state.process_completed:
    st.sidebar.title("Options")
    age_ranges = ["9-12 years"]  # You can expand the age ranges if desired
    age_range = st.sidebar.selectbox("Select the age range for the stories:", age_ranges)
    
    # Input for the number of stories
    number_of_stories = st.sidebar.number_input(
        "How many stories would you like to generate?",
        min_value=MIN_STORIES,
        max_value=MAX_STORIES,
        value=5,
        step=1,
        help=f"Select a number between {MIN_STORIES} and {MAX_STORIES}."
    )

    if st.sidebar.button("Generate Stories"):
        st.session_state.process_completed = True
        st.session_state.stories = []
        st.session_state.used_themes = []

        with st.spinner(f"Generating {int(number_of_stories)} stories..."):
            for i in range(1, int(number_of_stories) + 1):
                st.write(f"**Generating CHAPTER {i}...**")
                story = generate_story(age_range, i)
                if story:
                    # Ensure the theme is unique
                    if story['theme'] not in st.session_state.used_themes:
                        st.session_state.stories.append(story)
                        st.session_state.used_themes.append(story['theme'])
                    else:
                        st.warning(f"CHAPTER {i}: Duplicate theme detected. Regenerating...")
                        # Optionally, implement logic to regenerate the story
                else:
                    st.error(f"Could not generate CHAPTER {i}.")

        if st.session_state.stories:
            st.success(f"Successfully generated {len(st.session_state.stories)} stories!")

else:
    if st.session_state.stories:
        work_title = st.text_input("Title of the Collection:", value="Adventure Tales Collection")
        if st.button("Download Stories as Word Document"):
            document = create_document(work_title, st.session_state.stories)
            st.download_button(
                label="Download as Word",
                data=document,
                file_name="Adventure_Tales_Collection.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        
        # Display all generated stories
        st.markdown("---")
        st.header("📖 Generated Adventure Tales Collection")
        
        for idx, story in enumerate(st.session_state.stories, 1):
            st.subheader(f"CHAPTER {idx}: {story['title']}")
            st.markdown(f"**Summary:** {story['summary']}")
            st.markdown(f"**Theme:** {story['theme']}")
            st.write(story['content'])
            st.markdown("---")
