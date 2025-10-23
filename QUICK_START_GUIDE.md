# Sub Admin FAQ - Quick Start Guide 🚀

## ⚡ 3-Minute Setup

### Step 1: Start the Server
```bash
# Make sure you're in the project directory
cd chatbot-deployment

# Activate virtual environment (if needed)
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate  # Windows

# Run Flask
python app.py
```

**Expected Output:**
```
MongoDB connected successfully
Vector Store connected to Pinecone
Flask app running on http://0.0.0.0:5000
```

---

### Step 2: Login as Sub-Admin

1. **Open browser**: Navigate to `http://localhost:5000/sub-index`

2. **Select your office**: Choose from dropdown
   - Admission Office
   - Registrar's Office
   - ICT Office
   - Guidance Office
   - Office of Student Affairs (OSA)

3. **Login credentials**:
   | Office | Email | Password |
   |--------|-------|----------|
   | Admission Office | admissions@tcc.edu | admissions123 |
   | Registrar's Office | registrar@tcc.edu | registrar123 |
   | ICT Office | ict@tcc.edu | ict123 |
   | Guidance Office | guidance@tcc.edu | guidance123 |
   | OSA | osa@tcc.edu | osa123 |

---

### Step 3: Add Your First FAQ

1. **Navigate**: Click "FAQ Management" in the sidebar
2. **Click**: "Add New FAQ" button
3. **Fill in**:
   - **Question**: "What are your office hours?"
   - **Answer**: "We are open Monday-Friday, 8:00 AM - 5:00 PM"
   - **Status**: "Published"
4. **Submit**: Click "Create"

✅ **Done!** Your FAQ is now:
- Stored in MongoDB
- Indexed in Pinecone
- Available to the chatbot

---

### Step 4: Test the Chatbot

1. **Open new tab**: Navigate to `http://localhost:5000/`
2. **Type in chat**: "What are your office hours?"
3. **See magic**: Chatbot responds with your FAQ answer!

---

## 🎯 Key Features

| Feature | Description |
|---------|-------------|
| ✅ **Add FAQ** | Create new FAQs instantly |
| ✅ **Edit FAQ** | Update existing FAQs |
| ✅ **Delete FAQ** | Remove FAQs with confirmation |
| ✅ **Search** | Filter FAQs by keyword |
| ✅ **Status Control** | Draft vs Published |
| ✅ **Office Isolation** | Only see your office's FAQs |
| ✅ **Auto-Sync** | Chatbot uses FAQs immediately |
| ✅ **Admin Monitor** | Admins see all Sub-Admin FAQs |

---

## 🔑 Important URLs

| Page | URL | Purpose |
|------|-----|---------|
| Sub-Admin Login | `/sub-index` | Login page |
| FAQ Management | `/Sub-faq` | Manage FAQs |
| Chatbot Interface | `/` | Test FAQ responses |
| Admin Dashboard | `/dashboard` | View all FAQs (admin only) |

---

## 📋 API Endpoints

All endpoints require sub-admin authentication:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/sub-faq/list` | List all FAQs for your office |
| POST | `/api/sub-faq/add` | Add new FAQ |
| GET | `/api/sub-faq/<id>` | Get specific FAQ |
| PUT | `/api/sub-faq/<id>` | Update FAQ |
| DELETE | `/api/sub-faq/<id>` | Delete FAQ |
| POST | `/api/sub-faq/search` | Vector search FAQs |

---

## 🐛 Quick Troubleshooting

### Problem: Can't login

**Solution:**
- Check MongoDB connection in Flask console
- Verify credentials match office selected
- Clear browser cache/cookies

### Problem: FAQ not in chatbot responses

**Solution:**
- Ensure status is "Published" (not Draft)
- Check Pinecone connection: Look for "Vector Store connected" in console
- Try exact FAQ question first
- Wait 5 seconds and try again (indexing delay)

### Problem: "Authentication required" error

**Solution:**
- Login again at `/sub-index`
- Make sure you selected the correct office
- Don't manually change office in URL

---

## 💡 Best Practices

1. **Write clear questions**: Use natural language users would actually type
2. **Complete answers**: Include all necessary information in one place
3. **Test before publishing**: Use "Draft" status while testing
4. **Use search**: Check if similar FAQ exists before creating new one
5. **Keep it updated**: Review and update FAQs regularly

---

## 📊 How It Works (Simple Version)

```
You add FAQ → Stored in MongoDB → Embedded in Pinecone → Chatbot uses it
     ↓              ↓                    ↓                    ↓
  Interface      Database          Vector Search      Instant Response
```

---

## 🎓 Example FAQs

**Good FAQ Examples:**

```
Q: How do I reset my student portal password?
A: To reset your password, visit portal.tcc.edu/reset and enter your student ID. 
   You'll receive a reset link via your registered email within 5 minutes.

Q: What documents do I need for admission?
A: Required documents include: 1) Completed application form, 2) Official high school 
   transcripts, 3) Valid ID, 4) Two passport photos. Submit online at admissions.tcc.edu.

Q: When is the enrollment deadline?
A: Fall semester enrollment deadline is August 15. Spring semester deadline is January 10. 
   Late enrollment is available with a $50 fee until 2 weeks after semester start.
```

---

## 🚀 Next Steps

1. ✅ **Add 5-10 FAQs** for your office's most common questions
2. ✅ **Test chatbot** with various phrasings
3. ✅ **Train your team** on using the FAQ management interface
4. ✅ **Monitor usage** and update FAQs based on user questions
5. ✅ **Coordinate with other offices** to avoid duplicate FAQs

---

## 📞 Need Help?

- **Check logs**: Browser console (F12) and Flask terminal
- **Review docs**: See `SUB_ADMIN_FAQ_IMPLEMENTATION.md` for details
- **Test guide**: See `SUB_FAQ_TESTING_GUIDE.md` for comprehensive testing

---

## ✅ Success Checklist

- [ ] Flask server running
- [ ] Can login as sub-admin
- [ ] Can access FAQ Management page
- [ ] Can add new FAQ
- [ ] FAQ appears in table
- [ ] Can edit FAQ
- [ ] Can delete FAQ
- [ ] Search works
- [ ] Chatbot uses FAQ in responses
- [ ] No console errors

---

**🎉 You're all set! Start adding FAQs and watch your chatbot get smarter!**


