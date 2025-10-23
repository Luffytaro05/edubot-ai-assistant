# Usage Statistics Module - Sub Admin Portal

## 📊 Overview

A comprehensive usage statistics module for the EduChat Sub Admin portal that provides office-specific analytics and performance metrics. The system automatically detects which office the Sub Admin belongs to and displays only relevant statistics for that office.

---

## 🎯 Features Implemented

### Key Performance Indicators (KPIs)

1. **Total Sessions** - Number of conversation sessions between users and the chatbot
2. **Average Session Duration** - Average time users spend in conversation sessions
3. **Response Rate (%)** - Percentage of user messages that received bot responses
4. **Success Rate (%)** - Percentage of successfully resolved queries vs escalated ones

### Analytics & Visualizations

1. **Usage by Time of Day** - Bar chart showing usage patterns across:
   - Morning (6 AM - 12 PM)
   - Afternoon (12 PM - 5 PM)
   - Evening (5 PM - 9 PM)
   - Night (9 PM - 6 AM)

2. **Top Query Categories** - Ranked list of most frequent query categories/intents with:
   - Category name
   - Query count
   - Percentage of total queries
   - Visual progress bars

### Additional Features

- **Export to CSV** - Download usage statistics for reporting
- **Office-based Filtering** - Automatic office detection via session authentication
- **Real-time Data** - Live statistics from MongoDB
- **Responsive Design** - Mobile-friendly charts and cards
- **Caching** - 5-minute cache to improve performance

---

## 📁 File Structure

```
chatbot-deployment/
├── sub_usage.py                              # Flask Blueprint (Backend API)
├── templates/
│   └── Sub-usage.html                        # HTML Template (UI)
├── static/
│   └── Sub-assets/
│       └── js/
│           └── modules/
│               └── UsageStatsManager.js      # Frontend Logic
└── app.py                                    # Main Flask app (registers routes)
```

---

## 🔧 Backend Implementation

### File: `sub_usage.py`

Flask Blueprint with 4 API endpoints:

#### 1. **Overview Statistics**
```
GET /api/sub-admin/usage/overview
```

**Purpose**: Returns comprehensive KPI metrics

**Calculations**:
- **Total Sessions**: Count unique user conversation sessions
- **Avg Session Duration**: `∑(EndTime - StartTime) / TotalSessions`
- **Response Rate**: `(Bot Responses / User Messages) × 100`
- **Success Rate**: `(Resolved Queries / Total Queries) × 100`

**Response Example**:
```json
{
  "success": true,
  "data": {
    "totalSessions": 1543,
    "avgSessionDuration": "4m 32s",
    "avgSessionDurationSeconds": 272,
    "responseRate": 95.8,
    "successRate": 88.3,
    "totalUserMessages": 5421,
    "totalBotResponses": 5195,
    "resolvedQueries": 1362,
    "escalatedQueries": 181,
    "office": "Registrar's Office"
  }
}
```

#### 2. **Usage by Time of Day**
```
GET /api/sub-admin/usage/time-of-day
```

**Purpose**: Returns conversation counts grouped by time periods

**Response Example**:
```json
{
  "success": true,
  "data": {
    "labels": ["Morning", "Afternoon", "Evening", "Night"],
    "counts": [423, 891, 567, 234],
    "office": "Registrar's Office"
  }
}
```

#### 3. **Top Query Categories**
```
GET /api/sub-admin/usage/top-categories?limit=10
```

**Purpose**: Returns most frequent query categories

**Response Example**:
```json
{
  "success": true,
  "data": {
    "categories": [
      {
        "name": "Enrollment",
        "count": 342,
        "percentage": 22.5
      },
      {
        "name": "Transcript Request",
        "count": 289,
        "percentage": 19.0
      }
    ],
    "totalConversations": 1520,
    "office": "Registrar's Office"
  }
}
```

#### 4. **Export to CSV**
```
GET /api/sub-admin/usage/export
```

**Purpose**: Export statistics as CSV file

**Response Example**:
```json
{
  "success": true,
  "data": "Office,Metric,Value\nRegistrar's Office,Total Sessions,1543\n...",
  "filename": "Registrars_Office_usage_stats.csv"
}
```

### Authentication & Office Detection

All endpoints use `get_current_subadmin()` to:
1. Verify the Sub Admin is authenticated
2. Extract the office from the Flask session
3. Return only data for that specific office

```python
def get_current_subadmin():
    """Get logged-in sub-admin from Flask session"""
    if session.get("role") == "sub-admin" and session.get("office"):
        return {
            "office": session.get("office"),
            "name": session.get("name", "Sub Admin"),
            "email": session.get("email")
        }
    return None
```

---

## 💻 Frontend Implementation

### File: `static/Sub-assets/js/modules/UsageStatsManager.js`

Object-oriented JavaScript class that handles:

#### Key Methods:

