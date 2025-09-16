import streamlit as st
import base64
import os
import sys
import subprocess
import requests
import io
from fpdf import FPDF, XPos, YPos
import json
import time
import streamlit.components.v1 as components

# Update the secrets handling to be more secure
def get_required_secrets():
    """
    Check for required secrets and provide clear instructions if missing
    """
    required_secrets = [
        'OPENAI_API_KEY',
        'KIMI_API_KEY', 
        'DEEPSEEK_API_KEY'
    ]
    
    # For local development
    try:
        import toml
        with open('.streamlit/secrets.toml') as f:
            st.secrets = toml.load(f)
    except:
        # Will use deployed Streamlit secrets if file not found
        pass
        
    missing_secrets = []
    for secret in required_secrets:
        if secret not in st.secrets:
            missing_secrets.append(secret)
    
    if missing_secrets:
        st.error("""
        Missing required API keys. Please add them:
        
        1. For local development: Create `.streamlit/secrets.toml` with:
           ```
           OPENAI_API_KEY = "your-key-here"
           KIMI_API_KEY = "your-key-here"
           DEEPSEEK_API_KEY = "your-key-here"
           ```
           
        2. For deployment: Add these in Streamlit Cloud dashboard
        """)
        st.stop()

# Add this near the top of your script, after imports
get_required_secrets()

# Update the DEEPSEEK_API_URL to use the secret if available
DEEPSEEK_API_URL = st.secrets.get("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")

Kimi_API_KEY = st.secrets["KIMI_API_KEY"]
# Deepseek API configuration
DEEPSEEK_API_KEY = st.secrets["DEEPSEEK_API_KEY"]
# Initialize session state for model selection if not exists
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = 'kimi'  # Default to Kimi

# Add model selection in sidebar
with st.sidebar:
    st.header("🤖 Model Selection")
    selected_model = st.radio(
        "Choose AI Model",
        options=["kimi", "openai", "deepseek"],
        index=["kimi", "openai", "deepseek"].index(st.session_state.selected_model),
        help="Select which AI model to use for refinements"
    )
    st.session_state.selected_model = selected_model
    st.markdown("---")

def call_api(messages):
    """Unified API handler for multiple LLM providers"""
    model = st.session_state.selected_model
    
    # Create a friendly progress message
    progress_messages = {
        "openai": "✨ OpenAI is crafting your perfect resume...",
        "deepseek": "🔮 DeepSeek is working its magic...",
        "kimi": "🤖 Kimi is optimizing your content..."
    }
    
    # Create progress bar and status container
    progress_bar = st.progress(0)
    status = st.empty()
    
    if model == "openai":
        headers = {
            "Authorization": f"Bearer {st.secrets['OPENAI_API_KEY']}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "gpt-3.5-turbo",
            "messages": messages,
            "temperature": 0.5,  # Lower temperature for more consistent responses
            "max_tokens": 1000,  # Increased token limit
            "top_p": 0.9 
        }
        api_url = "https://api.openai.com/v1/chat/completions"
            
    elif model == "deepseek":
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "deepseek-chat",
            "messages": messages,
            "temperature": 0.5,  # Lower temperature for more consistent responses
            "max_tokens": 1000,  # Increased token limit
            "top_p": 0.9
        }
        api_url = DEEPSEEK_API_URL
            
    elif model == "kimi":
        headers = {
            "Authorization": f"Bearer {Kimi_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        data = {
            "model": "moonshot-v1-8k",
            "messages": messages,
            "temperature": 0.3,  # Lower temperature for more consistent responses
            "max_tokens": 1000,  # Increased token limit
            "top_p": 0.9,
            "stream": False
        }
        api_url = "https://api.moonshot.cn/v1/chat/completions"
    
    try:
        status.markdown(f'<div class="progress-text">{progress_messages[model]}</div>', unsafe_allow_html=True)
        for i in range(100):
            time.sleep(0.01)  # Smooth animation
            progress_bar.progress(i + 1)
            
        response = requests.post(api_url, headers=headers, json=data, timeout=30)
        
        if response.status_code != 200:
            status.error("🚨 Oops! Something went wrong with the AI service.")
            try:
                error_json = response.json()
                error_message = error_json.get('message', 'Unknown error')
                status.error(f"💬 The AI says: {error_message}")
            except:
                status.error("⚠️ Couldn't understand the error message from the AI")
            return None
            
        response.raise_for_status()
        response_json = response.json()
        
        # Clear progress indicators on success
        progress_bar.empty()
        status.empty()
        
        # Extract the content from the response
        try:
            return response_json["choices"][0]["message"]["content"]
        except KeyError as e:
            st.error("🤔 The AI responded in an unexpected format")
            st.error(f"Response JSON: {response_json}")
            return None
            
    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        if "getaddrinfo failed" in error_msg:
            st.error("📡 Whoops! Can't reach the AI. Is your internet connection okay?")
        elif "unauthorized" in error_msg.lower():
            st.error("🔑 Hmm... The AI doesn't recognize our secret handshake (API key issue)")
        elif "404" in error_msg:
            st.error("🗺️ Lost in cyberspace! Couldn't find the AI service.")
        else:
            st.error(f"🤖 The AI stumbled: {error_msg}")
        return None
    except Exception as e:
        st.error(f"💥 Unexpected plot twist: {str(e)}")
        return None
    finally:
        # Clean up progress indicators
        progress_bar.empty()
        status.empty()

# Replace the existing call_deepseek_api function with our new unified call_api function
def call_deepseek_api(messages):
    return call_api(messages)

# --- Dependency Check ---
def install_missing_dependencies():
    try:
        import fpdf
    except ImportError:
        st.info("Installing required dependencies... Please wait.")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "fpdf2"])
        st.rerun()

