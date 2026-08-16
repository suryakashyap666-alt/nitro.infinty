# Nitro Infinity Infinity AI - Setup & Start Guide

## 📥 Download & Install

### 1. Clone Repository 
```powershell
git clone <nitro-ai-repo> F:\Nitro Infinty AI
cd F:\Nitro Infinty AI
```

### 2. Install Python (3.8+)
```powershell
# Download from python.org or use Windows Store
# Verify installation:
python --version
```

### 3. Create Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 4. Install Dependencies
```powershell
pip install fastapi uvicorn cryptography piper-tts python-multipart
```

---

## 🚀 Start Server (Choose One)

> Run the environment variable lines and `python -m backend.main` in the same PowerShell terminal window. If you open a new window, re-run the env var lines there first.

### Step-by-step server start
1. Open PowerShell and change to the repository directory.
2. Activate the Python virtual environment: `.\.venv\Scripts\Activate.ps1`.
3. Set local server environment variables using your laptop's SSD path.
4. Start Nitro Infinity AI with `python -m backend.main`.
5. Open Nitro Infinity AI in the browser at `http://localhost


### Option 1: Local Browser Server (Recommended for SSD laptop)
```powershell
$env:NITRO_HOST="0.0.0.0"
$env:NITRO_PORT="8000"
$env:NITRO_DATA_DIR="D:\NitroData"
python -m backend.main
```
✅ Open Nitro Infinity AI in your browser at `http://localhost:8000`
✅ Uses the SSD laptop for backend storage and local data persistence
✅ Keeps all Nitro Infinity AI features and APIs working
❌ Not exposed to the internet unless you configure port forwarding

Open Nitro Infinity AI in your browser by typing:
- `http://localhost:8000`

### Option 2: Secure Local (Office/Building)
```powershell
$env:NITRO_HTTPS="true"
python -m backend.main
```
✅ Access: `https://localhost:8443` or `https://192.168.x.x:8443`
✅ Encrypted local traffic
⚠️ Browser shows cert warning (click "Advanced" → "Proceed")
❌ Still not for internet

### Option 3: Internet Access (Full Security) ⭐
```powershell
$env:NITRO_HTTPS="true"
$env:NITRO_API_KEY="YourSecureKey123"
$env:NITRO_API_KEY_REQUIRED="true"
python -m backend.main
```
✅ Access: `https://your-public-ip:8443` from internet
✅ Requires API key header for all requests
✅ Fully encrypted traffic
✅ Secure for remote use if port forwarding and firewall are configured

### Internet / Firewall / API Key Notes
- Environment variables are only active in the current PowerShell session.
- Use the same terminal to set vars and start the server.
- If Windows Firewall prompts appear, allow access for Python/port 8443.
- To allow port 8443 manually:
```powershell
New-NetFirewallRule -DisplayName "Nitro HTTPS" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8443
```
- If behind a router, set port forwarding from external port `8443` to your PC's local IP on port `8443`.
- Every request must include `X-API-Key: YourSecureKey123` when `NITRO_API_KEY_REQUIRED` is `true`.

---

## 🔍 Check If Running

### Get Your IP
```powershell
ipconfig | findstr "IPv4"
# Look for: 192.168.x.x (local) or public IP (remote)
```

### Check Server Started
```powershell
# Look for output like:
# 🚀 Server started on: https://0.0.0.0:8443
# Other devices: https://203.0.113.5:8443
```

### View Log Details
```powershell
# Server logs show in the same terminal window
# NITRO_LOG_LEVEL can be: debug, info, warning, error
$env:NITRO_LOG_LEVEL="debug"
python -m backend.main
```

---

## ✅ Test Server

### Test 1: Local HTTPS
```bash
curl --insecure https://localhost:8443/health
# Expected: {"ok":true}
```

### Test 2: Local Network
```bash
# From another device on same Wi-Fi
curl --insecure https://192.168.x.x:8443/health
# Expected: {"ok":true}
```

### Test 3: Chat API (No Auth)
```bash
curl -X POST https://localhost:8443/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","message":"Hello Nitro","guest_mode":true}'
```

