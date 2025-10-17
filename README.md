# LLM Code Deployment Project


Automated app generation and deployment system that receives requests, generates code using Claude AI, deploys to GitHub Pages, and notifies evaluators.

## 🎯 What This Does

1. **Receives** JSON requests with app briefs via API endpoint
2. **Generates** complete HTML applications using Claude AI
3. **Creates** GitHub repositories with code + LICENSE + README
4. **Deploys** to GitHub Pages automatically
5. **Notifies** evaluation API with repo details
6. **Handles** Round 2 update requests seamlessly

## 📦 Quick Start

### Prerequisites
- Python 3.8+
- GitHub account with Personal Access Token
- AI Pipe API token
- Your secret from Google Form submission

### Installation

```bash
# Run the setup script
bash setup.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Configuration

1. Copy `.env.example` to `.env`
2. Fill in your credentials:
   ```
   GITHUB_TOKEN=ghp_your_token_here
   GITHUB_USERNAME=your_username
   YOUR_SECRET=your_secret_from_form
   AIPIPE_TOKEN=your_aipipe_token_here
   ```

### Running Locally

```bash
python app.py
```

Server runs on `http://localhost:5000`

### Testing

```bash
# Test the API
python test_api.py

# Or with curl
curl -X POST http://localhost:5000/api/deploy \
  -H "Content-Type: application/json" \
  -d @test_request.json
```

## 🚀 Deployment

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed deployment instructions.

### Quick Deploy to Render

1. Push code to GitHub
2. Connect repo on Render.com
3. Set environment variables
4. Deploy!

Your API will be at: `https://your-app.onrender.com`

## 📋 API Endpoints

### POST /api/deploy

Accepts deployment requests and handles both Round 1 and Round 2.

**Request:**
```json
{
  "email": "student@example.com",
  "secret": "your_secret",
  "task": "task-id-123",
  "round": 1,
  "nonce": "unique-nonce",
  "brief": "Create an app that...",
  "checks": ["Check 1", "Check 2"],
  "evaluation_url": "https://eval.example.com/notify",
  "attachments": []
}
```

**Response:**
```json
{
  "status": "success",
  "repo_url": "https://github.com/user/repo",
  "pages_url": "https://user.github.io/repo/",
  "evaluator_response": {...}
}
```

### GET /health

Health check endpoint.

## 📁 Project Structure

```
.
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore rules
├── Procfile              # Deployment configuration
├── test_api.py           # API testing script
├── test_request.json     # Sample test request
├── setup.sh              # Quick setup script
├── DEPLOYMENT_GUIDE.md   # Detailed deployment guide
└── README.md             # This file
```

## 🔧 How It Works

1. **Request Reception**: API endpoint receives JSON POST request
2. **Secret Verification**: Validates request secret matches configured secret
3. **Code Generation**: Uses Claude AI to generate complete HTML application
4. **README Generation**: Creates professional README.md for the repo
5. **GitHub Operations**: Creates repo, pushes files (index.html, LICENSE, README.md)
6. **Pages Deployment**: Enables GitHub Pages on the repo
7. **Evaluation Notification**: POSTs repo details to evaluation_url
8. **Round 2 Handling**: Same process for update requests

## 🛠️ Technologies

- **Backend**: Flask (Python web framework)
- **AI**: Claude via AI Pipe for code generation
- **GitHub**: PyGithub for repository automation
- **Deployment**: Gunicorn for production server
- **Hosting**: Render/Railway/Vercel compatible


## 🐛 Troubleshooting

**Common Issues:**

1. **Secret Mismatch (403)**
   - Verify YOUR_SECRET in .env matches Google Form submission
   - Check for extra spaces or quotes

2. **GitHub API Errors**
   - Ensure GITHUB_TOKEN has correct scopes (repo, delete_repo)
   - Check rate limits: https://github.com/settings/tokens

3. **LLM Generation Failures**
   - Verify AIPIPE_TOKEN is valid
   - Check API credits/limits
   - Review logs for specific errors

4. **Pages Not Loading**
   - Wait 2-3 minutes after repo creation
   - Check repo Settings → Pages
   - Ensure main branch is selected

## 📊 Monitoring

**Check Logs:**
- Render: Dashboard → Logs tab
- Railway: Project → Deployment → View logs
- Local: Terminal output

**Key Metrics:**
- Request processing time: 30-90 seconds
- GitHub Pages deployment: 2-3 minutes
- Total workflow: <10 minutes (well within deadline)

## 🎯 Success Checklist

- [ ] Environment variables configured
- [ ] Local testing successful
- [ ] Deployed to production
- [ ] API endpoint publicly accessible
- [ ] Test request completes successfully
- [ ] GitHub repos created correctly
- [ ] GitHub Pages accessible
- [ ] Evaluation notifications working
- [ ] Submitted to Google Form

## 📞 Support

For issues:
1. Check DEPLOYMENT_GUIDE.md
2. Review logs for errors
3. Test with curl/test_api.py
4. Verify all credentials
5. Check GitHub API limits


## 📄 License

This project generates apps with MIT License.

---
