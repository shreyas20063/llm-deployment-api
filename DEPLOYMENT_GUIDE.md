# LLM Code Deployment Project - Complete Guide

## 🚀 QUICK START (8 HOUR TIMELINE)

### ⏰ HOUR 1-2: SETUP

#### Step 1: Get Your Keys (30 mins)

**GitHub Personal Access Token:**
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo`, `delete_repo`, `admin:repo_hook`
4. Copy the token: `ghp_xxxxxxxxxxxx`

**AI Pipe API Token:**
1. Go to https://aipipe.org/login
2. Create or copy your OpenRouter token
3. Copy: `eyJhbGciOi...`

**Your Secret:**
- Use the same secret you submitted in the Google Form
- Example: `my_super_secret_key_2025`

#### Step 2: Clone & Setup Environment (15 mins)

```bash
# Create project directory
mkdir llm-deployment
cd llm-deployment

# Copy all files (app.py, requirements.txt, .env.example)
# Then create your .env file
cp .env.example .env
nano .env  # Edit with your actual keys
```

Your `.env` should look like:
```
GITHUB_TOKEN=ghp_abc123xyz...
GITHUB_USERNAME=yourusername
YOUR_SECRET=my_super_secret_key_2025
AIPIPE_TOKEN=eyJhbGciOi...
```

#### Step 3: Install Dependencies (15 mins)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

#### Step 4: Test Locally (30 mins)

```bash
# Run the server
python app.py
```

Test with curl:
```bash
curl -X POST http://localhost:5000/api/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "secret": "my_super_secret_key_2025",
    "task": "test-task-123",
    "round": 1,
    "nonce": "test-nonce-456",
    "brief": "Create a simple HTML page that displays Hello World in a h1 tag with Bootstrap styling",
    "checks": [
      "Page displays Hello World",
      "Bootstrap is loaded"
    ],
    "evaluation_url": "https://httpbin.org/post",
    "attachments": []
  }'
```

---

### ⏰ HOUR 3-4: DEPLOY TO PRODUCTION

#### Option A: Deploy to Render.com (RECOMMENDED - FREE & EASY)

**Step 1: Push to GitHub (10 mins)**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/llm-deployment-api.git
git push -u origin main
```

**Step 2: Deploy on Render (20 mins)**
1. Go to https://render.com/
2. Sign up/Login with GitHub
3. Click "New +" → "Web Service"
4. Connect your `llm-deployment-api` repo
5. Settings:
   - **Name**: `llm-deployment-api`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: Free
6. Add Environment Variables:
   - `GITHUB_TOKEN`
   - `GITHUB_USERNAME`
   - `YOUR_SECRET`
   - `AIPIPE_TOKEN`
7. Click "Create Web Service"
8. Wait 5-10 mins for deployment
9. Your API URL: `https://llm-deployment-api.onrender.com`

#### Option B: Deploy to Railway.app (ALTERNATIVE)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize and deploy
railway init
railway up
railway open

# Add environment variables in Railway dashboard
```

Your API URL: `https://your-app.up.railway.app`

#### Option C: Deploy to Vercel (Requires serverless adaptation)

---

### ⏰ HOUR 5-6: TEST & MONITOR

#### Test Your Live API

```bash
# Replace with your actual API URL
export API_URL="https://llm-deployment-api.onrender.com"

curl -X POST $API_URL/api/deploy \
  -H "Content-Type: application/json" \
  -d @test_request.json
```

Create `test_request.json`:
```json
{
  "email": "your_email@example.com",
  "secret": "my_super_secret_key_2025",
  "task": "sum-of-sales-abc12",
  "round": 1,
  "nonce": "test-12345",
  "brief": "Create a Bootstrap page that displays a heading 'Sales Dashboard' and a button that says 'Load Data'",
  "checks": [
    "Page has Bootstrap loaded",
    "Heading exists",
    "Button exists"
  ],
  "evaluation_url": "https://httpbin.org/post",
  "attachments": []
}
```

#### Monitor Logs

**On Render:**
- Go to your service dashboard
- Click "Logs" tab
- Watch real-time logs

