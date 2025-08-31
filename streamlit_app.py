import streamlit as st
import os
from google import genai
from google.genai import types
import PIL.Image
import io
from datetime import datetime
import json

# Page config
st.set_page_config(
    page_title="🎨 AI Image Studio",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Enhanced Mobile CSS
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
    transition: all 0.3s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.stTextArea textarea {
    font-size: 16px !important;
    border-radius: 8px;
}

.feature-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem;
    border-radius: 10px;
    margin: 0.5rem 0;
    text-align: center;
}

.example-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 0.5rem;
    margin: 1rem 0;
}

.example-btn {
    padding: 0.5rem;
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 6px;
    font-size: 0.85rem;
    cursor: pointer;
    transition: all 0.2s ease;
}

.example-btn:hover {
    background: #e9ecef;
    transform: translateY(-1px);
}

.history-item {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 0.5rem;
    margin: 0.25rem 0;
    background: white;
}

@media (max-width: 768px) {
    .main .block-container {
        padding: 0.5rem;
    }
    .example-grid {
        grid-template-columns: 1fr 1fr;
    }
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'generation_history' not in st.session_state:
    st.session_state.generation_history = []
if 'edit_history' not in st.session_state:
    st.session_state.edit_history = []

@st.cache_resource
def get_client():
    api_key = st.secrets["GOOGLE_API_KEY"]
    return genai.Client(api_key=api_key)

MODEL_ID = "gemini-2.5-flash-image-preview"

# Style and content options
STYLE_PRESETS = {
    "Photorealistic": "ultra-realistic, high-definition, professional photography",
    "Digital Art": "digital painting, concept art, detailed illustration",
    "Cartoon Style": "cartoon, animated style, colorful and fun",
    "Oil Painting": "classical oil painting, artistic brushstrokes",
    "Sketch": "pencil sketch, hand-drawn, artistic lines",
    "Vintage": "vintage style, retro aesthetic, aged look",
    "Cyberpunk": "neon lights, futuristic, cyberpunk aesthetic",
    "Minimalist": "clean, simple, minimalist design"
}

ASPECT_RATIOS = {
    "Square (1:1)": "square format",
    "Portrait (3:4)": "portrait orientation, vertical",
    "Landscape (4:3)": "landscape orientation, horizontal",
    "Wide (16:9)": "wide format, cinematic"
}

CLOTHING_OPTIONS = {
    "Business Formal": "professional business suit, formal attire, corporate dress",
    "Casual Wear": "comfortable jeans and t-shirt, casual everyday clothing",
    "Elegant Evening": "sophisticated evening dress, formal party attire",
    "Traditional Indian": "beautiful traditional Indian clothing, saree or kurta",
    "Wedding Attire": "elegant wedding dress or formal wedding suit",
    "Sportswear": "athletic wear, gym clothes, sports uniform",
    "Winter Wear": "warm winter coat, cozy sweater, seasonal clothing",
    "Beach Wear": "summer beach outfit, light and breezy clothing",
    "Vintage Style": "retro vintage clothing from past decades",
    "Cultural Dress": "traditional cultural clothing from around the world"
}

POSE_OPTIONS = {
    "Confident Standing": "confident upright posture, hands on hips, strong stance",
    "Relaxed Casual": "relaxed natural pose, comfortable body language",
    "Professional Portrait": "professional headshot pose, business appropriate",
    "Dynamic Action": "energetic dynamic pose, movement and life",
    "Sitting Elegant": "graceful sitting position, elegant posture",
    "Walking Forward": "confident walking stride, forward motion",
    "Arms Crossed": "confident pose with arms crossed, assertive stance",
    "Waving Hello": "friendly waving gesture, welcoming pose",
    "Thinking Pose": "thoughtful pose, hand on chin, contemplative",
    "Victory Pose": "celebratory victory stance, arms raised"
}

FACIAL_EXPRESSIONS = {
    "Natural Smile": "genuine natural smile, warm and friendly",
    "Confident Look": "confident serious expression, professional demeanor",
    "Joyful Laugh": "happy laughing expression, pure joy",
    "Thoughtful": "contemplative thoughtful expression",
    "Surprised": "surprised expression, wide eyes",
    "Peaceful": "calm peaceful expression, serene look"
}

def enhance_prompt(base_prompt, style, aspect_ratio, quality_boost=True):
    """Enhance user prompt with style and technical improvements"""
    enhanced = base_prompt
    
    if style != "None":
        enhanced = f"{enhanced}, {STYLE_PRESETS[style]}"
    
    if aspect_ratio != "Default":
        enhanced = f"{enhanced}, {ASPECT_RATIOS[aspect_ratio]}"
    
    if quality_boost:
        enhanced = f"{enhanced}, high quality, detailed, professional"
    
    return enhanced

def generate_image(prompt, num_variants=1):
    """Generate image(s) from text prompt"""
    try:
        client = get_client()
        results = []
        
        for i in range(num_variants):
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
                    results.append(part.as_image())
                    break
        
        return results, "Images generated successfully!"
    except Exception as e:
        return [], f"Error: {str(e)}"

def advanced_edit_image(input_image, edit_type, options):
    """Advanced image editing with dress change and pose modification"""
    try:
        client = get_client()
        
        if edit_type == "outfit_change":
            prompt = f"Change the person's clothing to {options['clothing']}, keep the same person, face, and background. Make it look natural and well-fitted."
            
        elif edit_type == "pose_change":
            prompt = f"Change the person's body pose and position to {options['pose']} with {options['expression']} facial expression. Keep the same person, clothing, and background."
            
        elif edit_type == "complete_makeover":
            prompt = f"Transform this person: change clothing to {options['clothing']}, modify pose to {options['pose']}, expression to {options['expression']}. Keep the same face and background but make it look completely natural."
            
        elif edit_type == "style_transfer":
            prompt = f"Transform this image to {options['style']} style while keeping the same composition and subjects."
            
        else:  # custom edit
            prompt = options.get('custom_prompt', 'Enhance this image')
        
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[prompt, input_image],
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

def save_to_history(item_type, data):
    """Save generation or edit to history"""
    history_item = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'type': item_type,
        'data': data
    }
    
    if item_type == 'generation':
        st.session_state.generation_history.insert(0, history_item)
        if len(st.session_state.generation_history) > 10:  # Keep last 10
            st.session_state.generation_history.pop()
    else:
        st.session_state.edit_history.insert(0, history_item)
        if len(st.session_state.edit_history) > 10:
            st.session_state.edit_history.pop()

