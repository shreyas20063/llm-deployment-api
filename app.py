from flask import Flask, request, jsonify
import os
import json
import requests
import time
import hashlib
from github import Github
import base64
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configuration - SET THESE IN ENVIRONMENT VARIABLES
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME')
YOUR_SECRET = os.environ.get('YOUR_SECRET')  # The secret you submitted in the form
AIPIPE_TOKEN = os.environ.get('AIPIPE_TOKEN')  # AI Pipe token from aipipe.org/login

# Initialize GitHub client
github_client = Github(GITHUB_TOKEN)

# AI Pipe configuration
AIPIPE_BASE_URL = "https://aipipe.org/openrouter/v1/chat/completions"

def verify_secret(request_data):
    """Verify the secret matches"""
    return request_data.get('secret') == YOUR_SECRET

def generate_app_code(brief, checks, attachments):
    """Use Claude via AI Pipe to generate the complete app code"""
    
    # Prepare attachment info for Claude
    attachment_info = ""
    if attachments:
        attachment_info = "\n\nAttachments:\n"
        for att in attachments:
            attachment_info += f"- {att['name']}: {att['url'][:100]}...\n"
    
    # Build the prompt
    prompt = f"""You are an expert web developer. Generate a COMPLETE, PRODUCTION-READY single HTML file for this app.

REQUIREMENTS:
{brief}

EVALUATION CHECKS:
{chr(10).join('- ' + check for check in checks)}

{attachment_info}

CRITICAL REQUIREMENTS:
1. Everything must be in ONE HTML file (inline CSS and JavaScript)
2. Use CDN links for external libraries (Bootstrap, marked, highlight.js, etc.)
3. Handle attachments by decoding data URIs in JavaScript
4. Make it work on GitHub Pages (static hosting)
5. Follow all checks exactly
6. Make it clean, professional, and production-ready
7. Add error handling and user feedback

OUTPUT FORMAT:
Return ONLY the complete HTML code, nothing else. No explanations, no markdown code blocks.
Start directly with <!DOCTYPE html>"""

    # Call AI Pipe with OpenRouter (Claude via OpenRouter)
    response = requests.post(
        AIPIPE_BASE_URL,
        headers={
            "Authorization": f"Bearer {AIPIPE_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "model": "anthropic/claude-sonnet-4.5",  # Claude via OpenRouter
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 8000
        },
        timeout=120
    )
    
    response.raise_for_status()
    result = response.json()
    
    code = result['choices'][0]['message']['content'].strip()
    
    # Clean up if Claude wrapped it in markdown
    if code.startswith('```'):
        code = re.sub(r'^```html\n|^```\n|```$', '', code, flags=re.MULTILINE).strip()
    
    return code

def generate_readme(task_id, brief, checks, repo_url):
    """Generate a professional README.md"""
    
    readme = f"""# {task_id}

## Overview
This is an automated web application generated to fulfill the following requirements.

## Requirements
{brief}

## Evaluation Criteria
{chr(10).join('- ' + check for check in checks)}

## Setup
This is a static web application hosted on GitHub Pages. No installation required.

## Usage
1. Visit the live site: [GitHub Pages URL](https://{GITHUB_USERNAME}.github.io/{task_id}/)
2. The application loads automatically
3. Follow on-screen instructions

## Technical Implementation
- **Frontend**: HTML5, CSS3, JavaScript
- **Libraries**: Bootstrap 5, marked.js (if needed), highlight.js (if needed)
- **Hosting**: GitHub Pages
- **Architecture**: Single-page application with inline styles and scripts

## Code Structure
The application is contained in a single `index.html` file with:
- Inline CSS for styling
- Inline JavaScript for functionality
- CDN-hosted external libraries for enhanced features

## License
MIT License - See LICENSE file for details

## Author
Generated automatically via LLM-assisted development

**Source Code:** https://github.com/{GITHUB_USERNAME}/llm-deployment-api

**Generated App:** {repo_url}
"""
    return readme

