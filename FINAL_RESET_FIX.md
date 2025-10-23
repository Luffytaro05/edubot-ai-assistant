# Final Reset Context Fix - THE REAL BUG! 🐛

## 🎯 The ACTUAL Problem

The reset wasn't working because of **TWO CRITICAL BUGS**:

### Bug #1: Wrong User ID in Reset Request ❌

**Frontend was sending the WRONG user ID!**

```javascript
// ❌ WRONG - Line 652 and 1176 were using:
user: this.user  // undefined or wrong value!

// ✅ CORRECT - Should be:
user: this.user_id  // matches what predict endpoint uses
```

**What happened:**
1. When you send a message → uses `this.user_id` (e.g., "guest_12345")
2. Context gets stored under "guest_12345" ✅
3. When you click reset → was sending `this.user` (undefined or different)
4. Reset endpoint tries to clear context for "undefined" ❌
5. Your actual context under "guest_12345" remains! ❌
6. Next message still sees old context ❌

### Bug #2: Reset Function Didn't Handle Simple Structure ❌

The `reset_user_context` function in `chat.py` was looking for a complex structure:
```python
# Expected: {'current_office': 'x', 'offices': {...}}
# But we were storing: {'current_office': 'x'}  # No 'offices' key!
```

So even if user ID was correct, the reset condition failed.

## ✅ The Fixes

### Fix #1: Corrected User ID in Frontend

**File:** `static/app.js`

**Line 647** - Changed condition:
```javascript
// Before:
if (typeof fetch !== 'undefined' && this.user) {

// After:
if (typeof fetch !== 'undefined' && this.user_id) {  // ✅ Check correct property
```

**Line 652** - Fixed user parameter:
```javascript
// Before:
user: this.user,  // ❌ Wrong!

// After:
user: this.user_id,  // ✅ Matches predict endpoint
```

**Line 1176** - Fixed user parameter (duplicate reset function):
```javascript
// Before:
user: this.user,  // ❌ Wrong!

// After:
user: this.user_id,  // ✅ Matches predict endpoint
```

**Line 1172** - Added debug logging:
```javascript
console.log(`🔄 Sending reset request - User ID: ${this.user_id}, Office: ${currentOfficeTag}`);
```

### Fix #2: Updated Reset Function in Backend

**File:** `chat.py`, Lines 788-839

Updated `reset_user_context()` to:
1. Handle simple structure: `{'current_office': 'x'}`
2. Handle complex structure: `{'current_office': 'x', 'offices': {...}}`
3. Handle old string format: `user_contexts[user] = 'office_tag'`
4. Add comprehensive logging before and after reset

```python
def reset_user_context(user_id, office=None):
    if user_id not in user_contexts:
        print(f"🔄 No context found for user '{user_id}' - nothing to reset")
        return
    
    # Get current context info for logging
    current_context = user_contexts[user_id]
    print(f"🔍 Context before reset: {current_context}")
    
    if office:
        # Reset specific office
        if isinstance(user_contexts[user_id], dict):
            current_office = user_contexts[user_id].get("current_office")
            if current_office == office:
                # Clear the current office
                user_contexts[user_id]["current_office"] = None
                print(f"✅ Reset context for user '{user_id}' - Office: {office}")
    else:
        # Reset ALL contexts
        user_contexts.pop(user_id, None)
        print(f"✅ Reset ALL contexts for user '{user_id}'")
    
    print(f"🔍 Context after reset: {user_contexts.get(user_id, 'Removed from dictionary')}")
```

## 🧪 How to Test

### Step 1: Restart Flask Server ⚠️

**CRITICAL:** Changes don't take effect until restart!

```bash
# Stop current server (Ctrl+C)
python app.py
```

### Step 2: Clear Browser Cache

Open browser console (F12) and run:
```javascript
localStorage.clear();
location.reload();
```

This ensures you're starting fresh.

### Step 3: Manual Test in Browser

1. **Open chatbot** and **open browser console** (F12)

2. **Type:** `How can I enroll in TCC?`
   
   **Flask console should show:**
   ```
   🎯 Office detected: admission_office (score: 2)
   ✅ Stored office context for user 'guest_xxxxx': Admission Office
   ```
   
   **Browser console should show:**
   ```
   User ID: guest_xxxxx
   ```

3. **Type:** `How do I request a transcript?`
   
   **Should see:** ⚠️ Warning message in chat
   
   **Flask console should show:**
   ```
   🔍 Context Switch Check:
      User: guest_xxxxx
      Current office in context: admission_office
      Detected office from message: registrar_office
   ⚠️ Office context switch detected: Admission Office → Registrar's Office
   ```

