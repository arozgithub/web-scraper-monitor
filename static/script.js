async function fetchPages() {
    try {
        const response = await fetch('/api/pages');
        const pages = await response.json();
        renderPages(pages);
    } catch (error) {
        console.error('Error fetching pages:', error);
    }
}

function renderPages(groupedPages) {
    const grid = document.getElementById('pagesGrid');

    if (Object.keys(groupedPages).length === 0) {
        grid.innerHTML = '<div style="text-align:center; color:var(--text-secondary);">No pages monitored yet. Add a URL above.</div>';
        return;
    }

    grid.innerHTML = Object.entries(groupedPages).map(([rootUrl, data]) => `
        <div class="root-card" id="card-${btoa(rootUrl)}">
            <div class="root-header" onclick="toggleCard(this)">
                <div class="root-info">
                    <h3>${rootUrl}</h3>
                    <div class="root-stats">
                        ${data.pages.length} pages monitored • 
                        Schedule: Every ${data.schedule ? data.schedule.val + ' ' + data.schedule.unit : 'N/A'}
                    </div>
                </div>
                <div class="root-actions">
                    <label class="switch" onclick="event.stopPropagation()">
                        <input type="checkbox" ${data.schedule && data.schedule.active ? 'checked' : ''} onchange="toggleSchedule('${rootUrl}', this.checked)">
                        <span class="slider round"></span>
                    </label>
                    <button class="btn-delete" onclick="deleteRoot('${rootUrl}', event)">Delete</button>
                </div>
            </div>
            <div class="child-list">
                ${data.master_summary ? `<div class="master-summary"><strong>Site Overview:</strong><br>${data.master_summary}</div>` : ''}
                ${data.pages.map(page => `
                    <div class="child-item">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <a href="${page.url}" target="_blank" class="child-url">${page.url}</a>
                            <button class="btn-history" onclick="viewHistory('${page.url}', event)">History</button>
                        </div>
                        <div class="child-summary">${page.summary || 'No summary available.'}</div>
                        <div style="font-size:0.8rem; color: #64748b; margin-top:4px;">Last Scraped: ${new Date(page.last_scraped).toLocaleString()}</div>
                    </div>
                `).join('')}
            </div>
        </div>
    `).join('');
}

function toggleCard(header) {
    header.parentElement.classList.toggle('expanded');
}

async function toggleSchedule(rootUrl, isActive) {
    try {
        const response = await fetch('/api/schedule/toggle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ root_url: rootUrl, is_active: isActive })
        });
        const result = await response.json();
        if (!result.success) {
            alert('Error: ' + result.message);
            fetchPages(); // Revert UI on error
        }
    } catch (error) {
        console.error('Error toggling schedule:', error);
    }
}

async function deleteRoot(rootUrl, event) {
    event.stopPropagation(); // Prevent card expansion
    if (!confirm(`Are you sure you want to delete ${rootUrl} and all its ${rootUrl === 'Uncategorized' ? 'pages' : 'sub-pages'}?`)) return;

    try {
        const response = await fetch('/api/pages', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ root_url: rootUrl })
        });
        const result = await response.json();
        if (result.success) {
            fetchPages();
        } else {
            alert('Error: ' + result.message);
        }
    } catch (error) {
        console.error('Error deleting:', error);
    }
}

async function addUrl() {
    const input = document.getElementById('urlInput');
    const apiKeyInput = document.getElementById('apiKeyInput');
    const intervalVal = document.getElementById('intervalVal');
    const intervalUnit = document.getElementById('intervalUnit');
    const captureScreenshots = document.getElementById('captureScreenshots');

    const url = input.value;
    const apiKey = apiKeyInput.value;

    if (!url) {
        alert('Please enter a URL');
        return;
    }

    try {
        const response = await fetch('/api/pages', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: url,
                apiKey: apiKey,
                intervalVal: intervalVal.value,
                intervalUnit: intervalUnit.value,
                captureScreenshots: captureScreenshots.checked
            }),
        });

        const data = await response.json();
        if (data.success) {
            input.value = '';
            fetchPages();
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to add URL');
    }
}

