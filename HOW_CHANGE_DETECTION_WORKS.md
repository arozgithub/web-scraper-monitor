# 🔍 How Website Change Detection Works

## Simple Explanation

The scraper uses **content hashing** to detect changes - like a fingerprint for web pages!

---

## 📊 The Process

### Step 1: First Scrape
```
1. Visit website → Get HTML
2. Extract text content → "Welcome to our site..."
3. Calculate hash → "abc123def456..."
4. Save to database: {url: "example.com", hash: "abc123...", text: "Welcome..."}
```

### Step 2: Second Scrape (Later)
```
1. Visit website again → Get HTML
2. Extract text content → "Welcome to our NEW site..."
3. Calculate hash → "xyz789ghi012..."
4. Compare with database:
   - Old hash: "abc123..."
   - New hash: "xyz789..."
   - Different? → CHANGE DETECTED! ✅
```

---

## 🔐 What is Content Hashing?

**Hash** = A unique fingerprint of the content

```python
# Example
text1 = "Hello World"
hash1 = calculate_hash(text1)
# Result: "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"

text2 = "Hello World!"  # Added exclamation mark
hash2 = calculate_hash(text2)
# Result: "c0535e4be2b79ffd93291305436bf889314e4a3faec05ecffcbb7df31ad9e51a"
# ↑ Completely different hash!
```

**Key point:** Even tiny changes create a completely different hash!

---

## 🎯 How It's Used

### In the UI (Main Monitor App)

```
Every hour (or your schedule):
1. Scrape all tracked URLs
2. Calculate hash for each
3. Compare with last hash in database
4. If different:
   - Log change event
   - Show in "Recent Changes" feed
   - Update database with new hash
```

### In the API

```
When you call /scrape-complete:
1. Crawl all pages
2. For each page, calculate hash
3. Return hash in response

{
  "url": "example.com",
  "content_hash": "abc123...",
  "full_text": "..."
}

Then YOU can:
- Store this hash
- Compare on next scrape
- Detect changes yourself
```

---

## 💾 Database Storage

```sql
pages table:
- url
- last_hash
- last_text
- last_scraped

change_events table:
- url
- old_hash
- new_hash
- change_detected_at
- diff_summary
```

---

## 🔍 What Triggers a "Change"?

### ✅ These trigger changes:
- Text content modified
- New paragraphs added
- Content deleted
- Words changed
- Links updated (if text changes)

### ❌ These DON'T trigger changes:
- CSS/styling changes (visual only)
- JavaScript changes
- Image updates (unless alt text changes)
- HTML structure changes (if text stays same)
- Whitespace/formatting (cleaned before hashing)

---

## 📈 Example Scenario

### Day 1:
```
URL: https://releasenotes.bigchange.com/
Text: "Release 25.11.01 - Bug fixes"
Hash: "aaa111"
Stored in database ✅
```

### Day 2:
```
URL: https://releasenotes.bigchange.com/
Text: "Release 25.11.02 - New features"
Hash: "bbb222"

Compare:
- Old: "aaa111"
- New: "bbb222"
- Different! → Change detected! 🔔
- Log event: "Content changed on releasenotes.bigchange.com"
```

---

## 🧮 The Hash Algorithm

The scraper uses **SHA-256**:

```python
import hashlib

def calculate_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()
```

**Why SHA-256?**
- ✅ Fast to calculate
- ✅ Produces unique fingerprints
- ✅ Any change = different hash
- ✅ Industry standard
- ✅ Collision-resistant (no duplicates)

---

## 🎯 Benefits

1. **Efficient** - Don't need to store full text twice
2. **Fast** - Just compare two short strings
3. **Accurate** - Any change is detected
4. **Simple** - Easy to understand and implement

---

## 🔄 Complete Flow in Main App

```
[Scheduler runs every hour]
    ↓
[Loop through all tracked URLs]
    ↓
[For each URL:]
    1. Fetch current content
    2. Extract text
    3. Calculate hash: hash_new
    4. Get from DB: hash_old
    5. Compare:
        - If hash_new == hash_old → No change
        - If hash_new != hash_old → CHANGE!
            → Log to change_events table
            → Update pages table with new hash
            → Show in analytics
```

---

## 📊 In Analytics Dashboard

The analytics shows:
- Total changes detected
- Changes per site
- Recent changes feed
- Change rate percentage

All based on hash comparisons!

---

## 🎓 Summary

**Change Detection = Hash Comparison**

1. Scrape page → Extract text
2. Hash text → Get unique fingerprint
3. Compare with previous hash
4. Different hash = Content changed!

Simple, fast, and reliable! 🚀
