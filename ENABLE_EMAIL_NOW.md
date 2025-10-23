# ⚡ ENABLE EMAIL NOTIFICATIONS - DO THIS NOW!

## 🎯 You Only Need to Do 2 Things:

---

## 1️⃣ GET YOUR GMAIL APP PASSWORD (2 minutes)

### Visit this URL:
```
https://myaccount.google.com/apppasswords
```

### Follow these steps:
1. Enable 2-Factor Authentication (if not enabled)
2. Select "Mail" → "Other (Custom name)"
3. Name it: "EduChat"
4. Click "Generate"
5. **COPY THE PASSWORD** (looks like: `abcd efgh ijkl mnop`)

---

## 2️⃣ PASTE IT IN app.py (30 seconds)

### Open: `app.py`

### Find Line 101 (Press Ctrl+F and search for: `PASTE_YOUR`)

### You'll see this:
```python
EMAIL_CONFIG['SENDER_PASSWORD'] = 'PASTE_YOUR_16_CHAR_APP_PASSWORD_HERE'
```

### Change it to (remove spaces from your password):
```python
EMAIL_CONFIG['SENDER_PASSWORD'] = 'abcdefghijklmnop'  # ← YOUR PASSWORD HERE (no spaces!)
```

### SAVE THE FILE! (Ctrl+S)

---

## ✅ RESTART THE APP

```bash
# Stop Flask (Ctrl+C in terminal)
python app.py
```

### Look for this message:
```
✅ Email notifications ENABLED - Emails will be sent from dxtrzpc26@gmail.com
```

**If you see "⚠️ DISABLED"** → Go back and check you saved the file!

---

## 🧪 TEST IT

### Quick Test:
1. Go to **Settings** page in admin
2. Click "**Save & Reset**" tab
3. Click "**Send Test Email**" button
4. Check your email: **dxtrzpc26@gmail.com**
5. **Check spam folder too!**

---

## ❓ Problems?

### "SMTP Authentication Error"
**Fix**: Generate a NEW App Password and try again

### "Email notifications DISABLED"
**Fix**: 
- Check line 101 in app.py
- Make sure you replaced `PASTE_YOUR_16_CHAR_APP_PASSWORD_HERE`
- Remove ALL spaces from password
- Save file and restart app

### "Connection refused"
**Fix**: Check your internet connection and firewall

### Email not in inbox
**Fix**: **CHECK SPAM FOLDER!** (90% of the time it's there)

---

## 📸 Visual Guide

### What Line 101 Should Look Like:

**❌ BEFORE (won't work):**
```python
EMAIL_CONFIG['SENDER_PASSWORD'] = 'PASTE_YOUR_16_CHAR_APP_PASSWORD_HERE'
```

**✅ AFTER (will work):**
```python
EMAIL_CONFIG['SENDER_PASSWORD'] = 'abcdefghijklmnop'  # Your actual password
```

---

## 🎉 That's It!

Once you see:
```
✅ Email notifications ENABLED
```

You're done! Password change emails will be sent automatically!

---

**Need more help?** See: `EMAIL_CONFIGURATION_GUIDE.md`