def create_github_repo(task_id, html_code, readme_content):
    """Create repo, push code, enable Pages"""
    
    user = github_client.get_user()
    repo_name = f"{task_id}"
    
    # Create repo
    try:
        repo = user.create_repo(
            repo_name,
            description=f"Auto-generated app for {task_id}",
            private=False,
            auto_init=False
        )
    except Exception as e:
        # Repo might exist, try to get it
        repo = user.get_repo(repo_name)
    
    # Add LICENSE
    license_content = """MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""
    
    # Create files
    repo.create_file("index.html", "Initial commit: Add app", html_code)
    repo.create_file("LICENSE", "Add MIT LICENSE", license_content)
    repo.create_file("README.md", "Add README", readme_content)
    
    # Get commit SHA
    commit_sha = repo.get_commits()[0].sha
    
    # Enable GitHub Pages using REST API directly
    print("Enabling GitHub Pages...")
    pages_enabled = False
    for attempt in range(3):
        try:
            # Wait a moment for files to be committed
            if attempt > 0:
                time.sleep(2)
            
            # Use GitHub REST API to enable Pages
            pages_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/pages"
            headers = {
                "Authorization": f"token {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json"
            }
            data = {
                "source": {
                    "branch": "main",
                    "path": "/"
                }
            }
            
            response = requests.post(pages_url, headers=headers, json=data)
            
            if response.status_code == 201:
                print("✓ GitHub Pages enabled successfully")
                pages_enabled = True
                break
            elif response.status_code == 409:
                print("✓ GitHub Pages already enabled")
                pages_enabled = True
                break
            else:
                print(f"Attempt {attempt + 1}/3 failed: HTTP {response.status_code}")
                if attempt == 2:
                    print(f"⚠ Warning: {response.text}")
                    
        except Exception as e:
            print(f"Attempt {attempt + 1}/3 to enable Pages failed: {e}")
            if attempt == 2:
                print("⚠ Warning: Could not enable Pages automatically. Enable manually in repo settings.")
    
    if not pages_enabled:
        print("⚠ GitHub Pages may need manual activation")
    
    return {
        "repo_url": repo.html_url,
        "commit_sha": commit_sha,
        "pages_url": f"https://{GITHUB_USERNAME}.github.io/{repo_name}/"
    }

def notify_evaluator(evaluation_url, payload, max_retries=5):
    """POST to evaluation URL with exponential backoff"""
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                evaluation_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                return {"success": True, "response": response.json()}
            
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
        
        # Exponential backoff: 1, 2, 4, 8, 16 seconds
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)
    
    return {"success": False, "error": "Max retries exceeded"}

@app.route('/api/deploy', methods=['POST'])
def deploy_app():
    """Main endpoint that handles app deployment requests"""
    
    try:
        request_data = request.get_json()
        
        # Verify secret
        if not verify_secret(request_data):
            return jsonify({"error": "Invalid secret"}), 403
        
        # Extract data
        email = request_data['email']
        task = request_data['task']
        round_num = request_data['round']
        nonce = request_data['nonce']
        brief = request_data['brief']
        checks = request_data['checks']
        evaluation_url = request_data['evaluation_url']
        attachments = request_data.get('attachments', [])
        
        print("=" * 70)
        print(f"📥 Processing request for {email}, task: {task}, round: {round_num}")
        print("=" * 70)
        
        # Generate app code using LLM
        print("Generating app code...")
        html_code = generate_app_code(brief, checks, attachments)
        
        # Generate README
        print("Generating README...")
        readme = generate_readme(task, brief, checks, f"https://github.com/{GITHUB_USERNAME}/{task}")
        
        # Create GitHub repo and deploy
        print("Creating GitHub repo and deploying...")
        github_info = create_github_repo(task, html_code, readme)
        
        print(f"✓ Repo created: {github_info['repo_url']}")
        print(f"✓ Commit SHA: {github_info['commit_sha']}")
        print(f"✓ Pages URL: {github_info['pages_url']}")
        
        # Prepare notification payload
        notification = {
            "email": email,
            "task": task,
            "round": round_num,
            "nonce": nonce,
            "repo_url": github_info['repo_url'],
            "commit_sha": github_info['commit_sha'],
            "pages_url": github_info['pages_url']
        }
        
        # Notify evaluator
        print("Notifying evaluator...")
        result = notify_evaluator(evaluation_url, notification)
        
        if result.get('success'):
            print(f"✓ Evaluator notified successfully")
        else:
            print(f"⚠ Evaluator notification failed: {result.get('error')}")
        
        print("=" * 70)
        print(f"✅ Request completed successfully for {task}")
        print("=" * 70)
        print()
        
        return jsonify({
            "status": "success",
            "repo_url": github_info['repo_url'],
            "pages_url": github_info['pages_url'],
            "evaluator_response": result
        }), 200
        
    except Exception as e:
        print("=" * 70)
        print(f"❌ ERROR: {str(e)}")
        print("=" * 70)
        print()
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": time.time()}), 200

if __name__ == '__main__':
    # Check environment variables
    if not all([GITHUB_TOKEN, GITHUB_USERNAME, YOUR_SECRET, AIPIPE_TOKEN]):
        print("ERROR: Missing environment variables!")
        print("Required: GITHUB_TOKEN, GITHUB_USERNAME, YOUR_SECRET, AIPIPE_TOKEN")
        exit(1)
    
    print("=" * 70)
    print("🚀 LLM Deployment API Starting...")
    print("=" * 70)
    print(f"GitHub Username: {GITHUB_USERNAME}")
    print(f"Secret: {'*' * len(YOUR_SECRET)} (configured)")
    print(f"AI Pipe Token: {'*' * 20}... (configured)")
    print(f"GitHub Token: {'*' * 20}... (configured)")
    print("=" * 70)
    print()
    
    app.run(host='0.0.0.0', port=8000)