async function scrape(url) {
    try {
        const response = await fetch('/api/scrape', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });
        const result = await response.json();
        alert(result.message);
        fetchPages();
    } catch (error) {
        console.error('Error scraping:', error);
    }
}

async function viewHistory(url, event) {
    event.stopPropagation();

    try {
        const response = await fetch(`/api/history/${encodeURIComponent(url)}`);
        const history = await response.json();

        if (history.length === 0) {
            alert('No history available yet.');
            return;
        }

        const historyHtml = history.map((h, index) => `
            <div style="padding: 10px; border-bottom: 1px solid #333; ${h.changed ? 'background: rgba(251, 191, 36, 0.1);' : ''}">
                <strong>${index === 0 ? 'Latest' : `Version ${index + 1}`}</strong> - ${new Date(h.scraped_at).toLocaleString()}
                ${h.changed ? '<span style="color: #fbbf24;"> ⚠ Changed</span>' : ''}
                <div style="margin-top: 8px; font-size: 0.9rem;">${h.summary || 'No summary'}</div>
            </div>
        `).join('');

        // Create a modal-like display
        const modal = document.createElement('div');
        modal.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.8); z-index: 9999; display: flex; justify-content: center; align-items: center;';
        modal.innerHTML = `
            <div style="background: #1e293b; padding: 24px; border-radius: 16px; max-width: 800px; max-height: 80vh; overflow-y: auto; border: 1px solid rgba(255,255,255,0.1);">
                <h2 style="margin-top: 0; color: #38bdf8;">Scrape History</h2>
                <p style="color: #94a3b8; margin-bottom: 20px; word-break: break-all;">${url}</p>
                ${historyHtml}
                <button class="btn" style="margin-top: 20px; width: 100%;" onclick="this.parentElement.parentElement.remove()">Close</button>
            </div>
        `;
        document.body.appendChild(modal);
        modal.onclick = (e) => { if (e.target === modal) modal.remove(); };
    } catch (error) {
        console.error('Error fetching history:', error);
        alert('Failed to load history');
    }
}

// Tab Switching
function showTab(tabName) {
    // Update active tab button
    document.querySelectorAll('.nav-tab').forEach(tab => tab.classList.remove('active'));
    event.target.classList.add('active');

    // Show/hide views
    document.getElementById('monitor-view').style.display = tabName === 'monitor' ? 'block' : 'none';
    document.getElementById('analytics-view').style.display = tabName === 'analytics' ? 'block' : 'none';
    document.getElementById('linkedin-view').style.display = tabName === 'linkedin' ? 'block' : 'none';
    document.getElementById('outreach-view').style.display = tabName === 'outreach' ? 'block' : 'none';
    document.getElementById('chat-view').style.display = tabName === 'chat' ? 'block' : 'none';
    document.getElementById('diff-view').style.display = tabName === 'diff' ? 'block' : 'none';

    // Load analytics if switching to analytics tab
    if (tabName === 'analytics') {
        const timeWindow = document.getElementById('timeWindow').value;
        loadAnalytics(timeWindow);
    }

    // Load leads if switching to outreach tab
    if (tabName === 'outreach') {
        refreshLeads();
    }
}

// Analytics Functions
let trendsChart = null;
let topSitesChart = null;

async function loadAnalytics(window = '24h') {
    try {
        const response = await fetch(`/api/analytics?window=${window}`);
        const data = await response.json();

        // Render KPIs
        renderKPIs(data.kpis);

        // Render Charts
        renderCharts(data.trends, data.top_root_sites);

        // Render Recent Changes
        renderRecentChanges(data.recent_changes);

        // Render Site Insights
        renderSiteInsights(data.per_root_site_insights);
    } catch (error) {
        console.error('Error loading analytics:', error);
    }
}

