# Guidance Office Chatbot Admin Portal

A comprehensive sub-admin portal for managing chatbot operations, FAQs, announcements, and analytics for educational institutions.

## 🎯 Overview

The Guidance Office Chatbot Admin Portal is a web-based administrative interface designed to help guidance counselors and administrators manage their institution's chatbot system. It provides tools for content management, user analytics, and system monitoring.

## ✨ Features

### 🔐 Authentication & Security
- Secure login system with role-based access control
- Session management and automatic logout
- Protected routes for authenticated users only

### 📊 Dashboard
- Real-time KPI metrics and performance indicators
- Visual charts and analytics
- System overview and quick access to key functions

### 🤖 Chatbot Management
- **FAQ Management**: Create, edit, and manage frequently asked questions
- **Announcements**: Post and schedule important notices
- **Conversation Logs**: Monitor and analyze chatbot interactions
- **User Feedback**: Track user satisfaction and ratings

### 📈 Analytics & Reporting
- Usage statistics and trends
- User engagement metrics
- Export functionality for data analysis
- Performance monitoring

### 🎨 User Interface
- Modern, responsive design using Bootstrap 5
- Intuitive navigation with sidebar menu
- Mobile-friendly interface
- Toast notifications for user feedback

## 🚀 Getting Started

### Prerequisites
- Modern web browser (Chrome, Firefox, Safari, Edge)
- No server setup required - runs entirely in the browser

### Installation
1. Download or clone the project files
2. Open `index.html` in your web browser
3. The application will load with default data

### Default Login Credentials
```
Email: admin@guidance.edu
Password: admin123
```

## 📁 Project Structure

```
guidance/
├── index.html                 # Main login page
├── assets/
│   ├── css/
│   │   └── style.css         # Custom styles
│   └── js/
│       ├── app.js            # Main application logic
│       ├── UIManager.js      # UI management utilities
│       ├── core/
│       │   └── StorageManager.js  # Data storage and management
│       └── modules/
│           ├── AuthManager.js      # Authentication handling
│           ├── DashboardManager.js # Dashboard functionality
│           ├── FAQManager.js       # FAQ CRUD operations
│           ├── AnnouncementManager.js # Announcement management
│           ├── ConversationManager.js  # Conversation monitoring
│           ├── FeedbackManager.js      # User feedback handling
│           └── UsageStatsManager.js   # Analytics and statistics
└── pages/
    ├── dashboard.html         # Main dashboard
    ├── faq.html              # FAQ management
    ├── announcements.html     # Announcement management
    ├── conversations.html     # Conversation logs
    ├── feedback.html          # User feedback
    └── usage-stats.html      # Usage statistics
```

## 🔧 Configuration

### Storage
The application uses browser localStorage for data persistence. All data is stored locally and will persist between browser sessions.

### Customization
- **Branding**: Update office name and branding in HTML files and JavaScript
- **Colors**: Modify CSS variables in `style.css` for custom color schemes
- **Features**: Enable/disable modules by commenting out script includes

## 📱 Usage Guide

### 1. Login
- Navigate to the login page
- Enter your credentials
- Click "Sign in" to access the dashboard

### 2. Dashboard
- View key performance indicators
- Access quick navigation to all features
- Monitor system status

### 3. FAQ Management
- **Add FAQ**: Click "+ Add New FAQ" button
- **Edit FAQ**: Click edit icon on existing FAQs
- **Delete FAQ**: Click delete icon (with confirmation)
- **Search**: Use search bar to find specific FAQs

### 4. Announcements
- **Create**: Add new announcements with title, content, and dates
- **Schedule**: Set start and end dates for announcements
- **Priority**: Assign low, medium, or high priority
- **Status**: Manage draft, scheduled, active, or inactive states

### 5. Conversation Monitoring
- View chatbot conversation logs
- Analyze user interactions
- Monitor sentiment and escalation rates
- Track conversation categories

### 6. User Feedback
- Monitor user satisfaction ratings
- Filter feedback by rating (1-5 stars)
- Search through feedback comments
- Track feedback trends over time

### 7. Analytics
- Export usage statistics
- View performance metrics
- Monitor user engagement
- Track system performance

## 🛠️ Technical Details

### Frontend Technologies
- **HTML5**: Semantic markup and structure
- **CSS3**: Modern styling with CSS variables
- **JavaScript (ES6+)**: Modern JavaScript features
- **Bootstrap 5**: Responsive UI framework
- **Chart.js**: Data visualization library

### Data Management
- **LocalStorage**: Client-side data persistence
- **JSON**: Data format for storage and transfer
- **CRUD Operations**: Full create, read, update, delete functionality

### Browser Compatibility
- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## 🔒 Security Features

- Client-side authentication
- Session management
- Protected route access
- Input validation and sanitization

## 📊 Data Export

The system supports exporting data in CSV format for:
- FAQ lists
- Announcements
- User feedback
- Usage statistics
- Conversation logs

## 🚨 Troubleshooting

### Common Issues

1. **Login not working**
   - Verify credentials are correct
   - Check browser console for errors
   - Clear browser cache and try again

2. **Data not saving**
   - Ensure localStorage is enabled
   - Check browser storage limits
   - Verify JavaScript is enabled

3. **Page not loading**
   - Check all files are present
   - Verify file paths are correct
   - Check browser console for errors

### Browser Console
Use the browser's developer tools (F12) to:
- View error messages
- Monitor network requests
- Debug JavaScript issues
- Check localStorage contents

## 🔄 Updates and Maintenance

### Regular Tasks
- Review and update FAQs
- Monitor user feedback
- Analyze usage statistics
- Update announcements

### Data Backup
- Export important data regularly
- Backup localStorage data
- Document custom configurations

## 📞 Support

For technical support or questions:
- Check the browser console for error messages
- Review this README for common solutions
- Ensure all files are properly loaded
- Verify browser compatibility

## 📄 License

This project is designed for educational institution use. Please ensure compliance with your organization's policies and data protection regulations.

## 🔮 Future Enhancements

Potential features for future versions:
- Multi-user support with different permission levels
- Real-time notifications
- Advanced analytics and reporting
- Integration with external systems
- Mobile app version
- Cloud-based data storage
- API endpoints for external access

---

**Version:** 1.0.0  
**Last Updated:** December 2024  
**Compatibility:** Modern web browsers with JavaScript enabled
