# Sub Admin FAQ - Testing Guide

## ✅ Pre-Testing Checklist

Before testing, ensure:
- [ ] Flask server is running (`python app.py`)
- [ ] MongoDB Atlas connection is active
- [ ] Pinecone API key is set in environment variables
- [ ] Sub-admin user account is created and active

---

## 🧪 Test Scenarios

### **Test 1: Sub-Admin Login**

**Steps:**
1. Navigate to `/sub-index`
2. Select your office from dropdown (e.g., "Admission Office")
3. Enter sub-admin credentials:
   - Email: `admissions@tcc.edu`
   - Password: `admissions123`
4. Click "Login"

**Expected Result:**
- ✅ Redirected to Sub-dashboard
- ✅ Office name displayed in sidebar and header
- ✅ FAQ Management menu item visible

---

### **Test 2: Access FAQ Management Page**

**Steps:**
1. From Sub-dashboard, click "FAQ Management" in sidebar
2. Page loads at `/Sub-faq?office=Admission+Office`

**Expected Result:**
- ✅ Page loads without errors
- ✅ Page title shows "FAQ Management"
- ✅ Subtitle shows "Manage frequently asked questions for [Your Office]"
- ✅ Search bar and "Add New FAQ" button visible
- ✅ FAQ table displays (may be empty initially)

---

### **Test 3: Add New FAQ**

**Steps:**
1. Click "Add New FAQ" button
2. Modal opens with title "Add New FAQ"
3. Fill in the form:
   - **Question**: "What are the admission requirements for freshmen?"
   - **Answer**: "Freshmen applicants must have a high school diploma or equivalent, submit official transcripts, and complete the online application at admissions.tcc.edu. Additional requirements may include standardized test scores and letters of recommendation."
   - **Status**: "Published"
4. Click "Create" button

**Expected Result:**
- ✅ Modal closes automatically
- ✅ Success toast notification appears: "FAQ added successfully and synced to chatbot"
- ✅ New FAQ appears in the table
- ✅ Console logs show:
   ```
   FAQ inserted into sub_faqs collection with ID: [id]
   FAQ mirrored to admin faqs collection with ID: [id]
   FAQ vector stored in Pinecone with ID: [id]
   ```

**Verify in Database:**
```javascript
// MongoDB
use chatbot_db;
db.sub_faqs.find().pretty();
db.faqs.find({source: "sub_admin"}).pretty();
```

---

### **Test 4: View FAQ Details**

**Steps:**
1. Find the FAQ you just created in the table
2. Click the blue "eye" icon (View button)

**Expected Result:**
- ✅ "View FAQ" modal opens
- ✅ Question displayed correctly
- ✅ Answer displayed correctly
- ✅ Status shows "Published" badge (green)
- ✅ Created and Updated timestamps displayed

---

### **Test 5: Edit FAQ**

**Steps:**
1. Click the yellow "edit" icon on your FAQ
2. Modal opens with title "Edit FAQ"
3. Form is pre-filled with current FAQ data
4. Modify the answer:
   - Add: "For international students, additional documents including visa verification may be required."
5. Click "Update" button

**Expected Result:**
- ✅ Modal closes
- ✅ Success toast: "FAQ updated successfully"
- ✅ Table refreshes with updated FAQ
- ✅ Console shows:
   ```
   FAQ updated in MongoDB with ID: [id]
   FAQ vector updated in Pinecone with ID: [id]
   ```

---

### **Test 6: Search FAQs (Frontend)**

**Steps:**
1. In the search box, type "admission"
2. Observe table filtering in real-time

**Expected Result:**
- ✅ Table instantly filters to show only FAQs containing "admission"
- ✅ Other FAQs are hidden
- ✅ Clear search box to show all FAQs again

---

### **Test 7: Chatbot Integration (The Big Test!)**

**Steps:**
1. Open the main chatbot interface in a new tab (navigate to `/`)
2. In the chat, type: "What do I need to apply for admission?"
3. Send the message