**Troubleshooting:**
- If 500 error: Check logs for missing env vars
- If 403 error: Secret doesn't match
- If timeout: Increase timeout in Render settings (Services → Settings → Health Check)

---

### ⏰ HOUR 7: SUBMIT TO GOOGLE FORM

1. Go to the Google Form provided by instructors
2. Fill in:
   - **Email**: Your student email
   - **API Endpoint**: `https://your-api-url.onrender.com/api/deploy`
   - **Secret**: `my_super_secret_key_2025`
   - **GitHub Username**: Your GitHub username
3. Submit!

---

### ⏰ HOUR 8: HANDLE ROUND 2

**The same API endpoint handles Round 2 automatically!**

When you receive a Round 2 request (with `"round": 2`):
1. Your API verifies the secret
2. Generates updated code based on new brief
3. Updates the same GitHub repo (or creates new commit)
4. Reposts to evaluation_url with round: 2

**No additional code needed!** The existing system handles it.

---

## 🔧 TROUBLESHOOTING

### Common Issues

**1. GitHub Pages Not Loading**
- Wait 2-3 minutes after repo creation
- Check Settings → Pages in your repo
- Ensure "main" branch is selected

**2. LLM Generation Failures**
- Check AIPIPE_TOKEN is valid
- Ensure you have API credits
- Check logs for specific errors

**3. Evaluation POST Fails**
- Check evaluation_url is accessible
- Verify JSON payload structure
- Look for 200 response code

**4. Secret Mismatch**
- Double-check YOUR_SECRET matches form submission
- No extra spaces or quotes
- Case-sensitive!

### Debug Mode

Add this to app.py for verbose logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 📊 PROJECT CHECKLIST

- [ ] GitHub token with correct permissions
- [ ] AI Pipe token with credits
- [ ] Secret matches Google Form submission
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Local testing successful
- [ ] Deployed to Render/Railway
- [ ] Environment variables set in deployment
- [ ] API endpoint accessible publicly
- [ ] Test request completes successfully
- [ ] GitHub repo created with LICENSE
- [ ] GitHub Pages enabled and accessible
- [ ] README.md generated
- [ ] Submitted to Google Form
- [ ] Ready for Round 2 requests

---

## 🎯 EXPECTED BEHAVIOR

**Request Flow:**
1. POST arrives at `/api/deploy`
2. Secret verified ✓
3. Claude generates HTML code ✓
4. GitHub repo created ✓
5. Files pushed (index.html, LICENSE, README.md) ✓
6. GitHub Pages enabled ✓
7. Notification sent to evaluation_url ✓
8. Response returned to requester ✓

**Timing:**
- Total processing: 30-90 seconds
- Well within the 10-minute deadline

---

## 💡 TIPS FOR SUCCESS

1. **Test Early**: Don't wait to deploy. Test locally first, then deploy ASAP.
2. **Monitor Logs**: Keep logs open during the evaluation period.
3. **Have Backup Keys**: Keep extra GitHub tokens and API keys ready.
4. **Check Email**: Instructors might send multiple tasks.
5. **Don't Panic**: The system auto-retries on failures.

---

## 📞 EMERGENCY CONTACTS

If things break:
1. Check logs first
2. Test evaluation_url manually with curl
3. Verify all environment variables
4. Restart the service
5. Check GitHub API rate limits

---

## 🎓 WHAT THE CODE DOES

**app.py** - Main Flask server:
- `/api/deploy` - Receives JSON requests
- Verifies secret against YOUR_SECRET
- Calls Claude API to generate HTML
- Creates GitHub repo with PyGithub
- Pushes code + LICENSE + README
- Enables GitHub Pages
- POSTs to evaluation_url
- Returns success response

**Key Functions:**
- `verify_secret()` - Checks if secret matches
- `generate_app_code()` - Uses Claude to write HTML
- `generate_readme()` - Creates professional README
- `create_github_repo()` - Automates GitHub operations
- `notify_evaluator()` - POSTs with retry logic

---

## 🚀 YOU'RE READY!

Follow the timeline, test thoroughly, and you'll crush this project.

**khaana Kab?** team - let's go! 🔥
