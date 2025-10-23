# FAQ Rollback to Previous Versions - Feature Guide

## 🎯 Overview

The **Rollback to Previous Versions** feature allows admins to view version history and restore previous versions of FAQs whenever an incorrect or unwanted edit is made. This ensures you never lose important FAQ content and can easily revert mistakes.

## 📁 Files Modified

### Backend Files
- **`faq.py`** - Added version management functions and updated `update_faq()` to save versions
- **`app.py`** - Added new routes for version history and rollback functionality

### Frontend Files
- **`static/assets/js/modules/FAQManager.js`** - Added version management methods
- **`templates/faq.html`** - Added version history UI, modals, and JavaScript functions

### Database Collections
- **`faq_versions`** - Stores all historical versions of FAQs
- **`system_logs`** - Records rollback actions for audit trails

---

## 🔧 How It Works

### Automatic Version Saving

Every time an admin edits/updates an FAQ:
1. The current FAQ content is automatically saved to `faq_versions` collection
2. A new version number is assigned (incrementing from 1)
3. Metadata is saved including:
   - Version number
   - Question, Answer, Office, Status
   - Edited by (admin username)
   - Timestamp

### Version History UI

1. Each FAQ in the table has a new **"View History"** button (🕐 icon)
2. Clicking it opens a modal showing all past versions
3. Each version displays:
   - Version number (v1, v2, v3, etc.)
   - Question preview
   - Who edited it
   - When it was edited
   - Action buttons (Preview & Restore)

### Preview Functionality

- Click the **"Preview"** button (👁 icon) to view full content of a version
- Shows Office, Question, Answer, and Status
- No changes are made - just viewing

### Restore/Rollback

- Click the **"Restore"** button (↻ icon) to rollback to that version
- Confirmation dialog appears
- Current FAQ is automatically saved as a new version before rollback
- Selected version content replaces current FAQ content
- Rollback action is logged in `system_logs`

---

## 🚀 Usage Guide

### Step 1: Edit an FAQ (Creates First Version)

```
1. Go to FAQ Management page
2. Click Edit on any FAQ
3. Change the answer
4. Click "Update FAQ"
   
Result: Previous version is saved as v1 in faq_versions
```

### Step 2: Edit Again (Creates Second Version)

```
1. Edit the same FAQ again
2. Change the answer again
3. Click "Update FAQ"

Result: Previous version is saved as v2 in faq_versions
```

### Step 3: View Version History

```
1. Click the "View History" button (🕐 icon) on the FAQ
2. A modal opens showing all versions

Example display:
┌─────────────────────────────────────────────────────────────┐
│ FAQ Version History                                          │
├─────────────────────────────────────────────────────────────┤
│ v3 | "How do I..." | admin | Dec 15, 2024 3:45 PM | 👁 ↻   │
│ v2 | "How do I..." | admin | Dec 15, 2024 2:30 PM | 👁 ↻   │
│ v1 | "How do I..." | admin | Dec 15, 2024 1:15 PM | 👁 ↻   │
└─────────────────────────────────────────────────────────────┘
```

### Step 4: Preview a Version

```
1. Click the Preview button (👁) for any version
2. A new modal opens showing full content:
   
   Office: Registrar's Office
   Question: How do I drop a course?
   Answer: [Full answer text...]
   Status: Published
   
3. Click Close (no changes made)
```

### Step 5: Restore a Previous Version

```
1. Click the Restore button (↻) for the version you want
2. Confirmation dialog appears:
   "Are you sure you want to restore this FAQ to version 2?
    This will replace the current FAQ content."
    
3. Click OK

Result:
- Current FAQ is saved as a new version first
- Selected version content becomes the current FAQ
- Success message: "Successfully restored FAQ to version 2"
- FAQ list refreshes automatically
- Rollback is logged in system_logs
```

---

## 📊 Example Scenario

### Initial FAQ

```
Office: Registrar's Office
Question: How can I reset my student password?
Answer: Visit the ICT Office and fill out the password reset form.
Status: Published
```

### Edit 1 (Creates Version 1)

Admin updates answer to:
```
Answer: Use the ICT Portal and click 'Forgot Password'.
```

**Result:** Previous answer is saved as Version 1

### Edit 2 (Creates Version 2)

Admin realizes the new answer is wrong and updates again:
```
Answer: Email ict@university.edu with your student ID.
```

**Result:** Previous answer is saved as Version 2

### Rollback to Version 1

Admin wants the original answer back:
1. Clicks "View History"
2. Sees versions:
   - v2: "Email ict@university.edu..."
   - v1: "Use the ICT Portal..."
   
3. Clicks Preview on v1 to confirm it's the original
4. Clicks Restore on v1
5. Confirmation: "Restore to version 1?"
6. Clicks OK

**Result:** FAQ now has the original answer again!

---

## 🔐 Security & Permissions

- **Admin Only**: Only users with admin role can access version history and rollback
- **Authentication Required**: All API calls require valid JWT token
- **Audit Trail**: All rollback actions are logged with:
  - Who performed the rollback
  - Which FAQ was rolled back
  - Which version was restored
  - Timestamp
  
---

## 💾 Database Structure

### faq_versions Collection

```json
{
  "_id": "ObjectId",
  "faq_id": "string (original FAQ ID)",
  "version_number": 1,
  "office": "Registrar's Office",
  "question": "How can I reset my password?",
  "answer": "Visit the ICT Office...",
  "status": "published",
  "edited_by": "admin",
  "timestamp": "2024-12-15T14:30:00Z"
}
```

