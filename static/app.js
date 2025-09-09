class Chatbox {
    constructor() {
        this.args = {
            openButton: document.querySelector('.chatbox__button button'),
            chatBox: document.querySelector('.chatbox__support'),
            sendButton: document.querySelector('.send__button'),
            closeButton: document.querySelector('.chatbox__close'),
            resetButton: document.querySelector('.chatbox__reset'),
            clearButton: document.querySelector('.chatbox__clear'),
            ttsButton: document.querySelector('.chatbox__tts'),
            announcementsButton: document.querySelector('.chatbox__announcements'),
            micButton: document.querySelector('.mic__button'),
            suggestionButtons: document.querySelectorAll('.chatbox__suggestions button'),
            messageInput: document.querySelector('.chatbox__footer input'),
            characterCount: document.querySelector('.character-count'),
            contextIndicator: document.getElementById('context-indicator'),
            contextOffice: document.getElementById('context-office'),
            announcementsPanel: document.getElementById('announcements-panel'),
            announcementsContent: document.getElementById('announcements-content'),
            closeAnnouncementsButton: document.querySelector('.close-announcements')
        };

        this.state = false;
        this.messages = [];
        this.currentContext = null;
        this.user_id = this.getUserId(); // Unique per browser session
        this.ttsEnabled = false;
        this.isListening = false;
        this.recognition = null;
        this.currentUtterance = null;
        this.announcementsVisible = false;
        this.announcements = [];
        
        // Sub-suggestions data
        this.subSuggestions = {
            admission: [
                "How can I apply?",
                "Admission requirements",
                "Application deadline",
                "Enrollment process"
            ],
            registrar: [
                "Request transcript",
                "How to get my grades",
                "Academic records",
                "Change my subjects"
            ],
            ict: [
                "How to reset student portal password",
                "Internet issues",
                "WiFi password",
                "Student email problems"
            ],
            guidance: [
                "I need counseling",
                "Scholarship requirements",
                "Career advice",
                "Personal counseling"
            ],
            osa: [
                "Clubs and organizations",
                "Student activities",
                "Student discipline",
                "OSA events"
            ],
            announcements: [
                "Latest announcements",
                "College news",
                "What's new",
                "Recent updates"
            ]
        };

        // Office names for context display
        this.officeNames = {
            admission: "Admission Office",
            registrar: "Registrar's Office",
            ict: "ICT Office",
            guidance: "Guidance Office",
            osa: "Office of Student Affairs",
            announcements: "Announcements"
        };

        // Response templates for local mode
        this.responses = {
            admission: [
                "The Admission Office handles student applications. You can apply online or visit our office for more details.",
                "For admission requirements and deadlines, please contact the Admission Office at the main building.",
                "Enrollment information and forms are available at the Admission Office during business hours."
            ],
            registrar: [
                "The Registrar's Office manages student records and enrollment. Office hours: Mon–Fri, 8 AM–5 PM.",
                "For transcripts, enrollment forms, or schedule changes, visit the Registrar's Office at the main building, 2nd floor.",
                "Academic records and grade information can be obtained from the Registrar's Office."
            ],
            ict: [
                "The ICT Office handles tech support like student portal, WiFi, and email issues. They're located at the IT Building, Room 101.",
                "For password resets, visit the ICT Office or contact our IT support team.",
                "Technical assistance for student accounts and connectivity issues is available at the ICT Office."
            ],
            guidance: [
                "The Guidance Office offers counseling, scholarships, and career advice. Location: Main Building, Room 210.",
                "To schedule an appointment for counseling or career guidance, visit the Guidance Office.",
                "Scholarship information and personal counseling services are available through the Guidance Office."
            ],
            osa: [
                "The Office of Student Affairs manages student activities, clubs, and discipline. They're at the Student Center, Room 305.",
                "For joining clubs or student activities, visit OSA or check our student portal.",
                "Student organization information and campus events are coordinated by the Office of Student Affairs."
            ]
        };

        this.setupEventListeners();
        this.initializeSpeechRecognition();
        this.createVoiceIndicator();
        this.loadAnnouncements();
        
        // Make functions globally available
        window.resetContext = () => this.resetContext();
        window.speakMessage = (text) => this.speakMessage(text);
    }

    // Generate or get a stored user_id
    getUserId() {
        if (!this.sessionUserId) {
            this.sessionUserId = "user_" + Math.random().toString(36).substr(2, 9);
        }
        return this.sessionUserId;
    }

    setupEventListeners() {
        const { 
            openButton, chatBox, sendButton, closeButton, resetButton, 
            clearButton, ttsButton, announcementsButton, micButton, suggestionButtons, 
            messageInput, characterCount, closeAnnouncementsButton
        } = this.args;
        const subSuggestionBox = document.getElementById("sub-suggestions");

        // Open chatbox
        openButton.addEventListener('click', () => {
            this.toggleState(true);
        });

        // Close chatbox
        closeButton.addEventListener('click', () => {
            this.toggleState(false);
        });

        // Reset conversation context
        resetButton.addEventListener('click', () => {
            this.resetContext();
        });

        // Clear chat history
        clearButton.addEventListener('click', () => {
            this.clearHistory();
        });

        // Toggle TTS
        ttsButton.addEventListener('click', () => {
            this.toggleTTS();
        });

        // Toggle announcements panel
        announcementsButton.addEventListener('click', () => {
            this.toggleAnnouncementsPanel();
        });

        // Close announcements panel
        closeAnnouncementsButton.addEventListener('click', () => {
            this.toggleAnnouncementsPanel();
        });

        // Voice input
        micButton.addEventListener('click', () => {
            this.toggleVoiceInput();
        });

        // Send button
        sendButton.addEventListener('click', () => this.onSendButton());

        // Enter key
        messageInput.addEventListener("keyup", (event) => {
            if (event.key === "Enter") {
                this.onSendButton();
            }
        });

        // Character counter
        messageInput.addEventListener('input', () => {
            const length = messageInput.value.length;
            characterCount.textContent = `${length}/500`;
        });

        // Main suggestion buttons
        suggestionButtons.forEach(button => {
            button.addEventListener('click', () => {
                const category = button.getAttribute("data-sub");
                if (category === "announcements") {
                    this.sendSuggestion("What's new");
                } else {
                    this.loadSubSuggestions(category, subSuggestionBox);
                }
            });
        });
    }

    // Load announcements from backend
    async loadAnnouncements() {
        try {
            const response = await fetch('/announcements');
            const data = await response.json();
            this.announcements = data.announcements || [];
            this.renderAnnouncements();
        } catch (error) {
            console.log('Could not load announcements:', error);
            // Fallback to default announcements
            this.announcements = [
                {
                    id: 1,
                    title: "College Orientation 2025",
                    date: "2025-08-20",
                    priority: "high",
                    message: "Welcome to all freshmen! The college orientation will be held at the Main Auditorium on August 20, 2025, starting at 9:00 AM. Attendance is mandatory.",
                    category: "academic"
                }
            ];
            this.renderAnnouncements();
        }
    }

    // Render announcements in the panel
    renderAnnouncements() {
        const { announcementsContent } = this.args;
        
        if (!this.announcements || this.announcements.length === 0) {
            announcementsContent.innerHTML = '<p style="text-align: center; color: #666;">No announcements available.</p>';
            return;
        }

        let html = '';
        this.announcements.forEach(announcement => {
            const priorityClass = `${announcement.priority || 'medium'}-priority`;
            const priorityLabel = announcement.priority || 'medium';
            
            html += `
                <div class="announcement-item ${priorityClass}">
                    <div class="announcement-title">
                        ${announcement.title}
                        <span class="announcement-priority priority-${priorityLabel}">${priorityLabel.toUpperCase()}</span>
                    </div>
                    <div class="announcement-date">📅 ${announcement.date}</div>
                    <div class="announcement-message">${announcement.message}</div>
                </div>
            `;
        });

        announcementsContent.innerHTML = html;
    }

    // Toggle announcements panel
    toggleAnnouncementsPanel() {
        this.announcementsVisible = !this.announcementsVisible;
        
        if (this.announcementsVisible) {
            this.args.announcementsPanel.classList.add('active');
            this.args.announcementsButton.classList.add('active');
            this.loadAnnouncements(); // Refresh announcements when opened
        } else {
            this.args.announcementsPanel.classList.remove('active');
            this.args.announcementsButton.classList.remove('active');
        }
    }

    // Initialize Speech Recognition
    initializeSpeechRecognition() {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            this.recognition.continuous = false;
            this.recognition.interimResults = false;
            this.recognition.lang = 'en-US';

            this.recognition.onstart = () => {
                this.isListening = true;
                this.args.micButton.classList.add('listening');
                this.showVoiceIndicator();
            };

            this.recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                this.args.messageInput.value = transcript;
                this.args.characterCount.textContent = `${transcript.length}/500`;
            };

            this.recognition.onend = () => {
                this.isListening = false;
                this.args.micButton.classList.remove('listening');
                this.hideVoiceIndicator();
            };

            this.recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                this.isListening = false;
                this.args.micButton.classList.remove('listening');
                this.hideVoiceIndicator();
            };
        }
    }

    // Create voice indicator
    createVoiceIndicator() {
        // Voice indicator is already in HTML, just get reference
        this.voiceIndicator = document.getElementById('voice-indicator');
    }

    showVoiceIndicator() {
        if (this.voiceIndicator) {
            this.voiceIndicator.classList.add('active');
        }
    }

    hideVoiceIndicator() {
        if (this.voiceIndicator) {
            this.voiceIndicator.classList.remove('active');
        }
    }

    // Toggle voice input
    toggleVoiceInput() {
        if (!this.recognition) {
            alert('Speech recognition is not supported in your browser.');
            return;
        }

        if (this.isListening) {
            this.recognition.stop();
        } else {
            try {
                this.recognition.start();
            } catch (error) {
                console.error('Error starting speech recognition:', error);
            }
        }
    }

    // Toggle TTS
    toggleTTS() {
        this.ttsEnabled = !this.ttsEnabled;
        this.args.ttsButton.classList.toggle('active', this.ttsEnabled);
        
        if (!this.ttsEnabled && this.currentUtterance) {
            speechSynthesis.cancel();
        }
    }

    // Speak message
    speakMessage(text, button = null) {
        if (!this.ttsEnabled && !button) return;
        
        // Cancel any ongoing speech
        speechSynthesis.cancel();
        
        if (button) {
            button.classList.add('speaking');
        }
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.9;
        utterance.pitch = 1;
        utterance.volume = 0.8;
        
        utterance.onend = () => {
            if (button) {
                button.classList.remove('speaking');
            }
            this.currentUtterance = null;
        };
        
        utterance.onerror = () => {
            if (button) {
                button.classList.remove('speaking');
            }
            this.currentUtterance = null;
        };
        
        this.currentUtterance = utterance;
        speechSynthesis.speak(utterance);
    }

    toggleState(forceState = null) {
        const chatboxContainer = document.querySelector('.chatbox');
        this.state = forceState !== null ? forceState : !this.state;
        
        if (this.state) {
            chatboxContainer.classList.add('chatbox--active');
            
            // Load history if using backend
            if (typeof fetch !== 'undefined') {
                this.loadChatHistory();
            }
        } else {
            chatboxContainer.classList.remove('chatbox--active');
            // Hide announcements panel when closing chatbox
            if (this.announcementsVisible) {
                this.toggleAnnouncementsPanel();
            }
            // Reset to main suggestions when closing
            this.resetToMainSuggestions();
            // Stop any ongoing speech
            if (this.currentUtterance) {
                speechSynthesis.cancel();
            }
        }
    }

    // Clear chat history
    clearHistory() {
        if (confirm('Are you sure you want to clear all chat history?')) {
            this.messages = [];
            this.updateChatText();
            
            // Clear backend history if available
            if (typeof fetch !== 'undefined') {
                fetch('/clear_history', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: this.user_id })
                }).catch(err => console.log("History clear error:", err));
            }
        }
    }

    // Reset conversation context
    resetContext() {
        this.currentContext = null;
        this.updateContextIndicator();
        
        // Reset backend context if available
        if (typeof fetch !== 'undefined') {
            fetch('/reset_context', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: this.user_id })
            }).catch(err => console.log("Context reset error:", err));
        }
        
        this.resetToMainSuggestions();
        
        // Add context reset message
        const msg = { name: "System", message: "Context reset. You can now ask about any office." };
        this.messages.push(msg);
        this.updateChatText();
    }

    // Update context indicator
    updateContextIndicator() {
        const { contextIndicator, contextOffice } = this.args;
        
        if (this.currentContext && this.officeNames[this.currentContext]) {
            contextOffice.textContent = this.officeNames[this.currentContext];
            contextIndicator.style.display = 'flex';
        } else {
            contextIndicator.style.display = 'none';
        }
    }

    // Detect office from message (client-side)
    detectOfficeFromMessage(message) {
        const msgLower = message.toLowerCase();
        
        if (msgLower.includes('admission') || msgLower.includes('apply') || msgLower.includes('enroll')) {
            return 'admission';
        } else if (msgLower.includes('registrar') || msgLower.includes('transcript') || msgLower.includes('grades')) {
            return 'registrar';
        } else if (msgLower.includes('ict') || msgLower.includes('password') || msgLower.includes('wifi')) {
            return 'ict';
        } else if (msgLower.includes('guidance') || msgLower.includes('counseling') || msgLower.includes('scholarship')) {
            return 'guidance';
        } else if (msgLower.includes('osa') || msgLower.includes('student affairs') || msgLower.includes('clubs')) {
            return 'osa';
        } else if (msgLower.includes('announcement') || msgLower.includes('news') || msgLower.includes("what's new")) {
            return 'announcements';
        }
        
        return null;
    }

    // Load chat history from backend (optional)
    loadChatHistory() {
        fetch('/history', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: this.user_id })
        })
        .then(r => r.json())
        .then(data => {
            this.messages = data.messages || [];
            this.updateChatText();
        })
        .catch(err => {
            console.log("History load error (using local mode):", err);
        });
    }

    // Load sub-suggestions dynamically
    loadSubSuggestions(category, container) {
        container.innerHTML = ""; // Clear previous buttons
        
        if (this.subSuggestions[category]) {
            this.subSuggestions[category].forEach(text => {
                const btn = document.createElement("button");
                btn.textContent = text;
                btn.addEventListener("click", () => {
                    this.sendSuggestion(text);
                });
                container.appendChild(btn);
            });
            
            // Hide main suggestions
            document.querySelector('.chatbox__suggestions').style.display = 'none';
            document.querySelector('.suggestions-label').textContent = 'Related questions:';
        }
    }

    resetToMainSuggestions() {
        document.getElementById("sub-suggestions").innerHTML = "";
        document.querySelector('.chatbox__suggestions').style.display = 'flex';
        document.querySelector('.suggestions-label').textContent = 'Suggested topics:';
    }

    sendSuggestion(text) {
        const textField = this.args.messageInput;
        textField.value = text;
        this.onSendButton();
    }

    onSendButton() {
        const textField = this.args.messageInput;
        let text1 = textField.value.trim();
        if (text1 === "") return;

        let msg1 = { name: "User", message: text1 };
        this.messages.push(msg1);
        this.updateChatText();

        // Try to use backend API, fallback to local responses
        if (typeof fetch !== 'undefined') {
            fetch('/predict', {
                method: 'POST',
                body: JSON.stringify({ message: text1, user_id: this.user_id }),
                mode: 'cors',
                headers: { 'Content-Type': 'application/json' },
            })
            .then(r => r.json())
            .then(r => {
                let msg2 = { name: "Bot", message: r.answer };
                this.messages.push(msg2);
                this.updateChatText();
                textField.value = '';
                this.args.characterCount.textContent = '0/500';
                
                // Speak response if TTS is enabled
                if (this.ttsEnabled) {
                    setTimeout(() => this.speakMessage(r.answer), 500);
                }
                
                // Update context based on response
                this.updateContextFromMessage(text1, r.answer);
                
                // Reset to main suggestions after response
                setTimeout(() => this.resetToMainSuggestions(), 1000);
            })
            .catch((error) => {
                console.log('Backend not available, using local responses:', error);
                this.handleLocalResponse(text1);
                textField.value = '';
                this.args.characterCount.textContent = '0/500';
            });
        } else {
            this.handleLocalResponse(text1);
            textField.value = '';
            this.args.characterCount.textContent = '0/500';
        }
    }

    // Update context based on message and response
    updateContextFromMessage(userMessage, botResponse) {
        const detectedOffice = this.detectOfficeFromMessage(userMessage);
        
        // Check if it's a context switch message
        if (botResponse.includes("I think you might be asking about") || 
            botResponse.includes("Would you like me to connect you")) {
            // Don't update context for context switch warnings
            return;
        }
        
        // Check if user confirmed context switch
        const msgLower = userMessage.toLowerCase();
        if ((msgLower.includes('yes') || msgLower.includes('switch') || msgLower.includes('connect')) && 
            botResponse.includes("I've switched to help you")) {
            this.currentContext = detectedOffice;
            this.updateContextIndicator();
            return;
        }
        
        // Set context for office-specific responses
        if (detectedOffice && !this.currentContext) {
            this.currentContext = detectedOffice;
            this.updateContextIndicator();
        }
        
        // Reset context for general messages
        if (botResponse.includes("Hello!") || botResponse.includes("You're welcome") || 
            botResponse.includes("Goodbye")) {
            // Don't change context for greetings/thanks/goodbye
        }
    }

    handleLocalResponse(message) {
        const botResponse = this.generateLocalResponse(message);
        const msg2 = { name: "Bot", message: botResponse };
        this.messages.push(msg2);
        this.updateChatText();
        
        // Speak response if TTS is enabled
        if (this.ttsEnabled) {
            setTimeout(() => this.speakMessage(botResponse), 500);
        }
        
        // Update context
        this.updateContextFromMessage(message, botResponse);
        
        // Reset to main suggestions
        setTimeout(() => this.resetToMainSuggestions(), 1000);
    }

    generateLocalResponse(message) {
        const lowerMessage = message.toLowerCase();
        const detectedOffice = this.detectOfficeFromMessage(message);
        
        // Check for announcements requests
        if (detectedOffice === 'announcements') {
            return this.generateAnnouncementsResponse();
        }
        
        // Check for context conflicts
        if (this.currentContext && detectedOffice && detectedOffice !== this.currentContext) {
            const officeName = this.officeNames[detectedOffice] || "that office";
            const currentOfficeName = this.officeNames[this.currentContext] || "the current topic";
            return `I think you might be asking about the ${officeName}. Right now, I can only assist you with ${currentOfficeName} concerns. Would you like me to connect you to the ${officeName} information instead?`;
        }
        
        // Check for context switch confirmation
        if ((lowerMessage.includes('yes') || lowerMessage.includes('switch') || lowerMessage.includes('connect')) && 
            this.currentContext) {
            if (detectedOffice) {
                this.currentContext = detectedOffice;
                this.updateContextIndicator();
                return `Great! I've switched to help you with ${this.officeNames[detectedOffice]} information. How can I assist you?`;
            }
        }
        
        // Check for greetings
        const greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening'];
        if (greetings.some(greeting => lowerMessage.includes(greeting))) {
            const greetingResponses = [
                "Hello! How can I assist you today?",
                "Hi there, how can I help you?",
                "Good day! What can I do for you?"
            ];
            return greetingResponses[Math.floor(Math.random() * greetingResponses.length)];
        }
        
        // Check for thanks
        if (lowerMessage.includes('thank') || lowerMessage.includes('thanks')) {
            const thankResponses = [
                "You're welcome! Happy to help.",
                "Anytime! Glad I could assist."
            ];
            return thankResponses[Math.floor(Math.random() * thankResponses.length)];
        }
        
        // Check for goodbye
        if (lowerMessage.includes('bye') || lowerMessage.includes('goodbye')) {
            const goodbyeResponses = [
                "Goodbye — have a great day!",
                "See you later!",
                "Take care!"
            ];
            return goodbyeResponses[Math.floor(Math.random() * goodbyeResponses.length)];
        }
        
        // Check for office-specific queries
        if (detectedOffice && this.responses[detectedOffice]) {
            this.currentContext = detectedOffice;
            this.updateContextIndicator();
            return this.responses[detectedOffice][Math.floor(Math.random() * this.responses[detectedOffice].length)];
        }
        
        // Context-specific fallback
        if (this.currentContext) {
            const officeName = this.officeNames[this.currentContext];
            return `I'm currently helping you with ${officeName} information. Could you rephrase your question about this office, or would you like to switch to a different topic?`;
        }
        
        // Default fallback response
        const fallbackResponses = [
            "I'm not sure I understand. Could you rephrase your question or try one of the suggested topics?",
            "Sorry, I don't have that information yet. Please try selecting from the suggested topics."
        ];
        return fallbackResponses[Math.floor(Math.random() * fallbackResponses.length)];
    }

    // Generate announcements response
    generateAnnouncementsResponse() {
        if (!this.announcements || this.announcements.length === 0) {
            return "There are no active announcements at this time.";
        }
        
        let response = "📢 **Latest College Announcements:**\n\n";
        
        this.announcements.slice(0, 3).forEach((ann, i) => {
            const priorityEmoji = {"high": "🔴", "medium": "🟡", "low": "🟢"};
            const emoji = priorityEmoji[ann.priority] || "🔵";
            
            response += `${emoji} **${ann.title}**\n`;
            response += `📅 Date: ${ann.date}\n`;
            response += `📝 ${ann.message}\n\n`;
        });
        
        if (this.announcements.length > 3) {
            response += `📋 *And ${this.announcements.length - 3} more announcements available...*`;
        }
        
        return response;
    }

    updateChatText() {
        let html = `
            <div class="chatbox__greeting">
                <p>Hi there! I'm your TCC Connect assistant. How can I help you today?</p>
            </div>
            <div class="suggestions-label">Suggested topics:</div>
            <div class="chatbox__suggestions">
                <button data-sub="admission">Admission Office</button>
                <button data-sub="registrar">Registrar Office</button>
                <button data-sub="ict">ICT Office</button>
                <button data-sub="guidance">Guidance Office</button>
                <button data-sub="osa">Office of Student Affairs</button>
                <button data-sub="announcements">📢 View Announcements</button>
            </div>
            <div class="chatbox__sub-suggestions" id="sub-suggestions"></div>
            <div class="chatbox__context" id="context-indicator" style="display: none;">
                <span class="context-text">Currently helping with: <strong id="context-office">General</strong></span>
                <button class="context-reset" onclick="resetContext()">Switch Topic</button>
            </div>
        `;
        
        this.messages.forEach((item, index) => {
            if (item.name === "Bot") {
                // Check if it's a context switch message
                if (item.message.includes("I think you might be asking about") || 
                    item.message.includes("Would you like me to connect you")) {
                    html += `<div class="messages__item messages__item--context">${item.message}</div>`;
                } 
                // Check if it's an announcements message
                else if (item.message.includes("📢") && item.message.includes("Announcements")) {
                    html += `
                        <div class="messages__item messages__item--announcement">
                            ${item.message}
                            <button class="tts-button" onclick="speakMessage('${item.message.replace(/'/g, "\\'")}', this)" title="Read aloud">🔊</button>
                        </div>
                    `;
                } else {
                    html += `
                        <div class="messages__item messages__item--visitor">
                            ${item.message}
                            <button class="tts-button" onclick="speakMessage('${item.message.replace(/'/g, "\\'")}', this)" title="Read aloud">🔊</button>
                        </div>
                    `;
                }
            } else if (item.name === "System") {
                html += `<div class="messages__item messages__item--context">${item.message}</div>`;
            } else {
                html += `<div class="messages__item messages__item--operator">${item.message}</div>`;
            }
        });

        const chatmessage = document.querySelector('.chatbox__messages');
        chatmessage.innerHTML = html;
        
        // Update context indicator
        this.updateContextIndicator();
        
        // Re-attach event listeners for suggestion buttons
        this.reattachSuggestionListeners();
        
        // Auto-scroll to bottom
        chatmessage.scrollTop = chatmessage.scrollHeight;
    }
    
    reattachSuggestionListeners() {
        const suggestionButtons = document.querySelectorAll('.chatbox__suggestions button');
        const subSuggestionBox = document.getElementById("sub-suggestions");
        
        suggestionButtons.forEach(button => {
            button.addEventListener('click', () => {
                const category = button.getAttribute("data-sub");
                if (category === "announcements") {
                    this.sendSuggestion("What's new");
                } else {
                    this.loadSubSuggestions(category, subSuggestionBox);
                }
            });
        });
    }
}

// Initialize chatbox when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const chatbox = new Chatbox();
});