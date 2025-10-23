# Office Context Switching Protection

## 📋 Overview

This feature prevents users from jumping between different office contexts (e.g., Admission Office → Registrar's Office) without explicitly resetting the conversation context first. This ensures clearer communication and more accurate responses by maintaining office-specific conversation flow.

## 🎯 Problem Solved

**Before this implementation:**
- Users could ask about the Admission Office, then suddenly switch to Registrar's Office questions
- This caused context confusion and potentially inaccurate responses
- The chatbot had no mechanism to guide users through proper context switching

**After this implementation:**
- Users are explicitly warned when attempting to switch office contexts
- The chatbot guides them to reset the previous office context first
- Clear visual indicators (pulsing reset button) help users understand what action to take

## 🏗️ Architecture

### Backend (`app.py`)

**Location:** `/predict` endpoint (lines 1675-1726)

**Logic Flow:**
1. Detect the office from the user's new message
2. Check if user has an existing office context
3. If contexts differ and both exist:
   - Create a formatted warning message
   - Translate warning to user's language if needed
   - Return special response with `status: 'context_switch_warning'`
   - Include metadata about current and attempted offices
4. Otherwise, proceed with normal message processing

**Key Code:**
```python
# Check if user is trying to switch to a different office without resetting
current_office_tag = None
if user in user_contexts:
    if isinstance(user_contexts[user], dict):
        current_office_tag = user_contexts[user].get('current_office')
    else:
        current_office_tag = user_contexts[user] if isinstance(user_contexts[user], str) else None

# If user has an active office context and is trying to switch
if current_office_tag and detected_office_tag and current_office_tag != detected_office_tag:
    # Return warning message
    return jsonify({
        "answer": warning_message,
        "office": current_office_name,
        "status": "context_switch_warning",
        "current_office": current_office_name,
        "attempted_office": new_office_name,
        "requires_reset": True
    })
```

### Frontend (`static/app.js`)

**Location:** `onSendButton` method (lines 1557-1585)

**Logic Flow:**
1. Receive response from backend
2. Check if `status === 'context_switch_warning'` and `requires_reset === true`
3. If yes:
   - Display the warning message
   - Highlight the reset button with pulse animation
   - Stop further processing (early return)
4. Otherwise, proceed with normal message display

**Key Code:**
```javascript
// Check if backend is warning about office context switch
if (r.status === 'context_switch_warning' && r.requires_reset) {
    console.warn(`⚠️ Context switch blocked: ${r.current_office} → ${r.attempted_office}`);
    
    // Display warning message
    let msg2 = { 
        name: "Bot", 
        message: r.answer,
        status: 'context_switch_warning',
        isContextWarning: true,
        currentOffice: r.current_office,
        attemptedOffice: r.attempted_office
    };
    this.messages.push(msg2);
    this.updateChatText();
    
    // Highlight reset button
    this.highlightResetButton();
    
    return; // Stop processing
}
```

**Reset Button Highlight Method** (lines 1219-1242):
```javascript
highlightResetButton() {
    const resetButton = this.args.resetButton;
    if (!resetButton) return;
    
    // Add visual highlight
    resetButton.classList.add('pulse-highlight');
    resetButton.style.animation = 'pulse 1.5s ease-in-out 3';
    resetButton.style.boxShadow = '0 0 10px rgba(255, 152, 0, 0.7)';
    
    // Remove after 5 seconds
    setTimeout(() => {
        resetButton.classList.remove('pulse-highlight');
        resetButton.style.animation = '';
        resetButton.style.boxShadow = '';
    }, 5000);
}
```

### Styling (`static/style.css`)

**Location:** Lines 1193-1198

**CSS Animation:**
```css
/* Pulse highlight for reset button when context switch is needed */
.chatbox__reset.pulse-highlight {
    background: rgba(255, 152, 0, 0.2) !important;
    animation: pulse 1.5s ease-in-out 3;
    box-shadow: 0 0 10px rgba(255, 152, 0, 0.7);
}

@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.1); }
    100% { transform: scale(1); }
}
```

## 📊 Office Mapping

The system recognizes these office contexts:

| Office Tag | Display Name |
|-----------|--------------|
| `admission_office` | Admission Office |
| `registrar_office` | Registrar's Office |
| `ict_office` | ICT Office |
| `guidance_office` | Guidance Office |
| `osa_office` | Office of Student Affairs |

## 🔄 User Flow Example

### Scenario 1: Context Switch Blocked

1. **User:** "How can I enroll in TCC?"
   - **Bot:** Responds with enrollment info
   - **Context:** Set to `Admission Office`

2. **User:** "How do I request a transcript?"
   - **Bot:** ⚠️ **Context Switch Detected** warning
   - **Action:** Reset button pulses (orange highlight)
   - **Context:** Remains `Admission Office`

3. **User:** Clicks "Reset Context" button
   - **Bot:** "✅ Admission Office context has been reset"
   - **Context:** Cleared

4. **User:** "How do I request a transcript?"
   - **Bot:** Responds with transcript info
   - **Context:** Set to `Registrar's Office`

### Scenario 2: Normal Conversation

1. **User:** "What ICT services are available?"
   - **Bot:** Responds with ICT services
   - **Context:** Set to `ICT Office`

2. **User:** "How do I reset my password?"
   - **Bot:** Responds with password reset steps
   - **Context:** Remains `ICT Office` (same context)

3. **User:** Continues asking ICT-related questions
   - **Bot:** Responds normally
   - **Context:** Remains `ICT Office`

## 🧪 Testing

### Running Tests

```bash
# Start the Flask server
python app.py

# In another terminal, run the test script
python test_office_context_switching.py
```

### Test Scenarios Covered

1. ✅ **Initial Context Setting**
   - Verify office context is set on first query

2. ✅ **Context Switch Warning**
   - Verify warning is shown when switching offices

3. ✅ **Context Reset**
   - Verify reset clears the context properly

4. ✅ **Post-Reset Query**
   - Verify new office queries work after reset

5. ✅ **Multiple Office Switches**
   - Verify warning appears for different office combinations

### Expected Test Output

```
╔══════════════════════════════════════════════════════════╗
║          OFFICE CONTEXT SWITCHING TEST SUITE            ║
╚══════════════════════════════════════════════════════════╝

============================================================
  TEST SUMMARY
============================================================

  ✅ PASSED: Initial Context Setting
  ✅ PASSED: Context Switch Warning
  ✅ PASSED: Context Reset
  ✅ PASSED: Post-Reset Query
  ✅ PASSED: Multiple Office Switches

============================================================
  Total: 5/5 tests passed
============================================================

🎉 All tests passed! Office context switching protection is working correctly.
```

## 🌍 Multi-Language Support

The feature works seamlessly with both English and Filipino:

- **Warning messages** are automatically translated to the user's language
- **Detection** works regardless of input language
- **Context names** are displayed consistently

**Example in Filipino:**
```
⚠️ Nakita kong nagtatanong ka tungkol sa Admission Office dati. 
Mangyaring i-reset muna ang Admission Office context bago lumipat 
sa Registrar's Office.
```

## 🎨 Visual Indicators

### Reset Button Pulse Animation

When context switch is detected:
- Reset button background: Light orange (`rgba(255, 152, 0, 0.2)`)
- Animation: Pulses 3 times over 4.5 seconds
- Box shadow: Orange glow (`rgba(255, 152, 0, 0.7)`)
- Duration: 5 seconds total

### Warning Message Format

```
⚠️ **Context Switch Detected**

You're currently in the **Admission Office** context. 
I noticed you're now asking about the **Registrar's Office**.

To ensure clear and accurate responses, please **reset the 
Admission Office context** first before switching to the 
Registrar's Office.

💡 **How to reset:**
• Click the **'Reset Context'** button at the top of the chat
• Or type **'reset context'** to clear the current office context

This helps me provide you with the most relevant information 
for each office! 😊
```

## 🔧 Configuration

### Enabling/Disabling

The feature is **always enabled** by default. To disable temporarily for debugging:

**In `app.py`:**
```python
# Add this flag at the top of app.py
ENABLE_CONTEXT_SWITCHING_PROTECTION = False

# Then wrap the check:
if ENABLE_CONTEXT_SWITCHING_PROTECTION and current_office_tag and detected_office_tag:
    # ... warning logic
```

### Customizing Warning Message

**Location:** `app.py`, line 1693-1702

```python
warning_message = (
    f"⚠️ **Context Switch Detected**\n\n"
    f"You're currently in the **{current_office_name}** context. "
    f"I noticed you're now asking about the **{new_office_name}**.\n\n"
    # ... customize this text as needed
)
```

### Adjusting Highlight Duration

**Location:** `static/app.js`, line 1235

```javascript
// Change from 5000 to desired milliseconds
setTimeout(() => {
    resetButton.classList.remove('pulse-highlight');
    // ...
}, 5000); // <-- Change this value
```

## 📈 Benefits

1. **Improved Accuracy**: Prevents context confusion leading to better responses
2. **User Guidance**: Clear instructions help users navigate the chatbot
3. **Visual Feedback**: Pulsing button draws attention to the required action
4. **Conversation Clarity**: Maintains clean office-specific conversation threads
5. **Better Analytics**: Clearer office attribution in conversation data

## 🔍 Debugging

### Console Logs

**Backend (`app.py`):**
```python
print(f"⚠️ Office context switch detected: {current_office_name} → {new_office_name}")
```

**Frontend (`static/app.js`):**
```javascript
console.warn(`⚠️ Context switch blocked: ${r.current_office} → ${r.attempted_office}`);
console.log('✨ Reset button highlighted to guide user');
```

### Checking User Context

In Python console or debugger:
```python
from chat import user_contexts
print(user_contexts['user_id'])
# Output: {'current_office': 'admission_office', 'offices': {...}}
```

### Testing Manually

1. Start Flask server: `python app.py`
2. Open chatbot in browser
3. Ask: "How can I enroll?" (sets Admission context)
4. Ask: "How do I get a transcript?" (triggers warning)
5. Observe: Warning message + pulsing reset button
6. Click: Reset Context button
7. Ask: "How do I get a transcript?" (works normally)

## 📝 Files Modified

| File | Lines | Description |
|------|-------|-------------|
| `app.py` | 1675-1726 | Added context switch detection logic |
| `static/app.js` | 1557-1585 | Added warning handler in message flow |
| `static/app.js` | 1219-1242 | Added reset button highlight method |
| `static/style.css` | 1193-1198 | Added pulse-highlight CSS class |

## 🆕 New Files Created

| File | Purpose |
|------|---------|
| `test_office_context_switching.py` | Automated test suite |
| `OFFICE_CONTEXT_SWITCHING_PROTECTION.md` | This documentation |

## 🚀 Future Enhancements

Potential improvements for future versions:

1. **Smart Context Merging**: Allow related offices to share context
2. **Context History**: Show users their recent office contexts
3. **Quick Switch Mode**: Advanced users can enable unrestricted switching
4. **Context Suggestions**: Proactively suggest when to switch contexts
5. **Analytics Dashboard**: Track most common context switch patterns

## 📞 Support

For issues or questions:
1. Check console logs for debug information
2. Run the test suite to verify functionality
3. Review this documentation for configuration options
4. Check MongoDB for conversation history and context data

## ✅ Checklist for Deployment

- [x] Backend logic implemented in `app.py`
- [x] Frontend handler added in `static/app.js`
- [x] CSS styling added in `static/style.css`
- [x] Reset button highlight method created
- [x] Test suite created and passing
- [x] Documentation completed
- [ ] User acceptance testing
- [ ] Production deployment

---

**Implementation Date:** 2025-10-10  
**Version:** 1.0  
**Status:** ✅ Complete and Ready for Testing

