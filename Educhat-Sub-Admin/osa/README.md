# Office of Student Affairs (OSA) Chatbot Admin Portal

A comprehensive sub-admin portal for managing chatbot operations, content, and analytics in educational institutions. This portal provides administrators with tools to manage FAQs, announcements, monitor conversations, and analyze user feedback.

## 🚀 Features

### Core Functionality
- **User Authentication**: Secure login system with role-based access control
- **Dashboard Overview**: Real-time KPI metrics and performance indicators
- **FAQ Management**: Create, edit, and manage frequently asked questions
- **Announcement System**: Schedule and manage institutional announcements
- **Conversation Monitoring**: Track and analyze chatbot interactions
- **User Feedback Analysis**: Monitor user satisfaction and sentiment
- **Usage Statistics**: Comprehensive analytics and performance metrics
- **Export Capabilities**: CSV export for data analysis and reporting

### User Interface
- **Responsive Design**: Modern, mobile-friendly interface using Bootstrap 5
- **Intuitive Navigation**: Clean sidebar navigation with organized sections
- **Real-time Updates**: Live data updates and notifications
- **Search Functionality**: Advanced search across all content types
- **Modal Interfaces**: Streamlined forms for content management

## 🏗️ Project Structure

```
osa/
├── assets/
│   ├── css/
│   │   └── style.css                 # Custom styling and themes
│   └── js/
│       ├── core/
│       │   └── StorageManager.js     # Data persistence and management
│       ├── modules/
│       │   ├── AnnouncementManager.js # Announcement CRUD operations
│       │   ├── AuthManager.js        # Authentication and session management
│       │   ├── ConversationManager.js # Conversation monitoring
│       │   ├── DashboardManager.js   # Dashboard data and charts
│       │   ├── FAQManager.js         # FAQ CRUD operations
│       │   ├── FeedbackManager.js    # User feedback management
│       │   └── UsageStatsManager.js  # Analytics and statistics
│       └── UIManager.js              # UI interactions and modals
├── pages/
│   ├── dashboard.html                # Main dashboard view
│   ├── conversations.html            # Conversation logs
│   ├── faq.html                     # FAQ management interface
│   ├── announcements.html            # Announcement management
│   ├── usage-stats.html             # Usage analytics
│   └── feedback.html                # User feedback dashboard
├── index.html                       # Login page
└── README.md                        # This file
```

## 🛠️ Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **UI Framework**: Bootstrap 5.3.0
- **Icons**: Font Awesome 6.4.0
- **Charts**: Chart.js for data visualization
- **Storage**: Local Storage for data persistence
- **Build**: No build process required - pure client-side application

## 📋 Prerequisites

- Modern web browser (Chrome, Firefox, Safari, Edge)
- Local web server (for development)
- No additional software installation required

## 🚀 Quick Start

### 1. Clone or Download
```bash
# Clone the repository
git clone [repository-url]
cd osa

# Or download and extract the ZIP file
```

### 2. Setup Local Server
```bash
# Using Python 3
python -m http.server 8000

# Using Node.js
npx http-server

# Using PHP
php -S localhost:8000
```

### 3. Access the Application
Open your browser and navigate to:
```
http://localhost:8000
```

### 4. Default Login Credentials
- **Email**: `admin@studentaffairs.edu`
- **Password**: `admin123`

## 🔐 Authentication

The portal uses a secure authentication system with:
- Session management
- Role-based access control
- Automatic logout on inactivity
- Secure credential storage

## 📊 Dashboard Features

### KPI Cards
- **Total Users**: Active user count and growth trends
- **Chatbot Queries**: Total interactions and weekly growth
- **Query Success Rate**: Percentage of successful resolutions
- **Escalated Queries**: Cases requiring human intervention

### Analytics
- **Weekly Usage Charts**: Visual representation of chatbot activity
- **Time-based Analysis**: Usage patterns throughout the day
- **Category Distribution**: Query types and frequency
- **Performance Metrics**: Response times and success rates

## 📝 Content Management

### FAQ Management
- Create and edit frequently asked questions
- Set publication status (draft/published)
- Search and filter existing FAQs
- Bulk operations support

### Announcements
- Schedule announcements with start/end dates
- Set priority levels (low/medium/high)
- Manage publication status
- Content versioning and updates

## 📈 Analytics & Reporting

### Usage Statistics
- Daily, weekly, and monthly usage trends
- User engagement metrics
- Performance analytics
- Export functionality for external analysis

### User Feedback
- Rating-based feedback collection
- Sentiment analysis
- Category-based filtering
- Trend analysis over time

## 🔧 Configuration

### Storage Keys
The application uses the following localStorage keys:
- `studentaffairs_faqs` - FAQ data
- `studentaffairs_announcements` - Announcement data
- `studentaffairs_conversations` - Conversation logs
- `studentaffairs_feedback` - User feedback
- `studentaffairs_usage_stats` - Usage statistics
- `studentaffairs_users` - User accounts

### Customization
- Modify `assets/css/style.css` for theme changes
- Update `StorageManager.js` for data structure modifications
- Customize dashboard metrics in respective manager files

## 🚨 Security Considerations

- **Local Storage**: Data is stored locally in the browser
- **Authentication**: Basic session-based authentication
- **Data Privacy**: No external data transmission
- **Access Control**: Role-based permissions system

## 📱 Browser Compatibility

- **Chrome**: 90+
- **Firefox**: 88+
- **Safari**: 14+
- **Edge**: 90+

## 🐛 Troubleshooting

### Common Issues

1. **Login Not Working**
   - Clear browser cache and cookies
   - Verify default credentials
   - Check browser console for errors

2. **Data Not Loading**
   - Refresh the page
   - Check localStorage availability
   - Verify JavaScript is enabled

3. **Charts Not Displaying**
   - Ensure Chart.js is loaded
   - Check for JavaScript errors
   - Verify data format

### Debug Mode
Enable console logging by checking browser developer tools for detailed error messages and debugging information.

## 🔄 Updates & Maintenance

### Regular Maintenance
- Clear old conversation logs periodically
- Archive outdated announcements
- Review and update FAQs
- Monitor user feedback trends

### Data Backup
- Export important data regularly
- Backup localStorage data if needed
- Maintain offline copies of critical information

## 📞 Support

For technical support or feature requests:
- Check the browser console for error messages
- Review the JavaScript files for configuration issues
- Ensure all dependencies are properly loaded

## 📄 License

This project is developed for educational institutions and internal use. Please ensure compliance with your organization's data handling and privacy policies.

## 🤝 Contributing

To contribute to this project:
1. Review the existing code structure
2. Follow the established coding patterns
3. Test changes thoroughly
4. Update documentation as needed

## 📚 Additional Resources

- [Bootstrap Documentation](https://getbootstrap.com/docs/)
- [Chart.js Documentation](https://www.chartjs.org/docs/)
- [Font Awesome Icons](https://fontawesome.com/icons)
- [Local Storage API](https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage)

---

**Version**: 1.0.0  
**Last Updated**: December 2024  
**Maintained By**: Office of Student Affairs Development Team