function renderKPIs(kpis) {
    const grid = document.getElementById('kpiGrid');
    grid.innerHTML = `
        <div class="kpi-card">
            <div class="kpi-label">Total Sites</div>
            <div class="kpi-value">${kpis.total_root_sites}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Total Pages</div>
            <div class="kpi-value">${kpis.total_pages}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Scrapes</div>
            <div class="kpi-value">${kpis.scrapes_in_range}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Changes</div>
            <div class="kpi-value">${kpis.changes_in_range}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Success Rate</div>
            <div class="kpi-value">${kpis.success_rate}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Avg Duration</div>
            <div class="kpi-value">${kpis.avg_scrape_duration}</div>
        </div>
    `;
}

function renderCharts(trends, topSites) {
    // Trends Chart
    const trendsCtx = document.getElementById('trendsChart').getContext('2d');

    if (trendsChart) {
        trendsChart.destroy();
    }

    const dates = Object.keys(trends.daily_scrapes).sort();

    trendsChart = new Chart(trendsCtx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Scrapes',
                data: dates.map(d => trends.daily_scrapes[d] || 0),
                borderColor: '#38bdf8',
                backgroundColor: 'rgba(56, 189, 248, 0.1)',
                tension: 0.4
            }, {
                label: 'Changes',
                data: dates.map(d => trends.daily_changes[d] || 0),
                borderColor: '#fbbf24',
                backgroundColor: 'rgba(251, 191, 36, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#cbd5e1' } }
            },
            scales: {
                y: { ticks: { color: '#cbd5e1' }, grid: { color: 'rgba(203, 213, 225, 0.1)' } },
                x: { ticks: { color: '#cbd5e1' }, grid: { color: 'rgba(203, 213, 225, 0.1)' } }
            }
        }
    });

    // Top Sites Chart
    const topSitesCtx = document.getElementById('topSitesChart').getContext('2d');

    if (topSitesChart) {
        topSitesChart.destroy();
    }

    topSitesChart = new Chart(topSitesCtx, {
        type: 'bar',
        data: {
            labels: topSites.map(s => new URL(s.root_url || 'N/A').hostname),
            datasets: [{
                label: 'Changes',
                data: topSites.map(s => s.changes),
                backgroundColor: '#34d399'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { ticks: { color: '#cbd5e1' }, grid: { color: 'rgba(203, 213, 225, 0.1)' } },
                x: { ticks: { color: '#cbd5e1' }, grid: { color: 'rgba(203, 213, 225, 0.1)' } }
            }
        }
    });
}

function renderRecentChanges(changes) {
    const feed = document.getElementById('recentChangesFeed');
    if (changes.length === 0) {
        feed.innerHTML = '<p style="color: #94a3b8;">No recent activity</p>';
        return;
    }

    feed.innerHTML = changes.map(c => `
        <div class="feed-item" style="border-left: 4px solid ${c.changed ? '#4CAF50' : '#ddd'};">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                <div style="flex: 1;">
                    <div class="feed-time">${new Date(c.date).toLocaleString()}</div>
                    <div class="feed-url">${c.page_url}</div>
                </div>
                ${c.changed ? `
                <button onclick="viewDiffForUrl('${c.page_url}')" 
                    style="padding: 6px 12px; background: linear-gradient(135deg, #4CAF50, #45a049); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 12px; white-space: nowrap; margin-left: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                    🔍 View Diff
                </button>
                ` : `
                <span style="padding: 6px 12px; background: #f5f5f5; color: #999; border-radius: 6px; font-size: 12px; white-space: nowrap; margin-left: 10px;">
                    No changes
                </span>
                `}
            </div>
            <div class="feed-summary" style="color: ${c.changed ? '#333' : '#999'};">${c.summary || 'No summary available'}</div>
        </div>
    `).join('');
}

