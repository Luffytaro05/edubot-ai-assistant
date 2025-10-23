# 🚀 Quick Reference: Office-Specific Context Reset

## One-Page Guide for Developers

---

## 📌 Core Concept

**Before:** One context per user (resets everything)  
**After:** Separate context per office per user (reset individually)

---

## 🔧 API Usage

### Reset Specific Office
```javascript
fetch('/reset_context', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
        user: "TCC-0001",
        office: "ict_office"  // Only reset ICT
    })
})
```

### Reset All Offices
```javascript
fetch('/reset_context', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
        user: "TCC-0001"
        // No office param = reset all
    })
})
```

---

## 🐍 Python Functions

### Get Current Office
```python
from chat import get_user_current_office

office = get_user_current_office("TCC-0001")
# Returns: 'admission_office' or None
```

### Set Office Context
```python
from chat import set_user_current_office

set_user_current_office("TCC-0001", "registrar_office")
```

### Reset Office Context
```python
from chat import reset_user_context

# Reset specific office
reset_user_context("TCC-0001", "ict_office")

# Reset all
reset_user_context("TCC-0001")
```

---

## 🏢 Office Tags

| Frontend | Backend Tag | Display Name |
|----------|-------------|--------------|
| `admission` | `admission_office` | Admission Office |
| `registrar` | `registrar_office` | Registrar's Office |
| `ict` | `ict_office` | ICT Office |
| `guidance` | `guidance_office` | Guidance Office |
| `osa` | `osa_office` | Office of Student Affairs |

---

## 📊 Context Structure

```python
user_contexts = {
    "TCC-0001": {
        "current_office": "ict_office",
        "offices": {
            "admission_office": {
                "messages": [],
                "last_intent": None
            },
            "ict_office": {
                "messages": [],
                "last_intent": None
            }
        }
    }
}
```

---

## ✅ Testing

```bash
# Run test suite
.\venv\Scripts\python.exe test_office_context_reset.py

# Run demo
.\venv\Scripts\python.exe demo_office_context_reset.py
```

---

## 🐛 Debugging

```python
# Check current context
print(f"Current: {get_user_current_office('user_id')}")

# Check all offices
from chat import user_contexts
print(user_contexts.get('user_id', {}).get('offices', {}))

# Verify structure
print(user_contexts)
```

---

## 🎯 Common Use Cases

### Use Case 1: Switch Between Offices
```python
# Student talks to Admission
set_user_current_office("student123", "admission_office")

# Later talks to ICT
set_user_current_office("student123", "ict_office")

# Both contexts preserved ✅
```

### Use Case 2: Reset Current Office
```python
# Student wants fresh start with current office
current = get_user_current_office("student123")
reset_user_context("student123", current)
# Only current office reset ✅
```

### Use Case 3: Clean Slate
```python
# Admin resets all contexts for user
reset_user_context("student123")
# All offices reset ✅
```

---

## 🔍 Key Files

| File | Purpose |
|------|---------|
| `chat.py` | Context storage & management |
| `app.py` | `/reset_context` endpoint |
| `static/app.js` | Frontend reset logic |
| `templates/base.html` | Reset button UI |

---

## ⚡ Quick Commands

```bash
# Check for errors
python -m py_compile chat.py app.py

# Run Flask app
python app.py

# Test in browser
# 1. Chat with different offices
# 2. Click "Switch Topic"
# 3. Verify isolation
```

---

## 📝 Checklist for New Office

To add a new office (e.g., "Library"):

1. ✅ Add to `office_tags` in `chat.py`:
   ```python
   'library_office': 'Library'
   ```

2. ✅ Add detection in `detect_office_from_message()`:
   ```python
   elif 'library' in msg_lower or 'books' in msg_lower:
       return 'library_office'
   ```

3. ✅ Add to frontend mapping in `app.js`:
   ```javascript
   library: 'library_office'
   ```

4. ✅ Add to `officeNames` in `app.js`:
   ```javascript
   library: "Library"
   ```

That's it! The new office is integrated. ✅

---

## 🚨 Important Notes

⚠️ **Don't Do This:**
```python
# Bad: Direct access
user_contexts[user_id] = "office_tag"  # ❌ Old way
```

✅ **Do This Instead:**
```python
# Good: Use helper functions
set_user_current_office(user_id, "office_tag")  # ✅ New way
```

---

## 💡 Pro Tips

1. **Always use helper functions** - Don't access `user_contexts` directly
2. **Check current office first** - Before resetting or switching
3. **Handle None gracefully** - User might not have any context yet
4. **Test isolation** - Verify resets don't affect other offices

---

## 📞 Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| Reset not working | Check browser console, clear cache |
| Office not detected | Verify keywords in `detect_office_from_message()` |
| Context not saved | Check MongoDB connection |
| Wrong office shown | Verify `currentContext` in frontend |

---

## 🎓 Learning Resources

- **Full Docs:** `OFFICE_SPECIFIC_CONTEXT_RESET_README.md`
- **Implementation:** `IMPLEMENTATION_SUMMARY_OFFICE_CONTEXT.md`
- **Tests:** `test_office_context_reset.py`
- **Demo:** `demo_office_context_reset.py`

---

## ✨ One-Liner Summary

> "Each office gets its own conversation memory. Reset one without affecting others."

---

*Quick Reference v1.0 | Last Updated: Oct 7, 2025*

