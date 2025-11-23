# 🚀 Step-by-Step: Using Web Scraper API in n8n

## Prerequisites
1. ✅ Scraper API running on `http://localhost:5001` (already running!)
2. ✅ n8n installed and running (typically on `http://localhost:5678`)

---

## Quick Start: Scrape a Single URL

### Step 1: Create New Workflow in n8n

1. Open n8n (`http://localhost:5678`)
2. Click **"+ New Workflow"**
3. Name it: "Website Scraper"

### Step 2: Add HTTP Request Node

1. Click **"+"** to add a node
2. Search for **"HTTP Request"**
3. Click on it to add

### Step 3: Configure HTTP Request

**Basic Settings:**
- **Method**: `POST`
- **URL**: `http://localhost:5001/scrape`

**Headers:**
- Click "Add Header"
- Name: `Content-Type`
- Value: `application/json`

**Body:**
- **Send Body**: ✅ (toggle ON)
- **Body Content Type**: `JSON`
- **Specify Body**: `Using JSON`
- **JSON**:
```json
{
  "url": "https://example.com"
}
```

### Step 4: Test It!

1. Click **"Execute Node"** button
2. You'll see the scraped data in the output panel:
```json
{
  "success": true,
  "url": "https://example.com",
  "content_type": "html",
  "text_length": 1234,
  "text_preview": "...",
  "summary": null
}
```

---

## Example 1: Monitor Website for Changes

### Nodes Setup:

```
[Schedule Trigger] → [HTTP Request] → [If] → [Email/Slack]
```

### 1. Schedule Trigger
- Trigger Interval: `Every Hour`
- Or: `Cron: 0 * * * *`

### 2. HTTP Request (Scrape)
- URL: `http://localhost:5001/scrape`
- Method: `POST`
- Body:
```json
{
  "url": "https://example.com/products"
}
```

### 3. If Node (Check for Changes)
- **Condition**: `{{ $json.content_hash }}` is not equal to `YOUR_PREVIOUS_HASH`
- Store previous hash in n8n variables or database

### 4. Send Notification (When Changed)
- **Email/Slack** node
- Message: 
```
🔔 Website Changed!
URL: {{ $json.url }}
Hash: {{ $json.content_hash }}
```

---

## Example 2: Scrape Multiple URLs from Google Sheets

### Nodes Setup:

```
[Google Sheets] → [Loop] → [HTTP Request] → [Set] → [Google Sheets Write]
```

### 1. Google Sheets (Read)
- **Operation**: `Read Rows`
- **Sheet**: Your sheet with URLs in column A
- **Range**: `A:A`

### 2. Split In Batches
- **Batch Size**: `5` (process 5 URLs at a time)

### 3. HTTP Request (Scrape)
- **URL**: `http://localhost:5001/scrape`
- **Method**: `POST`
- **Body**:
```json
{
  "url": "{{ $json.url }}"
}
```

### 4. Set Node (Format Data)
```javascript
{
  "url": "{{ $json.url }}",
  "title": "{{ $json.text_preview.split('.')[0] }}",
  "content_hash": "{{ $json.content_hash }}",
  "scraped_at": "{{ $now }}"
}
```

### 5. Google Sheets (Write)
- **Operation**: `Append Row`
- Map the fields to columns

---

## Example 3: Crawl Entire Website

### Single Node Setup:

### HTTP Request
- **URL**: `http://localhost:5001/crawl`
- **Method**: `POST`
- **Body**:
```json
{
  "root_url": "https://example.com",
  "max_pages": 20
}
```

**Output**: You'll get an array of all crawled pages

### Process Results:

Add **Split Out** node after HTTP Request:
- **Field to Split**: `pages`
- This will create individual items for each page

Then you can process each page individually.

---

## Example 4: Extract All Links from a Page

### HTTP Request
- **URL**: `http://localhost:5001/extract-links`
- **Method**: `POST`
- **Body**:
```json
{
  "url": "https://example.com"
}
```

**Output**:
```json
{
  "success": true,
  "links_found": 25,
  "links": ["https://example.com/page1", "..."]
}
```

---

## Example 5: Scrape with AI Summary

### HTTP Request (with OpenAI)
- **URL**: `http://localhost:5001/scrape`
- **Method**: `POST`
- **Body**:
```json
{
  "url": "https://news.ycombinator.com",
  "api_key": "{{ $credentials.openai.apiKey }}"
}
```

**Or** hardcode your API key (not recommended for production):
```json
{
  "url": "https://news.ycombinator.com",
  "api_key": "sk-your-key-here"
}
```

**Output includes summary**:
```json
{
  "success": true,
  "url": "...",
  "summary": "AI-generated summary of the page content..."
}
```

---

## Advanced: Complete Monitoring Workflow

### Workflow Architecture:

