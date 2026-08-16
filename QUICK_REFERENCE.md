# Nitro Infinity AI - Quick Reference Card

## 🚀 Start Backend Server (3 seconds)

```powershell
cd d:\nitro.ai
python -m backend.main
```

Note the IP address shown (e.g., `192.168.x.x:8000`)

## 📱 Access from Other Devices

**Browser:**
```
http://192.168.x.x:8000
```

**Test Connection:**
```bash
curl http://192.168.x.x:8000/health
```

## 🔧 Configuration Quick Keys

### Common Setups

```powershell
# Default (recommended)
python -m backend.main

# Custom port
$env:NITRO_PORT="9000"; python -m backend.main

# Limited workers (slow laptop)
$env:NITRO_WORKERS="1"; python -m backend.main

# Debug mode
$env:NITRO_LOG_LEVEL="debug"; python -m backend.main

# All options at once
$env:NITRO_HOST="0.0.0.0"; $env:NITRO_PORT="8000"; `
$env:NITRO_WORKERS="2"; $env:NITRO_LOG_LEVEL="info"; `
python -m backend.main
```

## 🌐 Frontend Configuration (Browser Console)

```javascript
// Connect to network backend
localStorage.setItem('nitro_backend_url', 'http://192.168.x.x:8000');
location.reload();

// Clear & use default
localStorage.removeItem('nitro_backend_url');
location.reload();

// Check current backend URL
console.log(localStorage.getItem('nitro_backend_url'));
```

## 📊 Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/chat` | POST | Send message |
| `/history/{user_id}` | GET | Chat history |
| `/languages` | GET | Available languages |
| `/metrics` | GET | System metrics |
| `/metrics/prom` | GET | Prometheus metrics |
| `/bots` | GET | List bots |

## 🔍 Find Your IP Address

```powershell
# Quick IP check
ipconfig | Select-String "IPv4"

# Or use startup output:
# "Other devices: http://192.168.x.x:8000"
```

## 🛠️ Environment Variables

| Variable | Default | Example |
|----------|---------|---------|
| NITRO_HOST | 0.0.0.0 | 127.0.0.1 (localhost only) |
| NITRO_PORT | 8000 | 9000 |
| NITRO_WORKERS | auto | 1, 2, 4 |
| NITRO_RAM_LIMIT_MB | 3500 | 2500, 4000 |
| NITRO_LOG_LEVEL | info | debug, warning, error |
| NITRO_RELOAD | false | true (dev only) |

## 💾 Install Dependencies

```powershell
pip install fastapi uvicorn pydantic
pip install piper-tts          # For voice (optional)
```

## 📈 Monitor Performance

```powershell
# Watch RAM usage
while ($true) {
    Get-Process python | Select @{N="RAM(MB)";E={$_.WorkingSet/1MB}}
    Start-Sleep 2
}

# Check if port is in use
Get-NetTCPConnection -LocalPort 8000
```

## ❌ Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| "Port 8000 in use" | `$env:NITRO_PORT="9000"` |
| "Module not found" | `pip install fastapi uvicorn` |
| "Can't connect from other device" | Check firewall, same Wi-Fi |
| "Slow/OOM error" | `$env:NITRO_WORKERS="1"` |
| "No internet access" | Works offline (all local) |

## 🎯 Typical Workflow

```powershell
# 1. Activate environment
.venv\Scripts\Activate.ps1

# 2. Start backend
python -m backend.main

# 3. Note IP (e.g., 192.168.x.x)

# 4. On another device:
#    Browser: http://192.168.x.x:8000
#    API: curl http://192.168.x.x:8000/chat -X POST ...

# 5. Stop: Ctrl+C
```

## 📚 Full Documentation

- `CENTRAL_SERVER_SETUP.md` - Complete setup guide
- `NETWORK_SERVER_SETUP.md` - Detailed network config
- `FRONTEND_NETWORK_CONFIG.md` - Frontend connectivity
- `NITRO_VOICE_INTEGRATION.md` - Voice synthesis

## 🔑 API Usage Example

```bash
# Send chat message
curl -X POST http://192.168.x.x:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user1","message":"Hello","guest_mode":true}'

# Get chat history
curl http://192.168.x.x:8000/history/user1

# Check health
curl http://192.168.x.x:8000/health
```

## 🎨 Start Frontend (Optional)

```bash
cd frontend
npm install
npm start  # Runs on http://localhost:3000

# Then configure backend in browser console (see above)
```

## ⚡ Performance Tuning (4GB RAM)

```powershell
# Conservative (1 worker, 2.5GB RAM)
$env:NITRO_WORKERS="1"; $env:NITRO_RAM_LIMIT_MB="2500"

# Balanced (2 workers, 3.5GB RAM) - DEFAULT
$env:NITRO_WORKERS="2"; $env:NITRO_RAM_LIMIT_MB="3500"

# Aggressive (4 workers, 4GB RAM) - if RAM available
$env:NITRO_WORKERS="4"; $env:NITRO_RAM_LIMIT_MB="4000"
```

## 🔒 Security Notes

✅ Local network = safe (no config needed)
⚠️ Internet exposure = needs HTTPS + auth (advanced)

## 🎪 All Features

✅ Chat & History | ✅ Bots | ✅ Images | ✅ Voice | ✅ Search
✅ Recommendations | ✅ Puzzles | ✅ Multilingual (16 langs) | ✅ Metrics

## 🚨 Emergency

```powershell
# Force stop all Python processes
Stop-Process -Name python -Force

# Kill process on specific port
netstat -ano | findstr :8000  # Find PID
taskkill /PID <PID> /F

# Clear backend data (careful!)
Remove-Item backend\data\nitro_state.json
```

## 📞 Quick Help

```javascript
// In browser console
// Check if connected
fetch('http://192.168.x.x:8000/health').then(r=>r.json()).then(console.log)

// Send test message
fetch('http://192.168.x.x:8000/chat',{
  method:'POST',
  headers:{'Content-Type':'application/json'},
  body:JSON.stringify({user_id:'test',message:'hi',guest_mode:true})
}).then(r=>r.json()).then(console.log)

// Set backend URL
localStorage.setItem('nitro_backend_url','http://192.168.x.x:8000')
```

---

**Bookmark this page! 🔖**

Print or save for quick reference.
