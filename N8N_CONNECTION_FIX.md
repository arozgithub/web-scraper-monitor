# 🔧 Fixing n8n Connection Issues

## Problem: "The service refused the connection - perhaps it is offline"

This happens when n8n is running in **Docker** and can't access `localhost`.

---

## Solution 1: Use Host IP Address (RECOMMENDED)

### Find Your IP Address:

**Windows PowerShell:**
```powershell
ipconfig
```
Look for "IPv4 Address" under your active network adapter.

From the logs, your IP is: **`10.30.49.163`**

### Update n8n HTTP Request Node:

**Change URL from:**
```
http://localhost:5001/scrape
```

**To:**
```
http://10.30.49.163:5001/scrape
```

✅ This should work immediately!

---

## Solution 2: Use host.docker.internal (Docker Desktop)

If you're using Docker Desktop on Windows:

**URL:**
```
http://host.docker.internal:5001/scrape
```

This is a special DNS name that Docker provides to access host machine services.

---

## Solution 3: Run n8n on Host (Not in Docker)

If you want to use `localhost`:

1. **Stop Docker n8n**
2. **Install n8n globally:**
   ```powershell
   npm install -g n8n
   ```
3. **Run n8n:**
   ```powershell
   n8n
   ```
4. **Now you can use:**
   ```
   http://localhost:5001/scrape
   ```

---

## Solution 4: Add Network Access in Docker

If n8n is in Docker, add network mode:

```bash
docker run -it --rm \
  --name n8n \
  --network="host" \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
```

With `--network="host"`, localhost will work.

---

## Quick Test

Test which URL works from your n8n:

### Test 1: Host IP
```
http://10.30.49.163:5001/health
```

### Test 2: Docker DNS
```
http://host.docker.internal:5001/health
```

### Test 3: Localhost (if n8n not in Docker)
```
http://localhost:5001/health
```

---

## Step-by-Step Fix for n8n

1. **Open your n8n workflow**
2. **Click on the HTTP Request node**
3. **Change the URL:**
   
   **From:**
   ```
   http://localhost:5001/scrape
   ```
   
   **To:**
   ```
   http://10.30.49.163:5001/scrape
   ```

4. **Click "Execute Node"**
5. **✅ Should work now!**

---

## Verify API is Running

Open PowerShell and test:

```powershell
# Test with localhost (from your computer)
Invoke-WebRequest -Uri http://localhost:5001/health

# Test with IP (what n8n in Docker needs)
Invoke-WebRequest -Uri http://10.30.49.163:5001/health
```

Both should return:
```json
{
  "status": "healthy",
  "service": "web-scraper-api",
  "version": "1.0.0"
}
```

---

## Updated n8n Configuration

### HTTP Request Node Settings:

**Method:** `POST`

**URL:** `http://10.30.49.163:5001/scrape` ← **Use your IP!**

**Headers:**
- Content-Type: `application/json`

**Body:**
```json
{
  "url": "https://example.com"
}
```

**Options:**
- Timeout: `30000` (30 seconds)
- Redirect: `Follow All Redirects`

---

## Troubleshooting Checklist

- [ ] API server is running (check terminal shows "Ready for n8n integration!")
- [ ] Using correct IP address (not localhost if n8n is in Docker)
- [ ] Port 5001 is not blocked by firewall
- [ ] No typos in URL
- [ ] HTTP not HTTPS (no SSL on local server)
- [ ] Content-Type header is set to application/json

---

## Windows Firewall (If Still Not Working)

If n8n still can't connect, allow Python through firewall:

1. **Windows Security** → **Firewall & network protection**
2. **Allow an app through firewall**
3. **Change settings**
4. Find **Python** and check both Private and Public
5. **OK**

---

## Complete Working Example

```json
{
  "nodes": [
    {
      "name": "HTTP Request",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://10.30.49.163:5001/scrape",
        "options": {},
        "headerParameters": {
          "parameters": [
            {
              "name": "Content-Type",
              "value": "application/json"
            }
          ]
        },
        "bodyType": "json",
        "bodyParameters": {
          "parameters": []
        },
        "jsonBody": "{\n  \"url\": \"https://example.com\"\n}"
      }
    }
  ]
}
```

---

## Still Having Issues?

### Check API Logs
Look at the terminal running `scraper_api.py` - you should see incoming requests logged there.

### Test from n8n's Perspective
If n8n is in Docker, exec into the container and test:

```bash
docker exec -it n8n sh
curl http://host.docker.internal:5001/health
```

Or:
```bash
curl http://10.30.49.163:5001/health
```

---

## Summary

**The Fix:** Change URL in n8n from `localhost` to your IP address:

```
http://10.30.49.163:5001/scrape
```

This is because **n8n running in Docker cannot access `localhost`** - it needs your actual host IP address!

✅ **Try this now and it should work!**
