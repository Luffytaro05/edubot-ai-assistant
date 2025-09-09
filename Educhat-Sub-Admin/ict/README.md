# ICT Services Chatbot Admin Portal

A comprehensive web-based administration portal for managing an ICT Services chatbot system. This portal provides sub-administrators with tools to manage FAQs, announcements, monitor conversations, analyze usage statistics, and collect user feedback.

## 🚀 Features

### Core Functionality
- **User Authentication**: Secure login system for sub-administrators
- **Dashboard**: Overview of system performance and key metrics
- **FAQ Management**: Create, edit, delete, and manage frequently asked questions
- **Announcement System**: Post and manage system-wide announcements
- **Conversation Monitoring**: View and analyze chatbot conversation logs
- **Usage Analytics**: Comprehensive statistics and performance metrics
- **Feedback Management**: Monitor and analyze user satisfaction

### Technical Features
- **Responsive Design**: Mobile-friendly interface using Bootstrap 5
- **Local Storage**: Data persistence using browser localStorage
- **Modular Architecture**: Clean separation of concerns with dedicated managers
- **Real-time Updates**: Dynamic content updates without page refresh
- **Export Functionality**: CSV export for analytics and reports

## 🏗️ Project Structure

```
ict/
├── assets/
│   ├── css/
│   │   └── style.css          # Custom styling and theme
│   └── js/
│       ├── core/
│       │   └── StorageManager.js    # Data persistence layer
│       ├── modules/
│       │   ├── AnnouncementManager.js
│       │   ├── AuthManager.js
│       │   ├── ConversationManager.js
│       │   ├── DashboardManager.js
│       │   ├── FAQManager.js
│       │   ├── FeedbackManager.js
│       │   └── UsageStatsManager.js
│       └── UIManager.js       # User interface management
├── pages/
│   ├── dashboard.html         # Main dashboard view
│   ├── conversations.html     # Conversation logs
│   ├── faq.html             # FAQ management
│   ├── announcements.html    # Announcement management
│   ├── feedback.html         # User feedback
│   └── usage-stats.html     # Usage analytics
└── index.html                # Login page
```

## 🛠️ Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **UI Framework**: Bootstrap 5.3.0
- **Icons**: Font Awesome 6.4.0
- **Charts**: Chart.js
- **Storage**: Browser localStorage
- **Build**: No build process required (vanilla JavaScript)

## 📋 Prerequisites

- Modern web browser (Chrome, Firefox, Safari, Edge)
- Local web server (for development)
- No additional software installation required

## 🚀 Installation & Setup

### Option 1: Direct File Access
1. Download or clone the project files
2. Open `index.html` in your web browser
3. Use default credentials: `admin@ict.edu` / `admin123`

### Option 2: Local Web Server (Recommended)
1. Navigate to the project directory
2. Start a local web server:

```bash
# Using Python 3
python -m http.server 8000

# Using Node.js (if you have http-server installed)
npx http-server

# Using PHP
php -S localhost:8000
```

3. Open `http://localhost:8000` in your browser
4. Login with: `admin@ict.edu` / `admin123`

## 🔐 Default Credentials

- **Email**: `admin@ict.edu`
- **Password**: `admin123`
- **Role**: Sub Admin
- **Office**: ICT Services

## 📱 Usage Guide

### Dashboard
- View system overview and key performance indicators
- Monitor user activity and chatbot performance
- Access quick navigation to all features

### FAQ Management
- **Add FAQ**: Click "+ Add New FAQ" button
- **Edit FAQ**: Click edit icon on any FAQ row
- **Delete FAQ**: Click delete icon (with confirmation)
- **Search**: Use search bar to find specific FAQs
- **Status**: Toggle between Draft and Published states

### Announcements
- **Create**: Add new announcements with title, content, and dates
- **Priority**: Set low, medium, or high priority
- **Status**: Manage draft, scheduled, active, or inactive states
- **Date Range**: Set start and end dates for announcements

### Conversation Logs
- View all chatbot conversations
- Filter by user, date, or category
- Analyze conversation sentiment and duration
- Monitor escalated queries

### Usage Statistics
- View comprehensive analytics
- Export data to CSV format
- Monitor system performance trends
- Track user engagement metrics

### User Feedback
- Monitor user satisfaction ratings
- Filter feedback by rating (1-5 stars)
- Search through feedback comments
- Analyze feedback trends over time

## 🔧 Configuration

### Customizing Default Data
Edit `StorageManager.js` to modify:
- Default FAQs
- Sample announcements
- Initial user accounts
- Storage key prefixes

### Styling Customization
Modify `assets/css/style.css` to:
- Change color scheme
- Adjust layout dimensions
- Customize component appearances
- Modify responsive breakpoints

## 📊 Data Management

### Storage
- All data is stored in browser localStorage
- Data persists between browser sessions
- No external database required
- Automatic data initialization on first load

### Data Export
- Export usage statistics to CSV
- Download conversation logs
- Backup FAQ and announcement data
- Generate performance reports

## 🚨 Security Considerations

- **Local Storage**: Data is stored locally in the browser
- **Authentication**: Basic client-side authentication
- **No HTTPS**: For development/local use only
- **Production**: Implement proper server-side authentication and HTTPS

## 🐛 Troubleshooting

### Common Issues

1. **Page not loading properly**
   - Ensure all JavaScript files are accessible
   - Check browser console for errors
   - Verify file paths are correct

2. **Data not persisting**
   - Check if localStorage is enabled
   - Clear browser cache and try again
   - Verify browser supports localStorage

3. **Authentication issues**
   - Clear browser storage
   - Use default credentials: `admin@ict.edu` / `admin123`
   - Check if AuthManager is properly loaded

4. **Styling issues**
   - Ensure Bootstrap CSS is loading
   - Check if custom CSS file is accessible
   - Verify Font Awesome icons are loading

### Browser Compatibility
- **Chrome**: 60+ (Recommended)
- **Firefox**: 55+
- **Safari**: 12+
- **Edge**: 79+

## 🔄 Updates & Maintenance

### Adding New Features
1. Create new manager class in `assets/js/modules/`
2. Add corresponding HTML page in `pages/`
3. Update navigation in all pages
4. Implement storage methods in `StorageManager.js`

### Data Backup
- Export important data regularly
- Backup localStorage data
- Document custom configurations

## 📈 Performance Optimization

- **Lazy Loading**: Implement for large datasets
- **Pagination**: Add for conversation logs and feedback
- **Caching**: Implement data caching strategies
- **Compression**: Optimize CSS and JavaScript files

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is provided as-is for educational and development purposes.

## 📞 Support

For technical support or questions:
- Check the troubleshooting section
- Review browser console for errors
- Verify file structure and paths
- Ensure all dependencies are loaded

## 🔮 Future Enhancements

- **Real-time Updates**: WebSocket integration
- **Advanced Analytics**: More detailed reporting
- **User Management**: Multiple admin accounts
- **API Integration**: Connect to external systems
- **Mobile App**: Native mobile application
- **Cloud Storage**: Database integration
- **Advanced Security**: Role-based access control

---

**Note**: This is a development/demo version. For production use, implement proper security measures, server-side validation, and database storage.
