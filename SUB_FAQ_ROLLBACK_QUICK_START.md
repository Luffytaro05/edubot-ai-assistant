# Sub-Admin FAQ Rollback - Quick Start Guide

## 🚀 Quick Overview

The FAQ Rollback feature for SubAdmins lets you restore previous versions of FAQs for your office. Every time you edit an FAQ, the old version is automatically saved!

---

## 📝 How to Use (5 Simple Steps)

### Step 1: Edit an FAQ (Creates First Version)
1. Login to Sub-Admin Dashboard
2. Go to FAQ Management
3. Click Edit (✏️) on any FAQ for your office
4. Make changes and save
   
**What happens:** Previous version is automatically saved as v1!

### Step 2: View History
1. Click the History button (🕐) next to the FAQ
2. See list of all previous versions

Example:
```
┌─────────────────────────────────────────────────────────────┐
│ FAQ Version History                                          │
├─────────────────────────────────────────────────────────────┤
│ v3 | "How do I..." | John Doe | Dec 15, 3:45 PM | [👁] [↻]  │
│ v2 | "How do I..." | John Doe | Dec 15, 2:30 PM | [👁] [↻]  │
│ v1 | "How do I..." | John Doe | Dec 15, 1:15 PM | [👁] [↻]  │
└─────────────────────────────────────────────────────────────┘
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
- Current version saved as backup automatically
- Success message appears
- Chatbot immediately uses restored content

---

## 💡 Real Example

### Scenario: You Made a Mistake

**Your Original FAQ:**
```
Office: Registrar's Office
Question: Where can I view my grades?
Answer: Visit the Registrar's Office on the 2nd floor and request your grade report.
```

**You edited it to:**
```
Answer: Go to the Student Portal and click on grades.
```

**Then you edited it again:**
```
Answer: Email registrar@school.edu to request grades.
```

**Oops! The second edit is wrong. The portal method was correct!**

### Solution (Takes 30 seconds):
1. Click History (🕐) button
2. See:
   - v2: "Go to the Student Portal..." ← You want this!
   - v1: "Visit the Registrar's Office..."
3. Click Preview on v2 to confirm
4. Click Restore on v2
5. Confirm
6. **Done!** Portal answer is restored

---

## 🎯 Key Features

✅ **Automatic Backup** - Every edit saves previous version automatically  
✅ **Office-Specific** - Only see and manage FAQs for your office  
✅ **No Version Limit** - Keep all history forever  
✅ **Preview Before Restore** - Check content before restoring  
✅ **Safety Net** - Current version saved before rollback  
✅ **Audit Trail** - All rollbacks are logged  

---

## 🔍 UI Elements

### FAQ Table - New Button
```
[🕐 History] [👁 View] [✏️ Edit] [🗑️ Delete]
     ↑
  New button!
```

### Version History Modal
- **Table view** of all versions
- **Version badge** (v1, v2, v3...)
- **Question preview** (first 50 characters)
- **Editor name** (who made the change)
- **Date/time** (when it was changed)
- **Actions**: Preview (👁️) and Restore (↻)

### Version Preview Modal
- **Full question** text
- **Full answer** text
- **Status** badge
- **Read-only** display

---

## ⚠️ Important Notes

1. **First Edit Creates v1**: Original FAQs have no versions until first edit
2. **Office-Based**: You can only manage FAQs for your assigned office
3. **Irreversible After Delete**: If FAQ is deleted, versions are lost (but logged)
4. **Current Saved First**: Before rollback, current version is automatically saved
5. **Chatbot Synced**: Restored FAQ is immediately available to the chatbot via Pinecone
6. **Audit Trail**: All actions are logged in `sub_system_logs`

---

## 🐛 Quick Troubleshooting

### "No version history available"
**Reason:** FAQ hasn't been edited yet  
**Solution:** Edit it once to create first version

### "FAQ not found or access denied"
**Reason:** FAQ belongs to different office  
**Solution:** Only view/edit FAQs for your assigned office

### Preview not working
**Solution:** 
1. Refresh page
2. Check if you're still logged in
3. Try again

### Restore failed
**Check:**
- Are you logged in as sub-admin?
- Does the FAQ belong to your office?
- Is your session still active?

---

## 🎮 Practice Exercise

Try this to learn the feature:

### Step 1: Create Test FAQ
```
Question: Test FAQ for rollback
Answer: Version 1 - Original answer
Status: Published
```

### Step 2: Edit It
```
Answer: Version 2 - First edit
```

### Step 3: Edit Again
```
Answer: Version 3 - Second edit
```

### Step 4: View History
- Click History button
- Should see v2 and v1

### Step 5: Restore v1
- Click Restore on v1
- Confirm
- Answer changes back to "Version 1 - Original answer"

### Step 6: View History Again
- Should now see v3, v2, v1
- v3 is the "Version 2" you just rolled back from

---

## 📊 What Each Button Does

| Button | Icon | Action |
|--------|------|--------|
| **History** | 🕐 | Opens version history modal |
| **Preview** | 👁️ | Shows full version content (read-only) |
| **Restore** | ↻ | Rollback to that version |

---

## ✨ Tips for SubAdmins

### Best Practices:
1. **Review Before Restore**: Always preview version first
2. **Check the Date**: Make sure you're restoring the right version
3. **Practice First**: Try with test FAQs before using on important ones
4. **Keep Notes**: Remember why you made significant changes

### When to Use Rollback:
- ✅ Accidentally changed wrong information
- ✅ Made updates that caused confusion
- ✅ Want to revert to tested/approved answer
- ✅ Need to recover deleted content from edits

### When NOT to Use:
- ❌ Just to view old content (use Preview instead)
- ❌ For minor typos (just edit again - faster)
- ❌ As undo button right after edit (edit again instead)

---

## 🎉 You're Ready!

The Sub-Admin FAQ Rollback feature is simple and powerful:

1. **History button** (🕐) on each FAQ
2. **Preview** before restore
3. **Confirm** before restoring
4. **Automatic backup** of current version
5. **Office-specific** for your security

**Never lose important FAQ content again!** 🚀

---

## 📞 Need Help?

If you have issues:
1. Check you're logged in as sub-admin
2. Verify the FAQ belongs to your office
3. Try refreshing the page
4. Contact your system administrator

**For detailed technical info:** See `SUB_FAQ_ROLLBACK_IMPLEMENTATION_SUMMARY.md`

