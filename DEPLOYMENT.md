# GitHub Deployment Guide

## Prerequisites
- GitHub account
- Git installed on your system
- Project ready to deploy

## Step-by-Step Deployment

### 1. Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `enterprise-scraper` (or your choice)
3. Description: "Enterprise Web Scraper with AI-powered monitoring and n8n integration"
4. Choose **Public** or **Private**
5. **DO NOT** initialize with README (we have one)
6. Click "Create repository"

### 2. Initialize Local Git Repository

Open terminal in your project directory (`c:\Scraper`) and run:

```bash
# Initialize git
git init

# Add all files (respects .gitignore)
git add .

# Create first commit
git commit -m "Initial commit: Enterprise Web Scraper with AI features"
```

### 3. Connect to GitHub

Replace `yourusername` with your actual GitHub username:

```bash
# Add remote repository
git remote add origin https://github.com/yourusername/enterprise-scraper.git

# Verify remote
git remote -v
```

### 4. Push to GitHub

```bash
# Push to main branch
git branch -M main
git push -u origin main
```

### 5. Verify Deployment

1. Go to your GitHub repository URL
2. Check that all files are there
3. Verify README.md displays properly
4. Ensure sensitive files are NOT uploaded:
   - ✅ NO `monitor.db`
   - ✅ NO `venv/` folder
   - ✅ NO API keys

## What Gets Uploaded

### ✅ Included Files
- `*.py` - All Python code
- `templates/` - HTML templates
- `static/*.css, *.js` - Frontend assets
- `*.md` - Documentation
- `requirements.txt` - Dependencies
- `.gitignore` - Git configuration
- `run.bat` - Startup scripts

### ❌ Excluded Files (via .gitignore)
- `venv/` - Virtual environment
- `*.db` - Database files
- `__pycache__/` - Python cache
- `static/screenshots/` - Screenshots (optional)
- API keys and secrets

## Repository Settings (Optional but Recommended)

### 1. Add Topics
Go to repository → About → Settings → Add topics:
- `web-scraping`
- `monitoring`
- `ai`
- `rag`
- `playwright`
- `n8n`
- `flask`

### 2. Add Description
"Enterprise-grade web scraper with AI-powered change detection, RAG chat, headless browsing, and n8n integration"

### 3. Enable Issues
Settings → Features → Check "Issues"

### 4. Create Releases (Optional)
1. Go to "Releases" → "Create a new release"
2. Tag: `v1.0.0`
3. Title: "Enterprise Scraper v1.0"
4. Description: List major features

## Future Updates

To push future changes:

```bash
# Check status
git status

# Add modified files
git add .

# Commit changes
git commit -m "Description of changes"

# Push to GitHub
git push
```

## Common Git Commands

```bash
# View commit history
git log --oneline

# Create new branch
git checkout -b feature-name

# Switch branches
git checkout main

# Pull latest changes
git pull

# View differences
git diff
```

## Cloning (For Others)

Others can clone your repository:

```bash
git clone https://github.com/yourusername/enterprise-scraper.git
cd enterprise-scraper
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
playwright install chromium
```

## Troubleshooting

### "Repository not found"
- Check repository URL
- Verify you have access
- Ensure `git remote -v` shows correct URL

### "Permission denied"
- Set up SSH keys: https://docs.github.com/en/authentication
- Or use personal access token instead of password

### ".gitignore not working"
If files already tracked:
```bash
git rm -r --cached .
git add .
git commit -m "Fix .gitignore"
```

### Large Files Error
GitHub has 100MB file limit. If you get this error:
- Check what's large: `git ls-tree -r -t -l --full-name HEAD | sort -n -k 4`
- Add to `.gitignore`
- Use `git rm --cached <file>` to untrack

## Security Checklist

Before pushing, verify:
- [ ] No API keys in code
- [ ] No database files uploaded
- [ ] No screenshots with sensitive data
- [ ] No `.env` files
- [ ] No hardcoded passwords

## Next Steps

After deployment:
1. ✅ Add LICENSE file (MIT recommended)
2. ✅ Set up GitHub Actions for CI/CD (optional)
3. ✅ Enable GitHub Pages for documentation (optional)
4. ✅ Add contributing guidelines (CONTRIBUTING.md)
5. ✅ Star your own repo! ⭐

---

**Congratulations!** Your enterprise scraper is now on GitHub! 🎉
