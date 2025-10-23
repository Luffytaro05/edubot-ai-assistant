# Quick Installation - Google Translate Integration

## ✅ Fixed: httpcore.SyncHTTPTransport Error

The `AttributeError: module 'httpcore' has no attribute 'SyncHTTPTransport'` error has been resolved by switching from `googletrans` to `deep-translator`.

---

## Installation Commands

### Uninstall Old Package (if previously installed):

```bash
pip uninstall googletrans -y
```

### Install New Packages:

Run this single command in your terminal:

```bash
pip install deep-translator==1.11.4 langdetect==1.0.9
```

---

## Or Install All Requirements

```bash
pip install -r requirements.txt
```

---

## Restart Flask

After installation, restart your Flask server:

**Windows (PowerShell):**
```bash
python app.py
```

**Linux/Mac:**
```bash
python3 app.py
```

---

## Verify Installation

Open the chatbot and send a message in Filipino:

```
Kumusta! Ano ang oras ng opisina?
```

**Expected result:**
- ✅ Response comes back in Filipino
- ✅ No errors in console
- ✅ Console shows: `🌐 Detected language: tl`

---

## What Changed

### Fixed:
❌ `googletrans==4.0.0rc1` (had httpcore compatibility issue)
✅ `deep-translator==1.11.4` (stable, no compatibility issues)
✅ `langdetect==1.0.9` (for language detection)

### Modified Files:
1. **requirements.txt** - Updated dependencies
2. **app.py** - Changed import and API calls

---

## Libraries Comparison

| Feature | googletrans | deep-translator |
|---------|-------------|-----------------|
| Google Translate API | ✅ Yes | ✅ Yes |
| httpcore compatibility | ❌ Broken | ✅ Works |
| Actively maintained | ❌ No | ✅ Yes |
| Language detection | ✅ Built-in | Requires langdetect |
| Stability | ❌ Issues | ✅ Stable |
| Installation | ❌ Complex | ✅ Simple |

---

## Ready to Use!

Once installed and server restarted, your chatbot will automatically support 100+ languages! 🌐