# Using built-in Times font, so no custom font download is needed.

# --- Helper Function for Normalizing Text ---
def normalize_text(text):
    replacements = {
        "’": "'",
        "‘": "'",
        """: '"',
        """: '"'
    }
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)
    return text

# --- Custom CSS ---
custom_css = """
<style>
/* Modern Header */
.header {
    background: linear-gradient(135deg, #6DD5FA, #2980B9);
    padding: 25px 20px;
    text-align: center;
    color: #fff;
    font-size: 3rem;
    font-weight: 700;
    border-radius: 12px;
    margin-bottom: 20px;
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
    letter-spacing: 1.5px;
    text-transform: uppercase;
}
/* Design Settings Container */
.design-settings {
    background: linear-gradient(135deg, #6DD5FA, #2980B9);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
    color: #fff;
}
/* Ensure headings and labels within design settings appear with white text */
.design-settings h2, .design-settings h3, .design-settings label {
    color: #fff;
}

/* Main container styling */
.main-container { padding: 20px; }
/* Side-by-side columns */
.left-column, .right-column { padding: 10px; }
/* Input styling */
.stTextInput, .stTextArea { margin-bottom: 15px; }
/* PDF preview styling */
.pdf-container {
    width: 100%;
    height: 800px;
    border: none;
    margin-top: 20px;
}
/* Modern Progress Bar */
.progress-container {
    width: 100%;
    height: 20px;
    background-color: #f0f0f0;
    border-radius: 10px;
    overflow: hidden;
    margin: 15px 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.progress-bar {
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, #6DD5FA, #2980B9);
    background-size: 200% 200%;
    animation: gradientFlow 2s linear infinite;
    transition: width 0.3s ease;
}
@keyframes gradientFlow {
    0% { background-position: 200% 50%; }
    100% { background-position: -200% 50%; }
}
.progress-text {
    color: #2980B9;
    font-weight: bold;
    text-align: center;
    margin: 10px 0;
    font-size: 1.1em;
}
.loading-container {
    animation: fadeOut 0.5s forwards;
    animation-delay: 0.5s;
    opacity: 1;
}
@keyframes fadeOut {
    to { opacity: 0; height: 0; margin: 0; }
}

/* Modern floating PDF container */
.pdf-container {
    background: var(--background-color);
    border-radius: 12px;
    transition: all 0.3s ease;
    position: relative;
}

/* Light theme */
[data-theme="light"] .pdf-container {
    --background-color: white;
    box-shadow: 
        0 4px 6px -1px rgba(0, 0, 0, 0.1),
        0 2px 4px -1px rgba(0, 0, 0, 0.06),
        0 20px 25px -5px rgba(0, 0, 0, 0.1),
        0 10px 10px -5px rgba(0, 0, 0, 0.04),
        0 0 0 1px rgba(0, 0, 0, 0.05);
}

/* Dark theme */
[data-theme="dark"] .pdf-container {
    --background-color: #1E1E1E;
    box-shadow: 
        0 4px 6px -1px rgba(0, 0, 0, 0.2),
        0 2px 4px -1px rgba(0, 0, 0, 0.16),
        0 20px 25px -5px rgba(255, 255, 255, 0.1),
        0 10px 10px -5px rgba(255, 255, 255, 0.04),
        0 0 0 1px rgba(255, 255, 255, 0.05);
}

/* Hover effect */
.pdf-container:hover {
    transform: translateY(-4px);
}

/* Light theme hover */
[data-theme="light"] .pdf-container:hover {
    box-shadow: 
        0 6px 8px -1px rgba(0, 0, 0, 0.12),
        0 4px 6px -1px rgba(0, 0, 0, 0.08),
        0 25px 30px -5px rgba(0, 0, 0, 0.12),
        0 12px 12px -5px rgba(0, 0, 0, 0.06),
        0 0 0 1px rgba(0, 0, 0, 0.06);
}

/* Dark theme hover */
[data-theme="dark"] .pdf-container:hover {
    box-shadow: 
        0 6px 8px -1px rgba(0, 0, 0, 0.24),
        0 4px 6px -1px rgba(0, 0, 0, 0.18),
        0 25px 30px -5px rgba(255, 255, 255, 0.12),
        0 12px 12px -5px rgba(255, 255, 255, 0.06),
        0 0 0 1px rgba(255, 255, 255, 0.08);
}

/* Shared button styling for download and refine buttons */
.stDownloadButton > button, .stButton > button {
    background: linear-gradient(135deg, #6DD5FA, #2980B9) !important;
    color: white !important;
    padding: 0.6rem 1.2rem !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 8px !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
}

.stDownloadButton > button:hover, .stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15) !important;
    background: linear-gradient(135deg, #2980B9, #6DD5FA) !important;
}

.stDownloadButton > button:active, .stButton > button:active {
    transform: translateY(0) !important;
}

/* Specific styling for sidebar buttons */
.stSidebar .stButton > button {
    width: 100% !important;
    margin-top: 1rem !important;
    margin-bottom: 1rem !important;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)
st.markdown('<div class="header">Resume Generator</div>', unsafe_allow_html=True)

# --- Top Inputs ---
with st.container():
    st.subheader("Enter Job Information")
    
    # Initialize session state variables
    if 'job_desc_collapsed' not in st.session_state:
        st.session_state.job_desc_collapsed = True
    if 'job_description' not in st.session_state:
        st.session_state.job_description = ''
        
    # Collapsible job description input
    if st.session_state.job_desc_collapsed:
        job_description = st.text_input(
            "Job Description (click to expand):", 
            value=st.session_state.job_description,
            key='job_desc_input'
        )
    else:
        job_description = st.text_area(
            "Paste the Job Description here:", 
            height=150,
            value=st.session_state.job_description,
            key='job_desc_area'
        )
    
    # Update session state with current input
    st.session_state.job_description = job_description

    if st.checkbox("Provide additional refinement instructions for selected sections?"):
        additional_instructions = st.text_area("Enter additional refinement instructions:", height=80)
    else:
        additional_instructions = ""

# --- Default Resume Sections ---
default_summary = (
    "Data Scientist with a master's in applied data science and 3 years of analytics expertise. "
    "Proficient in Python, SQL, and R, with a significant portfolio of advanced data science projects "
    "involving neural networks, machine learning, and large language models."
)
default_skills_msds = "ML | Python | SQL | R | Stats"
default_skills_mscs = "Neural Nets | CV | Robotics | AI | Algos"
default_skills_bse = "Econometrics | Data Analysis | Modeling"
default_tech_skills = "Python | SQL | Excel | Tableau | Azure"

# --- Default Refinements for Specific Sections ---
default_refinements = {
    "Summary": default_summary,
    "Data Science Skills": default_skills_msds,
    "CS Skills": default_skills_mscs,
    "Economics Skills": default_skills_bse,
    "Technical Skills": default_tech_skills,
    "Intel Corp Bullet 1": "Designed and implemented automated data-driven solutions for big dataset analytics, including an automated dashboard reporting system that enhances maintenance of advanced semiconductor equipment.",
    "Intel Corp Bullet 2": "Collaborated with engineering and technician teams to coordinate work, ensuring leadership and execution of data analysis, algorithm development tasks, and operational systems.",
    "Intel Corp Bullet 3": "Provided hands-on support on the factory floor, assisting in manufacturing processes and procurement activities.",
    "NW Natural Bullet 1": "Built a Python-based data collection application with web scrapers enabling real-time data visualization.",
    "NW Natural Bullet 2": "Conducted benchmarking analysis to improve collection performance and reduce bad debt costs.",
    "NW Natural Bullet 3": "Presented findings to managers using PowerPoint, leading to improved debt collection practices.",
    "Selam Consultancy Bullet 1": "Developed Power BI dashboards, integrating strategic insights and demand planning, resulting in a 6% sales increase.",
    "Selam Consultancy Bullet 2": "Implemented an automated ETL framework with Python and SQL, improving data extraction from multiple sources and increasing dataset availability by 30%.",
    "Selam Consultancy Bullet 3": "Applied SQL queries for customer insights, statistical analysis, data modeling, and market research.",
    "Auxilary Bullet 1": "Developed a business plan and organized a team to develop an AI-powered data error detection and cleaning system.",
    "Auxilary Bullet 2": "Led a team of five in the software development process.",
    "Auxilary Bullet 3": "Balanced business and technical aspects of product development.",
    "Data Privacy Bullet 1": "Implemented automated code scans and statistical analysis to improve data privacy and governance.",
    "Data Privacy Bullet 2": "Integrated privacy-by-design principles in collaboration with cross-functional teams.",
    "Certifications Bullet": "- Skills: Data Visualization (Power BI)"
}

# --- Prompt Templates for Job-Specific Refinement ---
refine_prompt_templates = {
    # Summary Section
    "Summary": """Rewrite the professional summary to emphasize {key_skills}, {technical_skills}, {ds_tools}, and incorporate relevant points from {original_summary}, ensuring alignment with {key_requirements}.
    Format:
    - Start with a descriptive role phrase from the job discription (e.g., "Data Scientist", "AI Engineer", "Machine Learning Expert").
    - Keep it within 2-3 lines
    - Tone: energetic and engaging, not flat or generic.
    - Length: 2–3 concise sentences (max 250 characters total).

    Rewrite the original summary to be more aligned with the JD.
    Examples:
    1. Business Analyst with 3+ years of experience aligning business needs with AI and analytics solutions. Skilled in SQL, Python, and visualization tools with a focus on delivering efficiency and growth.
    2. Data Engineer with 3+ years of experience designing pipelines and managing large-scale datasets. Skilled in SQL, Python, and ETL frameworks with expertise in ensuring clean, reliable data for analytics.
    3. Business Intelligence Analyst with an M.S. in Applied Data Science and 3+ years of experience building dashboards and insights in Power BI and SQL. Adept at transforming raw data into actionable recommendations for stakeholders.

    Original: {original}""",
    
    # Education Skills
    "Data Science Skills": """Focus on Applied Data Science masters degree related, {ds_tools}, courses and skills that could be relvant to JD, {key_requirements} and {technical_skills}. 
    Format: 3-5 pipe-separated items | Max length: 150 characters
    Original: {original}""",
    
    "CS Skills": """Focus on Computer science masters degree related courses and skills that could be relvant to JD, {key_requirements} and {technical_skills}. Include frameworks/languages. 
    Format: 3-5 pipe-separated items | Max length: 150 characters
    Original: {original}""",
    
    "Economics Skills": """Highlight Economics and finance related courses and skills that could be relvant to {key_requirements} and also those matches {original} from the JD. 
    Format: 3-5 pipe-separated items | Max length: 100 characters
    Original: {original}""",

    # Technical Skills
    "Technical Skills": """Match to JD's {tech_stack}. Include tools and frameworks that mactch {original} from the JD
    Format: 5-9 pipe-separated items | Max length: 200 characters
    Example: Power BI | Python | SQL | Power BI | Excel | MySQL | Hadoop Hive | R Studio | T-Test | Excel | MATLAB | AZure | Tableau 
    Original: {original}""",

    # Intel Corporation Bullets
    "Intel Corp Bullet 1": """Emphasize {automation_terms} using {metrics}. 
    Format: "Verb + what + how + result" structure
    Max length: 120 characters
    Original: {original}""",
    
    "Intel Corp Bullet 2": """Highlight cross-functional collaboration from JD. 
    Format: Start with action verb | Max length: 120 characters
    Original: {original}""",
    
    "Intel Corp Bullet 3": """Focus on operational support aspects from JD. 
    Format: Quantify impact | Max length: 120 characters
    Original: {original}""",

    # NW Natural Bullets
    "NW Natural Bullet 1": """Emphasize real-time systems from JD. 
    Format: Technical stack + business impact
    Example: "Built X using Y, enabling Z% faster decisions"
    Max length: 120 characters
    Original: {original}""",
    
    "NW Natural Bullet 2": """Quantify financial impacts using JD's {metrics}. 
    Format: $$$ numbers or percentages
    Example: "Reduced costs by X% through Y..."
    Max length: 120 characters
    Original: {original}""",
    
    "NW Natural Bullet 3": """Highlight presentation/communication skills. 
    Format: Audience size + decision impact
    Example: "Presented to X stakeholders, influencing Y decision"
    Max length: 120 characters
    Original: {original}""",

    # Selam Consultancy Bullets
    "Selam Consultancy Bullet 1": """Focus on dashboard metrics from JD. 
    Format: Business impact + technical implementation
    Example: "Increased X by Y% through Z implementation"
    Max length: 120 characters
    Original: {original}""",
    
    "Selam Consultancy Bullet 2": """Detail ETL processes from JD. 
    Format: Technical specifics + efficiency gains
    Example: "Reduced processing time by X using Y"
    Max length: 120 characters
    Original: {original}""",
    
    "Selam Consultancy Bullet 3": """Emphasize SQL analysis from JD. 
    Format: Specific queries/analyses + insights
    Example: "Uncovered X trend through Y analysis of Z data"
    Max length: 120 characters
    Original: {original}""",

    # Auxilary Bullets
    "Auxilary Bullet 1": """Highlight AI/ML aspects from JD. 
    Format: Technical stack + business value
    Example: "Developed X using Y, achieving Z accuracy"
    Max length: 120 characters
    Original: {original}""",
    
    "Auxilary Bullet 2": """Focus on leadership/team aspects. 
    Format: Team size + development methodology
    Example: "Led X developers using Agile/Scrum"
    Max length: 120 characters
    Original: {original}""",
    
    "Auxilary Bullet 3": """Balance technical/business requirements. 
    Format: Dual-column approach
    Example: "Technical: X | Business: Y"
    Max length: 120 characters
    Original: {original}""",

    # Data Privacy Bullets
    "Data Privacy Bullet 1": """Emphasize technical implementation. 
    Format: Tools/techniques + compliance metrics
    Example: "Implemented X scanning, reducing Y risks by Z%"
    Max length: 120 characters
    Original: {original}""",
    
    "Data Privacy Bullet 2": """Highlight cross-functional collaboration. 
    Format: Team types + governance outcomes
    Example: "Partnered with X teams to implement Y framework"
    Max length: 120 characters
    Original: {original}""",

    # Certifications
    "Certifications Bullet": """Align with Google Data Analytics skills.
    Format: Pipe-separated
    Example: "Skills: SQL | Excel | Python | Tableau"
    Max length: 120 characters
    Original: {original}"""
}

# --- Enhanced Keyword Extraction ---
def extract_job_keywords(job_description):
    """Extract key terms using the selected API"""
    prompt = f"""Analyze this job description and return a JSON object in this EXACT format, with no additional text or explanation:

