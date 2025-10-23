# 📊 Status Detection System - Complete Guide

## 🎯 Overview

The **TCC Assistant Chatbot** now includes **automatic status detection** for every conversation, tracking whether messages are:
- ✅ **Resolved** - Question fully answered
- ⚠️ **Escalated** - Requires office visit or further action
- ❌ **Unresolved** - Chatbot couldn't provide helpful answer

This helps track chatbot performance and identify areas for improvement.

---

## 🔍 Status Types

### 1. **Resolved** ✅

**Definition:** The chatbot successfully answered the user's question with complete information.

**Examples:**
- **User:** "What are the office hours?"
- **Bot:** "TCC offices are open from 8:00 AM to 5:00 PM, Monday to Friday."
- **Status:** `resolved`

**Triggers:**
- Informational queries that have direct answers
- Greetings, thanks, goodbyes
- Simple "how-to" questions with clear instructions

### 2. **Escalated** ⚠️

**Definition:** The question requires an office visit or human assistance beyond the chatbot's scope.

**Examples:**
- **User:** "How do I reset my password?"
- **Bot:** "To reset your password, visit the ICT Office at the IT Building..."
- **Status:** `escalated`

**Triggers:**
- Password resets (requires office visit)
- Admission/enrollment inquiries (requires application)
- Complex requests needing human intervention

### 3. **Unresolved** ❌

**Definition:** The chatbot doesn't have information to answer the question.

**Examples:**
- **User:** "What's the cafeteria menu?"
- **Bot:** "I'm sorry, I don't have information about that yet..."
- **Status:** `unresolved`

**Triggers:**
- Questions outside chatbot's knowledge base
- Unclear or ambiguous queries
- Topics not yet covered

---

## 🛠️ Implementation Details

### **1. Backend (`chat.py`)**

The `get_chatbot_response()` function now returns a dictionary with status:

```python
def get_chatbot_response(message):
    """
    Returns:
        dict: {
            'response': str - The chatbot response text
            'status': str - 'resolved', 'unresolved', or 'escalated'
            'office': str - Detected office or 'General'
        }
    """
    # ... processing logic ...
    
    return {
        'response': response,
        'status': status,
        'office': office
    }
```

### **2. API Endpoint (`app.py`)**

The `/chat` endpoint returns status information:

**Request:**
```javascript
{
    "message": "How do I reset my password?",
    "original_message": "Paano mag-reset ng password?",
    "user_id": "user_abc123"
}
```

**Response:**
```javascript
{
    "response": "To reset your password, visit the ICT Office...",
    "user": "user_abc123",
    "status": "escalated",  // ← Status tracking
    "office": "ICT Office"
}
```

### **3. Frontend (`static/app.js`)**

The frontend logs and stores status:

```javascript
async sendMessageWithTranslation(userMsg) {
    // ... translation logic ...
    
    const data = await response.json();
    const status = data.status || 'resolved';
    const office = data.office || 'General';
    
    console.log(`Status: ${status}, Office: ${office}`);
    
    // Save to MongoDB with status
    await fetch("/save_bot_message", {
        body: JSON.stringify({
            message: botResponse,
            status: status,  // ← Saved to MongoDB
            office: office
        })
    });
}
```

### **4. MongoDB Storage**

Each message is now saved with status:

```javascript
{
    "user": "user_abc123",
    "sender": "bot",
    "message": "To reset your password, visit the ICT Office...",
    "office": "ICT Office",
    "status": "escalated",  // ← Status field
    "date": "2025-10-07"
}
```

---

## 📋 Status Logic by Query Type

### TCC E-Hub / Portal
- **Query:** "How do I access TCC E-Hub?"
- **Status:** `resolved`
- **Office:** ICT Office

### Username Queries
- **Query:** "What is my username?"
- **Status:** `resolved`
- **Office:** ICT Office

### Password Queries
- **Query:** "What's my password?"
- **Status:** `resolved`
- **Office:** ICT Office

### Password Reset
- **Query:** "How do I reset my password?"
- **Status:** `escalated` ⚠️ (Requires office visit)
- **Office:** ICT Office

### Registrar Queries
- **Query:** "Where is the registrar's office?"
- **Status:** `resolved`
- **Office:** Registrar's Office

### Office Hours
- **Query:** "What are the office hours?"
- **Status:** `resolved`
- **Office:** General

### Admission/Enrollment
- **Query:** "How do I apply?"
- **Status:** `escalated` ⚠️ (Requires application)
- **Office:** Admission Office

### ICT Support
- **Query:** "WiFi not working"
- **Status:** `resolved`
- **Office:** ICT Office

### Guidance Office
- **Query:** "I need counseling"
- **Status:** `resolved`
- **Office:** Guidance Office

### Student Affairs
- **Query:** "How to join clubs?"
- **Status:** `resolved`
- **Office:** Office of Student Affairs

### Greetings
- **Query:** "Hello!"
- **Status:** `resolved`
- **Office:** General

### Unknown Topics
- **Query:** "What's the cafeteria menu?"
- **Status:** `unresolved` ❌
- **Office:** General

---

## 📊 Analytics & Reporting

### **MongoDB Queries**

#### Count Resolved Messages
```javascript
db.conversations.count({ 
    sender: "bot", 
    status: "resolved" 
})
```

