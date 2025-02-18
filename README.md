# Personal AI Resume Optimizer

An AI-powered resume optimization tool built with Streamlit that helps tailor your resume for specific job descriptions using multiple AI models (Kimi, OpenAI, and Deepseek).

## Features
- Real-time resume optimization
- Multiple AI model support (Kimi, OpenAI, Deepseek)
- PDF generation and preview
- Customizable design settings
- Section-specific refinements

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/Personal-Ai-Resume-Optimizer.git
   cd Personal-Ai-Resume-Optimizer
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure API keys:

   For local development:
   - Create `.streamlit/secrets.toml` with:
     ```toml
     OPENAI_API_KEY = "your-openai-key"
     KIMI_API_KEY = "your-kimi-key"
     DEEPSEEK_API_KEY = "your-deepseek-key"
     ```

   For deployment:
   - Add these secrets in your Streamlit Cloud dashboard

4. Run the app:
   ```bash
   streamlit run resume.py
   ```

## Environment Variables

Required API keys:
- `OPENAI_API_KEY` - OpenAI API key
- `KIMI_API_KEY` - Kimi API key  
- `DEEPSEEK_API_KEY` - Deepseek API key

Optional:
- `DEEPSEEK_API_URL` - Custom Deepseek API endpoint (defaults to official endpoint)

## Security Note

Never commit API keys or secrets to version control. The `.gitignore` file is configured to prevent this, but always double check before committing. 