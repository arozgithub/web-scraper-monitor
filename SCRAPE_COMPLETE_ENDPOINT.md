# `/scrape-complete` Endpoint - Simple Complete Scraping

## Single Endpoint for Complete Website Scraping (No AI Summaries)

The `/scrape-complete` endpoint crawls entire websites and returns all the text data - NO AI summaries needed!

---

## ✅ Use in n8n Cloud

**URL:**
```
https://premonarchical-verona-unmeddled.ngrok-free.dev/scrape-complete
```

**Method:** `POST`

**Body:**
```json
{
  "url": "https://releasenotes.bigchange.com/",
  "max_pages": 10
}
```

**That's it!** No API key needed!

---

## 📊 Response Format

```json
{
  "success": true,
  "root_url": "https://releasenotes.bigchange.com/",
  "pages_crawled": 10,
  "pages": [
    {
      "url": "https://releasenotes.bigchange.com/page1",
      "content_hash": "abc123...",
      "text_length": 5432,
      "full_text": "Complete extracted text from the page..."
    },
    {
      "url": "https://releasenotes.bigchange.com/page2",
      "content_hash": "def456...",
      "text_length": 3210,
      "full_text": "Complete extracted text from the page..."
    }
  ]
}
```

---

## 🎯 What You Get

For each page:
- ✅ **URL** - The page URL
- ✅ **Full Text** - Complete extracted text content
- ✅ **Content Hash** - For change detection
- ✅ **Text Length** - Character count

Plus metadata:
- ✅ **Total pages crawled**
- ✅ **Root URL**
- ✅ **Success status**

---

## 🚀 n8n HTTP Request Tool Configuration

```json
{
  "method": "POST",
  "url": "https://premonarchical-verona-unmeddled.ngrok-free.dev/scrape-complete",
  "sendBody": true,
  "bodyType": "json",
  "jsonBody": {
    "url": "{{ $json.url || $json.chatInput }}",
    "max_pages": 10
  }
}
```

---

## 💡 Use Cases

Perfect for:
- ✅ **Data extraction** - Get all text from a website
- ✅ **Content aggregation** - Combine multiple pages
- ✅ **Documentation scraping** - Download entire docs
- ✅ **Change monitoring** - Track content changes via hashes
- ✅ **Feed your own AI** - Get raw text to process with your own prompts

---

## ⚡ Comparison

| Endpoint | What it does |
|----------|-------------|
| `/scrape` | Single page with optional summary |
| `/crawl` | Multiple pages, optional summaries, returns previews |
| **`/scrape-complete`** | **Multiple pages, NO summaries, returns FULL TEXT** |

---

## 🧪 Test with PowerShell

```powershell
$body = @{
    url = "https://example.com"
    max_pages = 5
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://premonarchical-verona-unmeddled.ngrok-free.dev/scrape-complete" `
  -Method POST `
  -Body $body `
  -ContentType "application/json"
```

---

## ⭐ Benefits

✅ **No API key needed** - No OpenAI costs!  
✅ **Full text** - Not just previews  
✅ **Fast** - No AI processing  
✅ **Simple** - Just URL + max_pages  
✅ **Complete** - Gets all linked pages

---

## 📝 Example n8n Workflow

```
[Webhook Trigger]
    ↓
[HTTP Request: /scrape-complete]
    URL: {{ $json.url }}
    max_pages: 20
    ↓
[Loop through pages]
    Access: {{ $json.pages }}
    ↓
[Process each page's full_text]
    Your own logic here!
```

---

## 🎯 Perfect For n8n!

- Get all the text data
- Process it however you want
- Use your own AI prompts
- Save to your database
- No external dependencies!

🚀 **Simple, fast, and exactly what you need!**
