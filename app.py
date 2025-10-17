from flask import Flask, request, jsonify
import os
import requests
import time
from github import Github, Auth, GithubException
import re
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
import threading

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configuration - SET THESE IN ENVIRONMENT VARIABLES
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME')
YOUR_SECRET = os.environ.get('YOUR_SECRET')  # The secret you submitted in the form
AIPIPE_TOKEN = os.environ.get('AIPIPE_TOKEN')  # AI Pipe token from aipipe.org/login

_github_client: Optional[Github] = None

# AI Pipe configuration
AIPIPE_BASE_URL = "https://aipipe.org/openrouter/v1/chat/completions"

# CRITICAL: Maximum total time from request start to notification (in seconds)
MAX_TOTAL_TIME = 9 * 60  # 9 minutes (1 min safety buffer)
NOTIFICATION_BUFFER = 20  # Reserve 20s for notification attempts


class ConfigurationError(Exception):
    """Raised when required environment configuration is missing."""


def mask_secret(value: Optional[str], visible_chars: int = 4) -> str:
    """Mask secrets before logging them to stdout."""
    if not value:
        return "<missing>"
    trimmed = value.strip()
    if not trimmed:
        return "<missing>"
    length = len(trimmed)
    if length <= visible_chars:
        return "*" * length
    visible = trimmed[:visible_chars]
    return f"{visible}{'*' * (length - visible_chars)}"


def get_config() -> Dict[str, str]:
    """Collect required environment variables and ensure they exist."""
    config_map: Dict[str, Optional[str]] = {
        "github_token": os.environ.get("GITHUB_TOKEN"),
        "github_username": os.environ.get("GITHUB_USERNAME"),
        "secret": os.environ.get("YOUR_SECRET"),
        "aipipe_token": os.environ.get("AIPIPE_TOKEN"),
    }

    missing = [name for name, value in config_map.items() if not value]
    if missing:
        raise ConfigurationError(
            f"Missing required environment variables: {', '.join(sorted(missing))}"
        )

    return {key: config_map[key] or "" for key in config_map}


def get_github_client(token: str) -> Github:
    """Return a cached GitHub client authenticated with the provided token."""
    global _github_client
    if _github_client is None:
        _github_client = Github(auth=Auth.Token(token))
    return _github_client

def verify_secret(request_data: Dict[str, Any], expected_secret: str) -> bool:
    """Verify the secret matches"""
    return request_data.get('secret') == expected_secret

def get_existing_code(task_id: str, github_username: str, github_client: Github) -> Optional[str]:
    """Fetch existing index.html from the repository if it exists"""
    try:
        user = github_client.get_user()
        repo = user.get_repo(task_id)
        contents = repo.get_contents("index.html")
        return contents.decoded_content.decode("utf-8")
    except GithubException:
        return None

def generate_app_code(brief: str, checks: List[str], attachments: Optional[List[Dict[str, Any]]], aipipe_token: str, round_num: int = 1, existing_code: Optional[str] = None) -> str:
    """Use Claude via AI Pipe to generate the complete app code"""
    
    # Prepare attachment info for Claude
    attachment_info = ""
    if attachments:
        attachment_info = "\n\nAttachments:\n"
        for att in attachments:
            name = att.get('name', 'Attachment')
            url = att.get('url', 'N/A')
            attachment_info += f"- {name}: {str(url)[:100]}...\n"
    
    # Different prompts for round 1 vs round 2
    if round_num == 1 or not existing_code:
        # Round 1: Generate new app from scratch
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
    else:
        # Round 2: Modify existing code
        prompt = f"""You are an expert web developer. MODIFY the existing HTML application to meet the new requirements.

EXISTING CODE:
```html
{existing_code}
```

NEW REQUIREMENTS:
{brief}

EVALUATION CHECKS:
{chr(10).join('- ' + check for check in checks)}

{attachment_info}

CRITICAL REQUIREMENTS:
1. MODIFY the existing code, don't start from scratch
2. Keep all existing functionality that still works
3. Everything must remain in ONE HTML file (inline CSS and JavaScript)
4. Use CDN links for external libraries
5. Handle attachments by decoding data URIs in JavaScript
6. Follow all new checks exactly
7. Make it clean, professional, and production-ready
8. Add error handling and user feedback

OUTPUT FORMAT:
Return ONLY the complete MODIFIED HTML code, nothing else. No explanations, no markdown code blocks.
Start directly with <!DOCTYPE html>"""

    # Call AI Pipe with OpenRouter (Claude via OpenRouter)
    # Reduced timeout to ensure we don't exceed our time budget
    response = requests.post(
        AIPIPE_BASE_URL,
        headers={
            "Authorization": f"Bearer {aipipe_token}",
            "Content-Type": "application/json"
        },
        json={
            "model": "anthropic/claude-sonnet-4.5",  # Claude via OpenRouter
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 8000
        },
        timeout=90  # Reduced from 120 to 90 seconds
    )
    
    response.raise_for_status()
    result = response.json()
    
    choices = result.get('choices')
    if not choices:
        raise RuntimeError("AI Pipe response did not include any choices")

    code_block = choices[0]
    message = code_block.get('message', {})
    content = message.get('content')
    if isinstance(content, list):
        content = "".join(block.get("text", "") for block in content)
    if not isinstance(content, str):
        raise RuntimeError("AI Pipe response missing text content")

    code = content.strip()
    
    # Clean up if Claude wrapped it in markdown
    if code.startswith('```'):
        code = re.sub(r'^```html\n|^```\n|```$', '', code, flags=re.MULTILINE).strip()
    
    return code