### Test 4: Chat API (With API Key)
```bash
curl -X POST https://192.168.x.x:8443/chat \
  -H "X-API-Key: YourSecureKey123" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user1","message":"Hello","guest_mode":true}'
```

### Test 5: In Browser
```
Local: https://localhost:8443
Network: https://192.168.x.x:8443 or https://your-ip:8443
(Click through cert warning, it's normal for self-signed)
```

---

## 🔧 Environment Variables (Optional)

### Network
```powershell
$env:NITRO_HOST="0.0.0.0"          # Listen on all interfaces (default)
$env:NITRO_PORT="8443"              # Port number (default: 8443 HTTPS, 8000 HTTP)
```

### Performance (4GB RAM)
```powershell
$env:NITRO_WORKERS="2"              # Auto-detect if not set
$env:NITRO_RAM_LIMIT_MB="3500"     # Leave 500MB for OS
```

### HTTPS/SSL
```powershell
$env:NITRO_HTTPS="true"             # Enable HTTPS
$env:NITRO_CERT_PATH="C:\path\cert.pem"  # Custom cert (optional)
$env:NITRO_KEY_PATH="C:\path\key.pem"    # Custom key (optional)
```

### API Key
```powershell
$env:NITRO_API_KEY="your-secret-key"      # Set API key
$env:NITRO_API_KEY_REQUIRED="true"        # Require for all requests
```

### Logging
```powershell
$env:NITRO_LOG_LEVEL="info"        # debug, info, warning, error
$env:NITRO_RELOAD="false"           # Auto-reload on changes
```

---

## 📱 Access Methods

### Local Machine (HTTP)
```
Browser: http://localhost:8000
```

### Local Machine (HTTPS)
```
Browser: https://localhost:8443
API: curl https://localhost:8443/chat
```

### Same Wi-Fi (HTTPS)
```
IP: 192.168.x.x (check with: ipconfig)
Browser: https://192.168.x.x:8443
API: curl https://192.168.x.x:8443/chat
```

### Remote/Internet (HTTPS + API Key)
```
IP: Your public IP (check: https://whatismyip.com)
Browser: https://your-public-ip:8443
API: curl -H "X-API-Key: key" https://your-public-ip:8443/chat

Requires:
1. Port forwarding setup (router settings)
2. API key header in all requests
3. Firewall exception for port 8443
```

---

## 🔐 Set Up API Key

### Generate Strong Key (PowerShell)
```powershell
$chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$'
$key = -join ((0..31) | ForEach-Object { Get-Random -InputObject $chars.ToCharArray() })
Write-Host "API Key: $key"
# Copy and use as: NITRO_API_KEY
```

### Use API Key in Requests
```bash
# Always include this header:
-H "X-API-Key: your-api-key"

# Example:
curl -X POST https://your-ip:8443/chat \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user1","message":"Hello"}'
```

---

## 🧪 Quick Test Script

```powershell
# 1. Start server (keep terminal open)
$env:NITRO_HTTPS="true"
$env:NITRO_API_KEY="TestKey123"
python -m backend.main

# 2. In another PowerShell window, test:
$headers = @{
  'X-API-Key' = 'TestKey123'
  'Content-Type' = 'application/json'
}

$body = @{
  user_id = 'test'
  message = 'Hello'
  guest_mode = $true
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri 'https://localhost:8443/chat' `
  -Method POST `
  -Headers $headers `
  -Body $body `
  -SkipCertificateCheck

$response.Content | ConvertFrom-Json
```

---

## 🌍 Internet Access Setup

### Step 1: Find Public IP
```powershell
# Check your public IP
Invoke-WebRequest -Uri 'https://api.ipify.org?format=json' | ConvertFrom-Json
```

### Step 2: Port Forward (Router)
```
1. Go to: http://192.168.1.1 (or your router IP)
2. Login with admin credentials
3. Find: Port Forwarding settings
4. Set:
   External Port: 8443
   Internal IP: 192.168.x.x (your laptop)
   Internal Port: 8443
5. Save and restart router
```

### Step 3: Allow Firewall
```powershell
# Windows Defender Firewall
New-NetFirewallRule -DisplayName "Nitro HTTPS" `
  -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8443
