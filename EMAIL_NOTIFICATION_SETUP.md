# Email Notification Setup Guide

## Overview
The system now sends email notifications when users change their passwords. This guide will help you configure the email settings.

## Email Configuration

### Location
The email configuration is in `app.py`:

```python
EMAIL_CONFIG = {
    'SMTP_SERVER': 'smtp.gmail.com',
    'SMTP_PORT': 587,
    'SENDER_EMAIL': 'dxtrzpc26@gmail.com',
    'SENDER_PASSWORD': 'your-app-password-here',
    'SENDER_NAME': 'EduChat Admin System'
}
```

## Setting Up Gmail App Password

### Step 1: Enable 2-Factor Authentication
1. Go to your Google Account: https://myaccount.google.com/
2. Click on "Security" in the left sidebar
3. Under "Signing in to Google", click on "2-Step Verification"
4. Follow the prompts to enable 2-Step Verification

### Step 2: Generate App Password
1. After enabling 2FA, go back to "Security" settings
2. Click on "2-Step Verification"
3. Scroll down and click on "App passwords"
4. Select "Mail" as the app and "Other" as the device
5. Enter a name like "EduChat Admin System"
6. Click "Generate"
7. Copy the 16-character password (remove spaces)

### Step 3: Update Configuration
1. Open `app.py`
2. Find the `EMAIL_CONFIG` dictionary (around line 76)
3. Replace `'your-app-password-here'` with your generated App Password:
   ```python
   'SENDER_PASSWORD': 'abcd efgh ijkl mnop',  # Your 16-character app password
   ```

### Step 4: Customize Email Settings (Optional)
You can customize:
- `SENDER_EMAIL`: The Gmail address that sends notifications
- `SENDER_NAME`: The display name in the "From" field
- `SMTP_SERVER` and `SMTP_PORT`: If using a different email service

## Email Features

### What Gets Sent
When a user changes their password, they receive:
- ✅ Confirmation of password change
- 📧 Account details (email and timestamp)
- ⚠️ Security notice (in case of unauthorized change)
- 💡 Security recommendations
- 🎨 Professional HTML-formatted email

### Email Template Preview
The email includes:
- Modern, responsive design
- Blue gradient header
- Clear information boxes
- Security warnings
- Plain text fallback for older email clients

## Troubleshooting

### Common Issues

#### 1. "Authentication failed" error
**Solution**: 
- Make sure you're using an App Password, not your regular Gmail password
- Verify 2-Factor Authentication is enabled
- Check that the App Password is correct (16 characters, no spaces)

#### 2. "SMTPAuthenticationError"
**Solution**:
- Ensure the Gmail account exists and is active
- Try generating a new App Password
- Check if "Less secure app access" is enabled (if not using App Password)

#### 3. Email not being received
**Solution**:
- Check spam/junk folder
- Verify the recipient email address is correct in MongoDB
- Check the console logs for error messages
- Test the email function manually

#### 4. "Connection timed out"
**Solution**:
- Check your internet connection
- Verify firewall isn't blocking port 587
- Try using port 465 with SSL instead of TLS

## Testing Email Functionality

### Manual Test
Add this test route to `app.py` temporarily:

```python
@app.route('/test-email', methods=['GET'])
def test_email():
    try:
        result = send_password_change_email(
            'your-test-email@example.com',
            'Test User'
        )
        if result:
            return jsonify({'success': True, 'message': 'Email sent!'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send email'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
```

Then visit: `http://localhost:5000/test-email`

## Using Other Email Services

### Microsoft Outlook/Office 365
```python
EMAIL_CONFIG = {
    'SMTP_SERVER': 'smtp.office365.com',
    'SMTP_PORT': 587,
    'SENDER_EMAIL': 'your-email@outlook.com',
    'SENDER_PASSWORD': 'your-password',
    'SENDER_NAME': 'EduChat Admin System'
}
```

### Yahoo Mail
```python
EMAIL_CONFIG = {
    'SMTP_SERVER': 'smtp.mail.yahoo.com',
    'SMTP_PORT': 587,
    'SENDER_EMAIL': 'your-email@yahoo.com',
    'SENDER_PASSWORD': 'your-app-password',
    'SENDER_NAME': 'EduChat Admin System'
}
```

### SendGrid
```python
EMAIL_CONFIG = {
    'SMTP_SERVER': 'smtp.sendgrid.net',
    'SMTP_PORT': 587,
    'SENDER_EMAIL': 'your-verified-sender@yourdomain.com',
    'SENDER_PASSWORD': 'your-sendgrid-api-key',
    'SENDER_NAME': 'EduChat Admin System'
}
```

## Security Best Practices

1. **Never commit passwords**: Keep your App Password secret
2. **Use environment variables**: For production, use environment variables:
   ```python
   'SENDER_PASSWORD': os.environ.get('EMAIL_PASSWORD', 'fallback-for-dev')
   ```
3. **Rotate passwords**: Change App Passwords periodically
4. **Monitor usage**: Check Gmail's "Recent security activity" regularly
5. **Limit access**: Only generate App Passwords when needed

## Production Deployment

For production, use environment variables:

```python
EMAIL_CONFIG = {
    'SMTP_SERVER': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    'SMTP_PORT': int(os.getenv('SMTP_PORT', 587)),
    'SENDER_EMAIL': os.getenv('SENDER_EMAIL'),
    'SENDER_PASSWORD': os.getenv('SENDER_PASSWORD'),
    'SENDER_NAME': os.getenv('SENDER_NAME', 'EduChat Admin System')
}
```

Set environment variables on your server:
```bash
export SENDER_EMAIL="your-email@gmail.com"
export SENDER_PASSWORD="your-app-password"
```

## Email Notification Flow

1. User submits password change form
2. Backend validates current password
3. Password is updated in MongoDB
4. Email notification is sent (doesn't block response)
5. User receives success message
6. Email arrives in user's inbox

## Customizing Email Template

The email template is in the `send_password_change_email()` function. You can modify:
- Colors and styling (CSS in the HTML template)
- Content and messaging
- Brand logo (add `<img>` tag in header)
- Footer information
- Security recommendations

## Support

If you encounter issues:
1. Check console logs for error messages
2. Verify email configuration
3. Test with a simple email first
4. Review Gmail security settings
5. Check recipient's spam folder

## Additional Features

Consider implementing:
- [ ] Email for new account creation
- [ ] Email for password reset requests
- [ ] Email for suspicious login attempts
- [ ] Email for account lockouts
- [ ] Weekly security summary emails
- [ ] Email templates for different events

---

**Last Updated**: December 2024  
**Version**: 1.0

