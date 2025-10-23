# 🌐 Automatic English ↔ Filipino Translation System

## Overview

The **TCC Assistant Chatbot** now features an **Automatic Translation System** that enables seamless bilingual communication between English and Filipino. The system automatically detects the user's language and provides responses in the same language—**without requiring any manual toggles or dropdowns**.

---

## 🎯 Key Features

✅ **Automatic Language Detection** - Detects whether the user is typing in English or Filipino  
✅ **Seamless Translation** - Translates user input to English for processing  
✅ **Response Translation** - Translates bot responses back to user's language  
✅ **Free Google Translate API** - Uses the free Google Translate Web API (no API key needed)  
✅ **Rules-Based Chatbot** - Simple keyword-based responses (no AI/OpenAI)  
✅ **Zero Configuration** - Works automatically without manual language selection  

---

## 📂 Files Modified

### 1. **`chat.py`**
- **Added:** `get_chatbot_response()` function
- **Purpose:** Rules-based chatbot logic with TCC-specific responses
- **Features:**
  - Handles TCC E-Hub, student portal, and office inquiries
  - Provides information about Admission, Registrar, ICT, Guidance, and OSA offices
  - Responds to greetings, thanks, and farewells
  - Supports both English and Filipino keywords (e.g., "salamat")
- **Exported:** `save_message()` function for MongoDB storage

