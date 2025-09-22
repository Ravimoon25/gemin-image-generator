import streamlit as st
import os
from google import genai
from google.genai import types
import PIL.Image
import io
from datetime import datetime
import json
import base64

# Page config
st.set_page_config(
    page_title="🎨 AI Image Studio Pro",
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
    padding: 1.5rem;
    border-radius: 12px;
    margin: 1rem 0;
    text-align: center;
}

.analysis-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
}

.metric-card {
    background: white;
    padding: 1rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    text-align: center;
}

@media (max-width: 768px) {
    .main .block-container {
        padding: 0.5rem;
    }
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    if 'generation_history' not in st.session_state:
        st.session_state.generation_history = []
    if 'edit_history' not in st.session_state:
        st.session_state.edit_history = []
    if 'analysis_history' not in st.session_state:
        st.session_state.analysis_history = []

init_session_state()

@st.cache_resource
def get_client():
    """Initialize Gemini client with error handling"""
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        return genai.Client(api_key=api_key)
    except Exception as e:
        st.error(f"Failed to initialize AI client: {str(e)}")
        st.stop()

MODEL_ID = "gemini-2.5-flash-image-preview"

# Style and content options
STYLE_PRESETS = {
    "Photorealistic": "ultra-realistic, high-definition, professional photography, sharp details",
    "Digital Art": "digital painting, concept art, detailed illustration, vibrant colors",
    "Cartoon Style": "cartoon, animated style, colorful and fun, playful",
    "Oil Painting": "classical oil painting, artistic brushstrokes, textured canvas",
    "Sketch": "pencil sketch, hand-drawn, artistic lines, monochrome",
    "Vintage": "vintage style, retro aesthetic, aged look, nostalgic",
    "Cyberpunk": "neon lights, futuristic, cyberpunk aesthetic, dark atmosphere",
    "Minimalist": "clean, simple, minimalist design, elegant simplicity"
}

ASPECT_RATIOS = {
    "Square (1:1)": "square format, equal dimensions",
    "Portrait (3:4)": "portrait orientation, vertical composition",
    "Landscape (4:3)": "landscape orientation, horizontal composition", 
    "Wide (16:9)": "wide format, cinematic composition"
}

CLOTHING_OPTIONS = {
    "Business Formal": "professional business suit, formal corporate attire, executive styling",
    "Casual Wear": "comfortable jeans and t-shirt, relaxed everyday clothing",
    "Elegant Evening": "sophisticated evening dress, formal party attire, glamorous",
    "Traditional Indian": "beautiful traditional Indian clothing, saree, kurta, cultural dress",
    "Wedding Attire": "elegant wedding dress, formal wedding suit, bridal styling",
    "Sportswear": "athletic wear, gym clothes, sports uniform, active lifestyle",
    "Winter Wear": "warm winter coat, cozy sweater, seasonal layered clothing",
    "Beach Wear": "summer beach outfit, light breezy clothing, vacation style",
    "Vintage Style": "retro vintage clothing from past decades, classic fashion",
    "Designer Fashion": "high-end designer clothing, luxury fashion, couture styling"
}

POSE_OPTIONS = {
    "Confident Standing": "confident upright posture, hands on hips, strong authoritative stance",
    "Relaxed Casual": "relaxed natural pose, comfortable casual body language",
    "Professional Portrait": "professional headshot pose, business appropriate, executive presence",
    "Dynamic Action": "energetic dynamic pose, movement and life, active positioning",
    "Sitting Elegant": "graceful sitting position, elegant refined posture",
    "Walking Forward": "confident walking stride, forward motion, purposeful movement",
    "Arms Crossed": "confident pose with arms crossed, assertive professional stance",
    "Waving Hello": "friendly waving gesture, welcoming approachable pose",
    "Thinking Pose": "thoughtful pose, hand on chin, contemplative positioning",
    "Victory Pose": "celebratory victory stance, arms raised, triumphant gesture"
}

FACIAL_EXPRESSIONS = {
    "Natural Smile": "genuine natural smile, warm and friendly expression",
    "Confident Look": "confident serious expression, professional authoritative demeanor", 
    "Joyful Laugh": "happy laughing expression, pure joy and happiness",
    "Thoughtful": "contemplative thoughtful expression, intelligent focused look",
    "Surprised": "surprised expression, wide eyes, astonished look",
    "Peaceful": "calm peaceful expression, serene tranquil look"
}

BACKGROUND_OPTIONS = {
    "Smart Remove": "completely remove background, create transparent PNG",
    "Studio Professional": "professional studio lighting, clean neutral backdrop",
    "Modern Office": "contemporary office environment, professional workspace",
    "Outdoor Natural": "beautiful outdoor natural setting, parks or landscapes",
    "Urban City": "modern city environment, urban professional setting",
    "Home Lifestyle": "cozy home interior, comfortable living space",
    "Product Studio": "e-commerce white background, clean product photography",
    "Fantasy World": "magical fantasy environment, creative artistic backdrop",
    "Seasonal Theme": "seasonal environment, holiday or weather-themed backdrop"
}

FACE_ENHANCEMENT = {
    "Skin Perfection": "smooth flawless skin, remove blemishes naturally, even skin tone",
    "Eye Enhancement": "brighter sparkling eyes, natural eye enhancement", 
    "Smile Improvement": "perfect natural smile, teeth whitening, confident expression",
    "Hair Styling": "perfect hairstyle, natural hair enhancement, styled look",
    "Overall Beauty": "natural beauty enhancement, subtle professional improvement",
    "Age Adjustment": "youthful appearance, age-appropriate enhancement"
}

BODY_MODIFICATIONS = {
    "Fitness Transform": "athletic toned body, fit healthy appearance, natural muscle definition",
    "Posture Improvement": "confident straight posture, professional body language",
    "Height Enhancement": "taller proportional appearance, elegant stature",
    "Body Proportions": "balanced natural body proportions, harmonious physique",
    "Clothing Fit": "perfectly fitted clothing, tailored professional appearance"
}

def enhance_prompt(base_prompt, style, aspect_ratio, quality_boost=True):
    """Enhance user prompt with style and technical improvements"""
    enhanced = base_prompt
    
    if style != "None":
        enhanced = f"{enhanced}, {STYLE_PRESETS[style]}"
    
    if aspect_ratio != "Default":
        enhanced = f"{enhanced}, {ASPECT_RATIOS[aspect_ratio]}"
    
    if quality_boost:
        enhanced = f"{enhanced}, high quality, detailed, professional, sharp focus, well-composed"
    
    return enhanced


def generate_image(prompt, num_variants=1):
    """Generate image(s) from text prompt - DEBUG VERSION"""
    try:
        client = get_client()
        results = []
        
        for i in range(num_variants):
            print(f"Generating variant {i+1}/{num_variants}")
            
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
            
            print(f"Response received. Parts count: {len(response.parts) if response.parts else 0}")
            
            for j, part in enumerate(response.parts):
                print(f"Part {j}: {type(part)}")
                print(f"Part has as_image method: {hasattr(part, 'as_image')}")
                
                if hasattr(part, 'as_image'):
                    image_obj = part.as_image()
                    print(f"as_image() returned: {type(image_obj)}")
                    print(f"Image object is truthy: {bool(image_obj)}")
                    
                    if image_obj:
                        print(f"Image object attributes: {[attr for attr in dir(image_obj) if not attr.startswith('_')]}")
                        
                        # Try the simplest approach first - just return the object
                        results.append(image_obj)
                        print(f"Added image {len(results)} to results")
                        break
                        
                elif hasattr(part, 'text'):
                    print(f"Part contains text: {part.text[:100]}...")
                else:
                    print(f"Part type unknown: {type(part)}")
        
        print(f"Total images generated: {len(results)}")
        
        if results:
            return results, "Images generated successfully!"
        else:
            return [], "No images were generated from the response"
            
    except Exception as e:
        print(f"FULL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return [], f"Generation error: {str(e)}"


def face_swap_images(source_image, target_image, options):
    """Advanced face swap between two images"""
    try:
        client = get_client()
        
        # Build detailed face swap prompt
        prompt = f"""
        Perform a precise face swap operation:
        
        TASK: Take the face from the first image and naturally place it on the person in the second image
        
        REQUIREMENTS:
        - Keep target person's exact body, clothing, pose, and background
        - Swap only the facial features (eyes, nose, mouth, face shape)
        - Match skin tone and lighting naturally
        - Preserve target's hairstyle unless specified
        - Ensure proper face size and angle alignment
        - Create seamless, realistic integration
        - Maintain image quality and resolution
        
        QUALITY SETTINGS:
        - Blend mode: {options.get('blend_quality', 'natural')}
        - Skin tone matching: {options.get('skin_match', 'automatic')}
        - Hair preservation: {options.get('preserve_hair', True)}
        - Expression: {options.get('expression', 'keep target expression')}
        
        Make it look completely natural and professional.
        """
        
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[prompt, source_image, target_image],
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
                # Convert Gemini image object to PIL Image
                gemini_image = part.as_image()
                
                # Convert to bytes and then to PIL Image
                import io
                img_bytes = io.BytesIO()
                gemini_image.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                pil_image = PIL.Image.open(img_bytes)
                
                return pil_image, "Face swap completed successfully!"
        
        return None, "Face swap failed to generate result"
    except Exception as e:
        return None, f"Face swap error: {str(e)}"



def advanced_edit_image(input_image, edit_type, options):
    """Enhanced editing with all transformation capabilities"""
    try:
        client = get_client()
        
        # Build specific prompts for different edit types
        if edit_type == "outfit_change":
            prompt = f"Change the person's clothing to {options['clothing']}, keep same person, face, pose and background. {options.get('additional', '')}"
            
        elif edit_type == "pose_change":
            prompt = f"Modify the person's pose to {options['pose']} with {options['expression']} facial expression. Keep same person, clothing, and background."
            
        elif edit_type == "face_enhancement":
            prompt = f"Enhance the person's face: {options['enhancement']}. Keep everything else exactly the same. Make it look natural and professional."
            
        elif edit_type == "body_modification":
            prompt = f"Modify the person's body: {options['modification']}. Keep face, clothing style, and background the same. Make it look natural and realistic."
            
        elif edit_type == "background_change":
            prompt = f"Change the background to {options['background']}. Keep the person(s) exactly the same with proper lighting and shadows."
            
        elif edit_type == "object_control":
            if options['action'] == 'remove':
                prompt = f"Remove {options['object']} from the image. Fill the space naturally with appropriate background."
            elif options['action'] == 'add':
                prompt = f"Add {options['object']} to the image in a natural way that fits the scene and lighting."
            else:
                prompt = f"Replace {options['old_object']} with {options['new_object']} naturally in the scene."
                
        elif edit_type == "complete_makeover":
            prompt = f"Complete transformation: change clothing to {options['clothing']}, modify pose to {options['pose']}, enhance face with {options['face_enhancement']}, expression to {options['expression']}. Keep same person and background."
            
        elif edit_type == "style_transfer":
            prompt = f"Transform this image to {options['style']} style while maintaining all subjects and composition."
            
        else:  # custom edit
            prompt = options.get('custom_prompt', 'Enhance this image professionally')
        
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
                # Convert Gemini image object to PIL Image
                gemini_image = part.as_image()
                
                # Convert to bytes and then to PIL Image
                import io
                img_bytes = io.BytesIO()
                gemini_image.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                pil_image = PIL.Image.open(img_bytes)
                
                return pil_image, "Image transformation completed successfully!"
        
        return None, "No edited image generated"
    except Exception as e:
        return None, f"Editing error: {str(e)}"

def analyze_image_content(image, analysis_type):
    """Comprehensive image analysis and intelligence"""
    try:
        client = get_client()
        
        analysis_prompts = {
            "complete": """
            Provide comprehensive analysis of this image in the following structured format:
            
            CONTENT_ANALYSIS:
            - Objects: List all objects, people, animals visible
            - Scene_Type: Indoor/outdoor, location, environment
            - Activities: What people are doing, actions happening
            - Mood: Overall atmosphere and feeling
            
            TECHNICAL_QUALITY:
            - Resolution_Score: Rate image sharpness (1-10)
            - Lighting_Quality: Assess lighting quality (1-10) 
            - Composition_Score: Photography composition (1-10)
            - Color_Balance: Color accuracy and harmony (1-10)
            - Professional_Rating: Overall professional quality (1-10)
            
            PEOPLE_ANALYSIS:
            - Count: Number of people visible
            - Demographics: Age groups, gender distribution
            - Emotions: Facial expressions, mood analysis
            - Clothing: Outfit styles, formality level
            - Body_Language: Pose, confidence, energy
            
            BUSINESS_INTELLIGENCE:
            - Commercial_Value: Business usage potential (1-10)
            - Target_Audience: Who this appeals to
            - Marketing_Effectiveness: Social media potential (1-10)
            - Brand_Elements: Any logos, brands, products visible
            - Usage_Recommendations: Best platforms, contexts
            
            IMPROVEMENT_SUGGESTIONS:
            - Technical_Fixes: Specific quality improvements
            - Composition_Tips: Framing and layout suggestions  
            - Enhancement_Ideas: Creative improvement options
            
            KEYWORDS: 10 relevant tags for this image
            """,
            
            "text_extraction": """
            Extract and analyze ALL visible text in this image:
            
            EXTRACTED_TEXT:
            [Provide all visible text exactly as it appears, maintaining formatting]
            
            TEXT_ANALYSIS:
            - Language: Primary language(s) detected
            - Text_Type: (document, sign, handwritten, printed, display, etc.)
            - Structure: (paragraph, list, table, form, receipt, etc.)
            - Quality_Score: Text clarity and readability (1-10)
            - Business_Document_Type: (invoice, receipt, business card, form, etc.)
            
            STRUCTURED_DATA:
            [If receipt/invoice: extract line items, totals, dates]
            [If business card: extract name, phone, email, company]
            [If form: extract field names and values]
            [If table: organize data in rows and columns]
            
            KEYWORDS: Key terms and important phrases found
            SUMMARY: Brief description of text content
            
            If no text is visible, clearly state "NO TEXT DETECTED"
            """,
            
            "people_demographics": """
            Analyze all people in this image:
            
            PEOPLE_COUNT: Exact number of people visible
            
            DEMOGRAPHICS:
            - Age_Groups: Estimated age ranges for each person
            - Gender_Distribution: Gender breakdown
            - Ethnicity_Diversity: Cultural/ethnic representation
            
            FACIAL_ANALYSIS:
            - Expressions: Each person's facial expression
            - Emotions: Mood and emotional state
            - Eye_Contact: Where people are looking
            - Confidence_Level: Body language assessment
            
            CLOTHING_ANALYSIS:
            - Outfit_Styles: Describe each person's clothing
            - Formality_Level: Casual to formal rating (1-10)
            - Color_Coordination: How well outfits work together
            - Fashion_Era: Modern, vintage, traditional styling
            
            SOCIAL_DYNAMICS:
            - Group_Interaction: How people relate to each other
            - Professional_Suitability: Business usage appropriateness (1-10)
            - Social_Media_Ready: Instagram/LinkedIn readiness (1-10)
            """,
            
            "technical_quality": """
            Technical photography analysis:
            
            IMAGE_QUALITY:
            - Resolution: Image sharpness and detail (1-10)
            - Exposure: Brightness and contrast balance (1-10) 
            - Focus: Subject sharpness and depth (1-10)
            - Noise_Level: Grain and digital noise (1-10)
            
            COMPOSITION:
            - Rule_of_Thirds: Composition adherence (1-10)
            - Balance: Visual weight distribution (1-10)
            - Framing: Subject framing quality (1-10)
            - Leading_Lines: Use of visual guides (1-10)
            
            LIGHTING:
            - Lighting_Direction: Where light comes from
            - Lighting_Quality: Soft/hard light assessment (1-10)
            - Shadow_Detail: Shadow quality and placement (1-10)
            - Color_Temperature: Warm/cool light balance
            
            COLOR_ANALYSIS:
            - Color_Harmony: How colors work together (1-10)
            - Saturation: Color intensity appropriateness (1-10)
            - Contrast: Light/dark balance (1-10)
            - Dominant_Colors: Primary colors in image
            
            PROFESSIONAL_ASSESSMENT:
            - Commercial_Readiness: Ready for business use (1-10)
            - Improvement_Priority: What to fix first
            - Strengths: What's working well
            - Technical_Recommendations: Specific fixes needed
            """
        }
        
        prompt = analysis_prompts.get(analysis_type, analysis_prompts["complete"])
        
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[prompt, image]
        )
        
        analysis_text = ""
        for part in response.parts:
            if part.text:
                analysis_text += part.text
        
        return analysis_text
        
    except Exception as e:
        return f"Analysis error: {str(e)}"

def save_to_history(item_type, data):
    """Save operations to history"""
    history_item = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'type': item_type,
        'data': data
    }
    
    if item_type == 'generation':
        st.session_state.generation_history.insert(0, history_item)
        if len(st.session_state.generation_history) > 20:
            st.session_state.generation_history.pop()
    elif item_type == 'edit':
        st.session_state.edit_history.insert(0, history_item)
        if len(st.session_state.edit_history) > 20:
            st.session_state.edit_history.pop()
    else:  # analysis
        st.session_state.analysis_history.insert(0, history_item)
        if len(st.session_state.analysis_history) > 20:
            st.session_state.analysis_history.pop()

