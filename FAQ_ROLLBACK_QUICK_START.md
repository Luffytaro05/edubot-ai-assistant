# FAQ Rollback - Quick Start Guide

## 🚀 Quick Overview

The FAQ Rollback feature lets you restore previous versions of FAQs. Every time you edit an FAQ, the old version is automatically saved.

---

## 📝 How to Use (5 Simple Steps)

### Step 1: Edit an FAQ
1. Go to FAQ Management page
2. Click Edit (✏️) on any FAQ
3. Make changes and save
   
**What happens:** Previous version is automatically saved!

### Step 2: View History
1. Click the History button (🕐) on the FAQ
2. See list of all previous versions

Example:
```
v3 | "How do I..." | admin | Dec 15, 3:45 PM | [Preview] [Restore]
v2 | "How do I..." | admin | Dec 15, 2:30 PM | [Preview] [Restore]
v1 | "How do I..." | admin | Dec 15, 1:15 PM | [Preview] [Restore]
```

### Step 3: Preview (Optional)
1. Click Preview (👁️) to see full content
2. Review the question and answer
3. Close preview

### Step 4: Restore
1. Click Restore (↻) on the version you want
2. Confirm: "Are you sure?"
3. Click OK

### Step 5: Done!
- FAQ is restored to selected version
- Current version saved as backup
- Success message appears

---

## 💡 Real Example

### Scenario: You made a mistake

**Original FAQ:**
```
Q: How do I drop a course?
A: Visit the Registrar's Office and submit Form DR-01.
```

**You edited it to:**
```
A: Email registrar@school.edu to drop courses.
```

**Then realized it's wrong!**

### Solution:
1. Click History (🕐) button
2. See v1 with original answer
3. Click Restore on v1
4. Original answer is back!

---

## 🎯 Key Features

✅ **Automatic Backup** - Every edit saves previous version
✅ **No Version Limit** - Keep all history forever
✅ **Preview Before Restore** - Check content first
✅ **Safety Net** - Current version saved before rollback
✅ **Audit Trail** - All rollbacks are logged

---

## 🔍 UI Elements

### FAQ Table - New Button
```
[🕐 History] [✏️ Edit] [🗑️ Delete]
     ↑
  New button!
```

### Version History Modal
```
┌─────────────────────────────────────────────┐
│ FAQ Version History            [Close]       │
├─────────────────────────────────────────────┤
│ v3 | Question... | admin | Dec 15 | [👁️] [↻] │
│ v2 | Question... | admin | Dec 14 | [👁️] [↻] │
│ v1 | Question... | admin | Dec 13 | [👁️] [↻] │
└─────────────────────────────────────────────┘
```

---

## ⚠️ Important Notes

1. **First Edit Creates v1**: Original FAQs have no versions until first edit
2. **Admin Only**: Only admins can view history and restore
3. **Irreversible After Delete**: If FAQ is deleted, versions are lost
4. **Current Saved First**: Before rollback, current version is saved
5. **Chatbot Updated**: Restored FAQ is immediately available to chatbot

---

## 🐛 Quick Troubleshooting

### "No version history available"
**Reason:** FAQ hasn't been edited yet
**Solution:** Edit it once to create first version

### Preview not working
**Solution:** Refresh page and try again

### Restore failed
**Check:** Are you logged in as admin?

---

## 🎮 Try It Out!

### Practice Exercise:

1. **Create Test FAQ**
   ```
   Question: Test FAQ
   Answer: Version 1
   ```

2. **Edit it**
   ```
   Answer: Version 2
   ```

3. **Edit again**
   ```
   Answer: Version 3
   ```

4. **View History**
   - Should see v2 and v1

5. **Restore v1**
   - Answer changes back to "Version 1"

6. **View History Again**
   - Should now see v3, v2, v1

---

## 📊 Version History Info

Each version shows:
- **Version Number** (v1, v2, v3...)
- **Question** (First 50 characters)
- **Who Edited** (Username)
- **When** (Date and time)
- **Actions** (Preview and Restore buttons)

---

## ✨ Tips & Tricks

### Best Practices:
1. **Preview First**: Always preview before restoring
2. **Check Date**: Verify you're restoring the right version
3. **Test FAQs**: Practice with test FAQs first
4. **Keep Notes**: Remember why you made major edits

### When to Use:
- ✅ Accidentally deleted important info
- ✅ Made wrong changes
- ✅ Want to revert to old answer
- ✅ Testing different versions

### When NOT to Use:
- ❌ Just to view old content (use Preview instead)
- ❌ As undo button (edit directly is faster)
- ❌ For minor typos (just edit again)

---

## 🎉 That's It!

You're ready to use FAQ Rollback! Key points:

1. **History button** (🕐) on each FAQ
2. **Preview** before restore
3. **Confirm** before restoring
4. **Automatic backup** before rollback

Questions? Check `FAQ_ROLLBACK_FEATURE_GUIDE.md` for detailed info!