#### Count Escalated Messages
```javascript
db.conversations.count({ 
    sender: "bot", 
    status: "escalated" 
})
```

#### Count Unresolved Messages
```javascript
db.conversations.count({ 
    sender: "bot", 
    status: "unresolved" 
})
```

#### Status Breakdown
```javascript
db.conversations.aggregate([
    { $match: { sender: "bot" } },
    { $group: { 
        _id: "$status", 
        count: { $sum: 1 } 
    }}
])
```

#### Status by Office
```javascript
db.conversations.aggregate([
    { $match: { sender: "bot" } },
    { $group: { 
        _id: { office: "$office", status: "$status" },
        count: { $sum: 1 } 
    }}
])
```

#### Resolution Rate
```javascript
// Percentage of resolved messages
db.conversations.aggregate([
    { $match: { sender: "bot" } },
    { $group: { 
        _id: "$status", 
        count: { $sum: 1 } 
    }},
    { $project: {
        status: "$_id",
        count: 1,
        percentage: { 
            $multiply: [
                { $divide: ["$count", { $sum: "$count" }] }, 
                100
            ] 
        }
    }}
])
```

---

## 🧪 Testing Status Detection

### Test Case 1: Resolved Query
```
Input:  "What are the office hours?"
Expected Status: "resolved"
Expected Office: "General"
```

### Test Case 2: Escalated Query
```
Input:  "How do I reset my password?"
Expected Status: "escalated"
Expected Office: "ICT Office"
```

### Test Case 3: Unresolved Query
```
Input:  "What's the cafeteria menu?"
Expected Status: "unresolved"
Expected Office: "General"
```

### Test Case 4: Filipino Escalated Query
```
Input:  "Paano mag-apply sa college?"
Translated: "How do I apply to college?"
Expected Status: "escalated"
Expected Office: "Admission Office"
```

---

## 🎯 Performance Metrics

### **Success Metrics**

| Metric | Target | Calculation |
|--------|--------|-------------|
| **Resolution Rate** | > 70% | (Resolved / Total) × 100 |
| **Escalation Rate** | 10-20% | (Escalated / Total) × 100 |
| **Unresolved Rate** | < 15% | (Unresolved / Total) × 100 |

### **Example Dashboard**

```
Total Conversations: 1,000
├─ Resolved:    750 (75%) ✅
├─ Escalated:   150 (15%) ⚠️
└─ Unresolved:  100 (10%) ❌
```

---

## 💡 Best Practices

### 1. **Monitor Unresolved Messages**
- Review unresolved queries weekly
- Add new responses for common questions
- Update chatbot knowledge base

### 2. **Track Escalation Patterns**
- Identify which topics require most escalation
- Create self-service guides for common escalations
- Train staff on frequent escalation topics

### 3. **Improve Resolution Rate**
- Analyze resolved vs unresolved ratios
- Add more detailed responses
- Cover edge cases and variations

### 4. **Office-Specific Insights**
- Track which offices get most queries
- Identify underperforming office responses
- Optimize frequently asked office questions

---

## 🔍 Debugging

### **Browser Console**

Check status logging:
```javascript
// Open DevTools (F12)
// You should see:
Status: escalated, Office: ICT Office
Message status: escalated | Office: ICT Office
```

### **MongoDB Verification**

Check if status is being saved:
```javascript
// In MongoDB Shell
db.conversations.find().sort({date: -1}).limit(5).pretty()

// Should show:
{
    "message": "...",
    "status": "escalated",  // ← Status field present
    "office": "ICT Office"
}
```

---

## 📈 Continuous Improvement

### **Weekly Review Process**

1. **Export Unresolved Messages**
   ```javascript
   db.conversations.find({ 
       sender: "user", 
       status: "unresolved" 
   }).limit(50)
   ```

2. **Analyze Common Patterns**
   - Group by similar topics
   - Identify knowledge gaps

3. **Add New Responses**
   - Update `get_chatbot_response()` in `chat.py`
   - Add new keyword patterns
   - Set appropriate status

4. **Test and Deploy**
   - Test new responses
   - Verify status assignment
   - Monitor improvement

---

## ✅ Benefits

1. **📊 Better Analytics** - Track chatbot performance accurately
2. **🎯 Identify Gaps** - See what topics need improvement
3. **⚡ Faster Improvements** - Data-driven chatbot enhancements
4. **👥 Resource Planning** - Know which offices need more support
5. **📈 Measure Success** - Quantify chatbot effectiveness

---

## 🚀 Future Enhancements

### Planned Features
- [ ] Real-time status dashboard
- [ ] Automated weekly reports
- [ ] Status-based conversation routing
- [ ] A/B testing for response effectiveness
- [ ] Predictive analytics for common issues

---

## 📝 Summary

**Status Detection is now fully integrated:**

✅ **Backend** - Returns status with every response  
✅ **API** - Includes status in all responses  
✅ **Frontend** - Logs and displays status  
✅ **MongoDB** - Stores status with messages  
✅ **Translation** - Works with Filipino/English  
✅ **Analytics** - Ready for reporting  

**All conversations are now tracked with resolved/escalated/unresolved status!** 🎉

---

**Last Updated:** October 7, 2025  
**Version:** 1.2.0  
**Status:** ✅ Production Ready