```

### Step 4: Start with Security
```powershell
$env:NITRO_HTTPS="true"
$env:NITRO_API_KEY="your-strong-key-here"
$env:NITRO_API_KEY_REQUIRED="true"
python -m backend.main
```

### Step 5: Test from Remote Device
```bash
curl -X POST https://your-public-ip:8443/chat \
  -H "X-API-Key: your-strong-key-here" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","message":"Hello from far away"}'
```

---





## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 8443 already in use | Change port: `$env:NITRO_PORT="9443"` |
| Certificate error (SSL) | Add `--insecure` to curl or `verify=False` in Python |
| Out of memory | Reduce workers: `$env:NITRO_WORKERS="1"` |
| API key rejected | Check header is exact: `X-API-Key` (case-sensitive) |
| Connection refused | Check firewall allows port 8443 |
| High CPU usage | Normal during inference, <80% is OK |
| Can't access from network | Check firewall, CORS enabled, correct IP |

---

## 📊 System Resources

**4GB RAM + SSD:**
- Base memory: 500-700 MB
- Load memory: 800-1500 MB
- Concurrent users: 2-3
- Response time: 200-500 ms
- Startup: 2-3 seconds

---

## ✨ What's Built In

✅ Chat with AI (all topics)
✅ Voice synthesis (16 languages)
✅ Image generation & analysis
✅ Bot marketplace
✅ Learning system
✅ Web search
✅ Puzzle games
✅ Food recommendations
✅ Emotion detection
✅ Code assistance
✅ Math solver
✅ Memory system
✅ Multi-device access
✅ HTTPS encryption
✅ API key security
✅ 4GB RAM optimized

---

## 🎯 Common Commands

```powershell
# Activate environment
.\.venv\Scripts\Activate.ps1

# Start local
python -m backend.main

# Start with HTTPS
$env:NITRO_HTTPS="true"; python -m backend.main

# Start with full security
$env:NITRO_HTTPS="true"; $env:NITRO_API_KEY="key"; $env:NITRO_API_KEY_REQUIRED="true"; python -m backend.main

# Check IP
ipconfig | findstr "IPv4"

# View processes
Get-Process python | Select-Object ProcessName, @{N="RAM_MB"; E={[math]::Round($_.WorkingSet/1MB)}}

# Kill server
Stop-Process -Name python
```

---

## 🐧 Linux / macOS — Start server (quick)

Run these commands from your project root. On Ubuntu, recreate the venv if it was created by Windows or if pip reports an externally-managed environment.

> Note: If your repo is on a FAT/VFAT drive (`/run/media/...`), Linux virtual environments often fail because that filesystem does not support the symlinks Python uses. In that case, create the venv on your home directory or another Linux filesystem (`ext4`) and run the app from there.

```bash
cd '/run/media/lakshya-kashyap/B630-A264/Nitro Infinity AI'
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn cryptography piper-tts python-multipart
# Start in foreground (useful for debugging)
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

To run detached (so it survives closing the terminal):

```bash
cd '/run/media/lakshya-kashyap/B630-A264/Nitro Infinity AI'
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn cryptography piper-tts
nohup python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 > uvicorn.log 2>&1 &
echo $! > run/nitro.pid
```

Stop the detached server:

```bash
kill $(cat run/nitro.pid) || pkill -f 'uvicorn' || true
```

Quick health check:

```bash
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/health').read())"
```

Logs are written to `uvicorn.log` when using `nohup`. The `run/` folder stores the pid file.

---

## 💡 Next Steps

1. **Install & Start**: `python -m backend.main`
2. **Test Local**: `curl https://localhost:8443/health`
3. **Get IP**: `ipconfig | findstr "IPv4"`
4. **Test Network**: `curl https://192.168.x.x:8443/health`
5. **Deploy**: Set `NITRO_HTTPS=true` + `NITRO_API_KEY=...`
6. **Access Anywhere**: Use public IP + API key

---

**That's it! Your Nitro Infinity AI is ready. 🚀**








## ⚡ Quickstart: Start Nitro Infinity AI Easily on Ubuntu

 killall node uvicorn python3 2>/dev/null || true

cd ~/Desktop/Nitro_Decoupled_AI/nitro

./start.sh 