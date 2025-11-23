# 🌐 Exposing Local Scraper API to n8n Cloud

Since you're using **n8n Cloud**, it runs on n8n's servers and **cannot access your local machine**. You need to create a **public tunnel** to your local API.

## ✅ Solution: Use ngrok (Free & Easy)

### Step 1: Install ngrok

**Option A: Download from website**
1. Go to: https://ngrok.com/download
2. Download for Windows
3. Extract to a folder (e.g., `C:\ngrok`)

**Option B: Using Chocolatey (if you have it)**
```powershell
choco install ngrok
```

### Step 2: Create ngrok Account (Free)

1. Go to: https://dashboard.ngrok.com/signup
2. Sign up (it's free)
3. Copy your authtoken from: https://dashboard.ngrok.com/get-started/your-authtoken

### Step 3: Configure ngrok

Open PowerShell and run:
```powershell
# Navigate to ngrok folder
cd C:\ngrok

# Add your authtoken (replace with yours)
.\ngrok config add-authtoken YOUR_AUTH_TOKEN_HERE
```

### Step 4: Start the Tunnel

Keep your scraper API running on port 5001, then run:

```powershell
.\ngrok http 5001
```

You'll see output like:
```
Session Status                online
Account                       your-email@example.com
Forwarding                    https://abc123.ngrok.io -> http://localhost:5001
```

**⚠️ Copy the HTTPS URL** (e.g., `https://abc123.ngrok.io`)

### Step 5: Update n8n Workflow

In your n8n Cloud workflow, change the HTTP Request URL to:

```json
{
  "url": "https://abc123.ngrok.io/scrape"
}
```

### Step 6: Test It!

Now your n8n Cloud can reach your local API through the ngrok tunnel! ✅

---

## 🚀 Quick Start Script

Save this as `start_tunnel.bat`:

```batch
@echo off
echo ====================================
echo Starting Scraper API Tunnel
echo ====================================
echo.
echo Starting ngrok tunnel on port 5001...
echo.
cd C:\ngrok
ngrok http 5001
```

Double-click to run!

---

## 📝 Complete Setup Checklist

- [ ] ngrok installed
- [ ] ngrok account created
- [ ] Authtoken configured
- [ ] Scraper API running (port 5001)
- [ ] ngrok tunnel started
- [ ] Copied ngrok HTTPS URL
- [ ] Updated n8n workflow with ngrok URL
- [ ] Tested in n8n Cloud

---

## ⚡ Using the Tunnel in n8n

### HTTP Request Node Configuration:

**Method:** `POST`

**URL:** `https://YOUR-NGROK-URL.ngrok.io/scrape`

**Headers:**
- Content-Type: `application/json`

**Body:**
```json
{
  "url": "https://example.com",
  "api_key": "sk-..." 
}
```

---

## 📊 Available Endpoints via Tunnel

- `https://YOUR-URL.ngrok.io/scrape` - Scrape single URL
- `https://YOUR-URL.ngrok.io/crawl` - Crawl entire website
- `https://YOUR-URL.ngrok.io/extract-links` - Extract links
- `https://YOUR-URL.ngrok.io/health` - Health check
- `https://YOUR-URL.ngrok.io/info` - API info

---

## 🔒 Security Notes

**Free ngrok limitations:**
- URL changes each time you restart ngrok
- Limited to 40 connections/minute
- Session expires after 2 hours

**For production:**
- Upgrade to ngrok paid plan for static URL
- Or deploy API to cloud (AWS, Heroku, Railway, etc.)

---

## 🆓 Alternative Free Tunnels

### Option 2: Cloudflare Tunnel (cloudflared)

```powershell
# Install
powershell -Command "iwr https://bin.equinox.io/c/VdrWdbjqyF/cloudflared-stable-windows-amd64.exe -OutFile cloudflared.exe"

# Run tunnel
.\cloudflared tunnel --url http://localhost:5001
```

### Option 3: localtunnel

```powershell
npm install -g localtunnel
lt --port 5001
```

---

## 🎯 Recommended Workflow

1. **Keep 3 terminals open:**
   - Terminal 1: `python app.py` (main monitoring app on port 5000)
   - Terminal 2: `python scraper_api.py` (API for n8n on port 5001)
   - Terminal 3: `ngrok http 5001` (tunnel to internet)

2. **Use the ngrok URL in n8n Cloud**

3. **When ngrok restarts, update URL in n8n**

---

## ⚠️ Important Notes

- ❗ ngrok free URL changes every restart
- ❗ Keep ngrok running while using n8n Cloud
- ❗ Don't close the ngrok terminal window
- ❗ Update n8n workflow when ngrok URL changes
- ❗ Never share your ngrok URL publicly (it's your API!)

---

## 🐛 Troubleshooting

### ngrok not working?
- Make sure your scraper API is running first
- Check firewall isn't blocking ngrok
- Try restarting ngrok

### Connection still refused?
- Verify scraper_api.py is running on port 5001
- Test locally first: `http://localhost:5001/health`
- Then test ngrok URL: `https://your-url.ngrok.io/health`

### URL keeps changing?
- Use ngrok paid plan for static URL ($8/month)
- Or deploy API to cloud platform

---

## 🌟 Next Step: Deploy to Cloud (Optional)

For a permanent solution, deploy your API to:
- **Railway** (free tier available)
- **Render** (free tier available)
- **Heroku** (paid plans)
- **AWS Lambda** (free tier available)

This eliminates the need for ngrok!

---

## ✅ Success!

Once ngrok is running, you'll have a public HTTPS URL that n8n Cloud can access!

Example n8n request:
```
POST https://abc123.ngrok.io/scrape
{
  "url": "https://example.com"
}
```

🎉 **Your local scraper is now accessible from n8n Cloud!**
