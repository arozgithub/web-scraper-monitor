# Visual Diff & Screenshot Features - User Guide

## 🔍 Visual Diff Feature

### What It Does
Generates a side-by-side HTML comparison showing:
- **Red highlighting**: Content that was removed
- **Green highlighting**: Content that was added
- **Line-by-line comparison**: Easy to see exactly what changed

### How It Works

**API Endpoint:** `POST /api/diff`

**Request Format:**
```json
{
  "text1": "Original content here",
  "text2": "New content here"
}
```

**Response:**
- Returns HTML document with visual diff
- Can be displayed in browser or saved as file

### Use Cases

1. **Compare Scrape History**
   - Get two versions of the same page
   - See exactly what changed

2. **Monitor Release Notes**
   - Compare old vs new release notes
   - Highlight new features

3. **Track Content Updates**
   - Monitor blog posts or documentation
   - Identify modifications

### Example with Python

```python
import requests

response = requests.post('http://localhost:5000/api/diff', json={
    'text1': 'Version 1.0 released\nBug fixes included',
    'text2': 'Version 2.0 released\nNew features\nBug fixes included'
})

with open('diff.html', 'w') as f:
    f.write(response.text)
```

### Example with n8n

**HTTP Request Node:**
- Method: POST
- URL: `{{$node["Webhook"].json["ngrok_url"]}}/diff`
- Body:
  ```json
  {
    "text1": "{{$json.old_content}}",
    "text2": "{{$json.new_content}}"
  }
  ```

---

## 📸 Screenshot Feature

### What It Does
Takes full-page screenshots of websites using headless Chrome browser.

### How It Works

**API Endpoint:** `POST /screenshot`

**Request Format:**
```json
{
  "url": "https://example.com",
  "use_proxy": false
}
```

**Response:**
```json
{
  "success": true,
  "screenshot_url": "/static/screenshots/screenshot_1234567890_1234.png",
  "message": "Screenshot saved successfully"
}
```

**Screenshot Storage:**
- Saved in: `static/screenshots/`
- Filename format: `screenshot_<timestamp>_<random>.png`
- Accessible via: `http://localhost:5000/static/screenshots/<filename>`

### Features

1. **Full-Page Capture**
   - Captures entire page, not just viewport
   - Handles long pages automatically

2. **JavaScript Rendering**
   - Uses Playwright browser
   - Waits for content to load
   - Scrolls to trigger lazy loading

3. **Random User-Agents**
   - Avoids detection
   - Rotates headers automatically

4. **Proxy Support**
   - Can route through proxy
   - Configurable per request

### Use Cases

1. **Visual Monitoring**
   - Track layout changes
   - Monitor design updates
   - Detect visual bugs

2. **Historical Archive**
   - Keep visual record of website evolution
   - Compare UI changes over time

3. **Compliance**
   - Document website state
   - Legal evidence of content

4. **Testing**
   - Visual regression testing
   - Cross-browser comparison

### Example with Python

```python
import requests

# Take screenshot
response = requests.post('http://localhost:5001/screenshot', json={
    'url': 'https://example.com',
    'use_proxy': False
})

data = response.json()
print(f"Screenshot saved: {data['screenshot_url']}")

# Download the image
img_response = requests.get(f"http://localhost:5000{data['screenshot_url']}")
with open('my_screenshot.png', 'wb') as f:
    f.write(img_response.content)
```

### Example with n8n

**Workflow:**
1. **HTTP Request Node** - Take screenshot
   ```json
   {
     "url": "{{$json.website}}",
     "use_proxy": false
   }
   ```

2. **Set Node** - Extract URL
   ```javascript
   {
     "screenshot_url": "{{$json.screenshot_url}}"
   }
   ```

3. **HTTP Request Node** - Download image
   - URL: `http://localhost:5000{{$json.screenshot_url}}`
   - Response Format: File

4. **Write Binary File** - Save locally
   - File Path: `/path/to/screenshots/{{$json.filename}}`

---

## 🎨 UI Features (Coming)

### Visual Diff Viewer
- **Compare Tab**: Select two versions from history
- **Side-by-side view**: HTML diff display
- **Quick actions**: Export, share, bookmark

### Screenshot Gallery
- **Gallery Tab**: View all screenshots
- **Timeline view**: Organize by date
- **Comparison mode**: Side-by-side screenshot comparison
- **Annotations**: Mark important changes

---

## 🔧 Technical Details

### Screenshot Process
1. Launch headless Chromium
2. Navigate to URL
3. Wait for network idle
4. Scroll to bottom (trigger lazy load)
5. Capture full page
6. Save with unique filename
7. Return public URL

### Diff Algorithm
- Uses Python's `difflib.HtmlDiff()`
- Line-by-line comparison
- Context-aware (shows surrounding lines)
- Customizable context lines (`numlines` parameter)

### Storage Limits
- **Screenshots**: No automatic cleanup (manual deletion needed)
- **Typical size**: 200KB - 2MB per screenshot
- **Recommendation**: Clean old screenshots periodically

### Performance
- **Screenshot**: 2-5 seconds per page
- **Diff**: <1 second for most comparisons
- **Concurrent requests**: Limited by browser instances

---

## 🚀 Best Practices

### For Diff
1. **Clean text first**: Remove timestamps/session IDs that change every scrape
2. **Use consistent formatting**: Ensure both texts use same line endings
3. **Limit size**: Very large texts (>1MB) may be slow

### For Screenshots
1. **Wait for content**: Set appropriate wait time for JS-heavy sites
2. **Use consistent viewport**: Results more comparable
3. **Clean old files**: Delete screenshots you don't need
4. **Consider storage**: Each screenshot is ~500KB average

---

## 📋 Troubleshooting

### Diff Not Showing Changes
- **Problem**: Returns blank or minimal diff
- **Solution**: Check if texts are actually different
- **Tip**: Use hash comparison first

### Screenshot Fails
- **Problem**: Timeout or error
- **Solutions**:
  - Check Playwright is installed: `playwright install chromium`
  - Increase timeout in code
  - Try without proxy first
  - Check URL is accessible

### Screenshot File Not Found
- **Problem**: 404 when accessing screenshot URL
- **Solutions**:
  - Check `static/screenshots/` directory exists
  - Verify file permissions
  - Ensure Flask serves static files

---

## 🔗 API Reference

### Full Endpoint List

#### Diff
- **Endpoint**: `POST /api/diff`
- **Port**: 5000 (UI server)
- **Returns**: HTML (text/html)

#### Screenshot  
- **Endpoint**: `POST /screenshot`
- **Port**: 5001 (API server)
- **Returns**: JSON with URL

### Response Codes
- `200`: Success
- `400`: Bad request (missing parameters)
- `500`: Server error (Playwright crash, etc.)

---

**Ready to use these features? Start with the API examples above!** 🎯