1. **`initialize()`** - Load all statistics on page load
2. **`loadOverviewStats()`** - Fetch and render KPI cards
3. **`loadTimeOfDayChart()`** - Fetch and render bar chart
4. **`loadTopCategories()`** - Fetch and render category list
5. **`exportUsageStats()`** - Export data to CSV file

#### Chart Implementation:

Uses **Chart.js** for bar chart visualization:

```javascript
this.charts.timeOfDay = new Chart(ctx, {
    type: 'bar',
    data: {
        labels: ['Morning', 'Afternoon', 'Evening', 'Night'],
        datasets: [{
            label: 'Usage Count',
            data: [423, 891, 567, 234],
            backgroundColor: [
                'rgba(59, 130, 246, 0.8)',   // Blue
                'rgba(251, 191, 36, 0.8)',   // Yellow
                'rgba(249, 115, 22, 0.8)',   // Orange
                'rgba(99, 102, 241, 0.8)'    // Indigo
            ]
        }]
    },
    options: {
        responsive: true,
        // ... chart options
    }
});
```

#### Category List Rendering:

Dynamically generates HTML for top categories:

```javascript
renderTopCategories(data) {
    const categories = data.categories || [];
    let html = '<div class="category-list">';
    
    categories.forEach((category, index) => {
        html += `
            <div class="query-category-item">
                <span class="badge">${index + 1}</span>
                ${category.name}
                <div class="progress-bar" style="width: ${percentage}%"></div>
                <small>${category.percentage}%</small>
            </div>
        `;
    });
    
    container.innerHTML = html;
}
```

---

## 🎨 UI Implementation

### File: `templates/Sub-usage.html`

Bootstrap 5-based template with:

#### KPI Cards Section:
```html
<div class="row mb-4">
    <div class="col-md-3 mb-3">
        <div class="kpi-card">
            <div class="kpi-icon" style="background: var(--secondary-blue);">
                <i class="fas fa-users"></i>
            </div>
            <div class="kpi-value" id="totalSessions">0</div>
            <div class="kpi-label">Total Sessions</div>
            <div class="kpi-trend trend-up">
                <i class="fas fa-arrow-up"></i> +12%
            </div>
        </div>
    </div>
    <!-- 3 more KPI cards -->
</div>
```

#### Charts Section:
```html
<div class="row mb-4">
    <div class="col-md-8">
        <div class="chart-container">
            <h5 class="chart-title">Usage by Time of Day</h5>
            <canvas id="timeOfDayChart"></canvas>
        </div>
    </div>
    <div class="col-md-4">
        <div class="chart-container">
            <h5 class="chart-title">Top Query Categories</h5>
            <div id="queryCategoriesChart">
                <!-- Categories populated by JS -->
            </div>
        </div>
    </div>
</div>
```

#### JavaScript Initialization:
```html
<script>
document.addEventListener('DOMContentLoaded', async function() {
    // Get office from URL
    const office = window.authManager.getOfficeFromURL();

    // Require authentication
    const valid = await window.authManager.requireSubAdminAuth(office);
    if (!valid) return;

    // Initialize Usage Stats manager
    window.usageStatsManager = new UsageStatsManager();
    window.usageStatsManager.initialize();
});
</script>
```

---

## 🔐 Security & Authentication

### Office-based Access Control

1. **Session-based Authentication**: Flask session stores user's office
2. **Automatic Office Detection**: Backend extracts office from session
3. **Data Isolation**: MongoDB queries filter by office
4. **Frontend Validation**: AuthManager validates office access

### Authentication Flow:

```
1. Sub Admin logs in → Flask stores office in session
2. User visits /Sub-usage_stats → Flask renders template with office
3. Frontend JS fetches data → Backend validates session
4. MongoDB queries → Filter by office from session
5. Return office-specific data only
```

---

## 🚀 Usage Instructions

### For Developers:

#### 1. **Backend Setup** (Already Done):
- `sub_usage.py` - Flask Blueprint with API routes
- `app.py` - Blueprint registered (line 39)
- Route `/Sub-usage_stats` - Renders the template (line 1616)

#### 2. **Frontend Setup** (Already Done):
- `UsageStatsManager.js` - Fetch and render logic
- `Sub-usage.html` - UI template with Chart.js

#### 3. **Testing**:

**Start Flask App**:
```bash
python app.py
```

**Login as Sub Admin**:
- Navigate to: `http://localhost:5000/sub-index`
- Select office: "Registrar's Office"
- Email: `registrar@tcc.edu`
- Password: `registrar123`

**Access Usage Statistics**:
- Navigate to: `http://localhost:5000/Sub-usage_stats?office=Registrar's Office`
- Or click "Usage Statistics" in sidebar

### For Sub Admins:

1. **Login** to the Sub Admin portal
2. Click **"Usage Statistics"** in the sidebar
3. View **4 KPI cards** at the top
4. Explore **time of day chart** and **top categories**
5. Click **"Export"** button to download CSV

---