function renderSiteInsights(insights) {
    const list = document.getElementById('siteInsightsList');
    const keys = Object.keys(insights);

    if (keys.length === 0) {
        list.innerHTML = '<p style="color: #94a3b8;">No sites monitored</p>';
        return;
    }

    list.innerHTML = keys.map(key => {
        const insight = insights[key];
        return `
            <div class="insight-item">
                <div class="insight-header">${key}</div>
                <div class="insight-stats">
                    <span>📄 ${insight.total_pages} pages</span>
                    <span>🔄 ${insight.scrapes_in_range} scrapes</span>
                    <span>⚡ ${insight.changes_in_range} changes</span>
                    <span>📊 ${insight.change_rate} change rate</span>
                </div>
            </div>
        `;
    }).join('');
}

// Initial load
// Chat Function
async function sendChat() {
    const urlInput = document.getElementById('chatUrlInput');
    const apiKeyInput = document.getElementById('chatApiKeyInput');
    const queryInput = document.getElementById('chatQueryInput');
    const messagesDiv = document.getElementById('chatMessages');

    const url = urlInput.value;
    const apiKey = apiKeyInput.value;
    const query = queryInput.value;

    if (!query) return;
    if (!apiKey) {
        alert('API Key is required');
        return;
    }

    // Add user message
    messagesDiv.innerHTML += `
        <div class="chat-message user" style="margin: 10px 0; text-align: right;">
            <span style="background: #38bdf8; color: #0f172a; padding: 8px 12px; border-radius: 12px; display: inline-block;">${query}</span>
        </div>
    `;
    queryInput.value = '';
    messagesDiv.scrollTop = messagesDiv.scrollHeight;

    // Show loading
    const loadingId = 'loading-' + Date.now();
    messagesDiv.innerHTML += `
        <div class="chat-message system" id="${loadingId}" style="margin: 10px 0;">
            <span style="color: #94a3b8;">Thinking...</span>
        </div>
    `;

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, query, apiKey })
        });

        const data = await response.json();

        // Remove loading
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) loadingEl.remove();

        if (data.error) {
            messagesDiv.innerHTML += `
                <div class="chat-message system error" style="margin: 10px 0; color: #ef4444;">
                    Error: ${data.error}
                </div>
            `;
        } else {
            // Show answer
            const answerHtml = data.answer.replace(/\n/g, '<br>');
            messagesDiv.innerHTML += `
                <div class="chat-message system" style="margin: 10px 0;">
                    <div style="background: #1e293b; padding: 16px; border-radius: 12px; border: 1px solid #334155; color: #e2e8f0;">
                        ${answerHtml}
                    </div>
                </div>
            `;
        }
        messagesDiv.scrollTop = messagesDiv.scrollHeight;

    } catch (error) {
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) loadingEl.remove();
        console.error(error);
        alert('Chat failed');
    }
}