**Expected Result:**
- ✅ Chatbot responds with the FAQ answer you created
- ✅ Response matches your FAQ answer (may be slightly paraphrased)
- ✅ Flask console shows:
   ```
   FAQ match found with score: 0.XX
   Using FAQ response
   ```
- ✅ Score should be > 0.8 for exact matches

**Alternative Test Questions:**
- "admission requirements"
- "how to apply"
- "what are the requirements for freshmen"

---

### **Test 8: Draft Status (Not Visible to Chatbot)**

**Steps:**
1. Add a new FAQ with Status: "Draft"
   - Question: "Test draft FAQ"
   - Answer: "This is a draft FAQ"
2. Try asking the chatbot about this FAQ

**Expected Result:**
- ✅ FAQ appears in your Sub-admin FAQ table
- ✅ Status badge shows "Draft" (gray)
- ✅ Chatbot does NOT use this FAQ in responses
- ✅ Only "Published" FAQs are used by chatbot

---

### **Test 9: Multiple FAQs**

**Steps:**
1. Add 3-5 more FAQs with different questions:
   - "What is the application deadline?"
   - "How do I submit my transcripts?"
   - "Are there any application fees?"
2. Save all as "Published"

**Expected Result:**
- ✅ All FAQs appear in table
- ✅ Search functionality works across all FAQs
- ✅ Chatbot can answer any of these questions

---

### **Test 10: Delete FAQ**

**Steps:**
1. Click the red "trash" icon on a test FAQ
2. Confirmation dialog appears
3. Click "OK"

**Expected Result:**
- ✅ Confirmation prompt shown
- ✅ FAQ removed from table immediately
- ✅ Success toast: "FAQ deleted successfully"
- ✅ Console shows:
   ```
   FAQ deleted from MongoDB with ID: [id]
   FAQ vector deleted from Pinecone with ID: [id]
   ```

**Verify Deletion:**
```javascript
// MongoDB - should not exist
db.sub_faqs.find({_id: ObjectId("[deleted_id]")});
```

---

### **Test 11: Office Isolation**

**Steps:**
1. Login as a different office sub-admin (e.g., ICT Office)
   - Email: `ict@tcc.edu`
   - Password: `ict123`
2. Navigate to FAQ Management
3. Check the FAQ table

**Expected Result:**
- ✅ Only sees FAQs for ICT Office
- ✅ Cannot see Admission Office FAQs
- ✅ Cannot edit/delete other offices' FAQs

---

### **Test 12: Admin View (Centralized Monitoring)**

**Steps:**
1. Logout from Sub-admin
2. Login as Super Admin:
   - Email: `dxtrzpc26@gmail.com`
   - Password: `dexterpogi123`
3. Navigate to Admin FAQ Management
4. View all FAQs

**Expected Result:**
- ✅ Admin can see ALL FAQs from all offices
- ✅ Sub-admin FAQs are marked with `source: "sub_admin"`
- ✅ Can filter by office
- ✅ Can edit/delete any FAQ

---

### **Test 13: Error Handling**

**Test Empty Fields:**
1. Click "Add New FAQ"
2. Leave question or answer empty
3. Click "Create"

**Expected Result:**
- ✅ Validation toast appears
- ✅ Form not submitted

**Test Network Error:**
1. Stop Flask server
2. Try to add/edit FAQ

**Expected Result:**
- ✅ Error toast appears with message
- ✅ No data corruption

---

### **Test 14: Pinecone Vector Search Accuracy**

**Steps:**
1. Add FAQ: "How do I reset my student portal password?"
2. Ask chatbot variations:
   - "forgot my password"
   - "can't login to portal"
   - "reset password help"

**Expected Result:**
- ✅ All variations match the FAQ
- ✅ Chatbot responds with correct answer
- ✅ Similarity scores shown in console

---

### **Test 15: Performance Test**

**Steps:**
1. Add 20+ FAQs rapidly
2. Observe response times

**Expected Result:**
- ✅ Each FAQ adds in < 500ms
- ✅ Table renders smoothly
- ✅ Search remains fast
- ✅ No browser freezing

---

## 🔍 Monitoring & Debugging

