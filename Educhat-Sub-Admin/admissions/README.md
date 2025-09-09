# Admissions Office Sub Admin Portal

A comprehensive chatbot administration portal designed specifically for university admissions offices to manage their AI chatbot services, content, and analytics.

## 🎯 Overview

The Admissions Office Sub Admin Portal is a web-based administrative interface that allows admissions office staff to:
- Manage FAQ content for prospective students
- Post and manage announcements
- Monitor chatbot conversation logs
- Track usage statistics and user feedback
- Maintain chatbot knowledge base

## ✨ Features

### 🔐 Authentication & Security
- Secure login system with role-based access
- Session management and automatic logout
- Protected routes for administrative functions

### 📚 FAQ Management
- Create, edit, and delete frequently asked questions
- Categorize FAQs by topic
- Set publication status (draft/published)
- Search and filter FAQ content

### 📢 Announcement System
- Post time-sensitive announcements
- Set priority levels and date ranges
- Manage announcement status (draft/scheduled/active/inactive)
- Target specific student groups

### 💬 Conversation Monitoring
- View real-time chatbot conversation logs
- Analyze conversation sentiment and duration
- Identify escalated queries requiring human intervention
- Track conversation categories and user satisfaction

### 📊 Analytics Dashboard
- Comprehensive usage statistics
- User engagement metrics
- Performance analytics
- Export functionality for reporting

### 💭 User Feedback Management
- Monitor user satisfaction ratings
- Analyze feedback trends
- Filter feedback by rating and category
- Track improvement areas

## 🚀 Getting Started

### Prerequisites
- Modern web browser (Chrome, Firefox, Safari, Edge)
- No server setup required - runs entirely in the browser

### Installation
1. **Download** the project files to your local machine
2. **Navigate** to the `admissions` folder
3. **Open** `index.html` in your web browser

### First-Time Setup
1. The system automatically initializes with default data
2. Use the provided credentials to log in
3. Customize content according to your institution's needs

## 🔑 Login Credentials

- **Email:** `admin@admissions.edu`
- **Password:** `admin123`

## 📁 Project Structure

```
admissions/
├── index.html                 # Main login page
├── assets/
│   ├── css/
│   │   └── style.css         # Main stylesheet
│   └── js/
│       ├── app.js            # Main application logic
│       ├── UIManager.js      # User interface management
│       ├── core/
│       │   └── StorageManager.js  # Data storage and management
│       └── modules/
│           ├── AuthManager.js      # Authentication system
│           ├── DashboardManager.js # Dashboard functionality
│           ├── FAQManager.js       # FAQ management
│           ├── AnnouncementManager.js # Announcement system
│           ├── ConversationManager.js  # Conversation monitoring
│           ├── FeedbackManager.js      # User feedback
│           └── UsageStatsManager.js   # Analytics and statistics
└── pages/
    ├── dashboard.html         # Main dashboard
    ├── faq.html              # FAQ management
    ├── announcements.html     # Announcement system
    ├── conversations.html     # Conversation logs
    ├── usage-stats.html      # Usage analytics
    └── feedback.html         # User feedback
```

## 🎨 User Interface

### Dashboard
- **KPI Cards:** Quick overview of key metrics
- **Navigation Sidebar:** Easy access to all features
- **Responsive Design:** Works on desktop and mobile devices

### Navigation Structure
- **Dashboard:** Overview and main metrics
- **Chatbot Management:**
  - Conversation Logs
  - FAQ Management
  - Announcements
- **Analytics:**
  - Usage Statistics
  - User Feedback

## 💾 Data Management

### Local Storage
- All data is stored locally in the browser
- No external database required
- Data persists between browser sessions
- Automatic backup and recovery

### Data Types
- **FAQs:** Question-answer pairs with metadata
- **Announcements:** Time-sensitive information posts
- **Conversations:** Chatbot interaction logs
- **Feedback:** User satisfaction ratings and comments
- **Usage Stats:** System performance metrics
- **Users:** Administrative account information

## 🔧 Customization

### Content Management
- **FAQs:** Add institution-specific questions and answers
- **Announcements:** Customize for your application cycles
- **Categories:** Modify conversation and feedback categories

### Branding
- Update office name and contact information
- Modify color schemes in CSS
- Customize dashboard metrics

## 📱 Responsive Design

- **Desktop:** Full-featured interface with sidebar navigation
- **Tablet:** Optimized layout for medium screens
- **Mobile:** Touch-friendly interface for small screens

## 🛡️ Security Features

- **Authentication Required:** All administrative functions require login
- **Session Management:** Automatic logout after inactivity
- **Data Validation:** Input sanitization and validation
- **Local Storage:** No external data transmission

## 📊 Analytics & Reporting

### Available Metrics
- **User Engagement:** Login frequency, session duration
- **Content Performance:** FAQ views, announcement reach
- **System Health:** Response rates, success metrics
- **User Satisfaction:** Feedback ratings and trends

### Export Functionality
- **CSV Export:** Download data for external analysis
- **Real-time Updates:** Live dashboard updates
- **Historical Data:** Track performance over time

## 🚨 Troubleshooting

### Common Issues
1. **Login Problems:** Verify credentials and clear browser cache
2. **Data Not Loading:** Check browser console for errors
3. **Styling Issues:** Ensure CSS files are properly loaded

### Browser Compatibility
- **Chrome:** 80+ (Recommended)
- **Firefox:** 75+
- **Safari:** 13+
- **Edge:** 80+

## 🔄 Updates & Maintenance

### Regular Tasks
- Review and update FAQ content
- Monitor user feedback and satisfaction
- Update announcements for current application cycles
- Analyze usage statistics for improvements

### Content Guidelines
- Keep FAQs current and relevant
- Use clear, concise language
- Regular announcement updates
- Monitor conversation quality

## 📞 Support

### Technical Support
- Check browser console for error messages
- Verify all JavaScript files are loaded
- Ensure localStorage is enabled

### Content Support
- Regular content reviews
- User feedback analysis
- Performance monitoring
- Continuous improvement

## 📄 License

This project is designed for educational and institutional use. Please ensure compliance with your institution's policies and data protection regulations.

## 🤝 Contributing

For institutional use, please:
1. Review and customize content for your specific needs
2. Update branding and contact information
3. Modify FAQ content for your programs
4. Adjust announcement templates for your cycles

## 📈 Future Enhancements

Potential improvements include:
- **Multi-language Support:** International student accessibility
- **Advanced Analytics:** Machine learning insights
- **Integration APIs:** Connect with existing systems
- **Mobile App:** Native mobile application
- **Real-time Chat:** Live chat support integration

---

**Last Updated:** December 2024  
**Version:** 1.0.0  
**Compatibility:** Modern Web Browsers  
**Data Storage:** Local Browser Storage