// Screenshot Functions
async function takeScreenshot() {
    const urlInput = document.getElementById('screenshotUrlInput');
    const url = urlInput.value.trim();

    if (!url) {
        alert('Please enter a URL');
        return;
    }

    try {
        const response = await fetch('http://localhost:5001/screenshot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, use_proxy: false })
        });

        const data = await response.json();

        if (data.success) {
            alert('Screenshot captured successfully!');
            loadScreenshotGallery();
            urlInput.value = '';
        } else {
            alert('Failed to capture screenshot: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error(error);
        alert('Error capturing screenshot: ' + error.message);
    }
}

async function loadScreenshotGallery() {
    const gallery = document.getElementById('screenshotGallery');

    try {
        // List screenshot files from static directory
        const response = await fetch('/static/screenshots/');

        if (response.ok) {
            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const links = Array.from(doc.querySelectorAll('a'))
                .filter(a => a.href.endsWith('.png'))
                .map(a => a.href);

            if (links.length === 0) {
                gallery.innerHTML = '<p style="color: #999; text-align: center; padding: 40px;">No screenshots yet. Capture one above!</p>';
                return;
            }

            gallery.innerHTML = links.map(link => {
                const filename = link.split('/').pop();
                return `
                    <div class="screenshot-item" style="margin: 15px 0; padding: 15px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <div style="margin-bottom: 10px;">
                            <strong>📸 ${filename}</strong>
                            <a href="${link}" download style="float: right; color: #2196F3; text-decoration: none;">⬇️ Download</a>
                        </div>
                        <img src="${link}" alt="${filename}" 
                            style="width: 100%; max-height: 300px; object-fit: contain; border: 1px solid #ddd; border-radius: 4px; cursor: pointer;"
                            onclick="window.open('${link}', '_blank')">
                    </div>
                `;
            }).join('');
        } else {
            gallery.innerHTML = '<p style="color: #999; text-align: center; padding: 40px;">Unable to load screenshot gallery. Directory may be empty.</p>';
        }
    } catch (error) {
        console.error('Error loading screenshots:', error);
        gallery.innerHTML = '<p style="color: #999; text-align: center; padding: 40px;">Use the screenshot API to capture pages. Screenshots will appear here.</p>';
    }
}

// Visual Diff Functions
async function generateDiff() {
    const text1 = document.getElementById('diffText1').value;
    const text2 = document.getElementById('diffText2').value;
    const resultDiv = document.getElementById('diffResult');

    if (!text1 || !text2) {
        alert('Please enter text in both boxes');
        return;
    }

    resultDiv.innerHTML = '<p style="text-align: center; color: #666;">Generating diff...</p>';

    try {
        const response = await fetch('/api/diff', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text1, text2 })
        });

        if (response.ok) {
            const diffHtml = await response.text();
            resultDiv.innerHTML = diffHtml;
        } else {
            resultDiv.innerHTML = '<p style="color: red; text-align: center;">Error generating diff</p>';
        }
    } catch (error) {
        console.error(error);
        resultDiv.innerHTML = '<p style="color: red; text-align: center;">Error: ' + error.message + '</p>';
    }
}

// Toggle between diff modes
function toggleDiffMode() {
    const mode = document.querySelector('input[name="diffMode"]:checked').value;
    document.getElementById('urlCompareMode').style.display = mode === 'url' ? 'block' : 'none';
    document.getElementById('textCompareMode').style.display = mode === 'text' ? 'block' : 'none';
}

// Compare website versions
async function compareWebsiteVersions() {
    const url = document.getElementById('compareUrlInput').value.trim();
    const resultDiv = document.getElementById('versionComparisonResult');

    if (!url) {
        alert('Please enter a URL');
        return;
    }

    resultDiv.innerHTML = '<p style="text-align: center; padding: 40px; color: #666;">Loading versions...</p>';

    try {
        const response = await fetch('/api/compare-versions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to compare versions');
        }

        const data = await response.json();

        // Display comparison
        resultDiv.innerHTML = `
            <div style="background: white; border-radius: 12px; padding: 25px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <div style="margin-bottom: 20px; padding-bottom: 15px; border-bottom: 2px solid #eee;">
                    <h3 style="margin: 0 0 5px 0; color: #333;">📊 Comparing: ${data.url}</h3>
                    <p style="color: #666; margin: 0; font-size: 14px;">
                        <strong>Old:</strong> ${data.old_version.date} → 
                        <strong>New:</strong> ${data.new_version.date}
                    </p>
                </div>
                
                <div style="margin-bottom: 25px;">
                    <h4 style="margin:0 0 10px 0; color: #4CAF50;">✨ Summaries</h4>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                        <div style="padding: 12px; background: #f5f5f5; border-radius: 8px; border-left: 3px solid #999;">
                            <strong style="color: #666;">Old Version</strong>
                            <p style="margin: 8px 0 0 0; font-size: 13px; color: #555;">${data.old_version.summary || 'No summary available'}</p>
                        </div>
                        <div style="padding: 12px; background: #e8f5e9; border-radius: 8px; border-left: 3px solid #4CAF50;">
                            <strong style="color: #2e7d32;">New Version</strong>
                            <p style="margin: 8px 0 0 0; font-size: 13px; color: #555;">${data.new_version.summary || 'No summary available'}</p>
                        </div>
                    </div>
                </div>
                
                <div>
                    <h4 style="margin: 0 0 10px 0; color: #2196F3;">📝 Text Diff</h4>
                    <div style="max-height: 600px; overflow-y: auto; border: 1px solid #ddd; border-radius: 8px;">
                        ${data.diff_html}
                    </div>
                </div>
            </div>
        `;

    } catch (error) {
        console.error(error);
        resultDiv.innerHTML = `
            <div style="text-align: center; padding: 40px; background: #ffebee; border-radius: 12px; color: #c62828;">
                <h3 style="margin: 0 0 10px 0;">❌ Error</h3>
                <p style="margin: 0;">${error.message}</p>
                <p style="margin: 10px 0 0 0; font-size: 13px;">Make sure this URL has been monitored and has at least 2 versions.</p>
            </div>
        `;
    }
}