### **Check Console Logs (Browser)**
Open browser DevTools (F12) and check for:
- ✅ No JavaScript errors
- ✅ Successful API responses (200 status codes)
- ✅ Proper data being sent/received

### **Check Flask Console Logs**
Monitor Flask terminal for:
```
FAQ inserted into sub_faqs collection with ID: ...
FAQ mirrored to admin faqs collection with ID: ...
FAQ vector stored in Pinecone with ID: ...
FAQ match found with score: 0.XX
```

### **Check MongoDB**
```javascript
// Count FAQs
db.sub_faqs.count();
db.faqs.count({source: "sub_admin"});

// View recent FAQs
db.sub_faqs.find().sort({created_at: -1}).limit(5).pretty();
```

### **Check Pinecone**
```python
from vector_store import VectorStore
vs = VectorStore()
print(vs.get_stats())
# Should show increased vector count
```

---

## 🐛 Common Issues & Solutions

### Issue: "FAQ not synced to chatbot"

**Possible Causes:**
- Pinecone API key not set
- Vector store initialization failed
- FAQ status is "draft"

**Solutions:**
1. Check environment variable: `echo $PINECONE_API_KEY`
2. Check Flask logs for Pinecone errors
3. Verify FAQ status is "published"

---

### Issue: "Sub-admin authentication required"

**Possible Causes:**
- Not logged in as sub-admin
- Session expired
- Wrong office parameter in URL

**Solutions:**
1. Re-login as sub-admin
2. Check session in browser DevTools (Application > Cookies)
3. Verify URL has correct `?office=...` parameter

---

### Issue: "FAQ not appearing in chatbot responses"

**Possible Causes:**
- Low similarity score (< 0.8)
- FAQ not embedded in Pinecone
- Question wording too different from user query

**Solutions:**
1. Check console for similarity scores
2. Verify FAQ in Pinecone: `vs.index.describe_index_stats()`
3. Try asking with exact FAQ question first
4. Consider lowering threshold (in app.py, change `> 0.8` to `> 0.7`)

---

### Issue: "Can see other offices' FAQs"

**Possible Causes:**
- Office filtering not working
- Database query issue

**Solutions:**
1. Check Flask session for correct office
2. Verify MongoDB query includes office filter
3. Check `require_sub_admin_auth` decorator

---

## ✅ Success Criteria

All tests passed when:
- [x] Can login as sub-admin
- [x] Can view FAQ page
- [x] Can add new FAQs
- [x] Can edit existing FAQs
- [x] Can delete FAQs
- [x] FAQs stored in MongoDB
- [x] FAQs indexed in Pinecone
- [x] Chatbot uses FAQs in responses
- [x] Office isolation working
- [x] Admin can view all FAQs
- [x] Search functionality working
- [x] No JavaScript errors
- [x] Performance acceptable

---

## 📊 Test Report Template

```
=== Sub Admin FAQ Testing Report ===
Date: [Date]
Tester: [Name]
Environment: [Local/Production]

Test Results:
✅ Test 1: Sub-Admin Login - PASS
✅ Test 2: Access FAQ Page - PASS
✅ Test 3: Add FAQ - PASS
✅ Test 4: View FAQ - PASS
✅ Test 5: Edit FAQ - PASS
✅ Test 6: Search FAQs - PASS
✅ Test 7: Chatbot Integration - PASS
✅ Test 8: Draft Status - PASS
✅ Test 9: Multiple FAQs - PASS
✅ Test 10: Delete FAQ - PASS
✅ Test 11: Office Isolation - PASS
✅ Test 12: Admin View - PASS
✅ Test 13: Error Handling - PASS
✅ Test 14: Vector Search - PASS
✅ Test 15: Performance - PASS

Issues Found: [None / List issues]

Overall Status: ✅ READY FOR PRODUCTION
```

---

## 🎯 Next Steps After Testing

1. ✅ All tests pass → Mark feature as complete
2. ❌ Some tests fail → Review error logs and fix issues
3. 📝 Document any discovered edge cases
4. 🚀 Deploy to production when ready

---

**Happy Testing!** 🎉