{{
    "technical_skills": ["skill1", "skill2", "skill3", "skill4", "skill5"],
    "key_requirements": ["req1", "req2", "req3", "req4"],
    "ds_tools": ["tool1", "tool2", "tool3"],
    "programming_languages": ["lang1", "lang2"],
    "metrics": ["metric1", "metric2"],
    "certifications": ["cert1", "cert2"]
}}

Replace the placeholder values with actual values from this job description: {job_description[:2000]}"""

    try:
        response = call_api([
            {"role": "system", "content": "You are a job description analyzer. Return only valid JSON in the exact format requested, with no additional text or markdown formatting."},
            {"role": "user", "content": prompt}
        ])
        
        if not response:
            st.error("Received empty response from API")
            return default_keywords()
        
        # Clean the response to ensure it only contains JSON
        response = response.strip()
        # Remove markdown formatting if present
        if response.startswith('```json'):
            response = response[7:]
        if response.startswith('```'):
            response = response[3:]
        if response.endswith('```'):
            response = response[:-3]
        response = response.strip()
        
        # Try to find JSON in the response if it contains other text
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            # If direct parsing fails, try to extract JSON object
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != 0:
                try:
                    result = json.loads(response[start:end])
                except json.JSONDecodeError as e:
                    st.error(f"Failed to parse JSON after extraction: {str(e)}")
                    st.error(f"Extracted JSON: {response[start:end]}")
                    return default_keywords()
            else:
                st.error("No valid JSON object found in response")
                return default_keywords()
        
        # Validate structure
        required_keys = ["technical_skills", "key_requirements", "ds_tools",
                        "programming_languages", "metrics", "certifications"]
        for key in required_keys:
            if key not in result:
                st.error(f"Missing key in API response: {key}")
                return default_keywords()
        
        # Validate that all values are lists
        for key, value in result.items():
            if not isinstance(value, list):
                st.error(f"Invalid value type for {key}: expected list, got {type(value)}")
                return default_keywords()
        
        return result
        
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse JSON response: {str(e)}")
        st.error(f"Raw response: {response}")
        return default_keywords()
    except Exception as e:
        st.error(f"Failed to parse job keywords: {str(e)}")
        st.error(f"Raw response: {response if 'response' in locals() else 'No response'}")
        return default_keywords()

def default_keywords():
    return {
        "technical_skills": ["Data Analysis", "Machine Learning", "Python"],
        "key_requirements": ["Analytical Skills", "Technical Communication", "Problem Solving"],
        "ds_tools": ["Pandas", "NumPy"],
        "programming_languages": ["Python", "SQL"],
        "metrics": ["process efficiency", "performance improvements"],
        "certifications": []
    }

# --- Sidebar: Refine Specific Sections ---
with st.sidebar.expander("Refine Specific Sections"):
    st.markdown("**Summary of Qualifications**")
    refine_summary = st.checkbox("Summary")
    
    st.markdown("**Education**")
    refine_ds = st.checkbox("Data Science Skills")
    refine_cs = st.checkbox("CS Skills")
    refine_econ = st.checkbox("Economics Skills")
    
    st.markdown("**Technical Skills**")
    refine_tech = st.checkbox("Technical Skills")
    
    st.markdown("**Relevant Experience**")
    st.markdown("Intel Corporation (Graduate Technical Intern)")
    refine_intel1 = st.checkbox("Intel Corp Bullet 1")
    refine_intel2 = st.checkbox("Intel Corp Bullet 2")
    refine_intel3 = st.checkbox("Intel Corp Bullet 3")
    
    st.markdown("NW Natural (Financial Analytics Intern)")
    refine_nw1 = st.checkbox("NW Natural Bullet 1")
    refine_nw2 = st.checkbox("NW Natural Bullet 2")
    refine_nw3 = st.checkbox("NW Natural Bullet 3")
    
    st.markdown("Selam Consultancy (Data Engineer / Python Developer)")
    refine_selam1 = st.checkbox("Selam Consultancy Bullet 1")
    refine_selam2 = st.checkbox("Selam Consultancy Bullet 2")
    refine_selam3 = st.checkbox("Selam Consultancy Bullet 3")
    
    st.markdown("**Key Projects**")
    st.markdown("Auxilary.ai (Founded and Led)")
    refine_Auxilary1 = st.checkbox("Auxilary Bullet 1")
    refine_Auxilary2 = st.checkbox("Auxilary Bullet 2")
    refine_Auxilary3 = st.checkbox("Auxilary Bullet 3")
    
    st.markdown("Data Privacy and Governance for BI, Privado.ai")
    refine_privacy1 = st.checkbox("Data Privacy Bullet 1")
    refine_privacy2 = st.checkbox("Data Privacy Bullet 2")
    
    st.markdown("**Certifications**")
    refine_cert = st.checkbox("Certifications Bullet")
    
    if st.button("✨ Refine Selected Sections", use_container_width=True):
        job_desc = st.session_state.job_description
        if not job_desc.strip():
            st.warning("Please enter a job description first!")
        else:
            keywords = extract_job_keywords(job_desc)
            
            options = {
                "Summary": refine_summary,
                "Data Science Skills": refine_ds,
                "CS Skills": refine_cs,
                "Economics Skills": refine_econ,
                "Technical Skills": refine_tech,
                "Intel Corp Bullet 1": refine_intel1,
                "Intel Corp Bullet 2": refine_intel2,
                "Intel Corp Bullet 3": refine_intel3,
                "NW Natural Bullet 1": refine_nw1,
                "NW Natural Bullet 2": refine_nw2,
                "NW Natural Bullet 3": refine_nw3,
                "Selam Consultancy Bullet 1": refine_selam1,
                "Selam Consultancy Bullet 2": refine_selam2,
                "Selam Consultancy Bullet 3": refine_selam3,
                "Auxilary Bullet 1": refine_Auxilary1,
                "Auxilary Bullet 2": refine_Auxilary2,
                "Auxilary Bullet 3": refine_Auxilary3,
                "Data Privacy Bullet 1": refine_privacy1,
                "Data Privacy Bullet 2": refine_privacy2,
                "Certifications Bullet": refine_cert
            }
            
            for key, selected in options.items():
                if selected:
                    template = refine_prompt_templates.get(key, "")
                    # If additional instructions are provided, prepend a high-priority clause
                    important_additional = ""
                    if additional_instructions.strip():
                        important_additional = (
                            f"IMPORTANT: Please prioritize the following additional instructions: "
                            f"{additional_instructions.strip()}\n\n"
                        )
                    prompt = important_additional + template.format(
                        key_skills=", ".join(keywords.get('technical_skills', [])[:3]),
                        key_requirements=", ".join(keywords.get('key_requirements', [])[:2]),
                        ds_tools=", ".join(keywords.get('ds_tools', [])),
                        tech_stack=", ".join(keywords.get('technical_skills', [])),
                        metrics=", ".join(keywords.get('metrics', ["efficiency gains", "performance improvements"])),
                        certifications=", ".join(keywords.get('certifications', [])),
                        automation_terms=", ".join(keywords.get('automation_terms', ["process automation", "workflow optimization"])),
                        technical_skills=", ".join(keywords.get('technical_skills', [])),
                        additional=additional_instructions,
                        original=default_refinements.get(key, "")
                    )
                    refined_text = call_deepseek_api([
                        {"role": "system", "content": "You are a resume optimization expert."},
                        {"role": "user", "content": prompt}
                    ])
                    if refined_text:
                        st.session_state["refined_" + key] = refined_text.strip()
            st.balloons()
            st.success("🎉 Your resume sections have been magically enhanced! ✨")

# --- Sidebar: General Design Settings ---
with st.sidebar:
    st.markdown('<div class="design-settings">', unsafe_allow_html=True)
    st.header("Design Settings")
    # Using Times New Roman as default; font selector removed from UI
    selected_font = "Times"
    
    st.subheader("Spacing Adjustments")
    line_spacing = st.slider("Line Spacing", 1.0, 2.0, 1.3, 0.1)
    section_spacing = st.slider("Section Spacing", 1, 10, 3)
    
    with st.expander("Advanced Typography"):
        header_font_size = st.slider("Titles Font Size", 16, 24, 20)
        body_font_size = st.slider("Body Font Size", 10, 16, 13)
        contact_info_size = st.slider("Contact Info Font Size", 8, 14, 12)
    st.markdown('</div>', unsafe_allow_html=True)

# --- PDF Class (ResumePDFA3) ---
class ResumePDFA3(FPDF):
    def __init__(self, font_settings):
        super().__init__(format='A3')
        self.font_settings = font_settings
        self.set_margins(10, 10, 10)
        self.set_auto_page_break(auto=True, margin=8)
        # Use built-in Times font (Times New Roman) for default PDF output
        self.font_settings['base_font'] = 'Times'
        self.set_font('Times', size=12)  # Set initial font
    
    def header(self):
        self.set_font(self.font_settings['base_font'], style="B", size=self.font_settings['header_size'])
        self.cell(0, 8, normalize_text("Girum Wondemagegn"), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        self.set_font(self.font_settings['base_font'], size=self.font_settings['contact_size'])
        self.cell(0, 5, normalize_text("971-330-1599 | girumgk63@gmail.com | Beaverton, OR | www.linkedin.com/in/girum-wondemagegn"),
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        self.ln(3)
    
    def section_title(self, title):
        title = normalize_text(title)
        self.set_font(self.font_settings['base_font'], style="B", size=self.font_settings['header_size']-2)
        self.cell(0, 6, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")
        self.line(10, self.get_y(), 287, self.get_y())
        self.ln(self.font_settings['section_spacing'])
    
    def section_subtitle(self, title, subtitle, bold=False):
        if bold:
            self.set_font(self.font_settings['base_font'], style="B", size=self.font_settings.get('body_size', 13))
        else:
            self.set_font(self.font_settings['base_font'], style="", size=self.font_settings.get('body_size', 13))
        self.cell(0, 6, normalize_text(title), ln=0)
        self.cell(0, 6, normalize_text(subtitle), ln=1, align="R")
        self.ln(self.font_settings['section_spacing'])
    
    def section_body(self, text, bullet=False, bold=False):
        if bold:
            self.set_font(self.font_settings['base_font'], style="B", size=self.font_settings['body_size'])
        else:
            self.set_font(self.font_settings['base_font'], style="", size=self.font_settings['body_size'])
        line_spacing_px = 6 * self.font_settings['line_spacing']
        lines = text.split("\n")
        if bullet:
            for line in lines:
                current_x = self.get_x()
                current_y = self.get_y()
                self.cell(8)
                self.set_fill_color(0, 0, 0)
                self.rect(current_x + 4, current_y + 2, 2, 2, 'F')
                self.set_fill_color(255, 255, 255)
                self.multi_cell(0, line_spacing_px, " " + normalize_text(line), align="J")
        else:
            for line in lines:
                self.multi_cell(0, line_spacing_px, normalize_text(line), align="J")
        self.ln(1)

# --- Generate PDF File ---
def generate_pdf_file():
    from datetime import datetime
    import re
    def clean_filename(text):
        cleaned = re.sub(r'[<>:"/\\|?*]', '', text)
        cleaned = re.sub(r'[\s_]+', '_', cleaned)
        return cleaned.strip('_')
    extracted_title, extracted_company = None, None
    if job_description.strip():
        extracted_title, extracted_company = extract_job_details(job_description)
    final_job_title = extracted_title if extracted_title else "Girum Wondemagegn"
    final_company_name = extracted_company if extracted_company else "Girum Wondemagegn"
    timestamp = datetime.now().strftime("%Y%m%d")
    if final_job_title and final_company_name:
        filename = f"Resume_{clean_filename(final_job_title)}-{clean_filename(final_company_name)}_{timestamp}.pdf"
    else:
        filename = f"Girum_Wondemagegn_Resume_{timestamp}.pdf"
    if not extracted_title:
        st.session_state['job_title'] = final_job_title.replace('_', ' ')
    if not extracted_company:
        st.session_state['company_name'] = final_company_name.replace('_', ' ')
    font_config = {
        'base_font': selected_font,
        'line_spacing': line_spacing,
        'section_spacing': section_spacing,
        'header_size': header_font_size,
        'body_size': body_font_size,
        'contact_size': contact_info_size
    }
    pdf = ResumePDFA3(font_config)
    pdf.add_page()
    pdf.set_title(f"Resume for {final_job_title} position at {final_company_name}" if final_job_title and final_company_name else "Resume")
    pdf.set_author("Girum Wondemagegn")
    pdf.set_creator("Resume Generator")
    pdf.set_keywords(f"resume, {final_job_title}, {final_company_name}, {timestamp}")
    
    # SUMMARY
    summary_text = st.session_state.get("refined_Summary", default_refinements["Summary"])
    pdf.section_title("SUMMARY OF QUALIFICATIONS")
    pdf.section_body(summary_text)
    
    # EDUCATION
    pdf.section_title("EDUCATION")
    # Data Science Skills (MS Applied)
    ds_text = st.session_state.get("refined_Data Science Skills", default_refinements["Data Science Skills"])
    pdf.section_subtitle("Master of Science in Applied Data Science (3.98 GPA)", "Portland, OR", bold=True)
    pdf.set_font("Times", size=13)
    pdf.section_body("Portland State University")
    pdf.set_font("Times", size=13)
    pdf.section_body(ds_text)
    # CS Skills (MS Computer Science)
    cs_text = st.session_state.get("refined_CS Skills", default_refinements["CS Skills"])
    pdf.section_subtitle("Master of Science in Computer Science (Ongoing)", "Atlanta, OR", bold=True)
    pdf.set_font("Times", size=13)
    pdf.section_body("Georgia Institute of Technology")
    pdf.set_font("Times", size=13)
    pdf.section_body(cs_text)
    # Economics Skills (BS Economics)
    econ_text = st.session_state.get("refined_Economics Skills", default_refinements["Economics Skills"])
    pdf.section_subtitle("Bachelor of Science in Economics", "Portland, OR", bold=True)
    pdf.set_font("Times", size=13)
    pdf.section_body("Portland State University")
    pdf.set_font("Times", size=13)
    pdf.section_body(econ_text)
    
    # TECHNICAL SKILLS
    tech_text = st.session_state.get("refined_Technical Skills", default_tech_skills)
    pdf.section_title("TECHNICAL SKILLS")
    pdf.section_body(tech_text)
    
    # RELEVANT EXPERIENCE
    pdf.section_title("RELEVANT EXPERIENCE")
    # Intel Corporation bullets
    pdf.section_subtitle("Graduate Technical Intern (Data Science/Data Analysis)", "Jun 2024 - Aug 2024", bold=True)
    pdf.section_body("Intel Corporation", bullet=False, bold=True)
    intel_b1 = st.session_state.get("refined_Intel Corp Bullet 1", default_refinements["Intel Corp Bullet 1"])
    intel_b2 = st.session_state.get("refined_Intel Corp Bullet 2", default_refinements["Intel Corp Bullet 2"])
    intel_b3 = st.session_state.get("refined_Intel Corp Bullet 3", default_refinements["Intel Corp Bullet 3"])
    pdf.set_font("Times", size=13)
    pdf.section_body(intel_b1, bullet=True)
    pdf.section_body(intel_b2, bullet=True)
    pdf.section_body(intel_b3, bullet=True)
    
    # NW Natural bullets
    pdf.section_subtitle("Financial Analytics Intern", "Jun 2023 - Sep 2023", bold=True)
    nw_b1 = st.session_state.get("refined_NW Natural Bullet 1", default_refinements["NW Natural Bullet 1"])
    nw_b2 = st.session_state.get("refined_NW Natural Bullet 2", default_refinements["NW Natural Bullet 2"])
    nw_b3 = st.session_state.get("refined_NW Natural Bullet 3", default_refinements["NW Natural Bullet 3"])
    pdf.section_body("NW Natural", bullet=False, bold=True)
    pdf.set_font("Times", size=13)
    pdf.section_body(nw_b1, bullet=True)
    pdf.section_body(nw_b2, bullet=True)
    pdf.section_body(nw_b3, bullet=True)
    
    # Selam Consultancy bullets
    pdf.section_subtitle("Data Engineer / Python Developer", "Jun 2015 - Feb 2018", bold=True)
    selam_b1 = st.session_state.get("refined_Selam Consultancy Bullet 1", default_refinements["Selam Consultancy Bullet 1"])
    selam_b2 = st.session_state.get("refined_Selam Consultancy Bullet 2", default_refinements["Selam Consultancy Bullet 2"])
    selam_b3 = st.session_state.get("refined_Selam Consultancy Bullet 3", default_refinements["Selam Consultancy Bullet 3"])
    pdf.section_body("Selam Consultancy", bullet=False, bold=True)
    pdf.set_font("Times", size=13)
    pdf.section_body(selam_b1, bullet=True)
    pdf.section_body(selam_b2, bullet=True)
    pdf.section_body(selam_b3, bullet=True)
    
    # KEY PROJECTS
    pdf.section_title("KEY PROJECTS")
    Auxilary_b1 = st.session_state.get("refined_Auxilary Bullet 1", default_refinements["Auxilary Bullet 1"])
    Auxilary_b2 = st.session_state.get("refined_Auxilary Bullet 2", default_refinements["Auxilary Bullet 2"])
    Auxilary_b3 = st.session_state.get("refined_Auxilary Bullet 3", default_refinements["Auxilary Bullet 3"])
    pdf.section_subtitle("Founded and Led Auxilary.ai", "Aug 2024 - Present", bold=True)
    pdf.section_body(Auxilary_b1, bullet=True)
    pdf.section_body(Auxilary_b2, bullet=True)
    pdf.section_body(Auxilary_b3, bullet=True)
    
    # Data Privacy bullets
    privacy_b1 = st.session_state.get("refined_Data Privacy Bullet 1", default_refinements["Data Privacy Bullet 1"])
    privacy_b2 = st.session_state.get("refined_Data Privacy Bullet 2", default_refinements["Data Privacy Bullet 2"])
    pdf.section_subtitle("Data Privacy and Governance for BI, Privado.ai", "Jan 2024 - Jun 2024", bold=True)
    pdf.section_body(privacy_b1, bullet=True)
    pdf.section_body(privacy_b2, bullet=True)
    
    # CERTIFICATIONS
    pdf.section_title("CERTIFICATIONS")
    cert_b = st.session_state.get("refined_Certifications Bullet", 
                                  default_refinements.get("Certifications Bullet", "Skills: Data Visualization (Power BI)"))
    # Remove the leading hyphen if present so the bullet is consistent with others
    cert_b = cert_b.lstrip("- ").strip()
    pdf.section_body("Google Data Analytics", bold=True)
    pdf.section_body(cert_b, bullet=True, bold=False)
    
    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer)
    pdf_bytes = pdf_buffer.getvalue()
    pdf_buffer.close()
    return pdf_bytes

def extract_job_details(job_description):
    """Extract job title and company name from job description using selected API"""
    if not job_description.strip():
        return None, None
        
    prompt = f"""Extract just the job title and company name from this job description.
    Return ONLY in this format: "Job Title | Company Name"
    Job Description: {job_description}"""
    
    result = call_api([
        {"role": "system", "content": "You are a job description parser."},
        {"role": "user", "content": prompt}
    ])
    
    try:
        job_title, company_name = result.split("|")
        return job_title.strip(), company_name.strip()
    except:
        return None, None

# --- Final PDF Display & Download ---
try:
    with st.spinner("Generating real-time preview..."):
        pdf_bytes = generate_pdf_file()
        
        # Encode PDF for embedding
        base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        
        # Add custom CSS for modern shadows and floating effect
        st.markdown("""
        <style>
        /* Modern floating PDF container */
        .pdf-container {
            background: var(--background-color);
            border-radius: 12px;
            transition: all 0.3s ease;
            position: relative;
        }

        /* Light theme */
        [data-theme="light"] .pdf-container {
            --background-color: white;
            box-shadow: 
                0 4px 6px -1px rgba(0, 0, 0, 0.1),
                0 2px 4px -1px rgba(0, 0, 0, 0.06),
                0 20px 25px -5px rgba(0, 0, 0, 0.1),
                0 10px 10px -5px rgba(0, 0, 0, 0.04),
                0 0 0 1px rgba(0, 0, 0, 0.05);
        }

        /* Dark theme */
        [data-theme="dark"] .pdf-container {
            --background-color: #1E1E1E;
            box-shadow: 
                0 4px 6px -1px rgba(0, 0, 0, 0.2),
                0 2px 4px -1px rgba(0, 0, 0, 0.16),
                0 20px 25px -5px rgba(255, 255, 255, 0.1),
                0 10px 10px -5px rgba(255, 255, 255, 0.04),
                0 0 0 1px rgba(255, 255, 255, 0.05);
        }

        /* Hover effect */
        .pdf-container:hover {
            transform: translateY(-4px);
        }

        /* Light theme hover */
        [data-theme="light"] .pdf-container:hover {
            box-shadow: 
                0 6px 8px -1px rgba(0, 0, 0, 0.12),
                0 4px 6px -1px rgba(0, 0, 0, 0.08),
                0 25px 30px -5px rgba(0, 0, 0, 0.12),
                0 12px 12px -5px rgba(0, 0, 0, 0.06),
                0 0 0 1px rgba(0, 0, 0, 0.06);
        }

        /* Dark theme hover */
        [data-theme="dark"] .pdf-container:hover {
            box-shadow: 
                0 6px 8px -1px rgba(0, 0, 0, 0.24),
                0 4px 6px -1px rgba(0, 0, 0, 0.18),
                0 25px 30px -5px rgba(255, 255, 255, 0.12),
                0 12px 12px -5px rgba(255, 255, 255, 0.06),
                0 0 0 1px rgba(255, 255, 255, 0.08);
        }

        /* Shared button styling for download and refine buttons */
        .stDownloadButton > button, .stButton > button {
            background: linear-gradient(135deg, #6DD5FA, #2980B9) !important;
            color: white !important;
            padding: 0.6rem 1.2rem !important;
            font-weight: 600 !important;
            border: none !important;
            border-radius: 8px !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
        }

        .stDownloadButton > button:hover, .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15) !important;
            background: linear-gradient(135deg, #2980B9, #6DD5FA) !important;
        }

        .stDownloadButton > button:active, .stButton > button:active {
            transform: translateY(0) !important;
        }

        /* Specific styling for sidebar buttons */
        .stSidebar .stButton > button {
            width: 100% !important;
            margin-top: 1rem !important;
            margin-bottom: 1rem !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Single centered download button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            # Single styled download button
            download_btn = st.download_button(
                label="Download Resume",
                data=pdf_bytes,
                file_name="resume.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="download_pdf"
            )

        # Enhanced PDF viewer with modern floating design
        pdf_display = f"""
            <div class="pdf-container" style="margin-top: 2rem; padding: 1rem;">
                <object
                    data="data:application/pdf;base64,{base64_pdf}"
                    type="application/pdf"
                    width="100%"
                    height="800px"
                    style="border-radius: 8px; transition: all 0.3s ease;">
                    <embed
                        src="data:application/pdf;base64,{base64_pdf}"
                        type="application/pdf"
                        width="100%"
                        height="800px"
                        style="border-radius: 8px;">
                        <iframe
                            src="data:application/pdf;base64,{base64_pdf}"
                            width="100%"
                            height="800px"
                            style="border-radius: 8px;"
                            allowfullscreen>
                            <p>This browser does not support PDF viewing. Please use the download button above.</p>
                        </iframe>
                </object>
            </div>
        """
        st.markdown(pdf_display, unsafe_allow_html=True)

except Exception as e:
    st.error(f"❌ Error generating PDF: {str(e)}")
    if "Permission denied" in str(e):
        st.error("💡 Tip: This error might be related to file permissions. Try using the download button instead.")
    elif "Cannot find" in str(e):
        st.error("💡 Tip: The PDF viewer might not be supported in your browser. Please use the download button.")
    else:
        st.error("💡 Tip: If you can't view the PDF, try using the download button above.")