// Quick access to view diff from analytics
function viewDiffForUrl(url) {
    // Switch to diff tab
    showTab('diff');

    // Set to URL comparison mode
    document.querySelector('input[name="diffMode"][value="url"]').checked = true;
    toggleDiffMode();

    // Fill in the URL and trigger comparison
    document.getElementById('compareUrlInput').value = url;
    compareWebsiteVersions();
}

async function linkedinLogin() {
    try {
        const btn = event.target;
        const originalText = btn.innerText;
        btn.innerText = "⏳ Opening Browser...";
        btn.disabled = true;

        const response = await fetch('/api/linkedin/login', { method: 'POST' });
        const data = await response.json();

        if (data.success) {
            alert("✅ Session Saved! You can now scrape LinkedIn pages.");
        } else {
            alert("❌ Login Failed: " + data.message);
        }

        btn.innerText = originalText;
        btn.disabled = false;
    } catch (error) {
        alert("Error: " + error);
    }
}

async function scrapeLinkedin() {
    const url = document.getElementById('linkedinUrlInput').value;
    if (!url) {
        alert("Please enter a LinkedIn URL");
        return;
    }

    const resultDiv = document.getElementById('linkedinResult');
    resultDiv.innerHTML = '<p style="color: #666; text-align: center;">⏳ Scraping... This may take a few seconds.</p>';

    try {
        const response = await fetch('/api/linkedin/scrape', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });

        const data = await response.json();

        if (data.success) {
            resultDiv.innerHTML = `<pre style="background: #fff; padding: 15px; border-radius: 8px; overflow-x: auto;">${JSON.stringify(data.data, null, 2)}</pre>`;
        } else {
            resultDiv.innerHTML = `<p style="color: red; text-align: center;">❌ Error: ${data.message}</p>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<p style="color: red; text-align: center;">❌ Error: ${error}</p>`;
    }
}

// --- Email Outreach Functions ---

async function searchLeads() {
    const keywords = document.getElementById('outreachKeywords').value;
    const location = document.getElementById('outreachLocation').value;
    const apiKey = document.getElementById('outreachApiKey').value;
    const maxResults = document.getElementById('outreachMaxResults').value;

    if (!keywords || !location) {
        alert('Please enter keywords and location');
        return;
    }

    try {
        const response = await fetch('/api/outreach/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ keywords, location, apiKey, maxResults })
        });

        const data = await response.json();
        alert(data.message);

        // Refresh leads after a delay
        setTimeout(refreshLeads, 2000);
    } catch (error) {
        console.error(error);
        alert('Error searching leads');
    }
}

async function refreshLeads() {
    try {
        const response = await fetch('/api/outreach/leads');
        const data = await response.json();
        renderLeads(data.leads);
    } catch (error) {
        console.error(error);
    }
}

