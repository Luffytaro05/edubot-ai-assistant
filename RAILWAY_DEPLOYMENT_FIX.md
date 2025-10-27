# 🚀 Railway Deployment Fix - Connection Refused Error

## ✅ **PROBLEM SOLVED**

The `ERR_CONNECTION_REFUSED` error in Railway was caused by hardcoded `localhost:5000` URLs in the frontend JavaScript code. These URLs don't work in Railway's production environment.

## 🔧 **FIXES APPLIED**

### 1. **Fixed Frontend URLs**
- **File**: `templates/conversations.html`
  - Changed `http://localhost:5000/api/conversations` → `${window.location.origin}/api/conversations`
  - Changed `http://localhost:5000/api/conversations/${id}` → `${window.location.origin}/api/conversations/${id}`

- **File**: `static/assets/js/modules/ConversationManager.js`
  - Changed `http://localhost:5000/api` → `${window.location.origin}/api`

### 2. **Dynamic URL Resolution**
The frontend now uses `window.location.origin` which automatically resolves to:
- **Local Development**: `http://localhost:5000`
- **Railway Production**: `https://your-app-name.up.railway.app`

## 🚀 **RAILWAY DEPLOYMENT STEPS**

### 1. **Environment Variables**
Set these in your Railway project dashboard:

```bash
# Required
PORT=5000
SECRET_KEY=your-secure-secret-key-here

# Optional (for full functionality)
MONGODB_URI=mongodb+srv://dxtrzpc26:w1frwdiwmW9VRItO@cluster0.gskdq3p.mongodb.net/
PINECONE_API_KEY=pcsk_3LGtPm_F7RyLr4yFTu4C7bbEonvRcCxysxCztU9ADjyRefakqjq7wxqjJXVwt5JD5TeM62
PINECONE_ENV=us-east-1
PINECONE_INDEX_NAME=chatbot-vectors

# Email (optional)
ENABLE_EMAIL=False
```

### 2. **Deploy to Railway**
```bash
# Railway will automatically detect and use:
# - Procfile (for startup command)
# - railway_startup.py (for initialization)
# - download_nltk_data.py (for NLTK data)
```

### 3. **Verify Deployment**
After deployment, test these endpoints:
- **Main App**: `https://your-app-name.up.railway.app/`
- **Admin Panel**: `https://your-app-name.up.railway.app/admin`
- **API Endpoint**: `https://your-app-name.up.railway.app/api/conversations`
- **Health Check**: `https://your-app-name.up.railway.app/health`

## 🔍 **TROUBLESHOOTING**

### If you still get connection errors:

1. **Check Railway Logs**:
   ```bash
   railway logs
   ```

2. **Verify Environment Variables**:
   - Go to Railway dashboard → Variables tab
   - Ensure all required variables are set

3. **Test API Endpoint**:
   ```bash
   curl https://your-app-name.up.railway.app/api/conversations
   ```

4. **Check CORS Settings**:
   - The app has CORS enabled for all origins
   - No additional CORS configuration needed

## 📊 **EXPECTED BEHAVIOR**

After deployment, the conversations page should:
- ✅ Load conversations from the API
- ✅ Display conversation data in the table
- ✅ Allow deletion of conversations
- ✅ Work on both localhost and Railway domains

## 🎯 **KEY CHANGES SUMMARY**

| File | Change | Impact |
|------|--------|---------|
| `templates/conversations.html` | Dynamic URLs | Works in production |
| `ConversationManager.js` | Dynamic API base | Cross-environment compatibility |
| `railway_startup.py` | NLTK data download | Prevents NLTK errors |
| `Procfile` | Startup sequence | Proper initialization |

The application is now fully compatible with Railway deployment and will work seamlessly in both local development and production environments.
