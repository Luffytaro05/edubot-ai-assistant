# Sentiment Analysis - Visual Examples

## What You'll See in the Dashboard

### Example 1: Positive Feedback ✅

**User Submits:**
```
Rating: ⭐⭐⭐⭐⭐ (5 stars)
Comment: "Excellent service! Very helpful and quick responses. I love this chatbot!"
```

**Dashboard Shows:**
```
┌─────────────────────────────────────────────────────────────────┐
│ Rating: ⭐⭐⭐⭐⭐                                                  │
│ Comment: "Excellent service! Very helpful and quick responses.  │
│          I love this chatbot!"                                  │
│ Sentiment: 😊 Positive  [Hover to see scores]                  │
│ Date: 10/21/2025 10:30:00                                      │
└─────────────────────────────────────────────────────────────────┘
```

**On Hover (Tooltip):**
```
┌──────────────────────────────┐
│ VADER Sentiment Analysis     │
├──────────────────────────────┤
│ Overall Score: 91.1%         │
│ Positive: 62.3%              │
│ Neutral: 37.7%               │
│ Negative: 0.0%               │
└──────────────────────────────┘
```

**Click "View" (Modal):**
```
┌─────────────────────────────────────────────────┐
│ Feedback Details                           [×]   │
├─────────────────────────────────────────────────┤
│ Rating: ⭐⭐⭐⭐⭐                                 │
│                                                 │
│ Sentiment: 😊 Positive                          │
│                                                 │
│ ╔═══════════════════════════════════╗          │
│ ║ VADER Sentiment Analysis          ║          │
│ ╠═══════════════════════════════════╣          │
│ ║ Overall Score: 91.1%              ║          │
│ ║ ████████████████████░░░░          ║          │
│ ║                                   ║          │
│ ║ 😊 Positive: 62.3%                ║          │
│ ║ ██████████████░░░░░░              ║          │
│ ║                                   ║          │
│ ║ 😐 Neutral: 37.7%                 ║          │
│ ║ ████████░░░░░░░░░░                ║          │
│ ║                                   ║          │
│ ║ 😞 Negative: 0.0%                 ║          │
│ ║ ░░░░░░░░░░░░░░░░░░░░              ║          │
│ ╚═══════════════════════════════════╝          │
│                                                 │
│ Date: 10/21/2025 10:30:00                      │
│                                                 │
│ Message:                                        │
│ "Excellent service! Very helpful and quick      │
│  responses. I love this chatbot!"              │
│                                                 │
│                          [Close]                │
└─────────────────────────────────────────────────┘
```

---

### Example 2: Negative Feedback ⚠️

**User Submits:**
```
Rating: ⭐⭐ (2 stars)
Comment: "Terrible experience. The bot was slow and unhelpful. Very disappointing."
```

**Dashboard Shows:**
```
┌─────────────────────────────────────────────────────────────────┐
│ Rating: ⭐⭐                                                     │
│ Comment: "Terrible experience. The bot was slow and unhelpful.  │
│          Very disappointing."                                   │
│ Sentiment: 😞 Negative  [Hover to see scores]                  │
│ Date: 10/21/2025 11:15:00                                      │
└─────────────────────────────────────────────────────────────────┘
```

**On Hover (Tooltip):**
```
┌──────────────────────────────┐
│ VADER Sentiment Analysis     │
├──────────────────────────────┤
│ Overall Score: -76.4%        │
│ Positive: 0.0%               │
│ Neutral: 54.8%               │
│ Negative: 45.2%              │
└──────────────────────────────┘
```

**Click "View" (Modal):**
```
┌─────────────────────────────────────────────────┐
│ Feedback Details                           [×]   │
├─────────────────────────────────────────────────┤
│ Rating: ⭐⭐                                     │
│                                                 │
│ Sentiment: 😞 Negative                          │
│                                                 │
│ ╔═══════════════════════════════════╗          │
│ ║ VADER Sentiment Analysis          ║          │
│ ╠═══════════════════════════════════╣          │
│ ║ Overall Score: -76.4%             ║          │
│ ║ ████████████████████░░░░ (RED)    ║          │
│ ║                                   ║          │
│ ║ 😊 Positive: 0.0%                 ║          │
│ ║ ░░░░░░░░░░░░░░░░░░░░              ║          │
│ ║                                   ║          │
│ ║ 😐 Neutral: 54.8%                 ║          │
│ ║ ████████████░░░░░░░░              ║          │
│ ║                                   ║          │
│ ║ 😞 Negative: 45.2%                ║          │
│ ║ ██████████░░░░░░░░░░              ║          │
│ ╚═══════════════════════════════════╝          │
│                                                 │
│ Date: 10/21/2025 11:15:00                      │
│                                                 │
│ Message:                                        │
│ "Terrible experience. The bot was slow and      │
│  unhelpful. Very disappointing."               │
│                                                 │
│                          [Close]                │
└─────────────────────────────────────────────────┘
```

