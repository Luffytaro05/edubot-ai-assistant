# Office Context Switching Protection - Quick Start Guide

## 🚀 Quick Test (2 Minutes)

### Step 1: Start the Server
```bash
python app.py
```

### Step 2: Open the Chatbot
Open your browser and navigate to the chatbot interface.

### Step 3: Test the Feature

**Test Case 1: Set Initial Context**
```
You: "How can I enroll in TCC?"
Bot: [Responds with enrollment information]
Context: ✅ Admission Office
```

**Test Case 2: Try to Switch Context**
```
You: "How do I request a transcript?"
Bot: ⚠️ Context Switch Detected warning appears
     Reset button pulses with orange highlight
Context: 🚫 Still Admission Office (switch blocked)
```

**Test Case 3: Reset Context**
```
Action: Click the "Reset Context" button (top of chat)
Bot: "✅ Admission Office context has been reset"
Context: ⭕ Cleared
```

**Test Case 4: Ask About New Office**
```
You: "How do I request a transcript?"
Bot: [Responds with transcript information]
Context: ✅ Registrar's Office
```

## 🧪 Automated Testing

Run the comprehensive test suite:

```bash
# Make sure server is running on localhost:5000
python test_office_context_switching.py
```

Expected output:
```
✅ PASSED: Initial Context Setting
✅ PASSED: Context Switch Warning
✅ PASSED: Context Reset
✅ PASSED: Post-Reset Query
✅ PASSED: Multiple Office Switches

Total: 5/5 tests passed
```

## 🎯 What to Look For

### ✅ Success Indicators
- Warning message appears when switching offices
- Reset button pulses with orange glow
- After reset, new office queries work normally
- No errors in console logs

### ❌ Failure Indicators
- No warning when switching offices
- Reset button doesn't highlight
- Errors in browser console or server logs
- Context doesn't reset properly

## 📋 Office Context Tags

| Question Example | Detected Office |
|-----------------|-----------------|
| "How to enroll?" | Admission Office |
| "Request transcript?" | Registrar's Office |
| "Reset password?" | ICT Office |
| "Need counseling?" | Guidance Office |
| "Student activities?" | Office of Student Affairs |

## 🔧 Troubleshooting

### Warning Not Appearing?

**Check 1:** Verify context is set
```javascript
// In browser console:
console.log(chatbox.currentContext);
// Should show: 'admission', 'registrar', etc.
```

**Check 2:** Check server logs
```
Look for: "🎯 Detected office: ..."
Look for: "⚠️ Office context switch detected: ..."
```

### Reset Button Not Pulsing?

**Check 1:** Verify CSS loaded
```javascript
// In browser console:
document.querySelector('.chatbox__reset').classList.contains('pulse-highlight');
```

**Check 2:** Check CSS file
```css
/* Verify this exists in static/style.css: */
.chatbox__reset.pulse-highlight { ... }
```

### Context Not Resetting?

**Check 1:** Verify endpoint works
```bash
curl -X POST http://localhost:5000/reset_context \
  -H "Content-Type: application/json" \
  -d '{"user": "guest"}'
```

**Expected response:**
```json
{"status": "success", "message": "Context reset"}
```

## 📖 More Information

See `OFFICE_CONTEXT_SWITCHING_PROTECTION.md` for:
- Complete architecture documentation
- Code explanations
- Customization options
- Advanced debugging

## ✨ Quick Demo Script

Copy and paste these messages in order:

1. `How can I enroll in TCC?` ← Sets Admission context
2. `How do I request a transcript?` ← Triggers warning
3. *Click Reset Context button*
4. `How do I request a transcript?` ← Works normally
5. `What are the requirements?` ← Continues in Registrar context
6. `Can I get counseling?` ← Triggers warning (Registrar → Guidance)

## 🎉 Success!

If you see:
- ✅ Warning message with clear instructions
- ✅ Pulsing orange reset button
- ✅ Context resets when button clicked
- ✅ New office queries work after reset

**The feature is working correctly!** 🚀

## 📞 Need Help?

1. Check console logs (F12 in browser)
2. Check server terminal output
3. Run automated tests
4. Review full documentation
5. Check MongoDB for conversation data

---

**Happy Testing!** 🎊

