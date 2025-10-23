# Admin Notification System

## Overview

The Admin Notification System provides a unified notification center that aggregates notifications from all admin content areas in the EduChat Admin Portal. This system helps administrators stay informed about important events, new content, and activities that require attention.

## Features

### 1. **Unified Notification Center**
- Single dropdown panel accessible from all admin pages
- Real-time notification updates
- Auto-refresh every 60 seconds
- Badge counter showing unread notifications

### 2. **Multi-Source Notifications**
The system aggregates notifications from:
- **Feedback** - New user feedback and ratings
- **Conversations** - Unresolved or escalated conversations
- **Users** - New sub-admin account creations
- **FAQs** - Recently added or modified FAQs
- **Usage** - High traffic alerts and usage spikes

### 3. **Interactive Features**
- Click to view details and navigate to relevant page
- Refresh notifications on demand
- Mark all as read functionality
- Color-coded notification types
- Time-relative timestamps ("2 hours ago")

## Components

### Backend API

**Endpoint:** `/api/admin/notifications`
- **Method:** GET
- **Authentication:** Required (token + admin role)
- **Returns:** JSON with notifications array and counts

**Response Structure:**
```json
{
  "success": true,
  "notifications": [
    {
      "id": "unique_id",
      "type": "feedback|conversation|user|faq|alert",
      "title": "Notification title",
      "message": "Notification message",
      "time": "2025-10-10 14:30",
      "icon": "fa-icon-name",
      "color": "success|warning|danger|info|primary",
      "link": "/page-url"
    }
  ],
  "total_count": 15,
  "unread_count": 15
}
```

### Frontend Components

#### 1. **NotificationManager.js** (`static/assets/js/modules/NotificationManager.js`)
JavaScript class that manages:
- Fetching notifications from backend
- Updating UI with notification data
- Handling user interactions
- Auto-refresh timer management
- Dropdown open/close logic

**Key Methods:**
- `initialize()` - Set up the notification system
- `loadNotifications()` - Fetch notifications from API
- `updateUI()` - Update badge and dropdown content
- `toggleDropdown()` - Show/hide notification panel
- `markAllAsRead()` - Clear notification count

#### 2. **CSS Styles** (`static/assets/css/style.css`)
Comprehensive styling for:
- Notification dropdown panel
- Notification items with color-coding
- Icons and badges
- Animations and transitions
- Responsive design for mobile

#### 3. **HTML Structure**
Notification dropdown added to page headers:
```html
<div class="notification-icon">
    <i class="fas fa-bell"></i>
    <span class="notification-badge" style="display: none;">0</span>
</div>

<div class="notification-dropdown" id="notificationDropdown">
    <div class="notification-header">...</div>
    <div class="notification-list" id="notificationList">...</div>
</div>
```

## Installation

### 1. Backend Setup (Already Implemented)
The notification API endpoint is added to `app.py`:
- Located at line 3498-3666
- Uses MongoDB to query multiple collections
- Aggregates data from last 24 hours

### 2. Frontend Integration

**For each admin template:**

1. **Add the notification dropdown HTML** (after notification-icon, before user-info-dropdown):
```html
<!-- Notification Dropdown Panel -->
<div class="notification-dropdown" id="notificationDropdown">
    <div class="notification-header">
        <h3><i class="fas fa-bell"></i> Notifications</h3>
        <div class="notification-header-actions">
            <button id="notificationRefreshBtn" title="Refresh notifications">
                <i class="fas fa-sync-alt"></i>
            </button>
            <button id="notificationMarkAllReadBtn" title="Mark all as read">
                <i class="fas fa-check-double"></i>
            </button>
        </div>
    </div>
    <div class="notification-list" id="notificationList">
        <div class="notification-empty">
            <i class="fas fa-bell-slash"></i>
            <p>Loading notifications...</p>
        </div>
    </div>
</div>
```

2. **Add NotificationManager.js script** (in script section):
```html
<script src="{{ url_for('static', filename='assets/js/modules/NotificationManager.js') }}"></script>
```

3. **Initialize in JavaScript** (in DOMContentLoaded):
```javascript
let notificationManager;

document.addEventListener('DOMContentLoaded', async function() {
    // ... other initializations ...
    
    notificationManager = new NotificationManager();
    await notificationManager.initialize();
});
```

