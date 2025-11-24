# Quick Diff Access from Analytics

## Overview
Added "View Diff" button to each change event in the Analytics tab's Recent Changes feed for instant comparison viewing.

## How It Works

### 1. **Recent Changes Display**
Each change event in the Analytics tab now shows:
- **Date & Time** - When the change was detected
- **URL** - Which page changed
- **Summary** - AI-generated description of what changed
- **🔍 View Diff Button** - Click to see the actual changes

### 2. **One-Click Comparison**
When you click "🔍 View Diff" on a change event:
1. Automatically switches to the "Visual Diff" tab
2. Enters the URL in the comparison field
3. Loads the last 2 versions from the database
4. Shows side-by-side comparison with:
   - Old vs New summaries
   - Full text diff with green/red highlighting
   - Date stamps for both versions

### 3. **What You'll See**
```
📊 Comparing: https://example.com/releases
Old: 2024-11-24 10:30:00 → New: 2024-11-24 14:45:00

✨ Summaries
┌─────────────────────────┬─────────────────────────┐
│ Old Version             │ New Version             │
│ Summary from yesterday  │ Latest summary today    │
└─────────────────────────┴─────────────────────────┘

📝 Text Diff
[Highlighted comparison showing exactly what changed]
```

## Usage Example

**Scenario:** You see a change notification for your release notes page

**Steps:**
1. Go to **Analytics** tab
2. Look at **Recent Changes** section
3. Find the change you're interested in
4. Click **🔍 View Diff** button
5. Instantly see what was added/removed/modified

## Benefits

✅ **No manual navigation** - Direct access from analytics  
✅ **Context preserved** - See when/where change happened  
✅ **Automatic loading** - No need to copy/paste URLs  
✅ **Visual clarity** - Color-coded differences  
✅ **Historical tracking** - Compare any monitored URL versions

## Technical Details

### Frontend Changes
- Modified `renderRecentChanges()` in `script.js` to add button to each feed item
- Added `viewDiffForUrl()` function to handle tab switching and auto-loading
- Button styled with gradient green color for visibility

### Data Flow
1. Analytics API provides change events with `page_url`
2. Button click calls `viewDiffForUrl(url)`
3. Function switches to diff tab and triggers `compareWebsiteVersions()`
4. `/api/compare-versions` endpoint fetches last 2 versions
5. Displays formatted comparison with summaries and diff

### API Endpoint Used
```
POST /api/compare-versions
{
  "url": "https://example.com/page"
}

Response:
{
  "success": true,
  "url": "...",
  "old_version": { "date": "...", "content": "...", "summary": "..." },
  "new_version": { "date": "...", "content": "...", "summary": "..." },
  "diff_html": "<table>...</table>"
}
```

## Requirements

- URL must have been monitored and scraped at least twice
- Content must be stored in the `scrape_history` table
- At least 2 versions needed for comparison

## Future Enhancements

Potential improvements:
- [ ] Choose which two versions to compare (not just last 2)
- [ ] Screenshot comparison alongside text
- [ ] Export diff as PDF
- [ ] Email notifications with diff preview
- [ ] Version timeline slider