---

### Example 3: Neutral Feedback 😐

**User Submits:**
```
Rating: ⭐⭐⭐ (3 stars)
Comment: "Average service. Nothing special but it works."
```

**Dashboard Shows:**
```
┌─────────────────────────────────────────────────────────────────┐
│ Rating: ⭐⭐⭐                                                   │
│ Comment: "Average service. Nothing special but it works."       │
│ Sentiment: 😐 Neutral  [Hover to see scores]                   │
│ Date: 10/21/2025 12:00:00                                      │
└─────────────────────────────────────────────────────────────────┘
```

**On Hover (Tooltip):**
```
┌──────────────────────────────┐
│ VADER Sentiment Analysis     │
├──────────────────────────────┤
│ Overall Score: -16.0%        │
│ Positive: 0.0%               │
│ Neutral: 78.6%               │
│ Negative: 21.4%              │
└──────────────────────────────┘
```

---

### Example 4: Comment Overrides Rating 🎯

**User Submits:**
```
Rating: ⭐⭐⭐⭐⭐ (5 stars)  ← High rating
Comment: "Actually found it helpful and easy to use after some time!"  ← Positive comment
```

**Dashboard Shows:**
```
┌─────────────────────────────────────────────────────────────────┐
│ Rating: ⭐⭐⭐⭐⭐                                                │
│ Comment: "Actually found it helpful and easy to use after       │
│          some time!"                                            │
│ Sentiment: 😊 Positive  [Comment confirms rating]              │
│ Date: 10/21/2025 13:00:00                                      │
└─────────────────────────────────────────────────────────────────┘
```

**Another Example:**
```
Rating: ⭐ (1 star)  ← Low rating
Comment: "Actually found it really helpful and easy to use!"  ← Positive comment
```

**Dashboard Shows:**
```
┌─────────────────────────────────────────────────────────────────┐
│ Rating: ⭐                                                      │
│ Comment: "Actually found it really helpful and easy to use!"    │
│ Sentiment: 😊 Positive  [Comment overrode low rating]          │
│ Date: 10/21/2025 13:30:00                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Feedback Table View

**What you see in the main dashboard:**

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Feedback Analytics                                                        │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│ KPI Cards:                                                                │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │
│ │ ⭐ Avg Rating│ │ 📝 Total    │ │ 😊 Positive │ │ 😞 Negative │        │
│ │    4.5       │ │    100      │ │    75%      │ │    15%      │        │
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘        │
│                                                                           │
│ Filters: [All] [Positive] [Negative] [Neutral]                          │
│                                                                           │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │ Rating │ Comment                   │ Sentiment    │ Date     │ Actions │
│ ├────────┼──────────────────────────┼──────────────┼──────────┼────────┤
│ │ ⭐⭐⭐⭐⭐│ Excellent service!       │ 😊 Positive  │10/21/25 │ [View] │
│ │ ⭐⭐⭐⭐  │ Great experience         │ 😊 Positive  │10/21/25 │ [View] │
│ │ ⭐⭐⭐    │ It's okay, not bad       │ 😐 Neutral   │10/21/25 │ [View] │
│ │ ⭐⭐     │ Very disappointing...    │ 😞 Negative  │10/21/25 │ [View] │
│ │ ⭐      │ Terrible experience      │ 😞 Negative  │10/21/25 │ [View] │
│ └─────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│ Page 1 of 10                              [< Previous] [Next >]          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Filter by Sentiment

**Click "Positive" filter:**
```
┌─────────────────────────────────────────────────────────────────────────┐
│ Filters: [All] [Positive*] [Negative] [Neutral]                         │
│                                                                          │
│ Showing 75 positive feedback entries                                    │
│                                                                          │
│ ┌───────────────────────────────────────────────────────────────────┐   │
│ │ Rating │ Comment                   │ Sentiment    │ Date     │ Actions│
│ ├────────┼──────────────────────────┼──────────────┼──────────┼───────┤
│ │ ⭐⭐⭐⭐⭐│ Excellent service!       │ 😊 Positive  │10/21/25 │ [View]│
│ │ ⭐⭐⭐⭐  │ Great experience         │ 😊 Positive  │10/21/25 │ [View]│
│ │ ⭐⭐⭐⭐⭐│ Amazing! So helpful!     │ 😊 Positive  │10/21/25 │ [View]│
│ │ ⭐⭐⭐⭐  │ Very satisfied           │ 😊 Positive  │10/21/25 │ [View]│
│ └───────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Export Data