4. **Click "Reset Context" button**
   
   **Browser console should show:**
   ```
   🔄 Sending reset request - User ID: guest_xxxxx, Office: admission_office
   ✅ Context reset successfully: {status: "success", ...}
   ```
   
   **Flask console should show:**
   ```
   🔄 Reset request - User: guest_xxxxx, Office: admission_office
   🔍 Context before reset: {'current_office': 'admission_office'}
   ✅ Reset context for user 'guest_xxxxx' - Office: Admission Office
   🔍 Context after reset: {'current_office': None}  ← KEY: Should show None!
   ```

5. **Type:** `How do I request a transcript?` (same question)
   
   **Should:** Work normally (NO warning!)
   
   **Flask console should show:**
   ```
   🔍 Context Switch Check:
      User: guest_xxxxx
      Current office in context: None  ← Fixed!
      Detected office from message: registrar_office
   ✅ Stored office context for user 'guest_xxxxx': Registrar's Office
   ```

6. **Type:** `How do I reset my password?`
   
   **Should:** Show warning again (Registrar → ICT)
   
   **This proves it's working!** ✅

## 🔍 Debug Checklist

If reset still doesn't work, check:

### ✅ Check 1: User ID Consistency

**Browser Console:**
```javascript
// After sending a message, check:
console.log("User ID:", chatbox.user_id);
```

**Flask Console:**
```
# When reset is called, verify same user ID appears:
🔄 Reset request - User: guest_xxxxx  ← Should match browser console
```

**If different → Problem with session or user ID generation**

### ✅ Check 2: Context Actually Stored

**Flask Console after first message:**
```
✅ Stored office context for user 'guest_xxxxx': Admission Office
```

**If missing → Context not being stored, check app.py lines 1831-1842**

### ✅ Check 3: Reset Actually Clears

**Flask Console after reset:**
```
🔍 Context before reset: {'current_office': 'admission_office'}  ← Has value
🔍 Context after reset: {'current_office': None}  ← Should be None or removed
```

**If still has value → Reset function not working, check chat.py lines 806-815**

### ✅ Check 4: Browser Sending Correct Data

**Browser Console → Network Tab:**
1. Click Reset button
2. Look for `/reset_context` request
3. Check Request Payload:
   ```json
   {
     "user": "guest_xxxxx",  ← Should be actual user ID, not "undefined"
     "office": "admission_office"
   }
   ```

**If user is undefined → Check static/app.js lines 1176 and 652**

## 📊 What Changed

| File | Lines | What Changed |
|------|-------|-------------|
| `static/app.js` | 647 | Fixed condition: `this.user` → `this.user_id` |
| `static/app.js` | 652 | Fixed parameter: `user: this.user` → `user: this.user_id` |
| `static/app.js` | 1172 | Added debug logging |
| `static/app.js` | 1176 | Fixed parameter: `user: this.user` → `user: this.user_id` |
| `chat.py` | 788-839 | Rewrote reset function to handle simple structure |

## ✅ Expected Behavior

### Complete Flow:

```
1. User: "How can I enroll?"
   Backend: Stores context for user "guest_12345"
   Context: {'current_office': 'admission_office'}

2. User: "How do I get a transcript?"
   Backend: Detects different office
   Response: ⚠️ Warning message
   Context: UNCHANGED (still admission_office)

3. User: [Clicks Reset]
   Frontend: Sends {"user": "guest_12345", "office": "admission_office"}
   Backend: Finds context for "guest_12345" ✅
   Backend: Sets current_office to None ✅
   Context: {'current_office': None}

4. User: "How do I get a transcript?"
   Backend: current_office is None (no warning)
   Response: Normal answer about transcripts
   Context: {'current_office': 'registrar_office'}

5. User: "How do I reset my password?"
   Backend: Detects different office (registrar → ict)
   Response: ⚠️ Warning message
   Context: UNCHANGED (still registrar_office)

SUCCESS! ✅
```

## 🎯 Key Points

✅ **User ID must match** between predict and reset endpoints  
✅ **Frontend now uses `this.user_id` consistently**  
✅ **Backend reset function handles simple structure**  
✅ **Debug logging on both frontend and backend**  
✅ **Must restart Flask server for changes to take effect**  
✅ **Must clear browser cache/localStorage for clean test**  

## 🚀 Success Criteria

The fix is working when:
1. ✅ Browser console shows same user ID in reset request
2. ✅ Flask console shows "Context before reset" has data
3. ✅ Flask console shows "Context after reset" is None or empty
4. ✅ After reset, no warning appears for different office
5. ✅ New office context is stored successfully
6. ✅ Subsequent switches trigger warnings again

## 💡 Why This Was Hard to Find

1. **Silent failure:** `this.user` being undefined didn't throw an error
2. **Two separate issues:** User ID mismatch AND reset logic issue
3. **No error logs:** Both issues failed silently
4. **Multiple reset functions:** Two places in code doing same thing
5. **Complex data structure:** Mismatch between expected and actual format

---

**Fix Applied:** 2025-10-10  
**Status:** ✅ READY TO TEST  
**Breaking Changes:** None  
**Requires:**
- Flask server restart
- Browser cache clear
- localStorage clear