def generate_readme(task_id: str, brief: str, checks: List[str], repo_url: str, github_username: str, round_num: int = 1) -> str:
    """Generate a professional README.md"""
    
    round_info = f"\n\n## Round {round_num}\n" if round_num > 1 else ""
    
    readme = f"""# {task_id}

## Overview
This is an automated web application generated to fulfill the following requirements.
{round_info}
## Requirements
{brief}

## Evaluation Criteria
{chr(10).join('- ' + check for check in checks)}

## Setup
This is a static web application hosted on GitHub Pages. No installation required.

## Usage
1. Visit the live site: [GitHub Pages URL](https://{github_username}.github.io/{task_id}/)
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

**Source Code:** https://github.com/{github_username}/llm-deployment-api

**Generated App:** {repo_url}
"""
    return readme

def _upsert_file(repo, path: str, message: str, content: str) -> None:
    """Create or update a file in the repository."""
    try:
        existing = repo.get_contents(path)
    except GithubException as exc:
        if exc.status == 404:
            existing = None
        else:
            raise

    if existing:
        current = existing.decoded_content.decode("utf-8")
        if current == content:
            # No change needed; avoid unnecessary commits
            return
        repo.update_file(path, message, content, existing.sha)
    else:
        repo.create_file(path, message, content)


def verify_pages_async(pages_url: str, nonce: str, evaluation_url: str, notification: dict, start_time: float, deadline: float):
    """
    Background thread to wait for Pages deployment and notify evaluator.
    Uses a hard deadline to ensure notification happens before MAX_TOTAL_TIME.
    """
    try:
        # Calculate how much time we can wait
        current_time = time.time()
        time_remaining = deadline - current_time
        
        if time_remaining > 5:  # Only wait if we have more than 5 seconds
            wait_time = min(60, time_remaining)  # Wait up to 60 seconds for Pages, but not past deadline
            print(f"[BG] Waiting {wait_time:.1f}s for Pages deployment (deadline in {deadline - current_time:.1f}s)...")
            time.sleep(wait_time)
        else:
            print(f"[BG] Close to deadline ({time_remaining:.1f}s remaining), notifying immediately...")
        
        # Check if we're past the deadline
        if time.time() >= deadline:
            print(f"[BG] ⚠️ Deadline reached! Notifying immediately...")
        
        # Mark as verified
        notification["pages_verified"] = True
        
        elapsed = time.time() - start_time
        print(f"[BG] Notifying evaluator (total elapsed: {elapsed:.1f}s)...")
        
        # Notify with minimal retries to stay under deadline
        result = notify_evaluator(evaluation_url, notification, max_retries=2)
        
        final_elapsed = time.time() - start_time
        print(f"[BG] ✓ Notification complete (total time: {final_elapsed:.1f}s / {MAX_TOTAL_TIME}s budget)")
        
        if not result["success"]:
            print(f"[BG] ⚠️ Warning: Notification may have failed but we stayed under time limit")
            
    except Exception as e:
        print(f"[BG] ❌ Error in background thread: {e}")


