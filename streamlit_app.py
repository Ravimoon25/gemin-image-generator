
import streamlit as st
import os
from google import genai
from google.genai import types
import PIL.Image
import io

st.set_page_config(page_title="🎨 AI Image Generator", page_icon="🎨")

@st.cache_resource
def get_client():
    api_key = st.secrets["GOOGLE_API_KEY"]
    return genai.Client(api_key=api_key)

st.title("🎨 Gemini AI Image Generator")

prompt = st.text_area("Describe your image:", "A beautiful sunset over mountains")

if st.button("Generate Image"):
    if prompt:
        try:
            with st.spinner("Creating image..."):
                client = get_client()
                response = client.models.generate_content(
                    model="gemini-2.5-flash-image-preview",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_modalities=['Text', 'Image']
                    )
                )
                
                for part in response.parts:
                    if hasattr(part, 'as_image') and part.as_image():
                        st.image(part.as_image())
                        st.success("Image generated!")
                        break
        except Exception as e:
            st.error(f"Error: {str(e)}")
