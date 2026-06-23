# Deployment Guide - Legal AI Backend

## Environment Variables Setup

Your backend requires the following environment variables to function properly:

### Required Environment Variables

1. **GROQ_API_KEY** - For AI-powered clause explanations
   - Get from: https://console.groq.com/api-keys
   - Without this: Explanations will fail with 500 error

2. **HF_TOKEN** - For Hugging Face model downloads (InLegalBERT)
   - Get from: https://huggingface.co/settings/tokens
   - Without this: Model loading will fail

3. **DATABASE_URL** - Database connection string (auto-set by Render)
   - Already configured to use Render PostgreSQL

### Deploying to Render

#### Step 1: Update Environment Variables on Render Dashboard

1. Go to your Render dashboard: https://dashboard.render.com
2. Select your "legal-ai-backend" service
3. Go to **Settings** → **Environment**
4. Add/update these variables:

```
GROQ_API_KEY = gsk_xxxxxxxxx...  (your actual key)
HF_TOKEN = hf_xxxxxxxxx...       (your actual key)
```

**IMPORTANT:** Copy the exact keys from your `.env` file:
```bash
cat .env | grep -E "GROQ_API_KEY|HF_TOKEN"
```

#### Step 2: Test the API After Deployment

Once deployed, test with:
```bash
curl -X GET https://legal-ai-backend-xhht.onrender.com/

# Should return: {"status":"healthy",...}
```

#### Step 3: Check Logs if Issues Occur

1. Go to Render Dashboard → legal-ai-backend → Logs
2. Look for error messages starting with:
   - `❌ PDF parsing failed`
   - `❌ Clause extraction failed`
   - `❌ Risk analysis failed`
   - `❌ AI explanation failed`

### Troubleshooting 500 Errors

If you see a 500 error from `/analyze`:

1. **Check Render Logs** for the exact error message
2. **Verify Environment Variables** are set:
   ```bash
   # This should show your keys
   curl https://your-backend-url/health  # Check if it's running
   ```

3. **Common Issues:**
   - ❌ GROQ_API_KEY not set → AI explanations will fail
   - ❌ HF_TOKEN not set → Model loading will fail
   - ❌ DATABASE_URL malformed → Database operations will fail
   - ❌ Memory exhausted → Free tier Render might be insufficient

### Fallback Behavior

The code includes fallback mechanisms:
- If GROQ_API_KEY is missing: Returns safe explanation without AI
- If model fails to load: Uses pattern-based risk scoring only
- If database fails: Still returns analysis results

### Local Development

For local testing, ensure your `.env` file has:
```
DATABASE_URL=mysql+pymysql://root:@localhost:3306/legal_ai_db
GROQ_API_KEY=your_key_here
HF_TOKEN=your_token_here
TESSERACT_CMD=/usr/bin/tesseract  # Windows: C:\Program Files\Tesseract-OCR\tesseract.exe
```

Then run:
```bash
source venv/bin/activate  # or .venv\Scripts\activate on Windows
python main.py
```

### API Endpoints

- `GET /` - Health check
- `POST /analyze` - Upload PDF and analyze (may take 30-60 seconds on free tier)
- `GET /contracts` - List all analyzed contracts
- `GET /reports/all` - Get all analysis reports

### Performance Notes

- **Free Tier Render:** Expected analysis time: 30-60 seconds
- **PDF Size:** Recommended < 10MB
- **Model Loading:** First request takes ~10 seconds to load InLegalBERT

### Need Help?

Check the `render.yaml` for service configuration or look at the backend logs in Render dashboard for specific error messages.