# Main app
def main():
    st.markdown("""
    <div class="feature-card">
        <h1>🎨 AI Image Studio</h1>
        <p>Generate, Edit & Transform Images with Advanced AI</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar for quick access
    with st.sidebar:
        st.title("🎯 Quick Access")
        if st.button("🔄 Clear All History"):
            st.session_state.generation_history = []
            st.session_state.edit_history = []
            st.success("History cleared!")
        
        st.markdown("---")
        st.markdown("**📊 Usage Today**")
        gen_count = len(st.session_state.generation_history)
        edit_count = len(st.session_state.edit_history)
        st.metric("Generations", gen_count)
        st.metric("Edits", edit_count)

    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🎭 Generate", "✏️ Edit & Transform", "📚 History", "💡 Templates"])

    with tab1:
        generation_tab()
    
    with tab2:
        editing_tab()
    
    with tab3:
        history_tab()
    
    with tab4:
        templates_tab()

def generation_tab():
    st.header("🎭 Advanced Image Generation")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Main prompt input
        prompt = st.text_area(
            "✨ Describe your image in detail:",
            "A professional businesswoman in modern office, confident pose, natural lighting",
            height=100,
            help="Be specific about people, clothing, poses, environment, lighting, and style"
        )
        
        # Advanced options
        st.markdown("**🎨 Style & Quality Options**")
        
        col1a, col1b = st.columns(2)
        with col1a:
            style = st.selectbox("Art Style:", ["None"] + list(STYLE_PRESETS.keys()))
            aspect_ratio = st.selectbox("Aspect Ratio:", ["Default"] + list(ASPECT_RATIOS.keys()))
        
        with col1b:
            num_variants = st.slider("Number of variations:", 1, 4, 2)
            quality_boost = st.checkbox("Quality boost", True)
        
        # Generate button
        if st.button("🎨 Generate Images", type="primary"):
            if prompt.strip():
                enhanced_prompt = enhance_prompt(prompt, style, aspect_ratio, quality_boost)
                
                with st.spinner(f"🎨 Creating {num_variants} image(s)..."):
                    images, message = generate_image(enhanced_prompt, num_variants)
                
                if images:
                    st.success(message)
                    
                    # Display images in grid
                    if len(images) == 1:
                        st.image(images[0], use_column_width=True)
                    else:
                        cols = st.columns(min(len(images), 2))
                        for i, img in enumerate(images):
                            with cols[i % 2]:
                                st.image(img, caption=f"Variation {i+1}")
                    
                    # Download options
                    for i, img in enumerate(images):
                        buf = io.BytesIO()
                        img.save(buf, format='PNG')
                        st.download_button(
                            f"📥 Download Image {i+1}",
                            buf.getvalue(),
                            f"generated_image_{i+1}.png",
                            "image/png",
                            key=f"download_gen_{i}"
                        )
                    
                    # Save to history
                    save_to_history('generation', {
                        'prompt': prompt,
                        'enhanced_prompt': enhanced_prompt,
                        'style': style,
                        'count': len(images)
                    })
                else:
                    st.error(message)
            else:
                st.warning("Please enter a description!")
    
    with col2:
        st.markdown("**🚀 Quick Examples**")
        
        example_prompts = [
            "Professional headshot in business attire",
            "Casual weekend outfit, relaxed pose",
            "Traditional wedding dress, elegant pose",
            "Athlete in sportswear, dynamic action",
            "Creative artist in studio, thoughtful pose",
            "Fashion model in evening wear",
            "Student in casual clothes, friendly smile",
            "Chef in kitchen uniform, confident stance"
        ]
        
        for example in example_prompts:
            if st.button(example[:25] + "...", key=f"gen_example_{example[:10]}", help=example):
                st.session_state.example_prompt = example
                st.rerun()
        
        # Handle example selection
        if 'example_prompt' in st.session_state:
            # This would update the prompt field (Streamlit limitation workaround)
            st.info(f"💡 Try this prompt: {st.session_state.example_prompt}")
            del st.session_state.example_prompt

def editing_tab():
    st.header("✏️ Advanced Photo Editing & Transformation")
    
    uploaded = st.file_uploader(
        "📤 Upload your photo to transform:",
        type=['png', 'jpg', 'jpeg'],
        help="Upload a clear photo with visible people for best results"
    )
    
    if uploaded:
        image = PIL.Image.open(uploaded)
        st.image(image, caption="📸 Original Photo", use_column_width=True)
        
        # Edit type selection
        st.markdown("**🎯 Choose Transformation Type:**")
        edit_type = st.radio(
            "What would you like to change?",
            ["👗 Change Outfit", "🕺 Change Pose", "🎭 Complete Makeover", "🎨 Style Transfer", "✨ Custom Edit"],
            horizontal=True
        )
        
        # Options based on edit type
        if edit_type == "👗 Change Outfit":
            st.markdown("**👗 Outfit Selection**")
            col1, col2 = st.columns(2)
            
            with col1:
                clothing = st.selectbox("New Outfit Style:", list(CLOTHING_OPTIONS.keys()))
                color_preference = st.text_input("Color preference (optional):", "")
            
            with col2:
                fit_style = st.selectbox("Fit Style:", ["Well-fitted", "Loose", "Tight", "Flowing"])
                occasion = st.selectbox("Occasion:", ["Casual", "Formal", "Party", "Work", "Traditional"])
            
            options = {
                'clothing': CLOTHING_OPTIONS[clothing],
                'color': color_preference,
                'fit': fit_style,
                'occasion': occasion
            }
            
        elif edit_type == "🕺 Change Pose":
            st.markdown("**🕺 Pose & Expression**")
            col1, col2 = st.columns(2)
            
            with col1:
                pose = st.selectbox("New Pose:", list(POSE_OPTIONS.keys()))
                expression = st.selectbox("Facial Expression:", list(FACIAL_EXPRESSIONS.keys()))
            
            with col2:
                energy_level = st.selectbox("Energy Level:", ["Calm", "Moderate", "High Energy"])
                hand_position = st.selectbox("Hand Position:", ["Natural", "On Hips", "Crossed", "Gesturing"])
            
            options = {
                'pose': POSE_OPTIONS[pose],
                'expression': FACIAL_EXPRESSIONS[expression],
                'energy': energy_level,
                'hands': hand_position
            }
            
        elif edit_type == "🎭 Complete Makeover":
            st.markdown("**🎭 Full Transformation**")
            col1, col2 = st.columns(2)
            
            with col1:
                clothing = st.selectbox("Outfit:", list(CLOTHING_OPTIONS.keys()), key="makeover_clothing")
                pose = st.selectbox("Pose:", list(POSE_OPTIONS.keys()), key="makeover_pose")
            
            with col2:
                expression = st.selectbox("Expression:", list(FACIAL_EXPRESSIONS.keys()), key="makeover_expression")
                style_vibe = st.selectbox("Overall Vibe:", ["Professional", "Casual", "Glamorous", "Artistic", "Traditional"])
            
            options = {
                'clothing': CLOTHING_OPTIONS[clothing],
                'pose': POSE_OPTIONS[pose],
                'expression': FACIAL_EXPRESSIONS[expression],
                'vibe': style_vibe
            }
            
        elif edit_type == "🎨 Style Transfer":
            st.markdown("**🎨 Artistic Style Transfer**")
            style = st.selectbox("Artistic Style:", list(STYLE_PRESETS.keys()))
            intensity = st.slider("Style Intensity:", 1, 10, 7)
            
            options = {
                'style': STYLE_PRESETS[style],
                'intensity': intensity
            }
            
        else:  # Custom Edit
            st.markdown("**✨ Custom Transformation**")
            custom_prompt = st.text_area(
                "Describe the changes you want:",
                "Change the background to a beautiful sunset, make the person look more confident",
                height=80
            )
            
            options = {'custom_prompt': custom_prompt}
        
        # Edit button
        if st.button("✨ Transform Image", type="primary"):
            edit_type_map = {
                "👗 Change Outfit": "outfit_change",
                "🕺 Change Pose": "pose_change", 
                "🎭 Complete Makeover": "complete_makeover",
                "🎨 Style Transfer": "style_transfer",
                "✨ Custom Edit": "custom_edit"
            }
            
            with st.spinner("✨ Transforming your image..."):
                edited_image, message = advanced_edit_image(image, edit_type_map[edit_type], options)
            
            if edited_image:
                st.success(message)
                
                # Before/After comparison
                col1, col2 = st.columns(2)
                with col1:
                    st.image(image, caption="📸 Before", use_column_width=True)
                with col2:
                    st.image(edited_image, caption="✨ After", use_column_width=True)
                
                # Download button
                buf = io.BytesIO()
                edited_image.save(buf, format='PNG')
                st.download_button(
                    "📥 Download Transformed Image",
                    buf.getvalue(),
                    f"transformed_{edit_type.replace(' ', '_').lower()}.png",
                    "image/png"
                )
                
                # Save to history
                save_to_history('edit', {
                    'edit_type': edit_type,
                    'options': options,
                    'success': True
                })
            else:
                st.error(message)

def history_tab():
    st.header("📚 Your Creation History")
    
    tab1, tab2 = st.tabs(["🎭 Generations", "✏️ Edits"])
    
    with tab1:
        if st.session_state.generation_history:
            for i, item in enumerate(st.session_state.generation_history):
                with st.expander(f"🎨 Generation {i+1} - {item['timestamp']}"):
                    st.write(f"**Prompt:** {item['data']['prompt']}")
                    st.write(f"**Style:** {item['data']['style']}")
                    st.write(f"**Images:** {item['data']['count']}")
                    if st.button(f"🔄 Regenerate", key=f"regen_{i}"):
                        st.info("Copy the prompt above to the Generate tab!")
        else:
            st.info("No generations yet. Create your first image in the Generate tab!")
    
    with tab2:
        if st.session_state.edit_history:
            for i, item in enumerate(st.session_state.edit_history):
                with st.expander(f"✏️ Edit {i+1} - {item['timestamp']}"):
                    st.write(f"**Type:** {item['data']['edit_type']}")
                    st.write(f"**Success:** {'✅' if item['data']['success'] else '❌'}")
                    st.json(item['data']['options'])
        else:
            st.info("No edits yet. Transform your first image in the Edit tab!")

def templates_tab():
    st.header("💡 Ready-to-Use Templates")
    
    st.markdown("**🚀 Quick Start Templates - Click to copy!**")
    
    templates = {
        "Professional Headshots": [
            "Professional businesswoman in navy blazer, confident smile, office background",
            "Executive man in dark suit, serious expression, corporate setting",
            "Young professional in casual blazer, friendly demeanor, modern office"
        ],
        "Social Media Ready": [
            "Influencer in trendy outfit, dynamic pose, urban background",
            "Content creator in colorful attire, engaging smile, bright lighting",
            "Lifestyle blogger in casual chic, relaxed pose, aesthetic background"
        ],
        "Traditional Wear": [
            "Elegant woman in red saree, graceful pose, traditional jewelry",
            "Man in white kurta, dignified stance, cultural background",
            "Bride in ornate lehenga, joyful expression, wedding setting"
        ],
        "Fitness & Sports": [
            "Athlete in workout gear, strong pose, gym environment",
            "Yoga instructor in activewear, peaceful expression, nature background",
            "Runner in sports attire, dynamic movement, outdoor track"
        ]
    }
    
    for category, prompts in templates.items():
        st.subheader(f"📁 {category}")
        for prompt in prompts:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"💡 {prompt}")
            with col2:
                if st.button("📋", key=f"copy_{prompt[:20]}", help="Copy to Generate tab"):
                    st.session_state.template_prompt = prompt
                    st.success("Copied! Go to Generate tab")

if __name__ == "__main__":
    main()
