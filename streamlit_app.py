import streamlit as st
import os
from google import genai
from google.genai import types
import PIL.Image
import io

# Page config
st.set_page_config(
    page_title="🎨 Gemini AI Image Generator",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Mobile CSS
st.markdown("""
<style>
.main .block-container {
    padding: 1rem;
    max-width: 100%;
}
.stButton > button {
    width: 100%;
    height: 3rem;
    font-size: 1.1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
}
.stTextArea textarea {
    font-size: 16px !important;
}
@media (max-width: 768px) {
    .main .block-container {
        padding: 0.5rem;
    }
}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_client():
    api_key = st.secrets["GOOGLE_API_KEY"]
    return genai.Client(api_key=api_key)

MODEL_ID = "gemini-2.5-flash-image-preview"

def generate_image(prompt):
    try:
        client = get_client()
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                safety_settings=[
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                        threshold=types.HarmBlockThreshold.BLOCK_NONE,
                    )
                ],
                response_modalities=['Text', 'Image']
            )
        )
        
        for part in response.parts:
            if hasattr(part, 'as_image') and part.as_image():
                return part.as_image(), "Image generated successfully!"
        return None, "No image generated"
    except Exception as e:
        return None, f"Error: {str(e)}"

def edit_image(input_image, edit_prompt):
    try:
        client = get_client()
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[edit_prompt, input_image],
            config=types.GenerateContentConfig(
                safety_settings=[
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                        threshold=types.HarmBlockThreshold.BLOCK_NONE,
                    )
                ]
            )
        )
        
        for part in response.parts:
            if hasattr(part, 'as_image') and part.as_image():
                return part.as_image(), "Image edited successfully!"
        return None, "No edited image generated"
    except Exception as e:
        return None, f"Error: {str(e)}"

# Main app
st.title("🎨 Gemini AI Image Generator")
st.markdown("*Mobile-optimized AI image generation and editing*")

tab1, tab2 = st.tabs(["🎭 Generate", "✏️ Edit"])

with tab1:
    st.header("Generate New Images")
    
    prompt = st.text_area(
        "Describe your image:",
        "Create a photorealistic image of people travelling in Metro train",
        height=100
    )
    
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("🎨 Generate Image", type="primary"):
            if prompt.strip():
                image, message = generate_image(prompt)
                if image:
                    st.success(message)
                    st.image(image, use_column_width=True)
                    
                    buf = io.BytesIO()
                    image.save(buf, format='PNG')
                    st.download_button(
                        "📥 Download",
                        buf.getvalue(),
                        "generated.png",
                        "image/png"
                    )
                else:
                    st.error(message)
            else:
                st.warning("Please enter a prompt!")
    
    with col2:
        st.write("**Examples:**")
        examples = [
            "Mountain sunrise",
            "Cyberpunk street", 
            "Robot in library",
            "Magical forest"
        ]
        for ex in examples:
            if st.button(ex, key=f"gen_{ex}"):
                st.session_state.prompt = ex
                st.rerun()

with tab2:
    st.header("Edit Images")
    
    uploaded = st.file_uploader("Upload image:", type=['png', 'jpg', 'jpeg'])
    
    if uploaded:
        image = PIL.Image.open(uploaded)
        st.image(image, caption="Original", use_column_width=True)
        
        edit_prompt = st.text_area(
            "How to edit:",
            "Change all people to animals wearing suits like Zootopia",
            height=80
        )
        
        if st.button("✏️ Edit Image", type="primary"):
            if edit_prompt.strip():
                edited, message = edit_image(image, edit_prompt)
                if edited:
                    st.success(message)
                    col1, col2 = st.columns(2)
                    with col1:
                        st.image(image, caption="Before", use_column_width=True)
                    with col2:
                        st.image(edited, caption="After", use_column_width=True)
                    
                    buf = io.BytesIO()
                    edited.save(buf, format='PNG')
                    st.download_button(
                        "📥 Download Edited",
                        buf.getvalue(),
                        "edited.png",
                        "image/png"
                    )
                else:
                    st.error(message)