**CSV Export includes sentiment:**
```csv
Rating,Message,Sentiment,VADER_Compound,Date,User ID
5,"Excellent service!",positive,0.911,2025-10-21 10:30:00,user123
2,"Very disappointing",negative,-0.764,2025-10-21 11:15:00,user456
3,"It's okay",neutral,-0.160,2025-10-21 12:00:00,user789
```

---

## Real-Time Detection

**User types comment:**
```
┌────────────────────────────────────────┐
│ Feedback Form                          │
├────────────────────────────────────────┤
│ Rating: ⭐⭐⭐⭐⭐                       │
│                                        │
│ Comment (optional):                    │
│ ┌────────────────────────────────────┐ │
│ │ This chatbot is amazing! It        │ │
│ │ helped me find the information     │ │
│ │ I needed quickly and easily.       │ │
│ └────────────────────────────────────┘ │
│                                        │
│           [Submit Feedback]            │
└────────────────────────────────────────┘
```

**After submission (backend):**
```
→ Analyzing sentiment...
→ VADER scores calculated:
  • Compound: 0.763 (76.3% positive)
  • Positive: 0.581
  • Neutral: 0.250
  • Negative: 0.169
→ Classification: POSITIVE
→ Saved to database ✓
```

**Admin sees immediately:**
```
┌─────────────────────────────────────────────────────────────┐
│ New Feedback Received!                                      │
├─────────────────────────────────────────────────────────────┤
│ Rating: ⭐⭐⭐⭐⭐                                            │
│ Sentiment: 😊 Positive (76.3% confidence)                  │
│ Comment: "This chatbot is amazing! It helped me..."        │
└─────────────────────────────────────────────────────────────┘
```

---

## Color Coding

**Badge Colors:**
- 😊 **Positive** → 🟢 Green badge (`#28a745`)
- 😐 **Neutral** → ⚪ Gray badge (`#6c757d`)
- 😞 **Negative** → 🔴 Red badge (`#dc3545`)

**Visual Example:**
```
Positive:  [🟢 😊 Positive ]  ← Green background
Neutral:   [⚪ 😐 Neutral  ]  ← Gray background
Negative:  [🔴 😞 Negative ]  ← Red background
```

---

## Mobile View

**On mobile devices:**
```
┌──────────────────────────┐
│ Feedback #1              │
├──────────────────────────┤
│ ⭐⭐⭐⭐⭐ (5 stars)      │
│                          │
│ 😊 Positive              │
│                          │
│ "Excellent service!      │
│  Very helpful and        │
│  quick responses."       │
│                          │
│ 10/21/2025              │
│         [View Details]   │
└──────────────────────────┘

┌──────────────────────────┐
│ Feedback #2              │
├──────────────────────────┤
│ ⭐⭐ (2 stars)           │
│                          │
│ 😞 Negative              │
│                          │
│ "Very disappointing      │
│  experience."            │
│                          │
│ 10/21/2025              │
│         [View Details]   │
└──────────────────────────┘
```

---

## Summary

**What You Get:**
- ✅ Automatic sentiment detection
- ✅ Visual indicators with emojis
- ✅ Color-coded badges
- ✅ Hover tooltips with scores
- ✅ Detailed modal views
- ✅ Filter by sentiment
- ✅ Export with sentiment data
- ✅ Mobile responsive

**No configuration needed - it just works!** 🎉