```
[Schedule: Every 6 hours]
    ↓
[HTTP Request: Crawl Website]
    ↓
[Split Out: pages array]
    ↓
[Set: Extract data]
    ↓
[IF: Check if new page]
    ↓ (true)
[PostgreSQL: Insert new page]
    ↓
[IF: Content changed]
    ↓ (true)
[Slack: Send alert]
```

### Node Details:

**1. Schedule Trigger**
```
Trigger Rules: Every 6 hours
```

**2. HTTP Request (Crawl)**
```json
{
  "root_url": "https://competitor-site.com",
  "max_pages": 30,
  "api_key": "{{ $credentials.openai.apiKey }}"
}
```

**3. Split Out**
```
Field to Split Out: pages
```

**4. Set Node**
```javascript
{
  "url": "{{ $json.url }}",
  "content_hash": "{{ $json.content_hash }}",
  "summary": "{{ $json.summary }}",
  "text_length": "{{ $json.text_length }}",
  "crawled_at": "{{ $now.toISO() }}"
}
```

**5. Postgres - Check if Exists**
```sql
SELECT * FROM scraped_pages 
WHERE url = '{{ $json.url }}'
```

**6. IF Node (Is New)**
```
Condition: {{ $json.id }} is empty
```

**7. Postgres - Insert**
```sql
INSERT INTO scraped_pages 
(url, content_hash, summary, text_length, crawled_at)
VALUES (...)
```

**8. IF Node (Content Changed)**
```
Condition: {{ $json.old_hash }} != {{ $json.content_hash }}
```

**9. Slack Alert**
```
Message:
🔥 Content Changed!

Page: {{ $json.url }}
Summary: {{ $json.summary }}
Old Hash: {{ $json.old_hash }}
New Hash: {{ $json.content_hash }}
```

---

## Using Variables in n8n

### Accessing Response Data:

```javascript
// Get URL from previous node
{{ $json.url }}

// Get scraped text
{{ $json.full_text }}

// Get content hash
{{ $json.content_hash }}

// Get summary
{{ $json.summary }}

// Get first page from crawl results
{{ $json.pages[0].url }}

// Get all links
{{ $json.links }}

// Count links
{{ $json.links.length }}
```

---

## Error Handling

### Add Error Trigger Node:

1. Add **"Error Trigger"** node
2. Connect it to **Email** or **Slack** node
3. Message:
```
❌ Scraping Failed!

Workflow: {{ $workflow.name }}
Error: {{ $json.error }}
URL: {{ $json.url }}
```

---

## Common Use Cases

### 1. **Price Monitoring**
```
Schedule Trigger (Daily)
  → Scrape competitor prices
  → Compare with database
  → Alert if price drops
```

### 2. **Content Aggregation**
```
RSS Trigger (New post)
  → Extract URL
  → Scrape full article
  → Save to WordPress/Database
```

### 3. **SEO Monitoring**
```
Schedule (Weekly)
  → Crawl your website
  → Extract all links
  → Check for broken links
  → Generate report
```

### 4. **Job Board Scraper**
```
Schedule (Every 2 hours)
  → Crawl job board
  → Filter new jobs
  → Send to Slack/Email
  → Save to Database
```

### 5. **News Aggregator**
```
Schedule (Hourly)
  → Scrape news sites
  → Generate AI summaries
  → Post to Twitter/LinkedIn
```

---

## Testing Your Workflow

### 1. Manual Testing
- Click **"Execute Workflow"** button
- Check the output of each node
- Verify data is correct

### 2. With Sample Data
- Use **"Manual"** trigger
- Click **"Execute Workflow"**
- Provide test URL

### 3. Monitor Execution
- Go to **"Executions"** tab
- View all past runs
- Debug any failures

---

## Tips & Best Practices

✅ **Use variables** for API keys (don't hardcode)  
✅ **Add error handling** with Error Trigger node  
✅ **Limit crawl depth** (max_pages: 20-50)  
✅ **Use batching** for multiple URLs  
✅ **Cache results** in database to avoid re-scraping  
✅ **Add delays** between requests (use Wait node)  
✅ **Log everything** to database for debugging  

---

## Troubleshooting

### Issue: "Connection Refused"
**Solution**: Make sure `scraper_api.py` is running on port 5001

```powershell
# Check if running:
Invoke-WebRequest -Uri http://localhost:5001/health
```

### Issue: "Timeout"
**Solution**: Increase timeout in HTTP Request node settings
- Options → Timeout: `30000` (30 seconds)

### Issue: "No data returned"
**Solution**: Check the URL is accessible
- Test URL manually in browser first
- Check API response in n8n output panel

### Issue: "Invalid JSON"
**Solution**: Make sure Body Content Type is set to JSON
- Body Content Type: `JSON`
- Specify Body: `Using JSON`

---

## Next Steps

1. ✅ Create your first workflow in n8n
2. ✅ Test with a simple scrape
3. ✅ Add schedule trigger for automation
4. ✅ Connect to database/notification service
5. ✅ Monitor and refine

**Need help?** Check the logs in the scraper_api.py terminal for debugging!