4. **Update notification badge visibility** (change from `3` to hidden by default):
```html
<span class="notification-badge" style="display: none;">0</span>
```

## Notification Types

### Color Coding
- 🟢 **Success (Green)** - Positive feedback, resolved issues
- 🟡 **Warning (Yellow)** - Unresolved conversations, moderate issues
- 🔴 **Danger (Red)** - Escalated issues, critical alerts
- 🔵 **Info (Blue)** - New users, general information
- 🟣 **Primary (Purple)** - FAQ updates, content changes

### Icons
- 💬 `fa-comments` - Conversations
- ❤️ `fa-heart` - Feedback
- 👤 `fa-user-plus` - New users
- ❓ `fa-question-circle` - FAQs
- 📊 `fa-chart-line` - Usage alerts

## Configuration

### Auto-Refresh Interval
Default: 60 seconds (60000ms)
```javascript
this.refreshInterval = 60000; // in NotificationManager constructor
```

### Recent Time Window
Default: Last 24 hours
```python
recent_time = datetime.now() - timedelta(hours=24)  # in app.py
```

### High Usage Threshold
Default: 50 conversations per hour
```python
if recent_conversations_count > 50:  # in app.py
    # Show usage spike alert
```

## Pages Implemented

✅ **dashboard.html** - Fully implemented with notification system

### Remaining Pages to Update:
- [ ] conversations.html
- [ ] faq.html
- [ ] feedback.html
- [ ] roles.html
- [ ] settings.html
- [ ] users.html
- [ ] usage.html

## Usage

### For Administrators
1. Click the bell icon in the top-right header
2. View notifications in the dropdown panel
3. Click a notification to navigate to its source page
4. Use the refresh button to manually update
5. Use "Mark all as read" to clear the badge

### For Developers

**Adding New Notification Types:**

1. **Backend (app.py):**
```python
# Add new notification source in get_admin_notifications()
try:
    new_collection = db['your_collection']
    new_items_count = new_collection.count_documents({
        'created_at': {'$gte': recent_time}
    })
    
    if new_items_count > 0:
        recent_items = list(new_collection.find({
            'created_at': {'$gte': recent_time}
        }).sort('created_at', -1).limit(3))
        
        for item in recent_items:
            notifications.append({
                'id': str(item.get('_id', '')),
                'type': 'your_type',
                'title': 'Your notification title',
                'message': 'Your message',
                'time': item.get('created_at', datetime.now()).strftime('%Y-%m-%d %H:%M'),
                'icon': 'fa-your-icon',
                'color': 'info',
                'link': '/your-page'
            })
        total_count += new_items_count
except Exception as e:
    print(f"Error fetching your notifications: {e}")
```

2. **Frontend:** No changes needed - the system automatically displays any notifications returned by the API.

## Technical Details

### Database Collections Used
- `feedback` - User feedback collection
- `conversations` - Chat conversations
- `sub_users` - Sub-admin users
- `faqs` - FAQ entries

### Dependencies
- MongoDB with PyMongo
- Flask for backend API
- Font Awesome for icons
- Chart.js (already included)

### Browser Compatibility
- Modern browsers (Chrome, Firefox, Edge, Safari)
- Mobile responsive design
- Works with all admin pages

## Troubleshooting

### Notifications not loading
1. Check browser console for errors
2. Verify authentication token is valid
3. Check MongoDB connection
4. Ensure API endpoint is accessible

### Badge not updating
1. Check auto-refresh is enabled
2. Verify notification count calculation
3. Check CSS styles for badge visibility

### Dropdown not appearing
1. Verify NotificationManager.js is loaded
2. Check for JavaScript errors
3. Ensure CSS is properly loaded
4. Check z-index conflicts

## Future Enhancements

Potential improvements:
- Persistent "read" status in database
- Per-user notification preferences
- Email/push notifications integration
- Notification categories filtering
- Search functionality in notifications
- Export notification history
- Notification sound alerts
- Desktop notifications API

## Support

For issues or questions about the notification system:
1. Check this documentation
2. Review browser console for errors
3. Verify database connectivity
4. Check API response in Network tab

---

**Version:** 1.0.0  
**Last Updated:** October 10, 2025  
**Author:** EduChat Development Team