### 2. **`app.py`**
- **Added:** `/chat` route - Chatbot endpoint with MongoDB storage
  - Saves original user message (in user's language)
  - Processes translated message (in English)
  - Returns English response for frontend translation
- **Added:** `/save_bot_message` route - Saves bot responses to MongoDB
  - Stores translated bot response in user's language
  - Maintains conversation history in MongoDB
- **Added:** `/translate` route - Optional backend translation endpoint
- **Dependencies:** Added `import requests`, `get_chatbot_response`, and `save_message` from chat.py

### 3. **`static/app.js`**
- **Added:** Translation system state variables (`userLanguage`, `translationEnabled`)
- **Added:** `translateText()` - Translates text using Google Translate API
- **Added:** `detectLanguage()` - Detects if message is English or Filipino
- **Added:** `sendMessageWithTranslation()` - Handles complete message flow:
  - Sends original message to backend for MongoDB storage
  - Sends translated message for processing
  - Translates response back to user's language
  - Saves translated response to MongoDB
- **Modified:** `onSendButton()` - Integrated translation into existing message flow

### 4. **`templates/base.html`**
- **Status:** Already properly configured
- **Elements:** Chatbot UI, input field, send button, typing indicator

---

## 🔄 How It Works

| Step | Process | Example |
|------|---------|---------|
| **1** | User types message in English or Filipino | `"Magandang umaga!"` |
| **2** | System detects language using Google Translate API | Detected: **Filipino** |
| **3** | **Original message saved to MongoDB** (user's language) | MongoDB: `"Magandang umaga!"` |
| **4** | Message translated to English for processing | `"Good morning!"` |
| **5** | Rules-based chatbot processes English message | Matches greeting pattern |
| **6** | Bot generates response in English | `"Hello! Welcome to TCC Assistant..."` |
| **7** | Response translated back to Filipino (if needed) | `"Kumusta! Maligayang pagdating sa TCC Assistant..."` |
| **8** | **Translated response saved to MongoDB** (user's language) | MongoDB: `"Kumusta! Maligayang..."` |
| **9** | User sees response in their own language | Filipino output displayed |

---

## 💬 Example Conversations

### English Example
```
User: "What are the office hours?"
Bot:  "TCC offices are open from 8:00 AM to 5:00 PM, Monday to Friday."
```

### Filipino Example
```
User: "Ano ang oras ng opisina?"
Bot:  "Ang mga opisina ng TCC ay bukas mula 8:00 AM hanggang 5:00 PM, Lunes hanggang Biyernes."
```

### Mixed Conversation
```
User: "Hi! Paano mag-reset ng password?"
Bot:  "Kumusta! Upang i-reset ang iyong password, bisitahin ang ICT Office sa IT Building, Room 101..."
```

---

## 🛠️ Technical Details

### Language Detection Logic

The system uses a **hybrid approach** for language detection:

1. **Google Translate Comparison**
   - Sends text to Google Translate API
   - Compares original vs. translated text
   - If texts are identical → English
   - If texts differ → Likely Filipino

2. **Filipino Keyword Detection**
   - Checks for common Filipino words:
     ```javascript
     ['ako', 'ikaw', 'siya', 'kami', 'tayo', 'kayo', 'sila', 
      'ang', 'ng', 'mga', 'sa', 'na', 'ay', 'po', 'opo',
      'magandang', 'salamat', 'paano', 'ano', 'saan', 'kailan']
     ```
   - Presence of these words → Filipino

3. **Default Fallback**
   - If uncertain → Defaults to English

### Translation API

- **Endpoint:** `https://translate.googleapis.com/translate_a/single`
- **Parameters:**
  - `client=gtx` - Web client (free, no key)
  - `sl=auto` - Auto-detect source language
  - `tl={target}` - Target language (en/fil)
  - `dt=t` - Return translation only
  - `q={text}` - Text to translate
- **Response Format:**
  ```javascript
  [[["translated text", "original text", null, null, ...], ...], ...]
  ```

---

## 📋 Supported Topics & Keywords

### TCC E-Hub / Portal
- **English:** "TCC E-Hub", "eHub", "student portal"
- **Filipino:** "TCC E-Hub", "portal ng estudyante"

### Admission Office
- **English:** "admission", "apply", "enroll"
- **Filipino:** "admission", "mag-apply", "mag-enroll"

### Registrar's Office
- **English:** "registrar", "transcript", "grades"
- **Filipino:** "registrar", "transcript", "grado"

### ICT Office
- **English:** "ICT", "password", "WiFi", "internet"
- **Filipino:** "ICT", "password", "WiFi", "internet"

### Guidance Office
- **English:** "guidance", "counseling", "scholarship"
- **Filipino:** "guidance", "counseling", "scholarship"

### Office of Student Affairs
- **English:** "OSA", "student affairs", "clubs", "activities"
- **Filipino:** "OSA", "student affairs", "samahan", "aktibidad"

### Office Hours
- **English:** "office hours", "open"
- **Filipino:** "oras ng opisina", "bukas"

### Greetings
- **English:** "hello", "hi", "good morning"
- **Filipino:** "kumusta", "magandang umaga", "kamusta"

### Thanks
- **English:** "thank you", "thanks"
- **Filipino:** "salamat"

### Goodbye
- **English:** "goodbye", "bye"
- **Filipino:** "paalam"

---

## ⚙️ Configuration

### Enable/Disable Translation

The translation system is **enabled by default**. To disable it:

```javascript
// In static/app.js, modify the constructor
this.translationEnabled = false; // Set to false to disable
```

### Backend Routes

The system uses two routes:

1. **`/chat`** (Translation Mode)
   - Receives: English-translated message
   - Returns: English response
   - Frontend handles translation

2. **`/predict`** (Original Mode)
   - Full NLP-based chatbot
   - Used when `translationEnabled = false`

---

## 🧪 Testing the Translation System

### Test Case 1: Pure English
```
Input:  "What are the office hours?"
Output: "TCC offices are open from 8:00 AM to 5:00 PM, Monday to Friday."
```

### Test Case 2: Pure Filipino
```
Input:  "Ano ang oras ng opisina?"
Output: "Ang mga opisina ng TCC ay bukas mula 8:00 AM hanggang 5:00 PM, Lunes hanggang Biyernes."
```

### Test Case 3: Filipino with English Terms
```
Input:  "Paano mag-reset ng password?"
Output: "Upang i-reset ang iyong password, bisitahin ang ICT Office..."
```

### Test Case 4: Greeting in Filipino
```
Input:  "Magandang umaga! Kumusta?"
Output: "Kumusta! Maligayang pagdating sa TCC Assistant. Paano kita matutulungan ngayong araw?"
```

### Test Case 5: Thank You in Filipino
```
Input:  "Salamat!"
Output: "Walang anuman! Magkaroon ng magandang araw!"
```

---

## 🚀 How to Run

1. **Start the Flask Server**
   ```bash
   python app.py
   ```

2. **Open in Browser**
   ```
   http://localhost:5000
   ```

3. **Test the Chatbot**
   - Click the floating chat button
   - Type a message in English or Filipino
   - Observe automatic translation

---

## 🔍 Debugging

### Enable Console Logging

The system logs translation activities to the browser console:

```javascript
console.log(`Detected language: ${this.userLanguage}`);
console.log(`Translated to English: ${translatedMsg}`);
console.log(`Translated response to Filipino: ${botResponse}`);
```

### Check Network Requests

Open **DevTools → Network** tab to monitor:
- Translation API calls to Google Translate
- `/chat` endpoint requests
- Response data

---

## 📌 Important Notes

1. **No API Key Required**
   - Uses Google's free web translation endpoint
   - No rate limits for casual use
   - May have usage restrictions for heavy traffic

2. **Translation Accuracy**
   - Google Translate provides good accuracy
   - Context-specific terms may vary
   - TCC-specific terminology handled by rules-based logic

3. **Performance**
   - Translation adds ~200-500ms latency
   - Network-dependent (requires internet)
   - Falls back to local response on error

4. **Fallback Behavior**
   - If translation fails → Returns original text
   - If chat endpoint fails → Uses local responses
   - Error handling ensures graceful degradation

---

## 🎓 Educational Use Case

This translation system is specifically designed for **Tanauan City College (TCC)** to:

- Support bilingual students (English/Filipino speakers)
- Improve accessibility for all students
- Provide seamless assistance without language barriers
- Enable natural communication in preferred language

---

## 📝 Future Enhancements

Potential improvements for the translation system:

1. **Language Indicator Badge**
   - Display detected language in UI
   - Show translation status

2. **Translation Cache**
   - Store frequently used translations
   - Reduce API calls

3. **Multi-Language Support**
   - Add support for other languages
   - Regional dialects

4. **Offline Mode**
   - Pre-translated common phrases
   - Basic offline functionality

5. **Translation Toggle**
   - Manual override option
   - Language preference settings

---

## ✅ Summary

The **Automatic English ↔ Filipino Translation System** successfully integrates:

✔️ **Free Translation API** - No costs or API keys  
✔️ **Automatic Detection** - No manual language selection  
✔️ **Rules-Based Logic** - Simple, maintainable chatbot  
✔️ **Seamless UX** - Natural bilingual conversations  
✔️ **Error Handling** - Graceful fallbacks  
✔️ **Production Ready** - Tested and documented  

**The system is fully functional and ready for production use!** 🎉

---

## 📧 Support

For questions or issues, please contact:
- **Developer:** Dexter
- **Email:** dxtrzpc26@gmail.com
- **Institution:** Tanauan City College

---

**Last Updated:** October 7, 2025  
**Version:** 1.0.0  
**Status:** ✅ Production Ready