### system_logs Collection

```json
{
  "action": "faq_rollback",
  "faq_id": "507f1f77bcf86cd799439011",
  "version_restored": 1,
  "admin": "admin_user",
  "timestamp": "2024-12-15T15:00:00Z",
  "details": {
    "question": "How can I reset my password?",
    "office": "Registrar's Office"
  }
}
```

---

## 🛠 API Endpoints

### Get Version History

```
GET /api/faqs/<faq_id>/versions

Headers:
  Authorization: Bearer <token>

Response:
{
  "success": true,
  "versions": [
    {
      "_id": "...",
      "faq_id": "...",
      "version_number": 2,
      "question": "...",
      "answer": "...",
      "office": "...",
      "status": "published",
      "edited_by": "admin",
      "timestamp": "2024-12-15T14:30:00Z"
    },
    ...
  ],
  "total": 2
}
```

### Rollback to Version

```
POST /api/faqs/<faq_id>/rollback/<version_number>

Headers:
  Authorization: Bearer <token>

Response:
{
  "success": true,
  "message": "Successfully rolled back to version 2"
}
```

---

## 🎨 UI Components

### View History Button

```html
<button class="btn btn-sm btn-outline-info" 
        onclick="viewFAQHistory('faq_id')" 
        title="View History">
  <i class="fas fa-history"></i>
</button>
```

### Version History Modal

- Shows table with all versions
- Sortable by version number (newest first)
- Action buttons for each version

### Preview Modal

- Read-only display of version content
- Shows all FAQ fields

---

## ✅ Features Checklist

- [x] Automatic version saving on every FAQ update
- [x] Version history UI with history button
- [x] Version history modal with table view
- [x] Preview functionality for viewing version content
- [x] Rollback/restore functionality
- [x] Confirmation dialog before rollback
- [x] Current state saved before rollback (safety)
- [x] Rollback action logging in system_logs
- [x] Admin-only access control
- [x] JWT authentication required
- [x] Vector database (Pinecone) updated after rollback
- [x] MongoDB updated after rollback
- [x] Success/error notifications
- [x] Responsive design for mobile

---

## 🐛 Troubleshooting

### Version History Not Showing

**Problem:** "No version history available" message appears

**Solution:**
- Version history is created only AFTER first edit
- Original FAQs won't have versions until edited
- Edit the FAQ once to create first version

### Preview Not Loading

**Problem:** Preview button doesn't work

**Check:**
1. Browser console for errors
2. JWT token is valid (not expired)
3. FAQ version still exists in database

### Rollback Failed

**Problem:** "Failed to rollback" error

**Possible Causes:**
1. Invalid version number
2. FAQ was deleted
3. Network error
4. Database connection issue

**Solution:**
- Check browser console for detailed error
- Verify FAQ still exists
- Try refreshing the page
- Check server logs

---

## 📈 Future Enhancements

Potential improvements for future versions:

1. **Compare Versions**: Side-by-side diff view
2. **Version Comments**: Add notes when saving versions
3. **Auto-cleanup**: Delete very old versions (e.g., older than 6 months)
4. **Version Tags**: Mark important versions
5. **Export Version History**: Download as PDF or CSV
6. **Batch Rollback**: Restore multiple FAQs at once
7. **Version Branching**: Create variations from versions

---

## 📝 Testing Guide

### Test Case 1: Create Version History

```
1. Go to FAQ Management
2. Edit an FAQ (change answer)
3. Save changes
4. Click "View History"
Expected: Shows v1 with previous answer
```

### Test Case 2: Preview Version

```
1. Open version history
2. Click Preview on v1
Expected: Modal shows full v1 content
```

### Test Case 3: Rollback Success

```
1. Edit FAQ twice (creates v1 and v2)
2. Click "View History"
3. Click Restore on v1
4. Confirm rollback
Expected: FAQ reverts to v1 content
```

### Test Case 4: Rollback Safety

```
1. Before rollback, note current FAQ content
2. Perform rollback
3. Check version history again
Expected: Current content saved as new version
```

### Test Case 5: Audit Log

```
1. Perform a rollback
2. Check system_logs collection in MongoDB
Expected: Rollback action recorded with details
```

---

## 💡 Best Practices

### For Admins

1. **Review Before Rollback**: Always preview version first
2. **Use Descriptive Edits**: Make meaningful changes so version history is useful
3. **Regular Cleanup**: Periodically review old versions
4. **Document Major Changes**: Keep notes of significant FAQ updates

### For Developers

1. **Version Retention**: Consider implementing auto-cleanup after X months
2. **Monitor Storage**: Version history increases database size
3. **Backup System Logs**: Ensure audit trail is preserved
4. **Test Rollback**: Regularly test rollback functionality

---

## 📞 Support

If you encounter issues:

1. Check browser console for errors
2. Verify JWT token is valid
3. Check server logs for backend errors
4. Review MongoDB collections for data integrity
5. Test with a simple FAQ first

**Key Collections to Check:**
- `faqs` - Current FAQ data
- `faq_versions` - Version history
- `system_logs` - Rollback audit trail

---

## 🎉 Summary

The FAQ Rollback feature provides:

✅ **Safety**: Never lose FAQ content permanently
✅ **Flexibility**: Easy revert to any previous version
✅ **Transparency**: Full audit trail of all changes
✅ **Ease of Use**: Simple UI with clear actions
✅ **Admin Control**: Only authorized users can rollback

This feature ensures your FAQ management is both powerful and safe, giving you confidence to make updates knowing you can always revert if needed!