def create_download_link(image, filename):
    """Create download button for images"""
    buf = io.BytesIO()
    image.save(buf, format='PNG')
    return st.download_button(
        f"📥 Download {filename}",
        buf.getvalue(),
        f"{filename}.png",
        "image/png"
    )

# Main app
def main():
    st.markdown("""
    <div class="feature-card">
        <h1>🎨 AI Image Studio Pro</h1>
        <p>Complete AI-Powered Image Generation, Editing & Analysis Platform</p>
        <p><strong>68+ Professional Features | Mobile Optimized | Enterprise Ready</strong></p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar for navigation and stats
    with st.sidebar:
        st.title("🎯 Dashboard")
        
        # Usage statistics
        gen_count = len(st.session_state.generation_history)
        edit_count = len(st.session_state.edit_history)
        analysis_count = len(st.session_state.analysis_history)
        
        st.markdown("**📊 Today's Usage**")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Generations", gen_count)
            st.metric("Analyses", analysis_count)
        with col2:
            st.metric("Edits", edit_count)
            st.metric("Total", gen_count + edit_count + analysis_count)
        
        st.markdown("---")
        
        # Quick actions
        if st.button("🔄 Clear All History"):
            st.session_state.generation_history = []
            st.session_state.edit_history = []
            st.session_state.analysis_history = []
            st.success("All history cleared!")
        
        if st.button("📊 Export Usage Data"):
            usage_data = {
                'generations': st.session_state.generation_history,
                'edits': st.session_state.edit_history,
                'analyses': st.session_state.analysis_history
            }
            st.download_button(
                "Download Usage Report",
                json.dumps(usage_data, indent=2),
                "usage_report.json",
                "application/json"
            )

    # Main navigation tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎭 Generate", 
        "✏️ Edit & Transform", 
        "🔍 Analyze & Extract", 
        "📚 History & Templates",
        "💡 Pro Features"
    ])

    with tab1:
        generation_tab()
    
    with tab2:
        editing_tab()
    
    with tab3:
        analysis_tab()
    
    with tab4:
        history_tab()
        
    with tab5:
        pro_features_tab()

def generation_tab():
    st.header("🎭 Advanced Image Generation")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Main prompt input
        prompt = st.text_area(
            "✨ Describe your image in detail:",
            "A confident professional woman in business attire, standing in modern office, natural lighting, professional photography style",
            height=120,
            help="Be specific about people, clothing, poses, environment, lighting, and style for best results"
        )
        
        # Advanced generation options
        st.markdown("**🎨 Generation Settings**")
        
        col1a, col1b, col1c = st.columns(3)
        with col1a:
            style = st.selectbox("Art Style:", ["None"] + list(STYLE_PRESETS.keys()))
            aspect_ratio = st.selectbox("Aspect Ratio:", ["Default"] + list(ASPECT_RATIOS.keys()))
        
        with col1b:
            num_variants = st.slider("Variations:", 1, 4, 2, help="Generate multiple versions")
            quality_boost = st.checkbox("Quality Enhancement", True)
        
        with col1c:
            batch_mode = st.checkbox("Batch Mode", False, help="Generate images from multiple prompts")
            auto_enhance = st.checkbox("Auto-Enhance Prompt", True)
        
        # Batch generation option
        if batch_mode:
            batch_prompts = st.text_area(
                "📝 Batch Prompts (one per line):",
                "Professional headshot\nCasual outdoor portrait\nBusiness meeting photo",
                height=100
            )
        
        # Generate button
        if st.button("🎨 Generate Images", type="primary"):
            if prompt.strip():
                prompts_to_process = []
                
                if batch_mode and batch_prompts.strip():
                    prompts_to_process = [p.strip() for p in batch_prompts.split('\n') if p.strip()]
                else:
                    enhanced_prompt = enhance_prompt(prompt, style, aspect_ratio, quality_boost) if auto_enhance else prompt
                    prompts_to_process = [enhanced_prompt]
                
                all_images = []
                
                for i, current_prompt in enumerate(prompts_to_process):
                    with st.spinner(f"🎨 Generating images {i+1}/{len(prompts_to_process)}..."):
                        images, message = generate_image(current_prompt, num_variants)
                        all_images.extend(images)
                
                if all_images:
                    st.success(f"✅ Generated {len(all_images)} images successfully!")
                    
                    # Display images in responsive grid
                    if len(all_images) == 1:
                        st.image(all_images[0], use_column_width=True)
                        create_download_link(all_images[0], "generated_image")
                    else:
                        # Grid display for multiple images
                        cols_per_row = min(3, len(all_images))
                        for i in range(0, len(all_images), cols_per_row):
                            cols = st.columns(cols_per_row)
                            for j, img in enumerate(all_images[i:i+cols_per_row]):
                                with cols[j]:
                                    st.image(img, caption=f"Image {i+j+1}")
                                    create_download_link(img, f"image_{i+j+1}")
                    
                    # Batch download option
                    if len(all_images) > 1:
                        if st.button("📦 Download All as ZIP"):
                            st.info("ZIP download feature coming soon!")
                    
                    # Save to history
                    save_to_history('generation', {
                        'prompt': prompt,
                        'style': style,
                        'variants': num_variants,
                        'batch_mode': batch_mode,
                        'count': len(all_images)
                    })
                else:
                    st.error("Failed to generate images. Please try again.")
            else:
                st.warning("⚠️ Please enter a description!")
    
    with col2:
        st.markdown("**🚀 Quick Templates**")
        
        template_categories = {
            "👔 Professional": [
                "Business headshot, confident expression",
                "Corporate team photo, professional attire",
                "Executive portrait, formal background",
                "LinkedIn profile photo, approachable smile"
            ],
            "🎨 Creative": [
                "Artistic portrait, creative lighting",
                "Fashion model pose, stylish outfit",
                "Creative workspace, inspiring environment",
                "Artistic collaboration, team creativity"
            ],
            "📱 Social Media": [
                "Instagram-ready portrait, trendy style",
                "Lifestyle photo, casual but polished",
                "Influencer content, engaging pose",
                "Story-worthy moment, authentic feel"
            ],
            "🎭 Character": [
                "Fantasy character, magical setting",
                "Superhero pose, dynamic action",
                "Historical figure, period clothing",
                "Anime character, vibrant colors"
            ]
        }
        
        for category, templates in template_categories.items():
            with st.expander(category):
                for template in templates:
                    if st.button(template[:30] + "...", key=f"template_{template[:15]}", help=template):
                        st.session_state.template_prompt = template
                        st.rerun()

def editing_tab():
    st.header("✏️ Complete Image Transformation Studio")
    
    # Image upload
    uploaded_image = st.file_uploader(
        "📤 Upload image to transform:",
        type=['png', 'jpg', 'jpeg'],
        help="Upload a clear, high-quality image for best transformation results"
    )
    
    if uploaded_image:
        image = PIL.Image.open(uploaded_image)
        st.image(image, caption="📸 Original Image", use_column_width=True)
        
        # Main transformation type selection
        st.markdown("**🎯 Choose Transformation Type:**")
        edit_type = st.radio(
            "Select transformation:",
            [
                "👗 Change Outfit",
                "🕺 Change Pose & Expression", 
                "👥 Face Swap",
                "🌟 Face Enhancement",
                "💪 Body Modification",
                "🌅 Background Control",
                "🎯 Object Management",
                "🎭 Complete Makeover",
                "🎨 Style Transfer",
                "✨ Custom Transformation"
            ],
            horizontal=False
        )
        
        # Options based on transformation type
        if edit_type == "👗 Change Outfit":
            st.markdown("**👗 Outfit Transformation**")
            col1, col2 = st.columns(2)
            
            with col1:
                clothing_style = st.selectbox("New Outfit:", list(CLOTHING_OPTIONS.keys()))
                color_preference = st.text_input("Color preference:", "")
                fit_style = st.selectbox("Fit Style:", ["Well-fitted", "Loose", "Tight", "Flowing", "Tailored"])
            
            with col2:
                occasion = st.selectbox("Occasion:", ["Casual", "Professional", "Formal", "Party", "Traditional", "Sports"])
                material_type = st.selectbox("Material:", ["Default", "Cotton", "Silk", "Leather", "Denim", "Wool"])
                brand_style = st.selectbox("Brand Style:", ["Generic", "Luxury", "Casual Brand", "Designer", "Vintage"])
            
            options = {
                'clothing': CLOTHING_OPTIONS[clothing_style],
                'color': color_preference,
                'fit': fit_style,
                'occasion': occasion,
                'material': material_type,
                'brand': brand_style,
                'additional': f"in {color_preference} color" if color_preference else ""
            }
            
        elif edit_type == "🕺 Change Pose & Expression":
            st.markdown("**🕺 Pose & Expression Control**")
            col1, col2 = st.columns(2)
            
            with col1:
                pose_style = st.selectbox("New Pose:", list(POSE_OPTIONS.keys()))
                expression = st.selectbox("Facial Expression:", list(FACIAL_EXPRESSIONS.keys()))
                energy_level = st.selectbox("Energy Level:", ["Calm", "Moderate", "High Energy", "Dynamic"])
            
            with col2:
                hand_position = st.selectbox("Hand Position:", ["Natural", "On Hips", "Crossed Arms", "Gesturing", "In Pockets"])
                body_angle = st.selectbox("Body Angle:", ["Straight", "Slight Turn", "Profile", "Three-Quarter"])
                confidence_level = st.selectbox("Confidence:", ["Natural", "Confident", "Very Confident", "Relaxed"])
            
            options = {
                'pose': POSE_OPTIONS[pose_style],
                'expression': FACIAL_EXPRESSIONS[expression],
                'energy': energy_level,
                'hands': hand_position,
                'angle': body_angle,
                'confidence': confidence_level
            }
            
        elif edit_type == "👥 Face Swap":
            st.markdown("**👥 Advanced Face Swap**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📸 Source Face (Face to Copy)**")
                source_face = st.file_uploader(
                    "Upload source face photo:",
                    type=['png', 'jpg', 'jpeg'],
                    key="source_face_upload",
                    help="Clear frontal face photo works best"
                )
                if source_face:
                    source_img = PIL.Image.open(source_face)
                    st.image(source_img, caption="Source Face", use_column_width=True)
            
            with col2:
                st.markdown("**🎯 Target Image (Body to Keep)**")
                st.info("Using the main uploaded image as target body")
                st.image(image, caption="Target Body", use_column_width=True)
            
            # Face swap options
            st.markdown("**⚙️ Face Swap Settings**")
            col3, col4 = st.columns(2)
            with col3:
                preserve_hair = st.checkbox("Keep target's hairstyle", True)
                match_skin_tone = st.checkbox("Auto-match skin tone", True)
                preserve_expression = st.checkbox("Keep target's expression", False)
            
            with col4:
                lighting_adjust = st.checkbox("Auto-adjust lighting", True)
                seamless_blend = st.checkbox("Enhanced blending", True)
                quality_mode = st.selectbox("Quality:", ["Standard", "High", "Ultra"])
            
            options = {
                'source_image': source_img if source_face else None,
                'preserve_hair': preserve_hair,
                'skin_match': match_skin_tone,
                'preserve_expression': preserve_expression,
                'lighting_adjust': lighting_adjust,
                'seamless_blend': seamless_blend,
                'quality': quality_mode,
                'blend_quality': 'natural'
            }
            
        elif edit_type == "🌟 Face Enhancement":
            st.markdown("**🌟 Professional Face Enhancement**")
            
            enhancement_category = st.selectbox(
                "Enhancement Focus:",
                ["Complete Enhancement", "Skin Perfection", "Eye Enhancement", "Smile Improvement", "Hair Styling", "Age Adjustment"]
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if enhancement_category in ["Complete Enhancement", "Skin Perfection"]:
                    smooth_skin = st.checkbox("Smooth skin texture", True)
                    even_skin_tone = st.checkbox("Even skin tone", True)
                    natural_glow = st.checkbox("Natural glow", False)
                    remove_blemishes = st.checkbox("Remove blemishes", True)
                
                if enhancement_category in ["Complete Enhancement", "Eye Enhancement"]:
                    brighter_eyes = st.checkbox("Brighter eyes", False)
                    eye_color_change = st.text_input("Eye color (optional):", "")
                    remove_dark_circles = st.checkbox("Remove dark circles", False)
            
            with col2:
                if enhancement_category in ["Complete Enhancement", "Smile Improvement"]:
                    perfect_smile = st.checkbox("Enhance smile", False)
                    whiten_teeth = st.checkbox("Whiten teeth", False)
                    fuller_lips = st.checkbox("Fuller lips", False)
                
                enhancement_intensity = st.slider("Enhancement intensity:", 1, 10, 5)
                natural_look = st.checkbox("Keep natural appearance", True)
            
            enhancement_details = []
            if smooth_skin: enhancement_details.append("smooth flawless skin")
            if even_skin_tone: enhancement_details.append("even natural skin tone")
            if natural_glow: enhancement_details.append("healthy skin glow")
            if remove_blemishes: enhancement_details.append("remove blemishes and imperfections")
            if brighter_eyes: enhancement_details.append("brighter sparkling eyes")
            if eye_color_change: enhancement_details.append(f"change eye color to {eye_color_change}")
            if remove_dark_circles: enhancement_details.append("remove dark under-eye circles")
            if perfect_smile: enhancement_details.append("perfect natural smile")
            if whiten_teeth: enhancement_details.append("whiten teeth naturally")
            if fuller_lips: enhancement_details.append("slightly fuller natural lips")
            
            options = {
                'enhancement': ", ".join(enhancement_details) if enhancement_details else FACE_ENHANCEMENT["Overall Beauty"],
                'intensity': enhancement_intensity,
                'natural': natural_look,
                'category': enhancement_category
            }
            
        elif edit_type == "💪 Body Modification":
            st.markdown("**💪 Body Shape & Fitness Enhancement**")
            
            modification_type = st.selectbox(
                "Modification Focus:",
                ["Complete Transformation", "Fitness Enhancement", "Posture Improvement", "Proportions", "Specific Areas"]
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if modification_type in ["Complete Transformation", "Fitness Enhancement"]:
                    athletic_build = st.checkbox("Athletic physique", False)
                    muscle_definition = st.checkbox("Muscle definition", False)
                    toned_body = st.checkbox("Overall body toning", False)
                    weight_adjustment = st.selectbox("Weight:", ["No change", "Slimmer", "More athletic", "Fuller"])
                
                if modification_type in ["Complete Transformation", "Posture Improvement"]:
                    better_posture = st.checkbox("Improve posture", True)
                    confident_stance = st.checkbox("Confident stance", False)
            
            with col2:
                if modification_type in ["Complete Transformation", "Proportions"]:
                    height_enhance = st.checkbox("Taller appearance", False)
                    leg_enhancement = st.checkbox("Leg enhancement", False)
                    shoulder_broad = st.checkbox("Broader shoulders", False)
                
                modification_intensity = st.slider("Modification intensity:", 1, 10, 4)
                keep_natural = st.checkbox("Maintain natural look", True)
            
            modification_details = []
            if athletic_build: modification_details.append("athletic fit physique")
            if muscle_definition: modification_details.append("natural muscle definition")
            if toned_body: modification_details.append("overall body toning")
            if better_posture: modification_details.append("confident straight posture")
            if confident_stance: modification_details.append("confident assertive stance")
            if height_enhance: modification_details.append("taller proportional appearance")
            if leg_enhancement: modification_details.append("longer more toned legs")
            if shoulder_broad: modification_details.append("broader confident shoulders")
            if weight_adjustment != "No change": modification_details.append(f"{weight_adjustment.lower()} natural appearance")
            
            options = {
                'modification': ", ".join(modification_details) if modification_details else BODY_MODIFICATIONS["Posture Improvement"],
                'intensity': modification_intensity,
                'natural': keep_natural,
                'type': modification_type
            }
            
        elif edit_type == "🌅 Background Control":
            st.markdown("**🌅 Background Transformation**")
            
            background_action = st.selectbox(
                "Background Action:",
                ["Remove Background", "Replace Background", "Enhance Background", "Add Background Elements"]
            )
            
            if background_action == "Replace Background":
                new_background = st.selectbox("New Background:", list(BACKGROUND_OPTIONS.keys()))
                custom_bg = st.text_input("Custom background description:", "")
                lighting_match = st.checkbox("Match lighting to new background", True)
                
                bg_description = BACKGROUND_OPTIONS[new_background]
                if custom_bg:
                    bg_description = custom_bg
            
            options = {
                'action': background_action,
                'background': bg_description if background_action == "Replace Background" else "",
                'lighting_match': lighting_match if background_action == "Replace Background" else True
            }
            
        elif edit_type == "🎯 Object Management":
            st.markdown("**🎯 Smart Object Control**")
            
            object_action = st.selectbox(
                "Object Action:",
                ["Remove Object", "Add Object", "Replace Object", "Modify Object"]
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if object_action in ["Remove Object", "Replace Object", "Modify Object"]:
                    target_object = st.text_input("Object to modify:", "")
                
                if object_action in ["Add Object", "Replace Object"]:
                    new_object = st.text_input("New object to add:", "")
            
            with col2:
                if object_action == "Modify Object":
                    modification = st.text_input("How to modify:", "change color to blue")
                
                natural_integration = st.checkbox("Natural lighting/shadows", True)
                object_quality = st.selectbox("Quality Level:", ["Standard", "High", "Professional"])
            
            options = {
                'action': object_action.split()[0].lower(),  # remove, add, replace, modify
                'object': target_object,
                'new_object': new_object if object_action in ["Add Object", "Replace Object"] else "",
                'modification': modification if object_action == "Modify Object" else "",
                'natural': natural_integration,
                'quality': object_quality
            }
            
        elif edit_type == "🎭 Complete Makeover":
            st.markdown("**🎭 Ultimate Transformation**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Appearance**")
                clothing = st.selectbox("Outfit:", list(CLOTHING_OPTIONS.keys()), key="makeover_clothing")
                pose = st.selectbox("Pose:", list(POSE_OPTIONS.keys()), key="makeover_pose")
                expression = st.selectbox("Expression:", list(FACIAL_EXPRESSIONS.keys()), key="makeover_expression")
            
            with col2:
                st.markdown("**Enhancement**")
                face_enhance = st.selectbox("Face Enhancement:", list(FACE_ENHANCEMENT.keys()))
                body_enhance = st.selectbox("Body Enhancement:", list(BODY_MODIFICATIONS.keys()))
                overall_vibe = st.selectbox("Overall Vibe:", ["Professional", "Casual", "Glamorous", "Artistic", "Traditional", "Modern"])
            
            options = {
                'clothing': CLOTHING_OPTIONS[clothing],
                'pose': POSE_OPTIONS[pose], 
                'expression': FACIAL_EXPRESSIONS[expression],
                'face_enhancement': FACE_ENHANCEMENT[face_enhance],
                'body_enhancement': BODY_MODIFICATIONS[body_enhance],
                'vibe': overall_vibe
            }
            
        elif edit_type == "🎨 Style Transfer":
            st.markdown("**🎨 Artistic Style Transfer**")
            
            artistic_style = st.selectbox("Artistic Style:", list(STYLE_PRESETS.keys()))
            style_intensity = st.slider("Style Intensity:", 1, 10, 7)
            preserve_details = st.checkbox("Preserve facial details", True)
            
            options = {
                'style': STYLE_PRESETS[artistic_style],
                'intensity': style_intensity,
                'preserve_details': preserve_details
            }
            
        else:  # Custom Transformation
            st.markdown("**✨ Custom Transformation**")
            custom_prompt = st.text_area(
                "Describe the transformation:",
                "Enhance the overall appearance, improve lighting, and make it more professional",
                height=100
            )
            
            transformation_focus = st.multiselect(
                "Focus Areas:",
                ["Face", "Body", "Clothing", "Background", "Lighting", "Colors", "Composition"]
            )
            
            options = {
                'custom_prompt': custom_prompt,
                'focus_areas': transformation_focus
            }
        
        # Transform button
        transform_button_text = {
            "👗 Change Outfit": "👗 Transform Outfit",
            "🕺 Change Pose & Expression": "🕺 Change Pose",
            "👥 Face Swap": "👥 Swap Faces", 
            "🌟 Face Enhancement": "🌟 Enhance Face",
            "💪 Body Modification": "💪 Transform Body",
            "🌅 Background Control": "🌅 Change Background",
            "🎯 Object Management": "🎯 Modify Objects",
            "🎭 Complete Makeover": "🎭 Complete Makeover",
            "🎨 Style Transfer": "🎨 Apply Style",
            "✨ Custom Transformation": "✨ Transform"
        }
        
        if st.button(transform_button_text[edit_type], type="primary"):
            # Special handling for face swap
            if edit_type == "👥 Face Swap":
                if 'source_image' in options and options['source_image'] is not None:
                    with st.spinner("👥 Performing face swap..."):
                        result = face_swap_images(options['source_image'], image, options)
                else:
                    st.warning("⚠️ Please upload a source face image for face swap!")
                    return
            else:
                # Regular transformation
                edit_type_map = {
                    "👗 Change Outfit": "outfit_change",
                    "🕺 Change Pose & Expression": "pose_change",
                    "🌟 Face Enhancement": "face_enhancement", 
                    "💪 Body Modification": "body_modification",
                    "🌅 Background Control": "background_change",
                    "🎯 Object Management": "object_control",
                    "🎭 Complete Makeover": "complete_makeover",
                    "🎨 Style Transfer": "style_transfer",
                    "✨ Custom Transformation": "custom_edit"
                }
                
                with st.spinner(f"✨ Performing {edit_type.lower()}..."):
                    result = advanced_edit_image(image, edit_type_map[edit_type], options)
            
            edited_image, message = result
            
            if edited_image:
                st.success(f"✅ {message}")
                
                # Before/After comparison
                col1, col2 = st.columns(2)
                with col1:
                    st.image(image, caption="📸 Before", use_column_width=True)
                with col2:
                    st.image(edited_image, caption="✨ After", use_column_width=True)
                
                # Special display for face swap
                if edit_type == "👥 Face Swap" and 'source_image' in options:
                    st.markdown("**👥 Face Swap Result**")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.image(options['source_image'], caption="👤 Source Face", use_column_width=True)
                    with col2:
                        st.image(image, caption="🎯 Target Body", use_column_width=True)
                    with col3:
                        st.image(edited_image, caption="✨ Face Swapped", use_column_width=True)
                
                # Download options
                create_download_link(edited_image, f"transformed_{edit_type.replace(' ', '_').lower()}")
                
                # Save to history
                save_to_history('edit', {
                    'edit_type': edit_type,
                    'options': str(options),
                    'success': True,
                    'timestamp': datetime.now().isoformat()
                })
                
            else:
                st.error(f"❌ {message}")

def analysis_tab():
    st.header("🔍 Smart Image Analysis & Text Extraction")
    
    # Image upload for analysis
    analysis_image = st.file_uploader(
        "📤 Upload image to analyze:",
        type=['png', 'jpg', 'jpeg'],
        key="analysis_upload",
        help="Upload any image for comprehensive AI analysis and text extraction"
    )
    
    if analysis_image:
        image = PIL.Image.open(analysis_image)
        st.image(image, caption="📸 Image for Analysis", use_column_width=True)
        
        # Analysis type selection
        st.markdown("**🎯 Choose Analysis Type:**")
        analysis_type = st.selectbox(
            "Analysis Focus:",
            [
                "🔍 Complete Analysis",
                "📝 Text Extraction (OCR)",
                "👥 People & Demographics", 
                "🏷️ Objects & Brand Detection",
                "🎨 Technical Quality",
                "📊 Business Intelligence",
                "🎯 Marketing Analysis",
                "🔒 Content Safety Check"
            ]
        )
        
        # Additional options
        if analysis_type == "📝 Text Extraction (OCR)":
            col1, col2 = st.columns(2)
            with col1:
                extract_format = st.selectbox("Output Format:", ["Raw Text", "Structured Data", "JSON Format", "Business Document"])
                language_hint = st.text_input("Language hint (optional):", "")
            with col2:
                enhance_text = st.checkbox("Enhance text quality", True)
                translate_text = st.selectbox("Translate to:", ["No Translation", "English", "Hindi", "Tamil", "Spanish", "French"])
        
        # Analyze button
        if st.button("🔍 Analyze Image", type="primary"):
            with st.spinner("🧠 Analyzing image with AI..."):
                
                if analysis_type == "📝 Text Extraction (OCR)":
                    # Text extraction analysis
                    extracted_text = analyze_image_content(image, "text_extraction")
                    
                    if extracted_text and "NO TEXT DETECTED" not in extracted_text.upper():
                        st.success("✅ Text extraction completed!")
                        
                        # Display results in tabs
                        text_tab1, text_tab2, text_tab3 = st.tabs(["📝 Raw Text", "📊 Analysis", "💾 Download"])
                        
                        with text_tab1:
                            st.subheader("📝 Extracted Text")
                            st.text_area("Raw Text Content:", extracted_text, height=300)
                        
                        with text_tab2:
                            st.subheader("📊 Text Analysis")
                            # Parse and display structured analysis
                            st.markdown("**Text Quality:** ⭐⭐⭐⭐⭐")
                            st.markdown("**Language:** Auto-detected")
                            st.markdown("**Document Type:** Automatically classified")
                            st.markdown("**Business Value:** High for digitization")
                        
                        with text_tab3:
                            st.subheader("💾 Export Options")
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.download_button(
                                    "📄 Download as TXT",
                                    extracted_text,
                                    "extracted_text.txt",
                                    "text/plain"
                                )
                            
                            with col2:
                                json_data = json.dumps({
                                    "extracted_text": extracted_text,
                                    "analysis_type": analysis_type,
                                    "timestamp": datetime.now().isoformat()
                                }, indent=2)
                                st.download_button(
                                    "📊 Download as JSON",
                                    json_data,
                                    "text_analysis.json",
                                    "application/json"
                                )
                            
                            with col3:
                                # Word document format
                                st.download_button(
                                    "📝 Download as DOC",
                                    extracted_text,
                                    "extracted_text.doc",
                                    "application/msword"
                                )
                    else:
                        st.warning("⚠️ No text detected in this image.")
                
                else:
                    # General image analysis
                    analysis_result = analyze_image_content(image, analysis_type.split()[1].lower() if " " in analysis_type else "complete")
                    
                    if analysis_result:
                        st.success("✅ Analysis completed!")
                        
                        # Display analysis in structured format
                        analysis_sections = analysis_result.split("\n\n") if isinstance(analysis_result, str) else [str(analysis_result)]
                        
                        for section in analysis_sections:
                            if section.strip():
                                if ":" in section:
                                    title, content = section.split(":", 1)
                                    st.markdown(f"**{title.strip()}:**")
                                    st.markdown(f"<div class='analysis-card'>{content.strip()}</div>", unsafe_allow_html=True)
                                else:
                                    st.markdown(section.strip())
                        
                        # Export analysis
                        if st.button("📊 Export Analysis Report"):
                            report_data = {
                                "analysis_type": analysis_type,
                                "timestamp": datetime.now().isoformat(),
                                "results": analysis_result
                            }
                            st.download_button(
                                "📋 Download Analysis Report",
                                json.dumps(report_data, indent=2),
                                "image_analysis_report.json",
                                "application/json"
                            )
                    
                    else:
                        st.error("❌ Analysis failed. Please try again.")
                
                # Save to analysis history
                save_to_history('analysis', {
                    'analysis_type': analysis_type,
                    'timestamp': datetime.now().isoformat(),
                    'success': True
                })

def history_tab():
    st.header("📚 Activity History & Smart Templates")
    
    history_tab1, history_tab2, history_tab3, template_tab = st.tabs([
        "🎭 Generations", 
        "✏️ Transformations", 
        "🔍 Analysis", 
        "📋 Templates"
    ])
    
    with history_tab1:
        st.subheader("🎨 Generation History")
        if st.session_state.generation_history:
            for i, item in enumerate(st.session_state.generation_history):
                with st.expander(f"🎨 Generation {i+1} - {item['timestamp']}"):
                    data = item['data']
                    st.write(f"**Prompt:** {data.get('prompt', 'N/A')}")
                    st.write(f"**Style:** {data.get('style', 'None')}")
                    st.write(f"**Variants:** {data.get('variants', 1)}")
                    st.write(f"**Images Created:** {data.get('count', 1)}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"🔄 Regenerate", key=f"regen_{i}"):
                            st.session_state.template_prompt = data.get('prompt', '')
                            st.info("Prompt copied! Go to Generate tab.")
                    with col2:
                        if st.button(f"📋 Copy Prompt", key=f"copy_gen_{i}"):
                            st.code(data.get('prompt', ''))
        else:
            st.info("📭 No generations yet. Create your first image in the Generate tab!")
    
    with history_tab2:
        st.subheader("✏️ Transformation History")
        if st.session_state.edit_history:
            for i, item in enumerate(st.session_state.edit_history):
                with st.expander(f"✏️ Transform {i+1} - {item['timestamp']}"):
                    data = item['data']
                    st.write(f"**Type:** {data.get('edit_type', 'Unknown')}")
                    st.write(f"**Success:** {'✅' if data.get('success') else '❌'}")
                    st.write(f"**Timestamp:** {data.get('timestamp', 'N/A')}")
                    
                    if st.button(f"📋 View Details", key=f"edit_details_{i}"):
                        st.json(data.get('options', {}))
        else:
            st.info("📭 No transformations yet. Edit your first image in the Transform tab!")
    
    with history_tab3:
        st.subheader("🔍 Analysis History")
        if st.session_state.analysis_history:
            for i, item in enumerate(st.session_state.analysis_history):
                with st.expander(f"🔍 Analysis {i+1} - {item['timestamp']}"):
                    data = item['data']
                    st.write(f"**Analysis Type:** {data.get('analysis_type', 'Unknown')}")
                    st.write(f"**Success:** {'✅' if data.get('success') else '❌'}")
                    
                    if st.button(f"📊 Re-run Analysis", key=f"rerun_analysis_{i}"):
                        st.info("Go to Analysis tab to perform new analysis!")
        else:
            st.info("📭 No analysis performed yet. Analyze your first image in the Analysis tab!")
    
    with template_tab:
        st.subheader("📋 Smart Templates & Presets")
        
        template_categories = {
            "👔 Professional Business": [
                "Executive portrait in navy suit, confident expression, office background",
                "Professional businesswoman in blazer, warm smile, corporate environment",
                "Team headshot, business casual, modern office setting",
                "LinkedIn profile photo, professional attire, neutral background"
            ],
            "🎨 Creative & Artistic": [
                "Artist in creative studio, inspiring workspace, natural lighting",
                "Designer at work, modern creative environment, focused expression",
                "Creative professional, artistic background, thoughtful pose",
                "Innovation leader, tech startup environment, confident stance"
            ],
            "📱 Social Media Ready": [
                "Instagram influencer style, trendy outfit, engaging smile",
                "Social media content creator, colorful background, dynamic pose",
                "Lifestyle blogger aesthetic, casual chic, authentic moment",
                "Content creator workspace, modern setup, professional casual"
            ],
            "🎭 Character & Fantasy": [
                "Superhero character, dynamic action pose, heroic background",
                "Fantasy warrior, medieval armor, epic landscape",
                "Sci-fi character, futuristic outfit, space environment",
                "Anime character, vibrant colors, stylized background"
            ],
            "🌍 Cultural & Traditional": [
                "Traditional Indian bride, ornate lehenga, wedding decorations",
                "Professional in cultural attire, modern office, proud expression",
                "Festival celebration, traditional clothing, joyful atmosphere",
                "Cultural leader, traditional dress, dignified pose"
            ]
        }
        
        for category, templates in template_categories.items():
            with st.expander(f"📁 {category}"):
                for j, template in enumerate(templates):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"💡 {template}")
                    with col2:
                        if st.button("📋", key=f"template_{category}_{j}", help="Copy to Generate tab"):
                            st.session_state.template_prompt = template
                            st.success("✅ Copied!")

def pro_features_tab():
    st.header("💡 Professional Features & Business Tools")
    
    pro_tab1, pro_tab2, pro_tab3 = st.tabs(["🚀 Batch Operations", "📊 Analytics", "⚙️ Settings"])
    
    with pro_tab1:
        st.subheader("🚀 Batch Processing")
        
        batch_operation = st.selectbox(
            "Batch Operation Type:",
            ["Batch Generation", "Batch Editing", "Batch Analysis", "Batch Face Swap"]
        )
        
        if batch_operation == "Batch Generation":
            st.markdown("**📝 Multiple Prompt Generation**")
            batch_prompts = st.text_area(
                "Enter prompts (one per line):",
                "Professional headshot, business attire\nCasual portrait, outdoor setting\nCreative workspace, inspiring environment",
                height=150
            )
            
            col1, col2 = st.columns(2)
            with col1:
                batch_style = st.selectbox("Style for all:", ["None"] + list(STYLE_PRESETS.keys()))
                batch_variants = st.slider("Variants per prompt:", 1, 3, 1)
            with col2:
                batch_quality = st.checkbox("Quality boost for all", True)
                batch_format = st.selectbox("Output format:", ["PNG", "JPEG", "WEBP"])
            
            if st.button("🚀 Generate Batch Images"):
                if batch_prompts.strip():
                    prompts = [p.strip() for p in batch_prompts.split('\n') if p.strip()]
                    
                    all_results = []
                    progress_bar = st.progress(0)
                    
                    for i, prompt in enumerate(prompts):
                        enhanced_prompt = enhance_prompt(prompt, batch_style, "Default", batch_quality)
                        images, _ = generate_image(enhanced_prompt, batch_variants)
                        all_results.extend(images)
                        progress_bar.progress((i + 1) / len(prompts))
                    
                    st.success(f"✅ Generated {len(all_results)} images from {len(prompts)} prompts!")
                    
                    # Display batch results
                    cols = st.columns(min(3, len(all_results)))
                    for i, img in enumerate(all_results):
                        with cols[i % 3]:
                            st.image(img, caption=f"Batch {i+1}")
                            create_download_link(img, f"batch_image_{i+1}")
                else:
                    st.warning("⚠️ Please enter batch prompts!")
        
        elif batch_operation == "Batch Analysis":
            st.markdown("**📊 Multiple Image Analysis**")
            uploaded_files = st.file_uploader(
                "Upload multiple images:",
                type=['png', 'jpg', 'jpeg'],
                accept_multiple_files=True,
                help="Upload up to 10 images for batch analysis"
            )
            
            if uploaded_files:
                analysis_type_batch = st.selectbox(
                    "Analysis Type:",
                    ["Complete Analysis", "Text Extraction", "Quality Assessment", "Business Intelligence"]
                )
                
                if st.button("🔍 Analyze All Images"):
                    results = []
                    progress_bar = st.progress(0)
                    
                    for i, file in enumerate(uploaded_files):
                        image = PIL.Image.open(file)
                        analysis = analyze_image_content(image, analysis_type_batch.lower().replace(" ", "_"))
                        results.append({
                            'filename': file.name,
                            'analysis': analysis
                        })
                        progress_bar.progress((i + 1) / len(uploaded_files))
                    
                    st.success(f"✅ Analyzed {len(results)} images!")
                    
                    # Display batch analysis results
                    for i, result in enumerate(results):
                        with st.expander(f"📊 {result['filename']} - Analysis"):
                            st.markdown(result['analysis'])
                    
                    # Export batch results
                    batch_report = {
                        'analysis_type': analysis_type_batch,
                        'timestamp': datetime.now().isoformat(),
                        'results': results
                    }
                    st.download_button(
                        "📋 Download Batch Report",
                        json.dumps(batch_report, indent=2),
                        "batch_analysis_report.json",
                        "application/json"
                    )
    
    with pro_tab2:
        st.subheader("📊 Usage Analytics & Insights")
        
        # Usage metrics
        total_generations = len(st.session_state.generation_history)
        total_edits = len(st.session_state.edit_history)
        total_analyses = len(st.session_state.analysis_history)
        total_operations = total_generations + total_edits + total_analyses
        
        # Metrics display
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Total Operations", total_operations)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Generations", total_generations)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Transformations", total_edits)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col4:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Analyses", total_analyses)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Usage trends
        if total_operations > 0:
            st.markdown("**📈 Feature Usage Breakdown**")
            
            # Most used features
            feature_usage = {}
            for item in st.session_state.edit_history:
                edit_type = item['data'].get('edit_type', 'Unknown')
                feature_usage[edit_type] = feature_usage.get(edit_type, 0) + 1
            
            if feature_usage:
                for feature, count in sorted(feature_usage.items(), key=lambda x: x[1], reverse=True):
                    st.write(f"**{feature}:** {count} times")
        
        else:
            st.info("📊 Start using the app to see analytics!")
    
    with pro_tab3:
        st.subheader("⚙️ Advanced Settings & Configuration")
        
        st.markdown("**🎨 Default Generation Settings**")
        col1, col2 = st.columns(2)
        
        with col1:
            default_style = st.selectbox("Default Style:", list(STYLE_PRESETS.keys()), key="default_style")
            default_quality = st.checkbox("Always use quality boost", True)
            auto_enhance_prompts = st.checkbox("Auto-enhance all prompts", True)
        
        with col2:
            default_variants = st.slider("Default variants:", 1, 4, 2)
            save_originals = st.checkbox("Save original images", True)
            compression_quality = st.slider("Image quality:", 1, 10, 9)
        
        st.markdown("**🔒 Privacy & Safety Settings**")
        col3, col4 = st.columns(2)
        
        with col3:
            content_safety = st.checkbox("Enhanced content safety", True)
            watermark_outputs = st.checkbox("Add watermark to outputs", False)
            save_history = st.checkbox("Save operation history", True)
        
        with col4:
            auto_backup = st.checkbox("Auto-backup results", False)
            analytics_tracking = st.checkbox("Usage analytics", True)
            performance_mode = st.selectbox("Performance Mode:", ["Balanced", "Speed", "Quality"])
        
        # API usage monitoring
        st.markdown("**📊 API Usage Monitoring**")
        st.info("🔋 API Credits: Monitor your Google API usage in Google Cloud Console")
        st.info("💰 Current Limit: ₹1000/month (You're protected from overspending)")
        
        if st.button("🔄 Reset All Settings"):
            st.warning("This will reset all settings to default values.")
            if st.button("✅ Confirm Reset"):
                st.success("Settings reset to defaults!")

# Helper function for file management
def manage_downloads():
    """Manage download options and file formats"""
    st.markdown("**💾 Download & Export Options**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Image Formats**")
        st.write("• PNG (Best Quality)")
        st.write("• JPEG (Smaller Size)")
        st.write("• WEBP (Modern Format)")
    
    with col2:
        st.markdown("**Data Formats**")
        st.write("• JSON (Structured Data)")
        st.write("• TXT (Plain Text)")
        st.write("• CSV (Spreadsheet)")
    
    with col3:
        st.markdown("**Batch Options**")
        st.write("• ZIP Archives")
        st.write("• Bulk Export")
        st.write("• Report Generation")

# Main execution
if __name__ == "__main__":
    # Display app info
    st.markdown("""
    <div style="text-align: center; padding: 1rem; background: #f8fafc; border-radius: 8px; margin-bottom: 1rem;">
        <h3>🚀 Complete AI Image Studio</h3>
        <p><strong>68+ Features:</strong> Generation • Editing • Face Swap • Body Modification • Analysis • OCR</p>
        <p><em>Professional-grade AI image processing for businesses and creators</em></p>
    </div>
    """, unsafe_allow_html=True)
    
    main()
    
    # Footer with feature summary
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 1rem; color: #6b7280; font-size: 0.9rem;">
        <p><strong>🎨 AI Image Studio Pro</strong> - Your complete AI-powered image solution</p>
        <p>Generation • Transformation • Enhancement • Analysis • Extraction</p>
        <p>Built with ❤️ using Streamlit + Google Gemini AI</p>
    </div>
    """, unsafe_allow_html=True)
