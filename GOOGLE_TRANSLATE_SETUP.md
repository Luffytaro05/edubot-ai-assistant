# Google Translate Integration - Quick Setup Guide

## ⚠️ Important: Using deep-translator Library

Due to compatibility issues with `googletrans` and `httpcore`, we're using the **deep-translator** library which is more stable and actively maintained.

## Installation Steps

### 1. Install the Required Packages

Run this command in your terminal (in the project directory):

```bash
pip install deep-translator==1.11.4 langdetect==1.0.9
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

### ✅ Fixed: httpcore.SyncHTTPTransport Error

**Previous issue:**
```
AttributeError: module 'httpcore' has no attribute 'SyncHTTPTransport'
```

**Solution:** Replaced `googletrans==4.0.0rc1` with `deep-translator==1.11.4` and `langdetect==1.0.9` which don't have compatibility issues.

---

### 2. Restart the Flask Server

After installing, restart your application:

**Stop the server:** Press `Ctrl+C` in the terminal

**Start the server:**
```bash
python app.py
```

---

### 3. Test the Integration

#### Test in Filipino:
```
User: Kumusta! Ano ang oras ng opisina?
Bot: Kamusta! Ang mga opisina ng TCC ay bukas mula 8:00 AM hanggang 5:00 PM...
```

#### Test in Spanish:
```
User: ¿Cuáles son las horas de oficina?
Bot: Las oficinas de TCC están abiertas de 8:00 AM a 5:00 PM...
```

#### Test in English:
```
User: What are the office hours?
Bot: TCC offices are open from 8:00 AM to 5:00 PM...
```

---

## Verify It's Working

### Check Console Logs:

When a user sends a message in Filipino, you should see:

```
🌐 Detected language: tl (confidence: 0.99)
📝 Translated to English: 'Kumusta!' → 'Hello!'
User guest asked: Hello!
Using neural network response
🌐 Translated response back to tl: 'Hello! How can I help you?' → 'Kamusta! Paano kita matutulungan?'
✅ Status: resolved | Office: General
```

### Check Browser Console:

Open Developer Tools (F12) → Console tab:

```javascript
🌐 Language detected: tl
📝 Original message: "Kumusta!"
📝 Translated to English: "Hello!"
💬 Response in tl: "Kamusta! Paano kita matutulungan?"
💬 Original English response: "Hello! How can I help you?"
✅ Status: resolved | Office: General
```

---

## Troubleshooting

### Problem: "No module named 'deep_translator'" or "No module named 'langdetect'"

**Solution:**
```bash
pip install deep-translator==1.11.4 langdetect==1.0.9
```

Then restart the server.

---

### Problem: "AttributeError: module 'httpcore' has no attribute 'SyncHTTPTransport'"

**Solution:** This was caused by the old `googletrans` library. We've switched to `deep-translator` which doesn't have this issue.

1. Uninstall old packages:
```bash
pip uninstall googletrans -y
```

2. Install new packages:
```bash
pip install deep-translator==1.11.4 langdetect==1.0.9
```

3. Restart Flask server

---

### Problem: Translation not working

**Check:**
1. Internet connection (Google Translate needs network access)
2. Console for error messages
3. Try restarting the Flask server

**Fallback:** If translation fails, the system automatically continues in English.

---

### Problem: Slow responses

**Cause:** Translation adds 1-2 seconds to response time

**Solutions:**
- Normal for free tier
- For faster responses, upgrade to Google Cloud Translation API (paid)
- Implement caching for common phrases

---

## What Changed

### ✅ Modified Files:

1. **app.py**
   - Line 43: Added `from googletrans import Translator`
   - Line 51: Added `translator = Translator()`
   - Lines 1462-1607: Modified `/predict` endpoint with translation

2. **static/app.js**
   - Lines 1557-1584: Enhanced logging for translation info

3. **requirements.txt**
   - Line 11: Added `googletrans==4.0.0rc1`

### ❌ NOT Modified:

- `/chat` endpoint - Remains unchanged
- Translation mode (`sendMessageWithTranslation`) - Unchanged
- Other endpoints - Unchanged

---

## Key Features

✅ **Automatic language detection** - No manual selection needed
✅ **100+ languages supported** - Including Filipino, Spanish, Chinese, etc.
✅ **Bidirectional translation** - User message → English → Response → User language
✅ **Error resilience** - Falls back to English if translation fails
✅ **Debug logging** - See translation process in console
✅ **Metadata included** - Language, status, office tracked
✅ **Admin visibility** - Conversations saved in user's language

---

## Testing Commands

```bash
# Test 1: Filipino
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"message": "Kumusta!", "user": "test_user"}'

# Test 2: Spanish  
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"message": "Hola", "user": "test_user"}'

# Test 3: English
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "user": "test_user"}'
```

---

## Important Reminder

**This integration only affects the `/predict` endpoint.**

- ✅ `/predict` - **Has Google Translate** (multilingual)
- ❌ `/chat` - **No changes** (existing translation system)

If you want to use the translated chatbot, make sure your frontend is calling `/predict`, not `/chat`.

---

## Date: October 10, 2025

Ready to test! 🌐✨

