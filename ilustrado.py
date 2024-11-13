import streamlit as st
import requests
import base64
import json
import re

# Get the API key from Streamlit secrets
TOGETHER_API_KEY = st.secrets["TOGETHER_API_KEY"]

# Set up headers for API requests
headers = {
    "Authorization": f"Bearer {TOGETHER_API_KEY}",
    "Content-Type": "application/json"
}

st.title("Fables and Stories Illustrated")

# Input: Text of the fable or story
story_text = st.text_area("Paste your fable or story here:", height=300)

if st.button("Generate Illustration"):
    if story_text.strip() == "":
        st.warning("Please enter the text of a fable or story.")
    else:
        with st.spinner("Processing..."):
            # Use Together's chat completion API to extract the most significant key moment
            messages = [
                {
                    "role": "system",
                    "content": "You are an assistant that extracts the most significant key moment from stories."
                },
                {
                    "role": "user",
                    "content": (
                        "Please extract the most significant key moment from the following story. "
                        "Provide a concise description of this moment in a JSON array containing a single string. "
                        "Provide only the JSON array and no additional text.\n\n"
                        f"{story_text}"
                    )
                }
            ]

            data = {
                "model": "Qwen/Qwen2.5-7B-Instruct-Turbo",
                "messages": messages,
                "max_tokens": 512,
                "temperature": 0.7,
                "top_p": 0.7,
                "top_k": 50,
                "repetition_penalty": 1,
                "stop": ["<|eot_id|>"],
                "stream": False
            }

            response = requests.post(
                "https://api.together.xyz/v1/chat/completions",
                headers=headers,
                json=data
            )

            if response.status_code == 200:
                response_data = response.json()
                # Debugging output
                st.write("Assistant's raw response:", response_data)

                # Extract the assistant's message content
                try:
                    assistant_message = response_data['choices'][0]['text']
                except KeyError:
                    try:
                        assistant_message = response_data['choices'][0]['message']['content']
                    except KeyError:
                        st.error("Could not find the assistant's response in the API response.")
                        st.stop()

                # Debugging output
                st.write("Assistant's response text:", assistant_message)

                # Try to parse the assistant's response as JSON
                try:
                    key_moments = json.loads(assistant_message)
                except json.JSONDecodeError:
                    # Try to extract JSON array from the text using regex
                    match = re.search(r'\[.*\]', assistant_message, re.DOTALL)
                    if match:
                        json_array_str = match.group(0)
                        try:
                            key_moments = json.loads(json_array_str)
                        except json.JSONDecodeError:
                            st.error("Failed to parse key moment from assistant's response.")
                            st.stop()
                    else:
                        st.error("Failed to find JSON array in assistant's response.")
                        st.stop()
            else:
                st.error(f"Error {response.status_code}: {response.text}")
                st.stop()

            # Generate image for the key moment
            if key_moments:
                moment = key_moments[0]
                # Prepare the prompt for image generation
                prompt = f"{moment}, pencil drawing in black and white"

                # Prepare the data for the image generation request
                image_data = {
                    "model": "black-forest-labs/FLUX.1.1-pro",
                    "prompt": prompt,
                    "width": 512,
                    "height": 512,
                    "steps": 1,
                    "n": 1,
                    "response_format": "b64_json"
                }

                image_response = requests.post(
                    "https://api.together.xyz/v1/images/generations",
                    headers=headers,
                    json=image_data
                )

                if image_response.status_code == 200:
                    image_response_data = image_response.json()
                    b64_image = image_response_data['data'][0]['b64_json']
                    image_bytes = base64.b64decode(b64_image)
                    # Display the image and moment
                    st.subheader("Key Moment")
                    st.write(moment)
                    st.image(image_bytes, caption=moment)
                else:
                    st.error(f"Error {image_response.status_code} generating image: {image_response.text}")
                    st.stop()
            else:
                st.error("No key moment was extracted.")