function renderLeads(leads) {
    const tbody = document.getElementById('leadsTableBody');
    const leadCount = document.getElementById('leadCount');

    if (leads.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" style="padding: 40px; text-align: center; color: #999;">
                    No leads yet. Click "Search & Extract Contacts" to find companies.
                </td>
            </tr>
        `;
        leadCount.textContent = '';
        return;
    }

    leadCount.textContent = `(${leads.length} total)`;

    tbody.innerHTML = leads.map(lead => {
        const statusColor = {
            'new': '#2196F3',
            'sent': '#4CAF50',
            'error': '#f44336'
        }[lead.status] || '#999';

        return `
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 12px;">
                    <input type="text" value="${lead.company_name || ''}" 
                        onchange="updateLead(${lead.id}, 'company_name', this.value)"
                        style="border: 1px solid #ddd; padding: 4px 8px; border-radius: 4px; width: 100%;">
                </td>
                <td style="padding: 12px;">
                    <input type="email" value="${lead.email || ''}" 
                        onchange="updateLead(${lead.id}, 'email', this.value)"
                        style="border: 1px solid #ddd; padding: 4px 8px; border-radius: 4px; width: 100%;">
                </td>
                <td style="padding: 12px;">
                    <input type="text" value="${lead.contact_name || ''}" 
                        onchange="updateLead(${lead.id}, 'contact_name', this.value)"
                        style="border: 1px solid #ddd; padding: 4px 8px; border-radius: 4px; width: 100%;">
                </td>
                <td style="padding: 12px;">${lead.location || 'N/A'}</td>
                <td style="padding: 12px;">
                    <span style="padding: 4px 8px; border-radius: 4px; background: ${statusColor}; color: white; font-size: 12px;">
                        ${lead.status}
                    </span>
                </td>
                <td style="padding: 12px;">
                    <button onclick="deleteLead(${lead.id})" style="background: #f44336; color: white; border:none; padding: 6px 12px; border-radius: 4px; cursor: pointer;">
                        🗑️
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

async function updateLead(leadId, field, value) {
    try {
        await fetch(`/api/outreach/leads/${leadId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ [field]: value })
        });
    } catch (error) {
        console.error(error);
        alert('Error updating lead');
    }
}

async function deleteLead(leadId) {
    if (!confirm('Delete this lead?')) return;

    try {
        await fetch(`/api/outreach/leads/${leadId}`, { method: 'DELETE' });
        refreshLeads();
    } catch (error) {
        console.error(error);
        alert('Error deleting lead');
    }
}

async function clearLeads() {
    if (!confirm('Clear all leads? This cannot be undone.')) return;

    try {
        const response = await fetch('/api/outreach/leads/clear', { method: 'POST' });
        const data = await response.json();
        alert(data.message);
        refreshLeads();
    } catch (error) {
        console.error(error);
        alert('Error clearing leads');
    }
}

async function sendCampaign() {
    const subject = document.getElementById('emailSubject').value;
    const body = document.getElementById('emailBody').value;
    const smtpHost = document.getElementById('smtpHost').value;
    const smtpPort = document.getElementById('smtpPort').value;
    const smtpUsername = document.getElementById('smtpUsername').value;
    const smtpPassword = document.getElementById('smtpPassword').value;
    const smtpFromEmail = document.getElementById('smtpFromEmail').value || smtpUsername;

    if (!subject || !body) {
        alert('Please enter email subject and body');
        return;
    }

    if (!smtpHost || !smtpPort || !smtpUsername || !smtpPassword) {
        alert('Please complete SMTP configuration');
        return;
    }

    if (!confirm('Send emails to all pending leads? This action cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch('/api/outreach/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                subject,
                body,
                smtpConfig: {
                    host: smtpHost,
                    port: parseInt(smtpPort),
                    username: smtpUsername,
                    password: smtpPassword,
                    from_email: smtpFromEmail
                }
            })
        });

        const data = await response.json();

        if (data.success) {
            alert(data.message);
            // Refresh leads after a delay to see updated statuses
            setTimeout(refreshLeads, 3000);
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        console.error(error);
        alert('Error sending campaign');
    }
}

// Initial load
fetchPages();
;