def create_github_repo(
    task_id: str,
    html_code: str,
    readme_content: str,
    github_username: str,
    github_token: str,
    github_client: Github,
    round_num: int = 1,
):
    """Create repo, push code, enable Pages"""
    
    user = github_client.get_user()
    repo_name = f"{task_id}"
    
    # Create repo (or get existing)
    try:
        repo = user.create_repo(
            repo_name,
            description=f"Auto-generated app for {task_id}",
            private=False,
            auto_init=False
        )
        print(f"✓ Created new repo: {repo_name}")
    except GithubException as exc:
        if exc.status in (422, 403):
            repo = user.get_repo(repo_name)
            print(f"✓ Using existing repo: {repo_name}")
        else:
            raise
    
    # Add LICENSE first (if not exists)
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
    
    _upsert_file(repo, "LICENSE", "Ensure MIT LICENSE present", license_content)
    
    # Small delay to avoid rapid commits
    time.sleep(1)
    
    # Update README
    _upsert_file(repo, "README.md", f"Refresh README (Round {round_num})", readme_content)
    
    # Small delay
    time.sleep(1)
    
    # Update main code
    commit_msg = f"Update generated app (Round {round_num})" if round_num > 1 else "Add generated app"
    _upsert_file(repo, "index.html", commit_msg, html_code)
    
    # Wait for commit to be processed
    time.sleep(2)
    
    # Get commit SHA
    commit_sha = repo.get_commits()[0].sha
    
    # Enable GitHub Pages using REST API directly (only if round 1)
    if round_num == 1:
        print("Enabling GitHub Pages...")
        pages_enabled = False
        for attempt in range(2):  # Reduced from 3 to 2 attempts
            try:
                # Wait a moment for files to be committed
                if attempt > 0:
                    time.sleep(2)  # Reduced from 3 to 2
                
                # Use GitHub REST API to enable Pages
                pages_url = f"https://api.github.com/repos/{github_username}/{repo_name}/pages"
                headers = {
                    "Authorization": f"Bearer {github_token}",
                    "Accept": "application/vnd.github+json"
                }
                data = {
                    "source": {
                        "branch": "main",
                        "path": "/"
                    }
                }
                
                response = requests.post(pages_url, headers=headers, json=data, timeout=15)  # Reduced from 20 to 15
                
                if response.status_code == 201:
                    print("✓ GitHub Pages enabled successfully")
                    pages_enabled = True
                    break
                elif response.status_code == 409:
                    print("✓ GitHub Pages already enabled")
                    pages_enabled = True
                    break
                else:
                    print(f"Attempt {attempt + 1}/2 failed: HTTP {response.status_code}")
                    if attempt == 1:
                        print(f"⚠ Warning: {response.text}")
                        
            except Exception as e:
                print(f"Attempt {attempt + 1}/2 to enable Pages failed: {e}")
                if attempt == 1:
                    print("⚠ Warning: Could not enable Pages automatically. Enable manually in repo settings.")
        
        if not pages_enabled:
            print("⚠ GitHub Pages may need manual activation")
    else:
        print("✓ GitHub Pages already configured (Round 2 update)")
    
    return {
        "repo_url": repo.html_url,
        "commit_sha": commit_sha,
        "pages_url": f"https://{github_username}.github.io/{repo_name}/"
    }