## 📊 Data Flow Diagram

```
┌─────────────────┐
│  Sub Admin User │
└────────┬────────┘
         │ Login
         ▼
┌─────────────────────┐
│  Flask Session      │ ← Office stored here
│  {office: "Reg..."}│
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Sub-usage.html     │
│  (UI Template)      │
└────────┬────────────┘
         │ User visits page
         ▼
┌──────────────────────────┐
│  UsageStatsManager.js    │
│  - Fetch KPIs            │
│  - Fetch Time of Day     │
│  - Fetch Top Categories  │
└────────┬─────────────────┘
         │ API Calls
         ▼
┌──────────────────────────┐
│  sub_usage.py (Backend)  │
│  - Validate session      │
│  - Extract office        │
│  - Query MongoDB         │
│  - Calculate metrics     │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│  MongoDB                 │
│  conversations collection│
│  Filter: {office: "..."} │
└──────────────────────────┘
```

---

## 🧪 Testing Checklist

- [x] Backend API endpoints return correct data
- [x] Office detection works from session
- [x] KPI cards display correct values
- [x] Time of day chart renders properly
- [x] Top categories list shows rankings
- [x] Export functionality generates CSV
- [x] Authentication redirects unauthorized users
- [x] Responsive design on mobile devices
- [ ] Test with real conversation data
- [ ] Test with multiple offices
- [ ] Performance testing with large datasets

---

## 📈 Metrics Explained

### 1. Total Sessions
**What it measures**: Number of unique conversation sessions

**Calculation**: Count distinct users who had conversations in the office

**Use Case**: Track engagement and chatbot adoption

---

### 2. Average Session Duration
**What it measures**: Average time users spend chatting

**Formula**: 
```
Avg Duration = ∑(Last Message Time - First Message Time) / Total Sessions
```

**Format**: `4m 32s` or `1h 15m`

**Use Case**: Understand user engagement depth

---

### 3. Response Rate
**What it measures**: How often the bot responds to user messages

**Formula**:
```
Response Rate = (Total Bot Responses / Total User Messages) × 100
```

**Ideal Value**: 95-100% (every user message gets a response)

**Use Case**: Measure chatbot reliability

---

### 4. Success Rate
**What it measures**: Percentage of queries successfully resolved

**Formula**:
```
Success Rate = (Resolved Queries / (Resolved + Escalated)) × 100
```

**Ideal Value**: 80-90% (most queries resolved without escalation)

**Use Case**: Measure chatbot effectiveness

---

## 🎨 Customization Options

### Adjust Time Periods:

Edit `classify_time_of_day()` in `sub_usage.py`:

```python
def classify_time_of_day(hour):
    if 6 <= hour < 12:
        return "Morning"
    elif 12 <= hour < 17:
        return "Afternoon"
    # Add more periods...
```

### Change Chart Colors:

Edit `renderTimeOfDayChart()` in `UsageStatsManager.js`:

```javascript
backgroundColor: [
    'rgba(59, 130, 246, 0.8)',   // Morning - Change this
    'rgba(251, 191, 36, 0.8)',   // Afternoon - Change this
    // ...
]
```

### Add More Metrics:

1. Add new API endpoint in `sub_usage.py`
2. Add fetch method in `UsageStatsManager.js`
3. Add HTML element in `Sub-usage.html`
4. Call fetch method in `initialize()`

---

## 🐛 Troubleshooting

### Issue: "Not authenticated" error

**Solution**: 
- Ensure Sub Admin is logged in
- Check Flask session has `role` and `office`
- Verify `get_current_subadmin()` returns data

### Issue: Charts not rendering

**Solution**:
- Check Chart.js CDN is loaded
- Verify canvas element exists with correct ID
- Check browser console for JavaScript errors

### Issue: No data showing

**Solution**:
- Verify MongoDB has conversations for the office
- Check conversations have required fields (office, timestamp, sender)
- Ensure office name in session matches MongoDB data

### Issue: Wrong office data showing

**Solution**:
- Verify session office matches URL parameter
- Check `requireSubAdminAuth()` is called
- Ensure MongoDB queries filter by correct office

---

## 📝 Future Enhancements

1. **Historical Trends**: Compare current metrics with previous periods
2. **Detailed Analytics**: Drill-down into specific categories
3. **User Satisfaction**: Integrate feedback scores with usage data
4. **Peak Hours Analysis**: Identify busiest times for staffing
5. **Comparative Analysis**: Compare office performance
6. **Real-time Updates**: WebSocket for live statistics
7. **Custom Date Ranges**: Filter by specific date periods
8. **Sentiment Analysis**: Track user sentiment over time

---

## 📞 Support

For technical support or questions:
- Check browser console for errors
- Verify MongoDB connection
- Test API endpoints directly with tools like Postman
- Review Flask logs for backend errors

---

**Usage Statistics Module** - Comprehensive analytics for office-specific chatbot performance tracking! ✨

