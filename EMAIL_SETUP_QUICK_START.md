# 📧 Email Notification - Quick Start Guide

## ⚡ Quick Setup (3 Minutes)

### Step 1: Get Your Gmail App Password

1. **Visit**: https://myaccount.google.com/apppasswords
   - If you see "2-Step Verification is not turned on", click to enable it first
   - Complete the 2FA setup (takes 2 minutes)

2. **Generate App Password**:
   - After 2FA is enabled, go back to: https://myaccount.google.com/apppasswords
   - App: Select **"Mail"**
   - Device: Select **"Other (Custom name)"**
   - Name: Type **"EduChat Admin"**
   - Click **"Generate"**

3. **Copy the Password**:
   - You'll see a 16-character password like: `abcd efgh ijkl mnop`
   - **Copy it** (you can include or remove spaces)

### Step 2: Add Password to app.py

1. **Open**: `app.py` in your editor
2. **Find Line 101** (around line 101):
   ```python
   EMAIL_CONFIG['SENDER_PASSWORD'] = 'PASTE_YOUR_16_CHAR_APP_PASSWORD_HERE'
   ```

3. **Replace** with your actual password:
   ```python
   EMAIL_CONFIG['SENDER_PASSWORD'] = 'abcdefghijklmnop'  # Your 16-char password (no spaces)
   ```

4. **Save** the file

### Step 3: Restart Your App

```bash
# Stop your Flask app (Ctrl+C)
# Start it again
python app.py
```

### Step 4: Test It!

**Look for this message when the app starts:**
```
✅ Email notifications ENABLED - Emails will be sent from dxtrzpc26@gmail.com
```

If you see:
```
⚠️ Email notifications DISABLED - Set SENDER_PASSWORD in app.py to enable
```
Go back to Step 2 and check your password.

### Step 5: Test Email Sending

**Option 1: Change Your Password**
1. Login to admin portal
2. Click your user info (top right)
3. Select "Change Password"
4. Change your password
5. Check your email inbox!

**Option 2: Use Test Endpoint**
Open your browser console on any admin page and run:
```javascript
fetch('/api/auth/test-email', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${authManager.getToken()}`,
        'Content-Type': 'application/json'
    }
}).then(r => r.json()).then(console.log);
```

## 🔍 Troubleshooting

### "Email notifications DISABLED"
**Fix**: You didn't replace the placeholder password
- Go to line 101 in `app.py`
- Replace `'PASTE_YOUR_16_CHAR_APP_PASSWORD_HERE'` with your actual password

### "SMTP Authentication Error"
**Fix**: Wrong password or 2FA not enabled
- Make sure you're using an **App Password**, not your regular Gmail password
- Verify 2FA is enabled: https://myaccount.google.com/security
- Generate a new App Password

### "Connection refused" or "Timeout"
**Fix**: Firewall or network issue
- Check your internet connection
- Make sure port 587 is not blocked by firewall
- Try different network/VPN

### Email not received
**Fix**: Check spam folder
- Look in spam/junk folder
- Add dxtrzpc26@gmail.com to contacts
- Check the email address in MongoDB is correct

## 📊 Email Configuration Status

When your app starts, check the console output:

**✅ WORKING:**
```
✅ Email notifications ENABLED - Emails will be sent from dxtrzpc26@gmail.com
```

**❌ NOT WORKING:**
```
⚠️ Email notifications DISABLED - Set SENDER_PASSWORD in app.py to enable
```

## 🎯 Example: Correct Configuration

**In app.py (around line 101):**

```python
# ❌ WRONG - Don't leave placeholder:
EMAIL_CONFIG['SENDER_PASSWORD'] = 'PASTE_YOUR_16_CHAR_APP_PASSWORD_HERE'

# ✅ CORRECT - Use your actual App Password:
EMAIL_CONFIG['SENDER_PASSWORD'] = 'abcdefghijklmnop'  # Replace with YOUR password
```

## 🚀 Production Setup (Optional)

For production, use environment variables:

```bash
export SENDER_EMAIL="your-email@gmail.com"
export SENDER_PASSWORD="your-app-password"
export ENABLE_EMAIL="true"
```

Then the app will automatically use these values!

## 📧 What the Email Looks Like

When a user changes their password, they receive:

**Subject**: Password Changed Successfully - EduChat Admin

**Content**:
- 🔐 Header with confirmation
- ✅ Success icon
- 👤 Personalized greeting
- 📋 Account details (email, date/time)
- ⚠️ Security warning (if unauthorized)
- 💡 Security tips
- 🎨 Beautiful HTML design

## ✅ Success Checklist

- [ ] 2-Factor Authentication enabled on Gmail
- [ ] App Password generated
- [ ] Password pasted in app.py line 101
- [ ] File saved
- [ ] App restarted
- [ ] See "✅ Email notifications ENABLED" message
- [ ] Test email sent successfully

## 🆘 Still Not Working?

1. **Check the console output** when you change password - look for detailed error messages
2. **Try the test endpoint** using the browser console command above
3. **Verify your App Password** - generate a new one if needed
4. **Check Gmail settings** - ensure IMAP is enabled
5. **Review server logs** for specific error messages

---

**Need Help?** Check the server console logs - they show detailed information about what's happening with email sending!