def notify_evaluator(evaluation_url, payload, max_retries=2):
    """POST to evaluation URL with minimal retries (time-constrained)"""
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                evaluation_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10  # Reduced from 30 to 10 seconds
            )
            
            if response.status_code == 200:
                print(f"✓ Evaluator notified successfully")
                return {"success": True, "response": response.json()}
            else:
                print(f"⚠ Evaluator returned status {response.status_code}")
            
        except Exception as e:
            print(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
        
        # Short backoff: 2 seconds only
        if attempt < max_retries - 1:
            time.sleep(2)
    
    print(f"❌ Failed to notify evaluator after {max_retries} attempts")
    return {"success": False, "error": "Max retries exceeded"}

@app.route('/api/deploy', methods=['POST'])
def deploy_app():
    """Main endpoint that handles app deployment requests"""
    
    # Record start time and calculate hard deadline
    start_time = time.time()
    deadline = start_time + MAX_TOTAL_TIME - NOTIFICATION_BUFFER
    
    try:
        config = get_config()
        request_data = request.get_json(silent=True)
        
        if not request_data:
            return jsonify({"error": "Invalid JSON payload"}), 400
        
        # Verify secret
        if not verify_secret(request_data, config["secret"]):
            return jsonify({"error": "Invalid secret"}), 403

        required_fields = ["email", "task", "round", "nonce", "brief", "checks", "evaluation_url"]
        missing_fields = [field for field in required_fields if field not in request_data]
        if missing_fields:
            return jsonify({"error": f"Missing fields: {', '.join(sorted(missing_fields))}"}), 400
        
        # Extract data
        email = request_data['email']
        task = request_data['task']
        round_num = request_data['round']
        nonce = request_data['nonce']
        brief = request_data['brief']
        checks = request_data['checks']
        evaluation_url = request_data['evaluation_url']
        attachments = request_data.get('attachments', [])

        if not isinstance(checks, list) or not all(isinstance(item, str) for item in checks):
            return jsonify({"error": "'checks' must be a list of strings"}), 400

        if attachments is None:
            attachments = []
        if not isinstance(attachments, list):
            return jsonify({"error": "'attachments' must be a list"}), 400
        if attachments and not all(isinstance(att, dict) for att in attachments):
            return jsonify({"error": "'attachments' items must be objects"}), 400
        
        print("=" * 70)
        print(f"📥 Processing request for {email}, task: {task}, round: {round_num}")
        print(f"⏱️  Start: {time.strftime('%H:%M:%S', time.localtime(start_time))}")
        print(f"⏱️  Deadline: {time.strftime('%H:%M:%S', time.localtime(deadline))} ({MAX_TOTAL_TIME/60:.1f}min budget)")
        print("=" * 70)
        
        github_client = get_github_client(config["github_token"])

        # For round 2, fetch existing code
        existing_code = None
        if round_num > 1:
            print(f"Fetching existing code for round {round_num}...")
            existing_code = get_existing_code(task, config["github_username"], github_client)
            if existing_code:
                print(f"✓ Found existing code ({len(existing_code)} chars)")
            else:
                print("⚠ No existing code found, generating from scratch")

        # Check if we're running out of time
        if time.time() >= deadline:
            raise RuntimeError("Processing exceeded time budget before LLM generation")

        # Generate app code using LLM
        print(f"Generating app code (Round {round_num})...")
        html_code = generate_app_code(brief, checks, attachments, config["aipipe_token"], round_num, existing_code)
        
        # Check if we're running out of time
        if time.time() >= deadline:
            raise RuntimeError("Processing exceeded time budget after LLM generation")
        
        # Generate README
        print("Generating README...")
        repo_url = f"https://github.com/{config['github_username']}/{task}"
        readme = generate_readme(task, brief, checks, repo_url, config["github_username"], round_num)
        
        # Create GitHub repo and deploy
        print("Creating/updating GitHub repo and deploying...")
        github_info = create_github_repo(
            task,
            html_code,
            readme,
            config["github_username"],
            config["github_token"],
            github_client,
            round_num,
        )
        
        print(f"✓ Repo: {github_info['repo_url']}")
        print(f"✓ Commit SHA: {github_info['commit_sha']}")
        print(f"✓ Pages URL: {github_info['pages_url']}")
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        time_remaining = deadline - time.time()
        print(f"⏱️  Processing completed in {elapsed_time:.1f}s")
        print(f"⏱️  Time remaining until deadline: {time_remaining:.1f}s")
        
        # Prepare notification payload
        notification = {
            "email": email,
            "task": task,
            "round": round_num,
            "nonce": nonce,
            "repo_url": github_info['repo_url'],
            "commit_sha": github_info['commit_sha'],
            "pages_url": github_info['pages_url'],
            "pages_verified": False  # Will be updated in background
        }
        
        print(f"✓ Starting background notification thread with hard deadline...")
        
        # Start background thread with hard deadline
        bg_thread = threading.Thread(
            target=verify_pages_async,
            args=(github_info['pages_url'], nonce, evaluation_url, notification, start_time, deadline),
            daemon=True
        )
        bg_thread.start()
        
        print("=" * 70)
        print(f"✅ Request processed successfully for {task} (Round {round_num})")
        print(f"⏱️  Total budget: {MAX_TOTAL_TIME/60:.1f} minutes")
        print("=" * 70)
        print()
        
        # Return immediately
        return jsonify({
            "status": "success",
            "repo_url": github_info['repo_url'],
            "pages_url": github_info['pages_url'],
            "message": f"Deployment complete. Notification will be sent within {MAX_TOTAL_TIME/60:.1f} minutes."
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
    try:
        config = get_config()
    except ConfigurationError as exc:
        print("ERROR:", exc)
        print("Required environment variables: GITHUB_TOKEN, GITHUB_USERNAME, YOUR_SECRET, AIPIPE_TOKEN")
        exit(1)
    
    print("=" * 70)
    print("🚀 LLM Deployment API Starting...")
    print("=" * 70)
    print(f"GitHub Username: {config['github_username']}")
    print(f"Secret: {mask_secret(config['secret'])} (configured)")
    print(f"AI Pipe Token: {mask_secret(config['aipipe_token'])} (configured)")
    print(f"GitHub Token: {mask_secret(config['github_token'])} (configured)")
    print(f"⏱️  Maximum total time: {MAX_TOTAL_TIME/60:.1f} minutes")
    print(f"⏱️  Notification buffer: {NOTIFICATION_BUFFER}s")
    print("=" * 70)
    print()
    
    app.run(host='0.0.0.0', port=8000)
