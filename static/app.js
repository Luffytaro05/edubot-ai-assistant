
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
        
        // Typing indicator state
        this.isTyping = false;
        this.typingTimeout = null;
        
        // Translation system state (✅ ENGLISH AND FILIPINO ONLY)
        this.userLanguage = "en"; // Default language ('en' or 'fil')
        this.translationEnabled = true; // Enable automatic translation (English ↔ Filipino only)
        
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
        this.loadBotSettings();
        this.selectedCategoryLabel = null; // last clicked category label from settings-driven UI
        this.inlineSuggestions = null; // suggestions to show under the latest bot response
        this.pendingInlineAfterResponse = false; // set true when a suggested message is clicked
        this.lastInlineBotIndex = null; // index of bot message to render inline suggestions under
        this.showInitialSuggestions = true; // ✅ Flag to show suggestions below initial greeting
        
        // Make functions globally available
        window.resetContext = () => this.resetContext();
        window.speakMessage = (text) => this.speakMessage(text);
        window.sendMessage = (text) => this.sendMessage(text);  // ✅ For office switch buttons
    }

    // Load bot settings from backend and apply to UI/theme
    async loadBotSettings() {
        try {
            const res = await fetch('/api/bot/settings', { method: 'GET' });
            const data = await res.json();
            this.botSettings = data || {};

            // Apply primary color theme if present
            if (this.botSettings.primary_color) {
                this.applyPrimaryColor(this.botSettings.primary_color);
            }

            // Apply bot name (chatbox header title)
            if (this.botSettings.bot_name) {
                const titleEl = document.querySelector('.chatbox__title strong');
                if (titleEl) titleEl.textContent = this.botSettings.bot_name;
            }

            // Apply bot avatar (logo in header and floating button)
            if (this.botSettings.bot_avatar) {
                const logoImg = document.querySelector('.chatbox__logo img');
                if (logoImg) logoImg.src = this.botSettings.bot_avatar;
                const floatBtnImg = document.querySelector('.chatbox__button img');
                if (floatBtnImg) floatBtnImg.src = this.botSettings.bot_avatar;
            }

            // Apply suggestions visibility
            this.applySuggestionsVisibility();
            
            // Apply typing indicator visibility
            this.applyTypingIndicatorVisibility();
            
            // Apply response timeout setting
            this.applyResponseTimeoutSetting();

            // Normalize suggested messages into category map
            this.suggestedByCategory = {};
            this.flatSuggestions = [];
            const sm = this.botSettings.suggested_messages;
            if (Array.isArray(sm)) {
                // Case 1: [{ category, messages: [] }, ...]
                let treatedAsGroups = false;
                for (const item of sm) {
                    if (item && typeof item === 'object' && Array.isArray(item.messages)) {
                        treatedAsGroups = true;
                        const cat = item.category ? String(item.category) : 'General';
                        const msgs = item.messages.filter(Boolean).map(String);
                        if (!this.suggestedByCategory[cat]) this.suggestedByCategory[cat] = [];
                        this.suggestedByCategory[cat].push(...msgs);
                        this.flatSuggestions.push(...msgs);
                    }
                }
                // Case 2: ["string", ...]
                if (!treatedAsGroups) {
                    this.flatSuggestions = sm.filter(Boolean).map(String);
                }
            } else if (sm && typeof sm === 'object') {
                // Case 3: { category: [msg, ...], ... }
                Object.keys(sm).forEach(key => {
                    const cat = String(key);
                    const msgs = Array.isArray(sm[key]) ? sm[key].filter(Boolean).map(String) : [];
                    if (msgs.length) {
                        this.suggestedByCategory[cat] = msgs;
                        this.flatSuggestions.push(...msgs);
                    }
                });
            }

            // Re-render chat content to reflect welcome message and suggestions
            this.updateChatText();
        } catch (e) {
            console.log('Could not load bot settings:', e);
        }
    }

    suggestionsEnabled() {
        return !(this.botSettings && this.botSettings.show_suggested_questions === false);
    }

    applySuggestionsVisibility() {
        const enabled = this.suggestionsEnabled();
        const label = document.querySelector('.suggestions-label');
        const main = document.querySelector('.chatbox__suggestions');
        const sub = document.querySelector('.chatbox__sub-suggestions');
        if (label) label.style.display = enabled ? '' : 'none';
        if (main) main.style.display = enabled ? '' : 'none';
        if (!enabled && sub) sub.innerHTML = '';
        console.log('Suggested questions setting applied:', enabled);
    }

    applyTypingIndicatorVisibility() {
        const enabled = this.typingIndicatorEnabled();
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            // Store the setting for later use
            typingIndicator.setAttribute('data-enabled', enabled.toString());
            console.log('Typing indicator setting applied:', enabled);
        }
    }

    typingIndicatorEnabled() {
        return !(this.botSettings && this.botSettings.show_typing_indicator === false);
    }

    getResponseTimeoutMs() {
        // Get response timeout from settings (in seconds) and convert to milliseconds
        const configuredSeconds = this.botSettings?.response_timeout || 30;
        const isLocal = ['localhost', '127.0.0.1'].includes(window.location.hostname);
        // Enforce a minimum of 15s online to avoid premature aborts on slower networks/backends
        const effectiveSeconds = isLocal ? configuredSeconds : Math.max(configuredSeconds, 15);
        return effectiveSeconds * 1000; // Convert to milliseconds
    }

    handleResponseTimeout() {
        // Handle when response timeout is reached
        console.log('Response timeout reached, showing timeout message');
        
        // Add a timeout message to the chat
        const timeoutMessage = {
            name: "Bot",
            message: "I'm taking longer than usual to respond. Please try again or contact support if the issue persists."
        };
        this.messages.push(timeoutMessage);
        this.updateChatText();
        
        // Show a toast notification
        if (window.toast) {
            toast.warning('Response timeout reached. Please try again.');
        }
    }

    applyResponseTimeoutSetting() {
        const timeoutSeconds = this.botSettings?.response_timeout || 30;
        console.log('Response timeout setting applied:', timeoutSeconds + ' seconds');
        
        // Store the timeout setting for use in requests
        this.responseTimeoutSeconds = timeoutSeconds;
    }

    applyPrimaryColor(color) {
        // Set CSS variable
        document.documentElement.style.setProperty('--primary-color', color);

        // Fallback: directly style common elements if theme var isn't used
        const header = document.querySelector('.chatbox__header');
        if (header) {
            header.style.borderColor = color;
            header.style.backgroundColor = color;
            header.style.color = '#ffffff';
        }

        const openBtn = document.querySelector('.chatbox__button button');
        if (openBtn) {
            openBtn.style.backgroundColor = color;
            openBtn.style.borderColor = color;
        }

        const sendBtn = document.querySelector('.send__button');
        if (sendBtn) {
            sendBtn.style.backgroundColor = color;
            sendBtn.style.borderColor = color;
        }

        const micBtn = document.querySelector('.mic__button');
        if (micBtn) {
            micBtn.style.backgroundColor = color;
            micBtn.style.borderColor = color;
            micBtn.style.color = '#ffffff';
            // Emphasize when listening
            const updateMicState = () => {
                if (micBtn.classList.contains('listening')) {
                    micBtn.style.boxShadow = `0 0 0 4px ${color}33`;
                } else {
                    micBtn.style.boxShadow = '';
                }
            };
            // Run once and on class changes
            updateMicState();
            const obs = new MutationObserver(updateMicState);
            obs.observe(micBtn, { attributes: true, attributeFilter: ['class'] });
        }

        // Suggested buttons (when rendered)
        document.querySelectorAll('.chatbox__suggestions button').forEach(btn => {
            btn.style.borderColor = color;
            btn.addEventListener('mouseenter', () => btn.style.backgroundColor = color);
            btn.addEventListener('mouseleave', () => btn.style.backgroundColor = '');
        });
    }

    // Generate or get a stored user_id
    getUserId() {
        if (!this.sessionUserId) {
            this.sessionUserId = "user_" + Math.random().toString(36).substr(2, 9);
        }
        return this.sessionUserId;
    }

    // ===========================
    // TRANSLATION METHODS
    // ===========================

    /**
     * Translate text using Google Translate API (free, no API key needed)
     * ✅ RESTRICTED TO ENGLISH AND FILIPINO ONLY
     * @param {string} text - Text to translate
     * @param {string} targetLang - Target language ('en' for English or 'fil' for Filipino)
     * @returns {Promise<string>} - Translated text
     */
    async translateText(text, targetLang) {
        if (!this.translationEnabled || !text) {
            return text;
        }
        
        // ✅ Restrict to English and Filipino only
        const ALLOWED_LANGUAGES = ['en', 'fil'];
        if (!ALLOWED_LANGUAGES.includes(targetLang)) {
            console.warn(`⚠️ Language '${targetLang}' not supported. Only English and Filipino are allowed.`);
            return text; // Return original text if unsupported language
        }
        
        try {
            const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=${targetLang}&dt=t&q=${encodeURIComponent(text)}`;
            const response = await fetch(url);
            const data = await response.json();
            
            // Google Translate API returns array: [[["translated", "original", null, null, ...], ...], ...]
            if (data && data[0] && data[0][0] && data[0][0][0]) {
                return data[0][0][0];
            }
            return text; // Return original if translation fails
        } catch (error) {
            console.error('Translation error:', error);
            return text; // Return original text on error
        }
    }

    /**
     * Detect language of the message (English or Filipino ONLY)
     * ✅ RESTRICTED TO ENGLISH AND FILIPINO ONLY
     * @param {string} text - Text to analyze
     * @returns {Promise<string>} - Language code ('en' for English or 'fil' for Filipino)
     */
    async detectLanguage(text) {
        if (!this.translationEnabled || !text) {
            return "en";
        }
        
        try {
            // ✅ Check for Filipino keywords first (more reliable than translation-based detection)
            const filipinoKeywords = [
                'ako', 'ikaw', 'siya', 'kami', 'tayo', 'kayo', 'sila',
                'ang', 'ng', 'mga', 'sa', 'na', 'ay', 'po', 'opo',
                'magandang', 'salamat', 'paano', 'ano', 'saan', 'kailan',
                'kumusta', 'mabuti', 'hindi', 'oo', 'wala', 'mayroon',
                'naman', 'lang', 'din', 'rin', 'ba', 'kasi', 'pero',
                'gusto', 'kailangan', 'pwede', 'paki'
            ];
            
            const textLower = text.toLowerCase();
            const words = textLower.split(/\s+/);
            
            // Check if any Filipino keyword is present as a complete word
            const hasFilipino = filipinoKeywords.some(keyword => 
                words.includes(keyword) || textLower.includes(keyword)
            );
            
            if (hasFilipino) {
                console.log('✅ Detected language: Filipino (keyword match)');
                return "fil";
            }
            
            // If no Filipino keywords found, try translation-based detection
            const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q=${encodeURIComponent(text)}`;
            const response = await fetch(url);
            const data = await response.json();
            
            if (data && data[0] && data[0][0] && data[0][0][0]) {
                const translated = data[0][0][0];
                
                // Normalize both texts for comparison
                const originalNormalized = text.trim().toLowerCase();
                const translatedNormalized = translated.trim().toLowerCase();
                
                // If translation is very different, it might be Filipino
                // But we already checked for keywords, so default to English
                if (originalNormalized === translatedNormalized) {
                    console.log('✅ Detected language: English');
                    return "en";
                } else {
                    // Translation is different but no Filipino keywords found
                    // Likely English with some variations or unsupported language
                    // Default to English since we only support English and Filipino
                    console.log('✅ Detected language: English (default - no Filipino keywords found)');
                    return "en";
                }
            }
            
            return "en"; // Default to English
        } catch (error) {
            console.error('Language detection error:', error);
            return "en"; // Default to English on error
        }
    }

    /**
     * Send message with automatic translation
     * ✅ RESTRICTED TO ENGLISH AND FILIPINO ONLY
     * @param {string} userMsg - User's message (English or Filipino only)
     * @returns {Object} { response: string, status: string, office: string }
     */
    async sendMessageWithTranslation(userMsg) {
        if (!this.translationEnabled) {
            // If translation is disabled, use existing message flow
            return this.sendMessageDirect(userMsg);
        }
        
        // ✅ Detect the user's language (English or Filipino only)
        this.userLanguage = await this.detectLanguage(userMsg);
        console.log(`✅ Detected language: ${this.userLanguage === 'en' ? 'English' : 'Filipino'}`);
        
        // ✅ Translate to English if message is in Filipino
        let translatedMsg = userMsg;
        if (this.userLanguage === "fil") {
            translatedMsg = await this.translateText(userMsg, "en");
            console.log(`📝 Translated Filipino to English: ${translatedMsg}`);
        } else {
            console.log(`✅ Message is in English, no translation needed`);
        }
        
        // Send to backend chatbot (in English)
        // Pass both original message (for MongoDB) and translated message (for processing)
        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ 
                    message: translatedMsg,           // Translated message for chatbot processing
                    original_message: userMsg,         // Original message in user's language for MongoDB
                    user_id: this.user_id              // User ID for conversation tracking
                }),
            });
            
            const data = await response.json();
            let botResponse = data.response;
            let botResponseOriginal = botResponse; // Keep English version
            const status = data.status || 'resolved';
            const office = data.office || 'General';
            
            // Log status for debugging
            console.log(`Status: ${status}, Office: ${office}`);
            
            // ✅ Translate response back to Filipino if user's language is Filipino
            if (this.userLanguage === "fil") {
                botResponse = await this.translateText(botResponse, "fil");
                console.log(`🌐 Translated response from English to Filipino: ${botResponse}`);
            } else {
                console.log(`✅ Response kept in English`);
            }
            
            // Save bot response to MongoDB (in user's language) with status
            // This ensures the conversation history shows messages in the language they were sent/received
            try {
                await fetch("/save_bot_message", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        user_id: this.user_id,
                        message: botResponse,  // Save translated version
                        original_message: botResponseOriginal,  // Also save English version
                        status: status,  // Add status tracking
                        office: office   // Add office tracking
                    })
                });
            } catch (saveError) {
                console.error("Failed to save bot response:", saveError);
                // Continue execution - don't block user experience
            }
            
            return {
                response: botResponse,
                status: status,
                office: office
            };
        } catch (error) {
            console.error('Chat error:', error);
            throw error;
        }
    }

    // ===========================
    // TYPING INDICATOR METHODS
    // ===========================

    showTypingIndicator() {
        // Check if typing indicator is enabled in settings
        if (!this.typingIndicatorEnabled()) {
            return; // Typing indicator is disabled
        }
        
        if (this.isTyping) return; // Prevent multiple indicators
        
        this.isTyping = true;
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.style.display = 'flex';
            typingIndicator.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }
        
        // Set timeout based on response_timeout setting
        const timeoutMs = this.getResponseTimeoutMs();
        if (timeoutMs > 0) {
            this.typingTimeout = setTimeout(() => {
                this.hideTypingIndicator();
                this.handleResponseTimeout();
            }, timeoutMs);
        }
    }

    hideTypingIndicator() {
        this.isTyping = false;
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.style.display = 'none';
        }
        if (this.typingTimeout) {
            clearTimeout(this.typingTimeout);
            this.typingTimeout = null;
        }
    }


    // ===========================
    // ENHANCED SUGGESTION METHODS
    // ===========================

    getContextualQuickReplies(context, botResponse) {
        // Define contextual quick replies based on office and response
        const contextualReplies = {
            admission: {
                general: ["What are the requirements?", "How to apply?", "Application deadline", "Contact admissions"],
                requirements: ["What documents needed?", "GPA requirements", "Entrance exam", "Interview process"],
                application: ["Online application", "Application fee", "Required documents", "Application status"]
            },
            registrar: {
                general: ["Request transcript", "View grades", "Academic records", "Schedule changes"],
                transcript: ["How to request", "Processing time", "Fees", "Pickup options"],
                grades: ["Grade inquiry", "Grade appeal", "Academic standing", "GPA calculation"]
            },
            ict: {
                general: ["Password reset", "WiFi issues", "Student portal", "Email problems"],
                password: ["Portal password", "Email password", "WiFi password", "Account recovery"],
                technical: ["Internet connection", "Software issues", "Hardware problems", "IT support"]
            },
            guidance: {
                general: ["Counseling services", "Scholarship info", "Career guidance", "Personal support"],
                counseling: ["Schedule appointment", "Available counselors", "Services offered", "Confidentiality"],
                scholarship: ["Requirements", "Application process", "Deadlines", "Available scholarships"]
            },
            osa: {
                general: ["Student organizations", "Events", "Student activities", "Discipline matters"],
                organizations: ["Available clubs", "How to join", "Club activities", "Leadership roles"],
                events: ["Upcoming events", "Event registration", "Event calendar", "Special activities"]
            }
        };

        // Get replies based on context and response content
        const contextReplies = contextualReplies[context] || {};
        const responseLower = botResponse.toLowerCase();
        
        // Determine which sub-category based on response content
        let subCategory = 'general';
        if (responseLower.includes('requirement') || responseLower.includes('document')) {
            subCategory = 'requirements';
        } else if (responseLower.includes('application') || responseLower.includes('apply')) {
            subCategory = 'application';
        } else if (responseLower.includes('transcript') || responseLower.includes('record')) {
            subCategory = 'transcript';
        } else if (responseLower.includes('grade') || responseLower.includes('gpa')) {
            subCategory = 'grades';
        } else if (responseLower.includes('password') || responseLower.includes('login')) {
            subCategory = 'password';
        } else if (responseLower.includes('technical') || responseLower.includes('support')) {
            subCategory = 'technical';
        } else if (responseLower.includes('counseling') || responseLower.includes('counselor')) {
            subCategory = 'counseling';
        } else if (responseLower.includes('scholarship') || responseLower.includes('financial')) {
            subCategory = 'scholarship';
        } else if (responseLower.includes('organization') || responseLower.includes('club')) {
            subCategory = 'organizations';
        } else if (responseLower.includes('event') || responseLower.includes('activity')) {
            subCategory = 'events';
        }

        return contextReplies[subCategory] || contextReplies.general || [];
    }


    // Enhanced reset context method (for simple chatbox class if exists)
    resetContext() {
        // Map frontend context to backend office tags
        const officeTagMap = {
            'admission': 'admission_office',
            'registrar': 'registrar_office',
            'ict': 'ict_office',
            'guidance': 'guidance_office',
            'osa': 'osa_office'
        };
        
        const currentOfficeTag = this.currentContext ? officeTagMap[this.currentContext] : null;
        
        // Send reset request to backend with office parameter
        if (typeof fetch !== 'undefined' && this.user_id) {  // ✅ FIX: Check this.user_id
            fetch('/reset_context', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    user: this.user_id,  // ✅ FIX: Use this.user_id to match predict endpoint
                    office: currentOfficeTag
                })
            })
            .then(response => response.json())
            .then(data => console.log("Context reset:", data))
            .catch(err => console.log("Reset error:", err));
        }
        
        this.currentContext = null;
        this.updateContextIndicator();
    }

    // Show suggested messages from backend
    showBackendSuggestions(suggestions) {
        const subSuggestionBox = document.getElementById("sub-suggestions");
        if (!subSuggestionBox || !suggestions || suggestions.length === 0) return;

        // Clear previous suggestions
        subSuggestionBox.innerHTML = "";

        // Create suggestion buttons
        suggestions.forEach(suggestion => {
            const button = document.createElement("button");
            button.textContent = suggestion;
            button.className = "sub-suggestion-btn";
            button.addEventListener("click", () => this.sendSuggestion(suggestion));
            subSuggestionBox.appendChild(button);
        });

        // Show the sub-suggestions container
        subSuggestionBox.style.display = "block";
        
        // Hide main suggestions
        const mainSuggestions = document.querySelector('.chatbox__suggestions');
        if (mainSuggestions) {
            mainSuggestions.style.display = 'none';
        }

        // Update label
        const label = document.querySelector('.suggestions-label');
        if (label) {
            label.textContent = 'Suggested questions:';
            label.style.display = 'block';
        }

        // Scroll to show suggestions
        subSuggestionBox.scrollIntoView({ behavior: 'smooth', block: 'end' });
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

    // Load announcements from backend (MongoDB + Pinecone only)
    async loadAnnouncements() {
        try {
            const response = await fetch('/announcements');
            const data = await response.json();
            this.announcements = data.announcements || [];
            this.renderAnnouncements();
            console.log(`Loaded ${this.announcements.length} announcements from MongoDB/Pinecone`);
        } catch (error) {
            console.error('Could not load announcements:', error);
            // No fallback - display empty state
            this.announcements = [];
            this.renderAnnouncements();
        }
    }

    // Render announcements in the panel with enhanced UI
    renderAnnouncements() {
        const { announcementsContent } = this.args;
        
        if (!this.announcements || this.announcements.length === 0) {
            announcementsContent.innerHTML = `
                <div class="empty-announcements">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12.87 15.07l-2.54-2.51.03-.03c1.74-1.94 2.01-4.65.75-6.78L6.87 1H4v4.84c-.46.63-.79 1.33-.98 2.09-.19.76-.19 1.55 0 2.31C3.46 12.13 4 13.56 4 15v1c0 .55.45 1 1 1h6.77c.12.38.31.76.57 1.10l1.86 1.82L12.87 15.07z"/>
                    </svg>
                    <p>No announcements available at the moment.</p>
                    <small>Check back later for updates!</small>
                </div>
            `;
            return;
        }

        let html = '<div class="announcements-list">';
        
        this.announcements.forEach((announcement, index) => {
            const priorityClass = `${announcement.priority || 'medium'}-priority`;
            const priorityLabel = announcement.priority || 'medium';
            const office = announcement.office || announcement.category || 'General';
            const source = announcement.source || 'unknown';
            
            // Priority emoji mapping
            const priorityEmoji = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            };
            
            const emoji = priorityEmoji[priorityLabel.toLowerCase()] || '📢';
            
            // Source badge
            let sourceBadge = '';
            if (source === 'mongodb' || source === 'sub_admin') {
                sourceBadge = '<span class="announcement-source-badge">NEW</span>';
            }
            
            html += `
                <div class="announcement-item ${priorityClass}" data-index="${index}">
                    <div class="announcement-header">
                        <div class="announcement-title-row">
                            <span class="announcement-emoji">${emoji}</span>
                            <div class="announcement-title">${this.escapeHtml(announcement.title)}</div>
                            ${sourceBadge}
                        </div>
                        <span class="announcement-priority priority-${priorityLabel}">
                            ${priorityLabel.toUpperCase()}
                        </span>
                    </div>
                    <div class="announcement-meta">
                        <span class="announcement-office">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
                            </svg>
                            ${this.escapeHtml(office)}
                        </span>
                        <span class="announcement-date">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M9 11H7v2h2v-2zm4 0h-2v2h2v-2zm4 0h-2v2h2v-2zm2-7h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V9h14v11z"/>
                            </svg>
                            ${this.formatDate(announcement.date)}
                        </span>
                    </div>
                    <div class="announcement-message">${this.escapeHtml(announcement.message)}</div>
                    <button class="announcement-ask-btn" onclick="chatbox.askAboutAnnouncement('${this.escapeHtml(announcement.title).replace(/'/g, "\\'")}')">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-7 9h-2V5h2v6zm0 4h-2v-2h2v2z"/>
                        </svg>
                        Ask about this
                    </button>
                </div>
            `;
        });

        html += '</div>';
        announcementsContent.innerHTML = html;
    }
    
    // Helper function to escape HTML
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Helper function to format date
    formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        const options = { year: 'numeric', month: 'short', day: 'numeric' };
        return date.toLocaleDateString('en-US', options);
    }
    
    // Function to ask chatbot about specific announcement
    askAboutAnnouncement(title) {
        this.toggleAnnouncementsPanel(); // Close panel
        const message = `Tell me more about "${title}"`;
        this.args.messageInput.value = message;
        this.onSendButton();
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

    // Show office-specific welcome message from settings
    showOfficeWelcome(category) {
        const officeMap = {
            admission: 'Admissions',
            registrar: "Registrar",
            ict: 'ICT',
            guidance: 'Guidance',
            osa: 'Office of Student Affairs'
        };
        let welcome = '';
        // Look into settings office_specific_messages using friendly labels
        if (this.botSettings && this.botSettings.office_specific_messages) {
            const friendly = officeMap[category];
            if (friendly && this.botSettings.office_specific_messages[friendly]) {
                welcome = this.botSettings.office_specific_messages[friendly];
            }
        }
        // Fallback: derive from office name
        if (!welcome && this.officeNames && this.officeNames[category]) {
            welcome = `Great! I can help you with questions about the ${this.officeNames[category]}. What would you like to know?`;
        }
        if (welcome) {
            const msg = { name: "Bot", message: welcome };
            this.messages.push(msg);
            // Also prepare inline suggestions based on office mapping
            this.inlineSuggestions = this.getSuggestionsForCurrent();
            // Ensure inline suggestions render under this new bot message
            this.lastInlineBotIndex = this.messages.length - 1;
            this.pendingInlineAfterResponse = false;
            this.updateChatText();
        }
    }

    // Show welcome by human-readable category label (for settings-driven categories)
    showOfficeWelcomeByLabel(label) {
        let welcome = '';
        if (this.botSettings && this.botSettings.office_specific_messages) {
            const exact = this.botSettings.office_specific_messages[label];
            if (exact) welcome = exact;
            if (!welcome) {
                // Try case-insensitive match
                const entries = Object.entries(this.botSettings.office_specific_messages);
                const found = entries.find(([k]) => String(k).toLowerCase() === String(label).toLowerCase());
                if (found) welcome = found[1];
            }
        }
        if (!welcome) {
            welcome = `Great! I can help you with questions about ${label}. What would you like to know?`;
        }
        const msg = { name: "Bot", message: welcome };
        this.messages.push(msg);
        // Track selected label and prepare inline suggestions
        this.selectedCategoryLabel = label;
        this.inlineSuggestions = this.getSuggestionsForCurrent();
        // Ensure inline suggestions render under this new bot message
        this.lastInlineBotIndex = this.messages.length - 1;
        this.pendingInlineAfterResponse = false;
        this.updateChatText();
    }

    // Derive suggestions based on selected category label or current context
    getSuggestionsForCurrent() {
        // Prefer selected category label from settings
        if (this.selectedCategoryLabel && this.suggestedByCategory && this.suggestedByCategory[this.selectedCategoryLabel]) {
            return (this.suggestedByCategory[this.selectedCategoryLabel] || []);
        }
        // Map context key to a friendly label and try again
        const officeMap = {
            admission: 'Admissions',
            registrar: 'Registrar',
            ict: 'ICT',
            guidance: 'Guidance',
            osa: 'Office of Student Affairs'
        };
        const label = officeMap[this.currentContext];
        if (label && this.suggestedByCategory && this.suggestedByCategory[label]) {
            return (this.suggestedByCategory[label] || []);
        }
        // Fallback to flat suggestions
        if (Array.isArray(this.flatSuggestions) && this.flatSuggestions.length > 0) {
            return this.flatSuggestions;
        }
        return null;
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

    // Reset conversation context with office-aware welcome
   resetContext() {
    // Map frontend context to backend office tags
    const officeTagMap = {
        'admission': 'admission_office',
        'registrar': 'registrar_office',
        'ict': 'ict_office',
        'guidance': 'guidance_office',
        'osa': 'osa_office'
    };
    
    // Get the current office tag for backend
    const currentOfficeTag = this.currentContext ? officeTagMap[this.currentContext] : null;

    // Clear chat messages immediately
    this.messages = [];
    
    // Reset all context and flags
    this.currentContext = null;
    this.selectedCategoryLabel = null;
    this.lastInlineBotIndex = null;
    this.showInitialSuggestions = true; // Re-enable initial suggestions
    
    // Clear context indicator
    this.updateContextIndicator();
    
    // Reset backend context if available (office-specific)
    if (typeof fetch !== 'undefined') {
        console.log(`🔄 Sending reset request - User ID: ${this.user_id}, Office: ${currentOfficeTag}`);
        fetch('/reset_context', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                user: this.user_id,  // ✅ FIX: Use this.user_id to match predict endpoint
                office: currentOfficeTag  // ✅ Send the specific office to reset
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log("✅ Context reset successfully:", data);
        })
        .catch(err => {
            console.log("Context reset error:", err);
        });
    }
    
    // Show Suggested Topics section immediately
    this.resetToMainSuggestions();
    
    // Re-render chat with welcome message and suggestions
    this.updateChatText();
}

    // Highlight reset button to draw user attention
    highlightResetButton() {
        const resetButton = this.args.resetButton;
        if (!resetButton) {
            console.warn('Reset button not found');
            return;
        }
        
        // Add highlight animation class
        resetButton.classList.add('pulse-highlight');
        
        // Add inline styles for pulsing effect if CSS class doesn't exist
        resetButton.style.animation = 'pulse 1.5s ease-in-out 3';
        resetButton.style.boxShadow = '0 0 0 0 rgba(255, 152, 0, 0.7)';
        
        // Remove highlight after 5 seconds
        setTimeout(() => {
            resetButton.classList.remove('pulse-highlight');
            resetButton.style.animation = '';
            resetButton.style.boxShadow = '';
        }, 5000);
        
        console.log('✨ Reset button highlighted to guide user');
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
    
    // Admission Office keywords
    if (msgLower.includes('admission') || msgLower.includes('apply') || 
        msgLower.includes('enroll') || msgLower.includes('application') ||
        msgLower.includes('requirements') || msgLower.includes('entrance')) {
        return 'admission';
    } 
    // Registrar Office keywords
    else if (msgLower.includes('registrar') || msgLower.includes('transcript') || 
             msgLower.includes('grades') || msgLower.includes('academic records') ||
             msgLower.includes('enrollment') || msgLower.includes('subjects') ||
             msgLower.includes('schedule')) {
        return 'registrar';
    } 
    // ICT Office keywords
    else if (msgLower.includes('ict') || msgLower.includes('password') || 
             msgLower.includes('wifi') || msgLower.includes('internet') ||
             msgLower.includes('student portal') || msgLower.includes('email') ||
             msgLower.includes('login') || msgLower.includes('technical')) {
        return 'ict';
    } 
    // Guidance Office keywords
    else if (msgLower.includes('guidance') || msgLower.includes('counseling') || 
             msgLower.includes('scholarship') || msgLower.includes('career advice') ||
             msgLower.includes('counselor') || msgLower.includes('mental health')) {
        return 'guidance';
    } 
    // OSA Office keywords
    else if (msgLower.includes('osa') || msgLower.includes('student affairs') || 
             msgLower.includes('clubs') || msgLower.includes('activities') ||
             msgLower.includes('events') || msgLower.includes('organizations') ||
             msgLower.includes('discipline')) {
        return 'osa';
    } 
    // Announcements keywords
    else if (msgLower.includes('announcement') || msgLower.includes('news') || 
             msgLower.includes("what's new") || msgLower.includes('updates') ||
             msgLower.includes('latest')) {
        return 'announcements';
    }
    
    return null;
}

    // Enhanced clear history function with visual feedback
clearHistory() {
    // ✅ Updated confirmation message to clarify only display is cleared
    if (confirm('Are you sure you want to clear the chat display?\n\n(Note: Your conversation records will be preserved in the database for admin review)')) {
        // Show loading state
        const originalChatText = this.chatText;
        this.chatText = "🗑️ Clearing chat display...";
        
        // Optional: Add a visual deletion animation
        this.showDeletionAnimation();
        
        fetch('/clear_history', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user: this.user_id })
        })
        .then(r => r.json())
        .then(res => {
            console.log("Clear history result:", res);
            
            // Clear everything after successful backend deletion
            this.messages = [];
            this.chatText = "";
            
            // ✅ Re-enable initial suggestions for next chat session
            this.showInitialSuggestions = true;
            this.lastInlineBotIndex = null;
            this.selectedCategoryLabel = null;
            
            // Clear localStorage cache
            localStorage.removeItem(`chat_${this.user_id}`);
            
            // Update UI to show empty state
            this.updateChatText();
            
            // Show success message temporarily
            // ✅ Updated message to reflect MongoDB data is preserved
            const successMsg = res.details?.mongodb_preserved 
                ? "✅ Chat display cleared! (Records preserved in database)" 
                : "✅ Chat history cleared successfully!";
            this.showTemporaryMessage(successMsg, 2500);
        })
        .catch(err => {
            console.log("History clear error:", err);
            
            // Restore original content on error
            this.chatText = originalChatText;
            this.showTemporaryMessage("❌ Failed to clear history. Please try again.", 3000);
        });
    }
}

// Show temporary status message
showTemporaryMessage(message, duration = 2000) {
    const originalText = this.chatText;
    this.chatText = message;
    
    setTimeout(() => {
        if (this.messages.length === 0) {
            this.chatText = ""; // Keep empty if no messages
        } else {
            this.updateChatText(); // Restore chat if messages exist
        }
    }, duration);
}

// Optional: Add deletion animation effect
showDeletionAnimation() {
    const chatContainer = document.querySelector('.chat-container'); // Adjust selector as needed
    if (chatContainer) {
        // Add fade-out effect
        chatContainer.style.transition = 'opacity 0.5s ease-out';
        chatContainer.style.opacity = '0.3';
        
        // Create deletion effect with falling text
        const messages = document.querySelectorAll('.message'); // Adjust selector as needed
        messages.forEach((msg, index) => {
            setTimeout(() => {
                msg.style.transition = 'transform 0.3s ease-in, opacity 0.3s ease-in';
                msg.style.transform = 'translateY(20px)';
                msg.style.opacity = '0';
            }, index * 50);
        });
        
        // Reset container after animation
        setTimeout(() => {
            chatContainer.style.opacity = '1';
        }, 1000);
    }
}

// Enhanced save with deletion tracking
saveMessagesToCache() {
    if (this.messages.length > 0) {
        localStorage.setItem(`chat_${this.user_id}`, JSON.stringify(this.messages));
    } else {
        // Remove from localStorage if no messages
        localStorage.removeItem(`chat_${this.user_id}`);
    }
}

// Enhanced load with better error handling
loadMessagesFromCache() {
    try {
        const cached = localStorage.getItem(`chat_${this.user_id}`);
        if (cached) {
            const parsedMessages = JSON.parse(cached);
            if (Array.isArray(parsedMessages) && parsedMessages.length > 0) {
                this.messages = parsedMessages;
                this.updateChatText();
                return true; // cache found
            }
        }
    } catch (e) {
        console.log("Error loading from cache:", e);
        localStorage.removeItem(`chat_${this.user_id}`); // Remove corrupted cache
    }
    return false;
}

// Enhanced load chat history with deletion state
loadChatHistory() {
    // Show loading state
    this.chatText = "📥 Loading chat history...";
    
    // 1. Try local cache first
    const cacheLoaded = this.loadMessagesFromCache();
    if (cacheLoaded) {
        console.log("Loaded chat from local cache.");
        this.showTemporaryMessage("📥 Loaded from cache", 1000);
    }

    // 2. Then sync with backend (MongoDB/in-memory)
    fetch('/history', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user: this.user_id })
    })
    .then(r => r.json())
    .then(data => {
        if (data.messages && data.messages.length > 0) {
            this.messages = data.messages;
            this.updateChatText();
            this.saveMessagesToCache(); // update local cache
            
            if (!cacheLoaded) {
                this.showTemporaryMessage("📥 Loaded from server", 1000);
            }
        } else if (!cacheLoaded) {
            // No messages anywhere
            this.messages = [];
            this.chatText = "";
            this.showTemporaryMessage("💬 Start a new conversation!", 2000);
        }
    })
    .catch(err => {
        console.log("History load error:", err);
        if (!cacheLoaded) {
            this.chatText = "";
            this.showTemporaryMessage("⚠️ Could not load history", 2000);
        }
    });
}

// Add this method to show progress during bulk operations
showProgressMessage(current, total, operation = "Processing") {
    const percentage = Math.round((current / total) * 100);
    this.chatText = `${operation}... ${percentage}% (${current}/${total})`;
}


    // Load sub-suggestions dynamically
    loadSubSuggestions(category, container) {
        container.innerHTML = ""; // Clear previous buttons

        // Helper to render a list of strings as buttons
        const renderButtons = (arr) => {
            arr.forEach(text => {
                const btn = document.createElement("button");
                btn.textContent = text;
                btn.addEventListener("click", () => this.sendSuggestion(text));
                container.appendChild(btn);
            });
        };

        // 1) Prefer settings-provided related suggestions by category
        let rendered = false;
        if (this.botSettings && this.suggestedByCategory) {
            const keys = Object.keys(this.suggestedByCategory);
            const lowerCat = String(category || '').toLowerCase();
            // Try exact, contains, and office display name matches
            let matchKey = keys.find(k => k.toLowerCase() === lowerCat);
            if (!matchKey) matchKey = keys.find(k => lowerCat.includes(k.toLowerCase()) || k.toLowerCase().includes(lowerCat));
            if (!matchKey && this.officeNames && this.officeNames[category]) {
                const officeName = this.officeNames[category];
                matchKey = keys.find(k => k.toLowerCase().includes(officeName.toLowerCase()) || officeName.toLowerCase().includes(k.toLowerCase()));
            }
            const messages = matchKey ? (this.suggestedByCategory[matchKey] || []) : [];
            if (messages.length && !(this.botSettings.show_suggested_questions === false)) {
                renderButtons(messages.slice(0, 8));
                rendered = true;
            }
        }

        // 2) Fallback to built-in static subSuggestions
        if (!rendered && this.subSuggestions[category]) {
            renderButtons(this.subSuggestions[category]);
            rendered = true;
        }

        if (rendered) {
            // Hide main suggestions
            document.querySelector('.chatbox__suggestions').style.display = 'none';
            document.querySelector('.suggestions-label').textContent = 'Related questions:';

            // Apply theme color to the newly rendered buttons
            if (this.botSettings && this.botSettings.primary_color) {
                this.applyPrimaryColor(this.botSettings.primary_color);
            }
        }
    }

    resetToMainSuggestions() {
        const subSuggestions = document.getElementById("sub-suggestions");
        if (subSuggestions) {
            subSuggestions.innerHTML = "";
        }
        const mainSuggestions = document.querySelector('.chatbox__suggestions');
        if (mainSuggestions) {
            mainSuggestions.style.display = 'flex';
        }
        const label = document.querySelector('.suggestions-label');
        if (label) {
            label.textContent = 'Suggested topics:';
            label.style.display = 'block'; // Ensure label is visible
        }
    }

    sendSuggestion(text) {
        const textField = this.args.messageInput;
        textField.value = text;
        this.onSendButton();
    }

    // ✅ Send message programmatically (for office switch buttons)
    sendMessage(text) {
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

        // Show typing indicator
        this.showTypingIndicator();

        // ✅ Always use /predict endpoint with Google Translate integration
        if (typeof fetch !== 'undefined') {
            // Create AbortController for timeout handling
            const controller = new AbortController();
            const timeoutMs = this.getResponseTimeoutMs();
            
            // Set up timeout
            const timeoutId = setTimeout(() => {
                controller.abort();
            }, timeoutMs);
            
            // Add performance timing
            const startTime = performance.now();
            console.log(`🚀 Starting request for: "${text1}"`);
            
            fetch('/predict', {
                method: 'POST',
                body: JSON.stringify({ 
                    message: text1, 
                    user: this.user_id,  // ✅ Backend expects 'user' not 'user_id'
                    user_id: this.user_id  // Keep for backward compatibility
                }),
                mode: 'cors',
                headers: { 'Content-Type': 'application/json' },
                signal: controller.signal
            })
            .then(r => {
                // Clear the timeout since we got a response
                clearTimeout(timeoutId);
                return r.json();
            })
            .then(r => {
                // Hide typing indicator
                this.hideTypingIndicator();
                
                // Log performance metrics
                const endTime = performance.now();
                const responseTime = endTime - startTime;
                console.log(`⚡ Response received in ${responseTime.toFixed(2)}ms`);
                
                // Log backend performance metrics if available
                if (r.response_time) {
                    console.log(`🔧 Backend processing time: ${r.response_time}ms`);
                }
                if (r.vector_stats) {
                    console.log(`📊 Vector search stats:`, r.vector_stats);
                }
                
                // ✅ CONTEXT SWITCH WARNING HANDLER
                // Check if backend is warning about office context switch
                if (r.status === 'context_switch_warning' && r.requires_reset) {
                    console.warn(`⚠️ Context switch blocked: ${r.current_office} → ${r.attempted_office}`);
                    
                    // Display the warning message from backend
                    let msg2 = { 
                        name: "Bot", 
                        message: r.answer,
                        status: 'context_switch_warning',
                        office: r.current_office || 'General',
                        isContextWarning: true,
                        currentOffice: r.current_office,
                        currentOfficeTag: r.current_office_tag,
                        attemptedOffice: r.attempted_office,
                        attemptedOfficeTag: r.attempted_office_tag
                    };
                    this.messages.push(msg2);
                    this.updateChatText();
                    
                    // Clear input field
                    textField.value = '';
                    this.args.characterCount.textContent = '0/500';
                    
                    // Highlight reset button if exists
                    this.highlightResetButton();
                    
                    return; // Stop processing, don't proceed with normal flow
                }
                
                // ✅ Google Translate Integration - Log translation info
                if (r.detected_language && r.detected_language !== 'en') {
                    console.log(`🌐 Language detected: ${r.detected_language}`);
                    console.log(`📝 Original message: "${r.original_message}"`);
                    if (r.translated_message) {
                        console.log(`📝 Translated to English: "${r.translated_message}"`);
                    }
                    console.log(`💬 Response in ${r.detected_language}: "${r.answer}"`);
                    if (r.original_answer) {
                        console.log(`💬 Original English response: "${r.original_answer}"`);
                    }
                }
                
                // ✅ Handle office switch confirmation
                if (r.office_switched && r.new_office_tag) {
                    const officeTagToContext = {
                        'admission_office': 'admission',
                        'registrar_office': 'registrar',
                        'ict_office': 'ict',
                        'guidance_office': 'guidance',
                        'osa_office': 'osa'
                    };
                    this.currentContext = officeTagToContext[r.new_office_tag];
                    this.updateContextIndicator();
                    console.log(`🔄 Office switched to: ${r.new_office}`);
                }
                
                let msg2 = { 
                    name: "Bot", 
                    message: r.answer,
                    status: r.status || 'resolved',
                    office: r.office || 'General',
                    language: r.detected_language || 'en',
                    suggested_office: r.suggested_office || null,  // ✅ Store suggested office
                    suggested_office_tag: r.suggested_office_tag || null
                };
                this.messages.push(msg2);
                
                // Log status and office for analytics
                console.log(`✅ Status: ${r.status || 'resolved'} | Office: ${r.office || 'General'}`);
                
                // ✅ Show office switch suggestion hint
                if (r.suggested_office && !r.office_switched) {
                    console.log(`💡 Office switch suggested: ${r.suggested_office}`);
                    console.log(`   Tag: ${r.suggested_office_tag}`);
                    console.log(`   💬 Click button or type "yes" to switch to ${r.suggested_office}`);
                } else if (r.office_switched) {
                    console.log(`✅ Office switch confirmed and completed`);
                } else {
                    console.log(`ℹ️ No office switch suggestion in this response`);
                }
                
                // Mark this index as the place to render inline suggestions if pending
                if (this.pendingInlineAfterResponse) {
                    this.lastInlineBotIndex = this.messages.length - 1;
                    this.pendingInlineAfterResponse = false;
                } else {
                    this.lastInlineBotIndex = null;
                }
                // Check for user farewell message BEFORE adding bot message
                const shouldShowFeedback = this.checkForUserFarewellMessage(text1);
                
                // Decide on feedback AFTER adding bot message
                this.checkForConversationEnd(r.answer);
                this.updateChatText();
                
                // Show feedback form if user sent farewell message
                if (shouldShowFeedback) {
                    setTimeout(() => {
                        this.showFeedbackForm();
                    }, 1000); // Show after bot response
                }
                textField.value = '';
                this.args.characterCount.textContent = '0/500';
                
                // Speak response if TTS is enabled
                if (this.ttsEnabled) {
                    setTimeout(() => this.speakMessage(r.answer), 500);
                }
                
                // Update context based on response (unless office switch was just confirmed)
                if (!r.office_switched) {
                    this.updateContextFromMessage(text1, r.answer);
                }
                
                // Show contextual suggested messages from backend
                if (r.suggested_messages && r.suggested_messages.length > 0) {
                    setTimeout(() => this.showBackendSuggestions(r.suggested_messages), 500);
                } else {
                    // Fallback to main suggestions
                    setTimeout(() => this.resetToMainSuggestions(), 1000);
                }
            })
            .catch((error) => {
                // Clear the timeout
                clearTimeout(timeoutId);
                
                // Hide typing indicator on error
                this.hideTypingIndicator();
                
                // ✅ Always use /predict endpoint - show error message instead of local response
                let errorMessage = '';
                if (error.name === 'AbortError') {
                    console.log('Request timed out');
                    errorMessage = 'Sorry, the request timed out. Please try again or rephrase your question.';
                } else {
                    console.log('Backend error:', error);
                    errorMessage = 'Sorry, I encountered an error. Please check your connection and try again.';
                }
                
                // Show error message to user
                let msg2 = { 
                    name: "Bot", 
                    message: errorMessage,
                    status: 'error',
                    office: 'System'
                };
                this.messages.push(msg2);
                this.updateChatText();
                
                textField.value = '';
                this.args.characterCount.textContent = '0/500';
            });
        } else {
            // Fetch is not available - show error
            this.hideTypingIndicator();
            let msg2 = { 
                name: "Bot", 
                message: 'Sorry, the chatbot requires an internet connection to function. Please check your connection.',
                status: 'error',
                office: 'System'
            };
            this.messages.push(msg2);
            this.updateChatText();
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
    
    // ENHANCED: Automatic context switching based on topic detection
    if (detectedOffice) {
        // If no current context, set it automatically
        if (!this.currentContext) {
            this.currentContext = detectedOffice;
            this.updateContextIndicator();
            
            // Add a subtle notification about context switch
            const contextMsg = { 
                name: "System", 
                message: `Switched to ${this.officeNames[detectedOffice]} topic.` 
            };
            this.messages.push(contextMsg);
        }
        // If different office detected, switch context automatically
        else if (detectedOffice !== this.currentContext) {
            const previousOffice = this.officeNames[this.currentContext];
            this.currentContext = detectedOffice;
            this.updateContextIndicator();
            
            // Add notification about automatic context switch
            const switchMsg = { 
                name: "System", 
                message: `Switched from ${previousOffice} to ${this.officeNames[detectedOffice]} topic.` 
            };
            this.messages.push(switchMsg);
        }
    }
    
    // Reset context for general messages that don't belong to any office
    if (!detectedOffice && (
        botResponse.includes("Hello!") || 
        botResponse.includes("You're welcome") || 
        botResponse.includes("Goodbye") ||
        msgLower.includes('thank') ||
        msgLower.includes('bye')
    )) {
        // Keep current context for greetings/thanks/goodbye
        // Don't reset unless explicitly requested
    }
}

    handleLocalResponse(message) {
        // Hide typing indicator for local responses
        this.hideTypingIndicator();
        
        // Check for user farewell message BEFORE generating response
        const shouldShowFeedback = this.checkForUserFarewellMessage(message);
        
        const botResponse = this.generateLocalResponse(message);
        const msg2 = { name: "Bot", message: botResponse };
        this.messages.push(msg2);
        if (this.pendingInlineAfterResponse) {
            this.lastInlineBotIndex = this.messages.length - 1;
            this.pendingInlineAfterResponse = false;
        }
        // Decide on feedback AFTER adding bot message
        this.checkForConversationEnd(botResponse);
        this.updateChatText();
        
        // Show feedback form if user sent farewell message
        if (shouldShowFeedback) {
            setTimeout(() => {
                this.showFeedbackForm();
            }, 1000); // Show after bot response
        }
        
        // Show contextual suggestions for local responses (fallback)
        const contextualSuggestions = this.getContextualQuickReplies(this.currentContext, botResponse);
        if (contextualSuggestions.length > 0) {
            setTimeout(() => this.showBackendSuggestions(contextualSuggestions), 500);
        } else {
            // Fallback to main suggestions
            setTimeout(() => this.resetToMainSuggestions(), 1000);
        }
        
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
    
    // No more context conflict warnings - automatic switching handles this
    
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
    
    // Check for office-specific queries (automatic context will be set)
    if (detectedOffice && this.responses[detectedOffice]) {
        return this.responses[detectedOffice][Math.floor(Math.random() * this.responses[detectedOffice].length)];
    }
    
    // Context-specific fallback
    if (this.currentContext && this.responses[this.currentContext]) {
        const responses = this.responses[this.currentContext];
        return responses[Math.floor(Math.random() * responses.length)];
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
        const welcome = (this.botSettings && this.botSettings.welcome_message) ? this.botSettings.welcome_message : "Hi there! I'm your TCC Connect assistant. How can I help you today?";
        const showSuggestions = this.suggestionsEnabled();

        // ✅ If no messages exist, add initial welcome message to show suggestions below it
        if (this.messages.length === 0 && this.showInitialSuggestions) {
            this.messages.push({ name: "Bot", message: welcome });
            this.lastInlineBotIndex = 0; // Show suggestions below this first message
            this.showInitialSuggestions = false; // Only add once
        }

        // ✅ No top-level suggestions - they will appear below bot responses only
        let html = `
            <!-- Quick Reply Suggestions (Enhanced) -->
            <div class="chatbox__quick-replies" id="quick-replies" style="display: none;">
                <div class="quick-replies-label">Quick replies:</div>
                <div class="quick-replies-container" id="quick-replies-container">
                    <!-- Quick reply buttons will be dynamically inserted here -->
                </div>
            </div>
            
            <div class="chatbox__context" id="context-indicator" style="display: none;">
                <span class="context-text">Currently helping with: <strong id="context-office">General</strong></span>
                <button class="context-reset" onclick="resetContext()">Switch Topic</button>
            </div>
        `;
        
        this.messages.forEach((item, index) => {
            if (item.name === "Bot") {
                // ✅ Check if it's a context switch message with suggested office
                if (item.message.includes("I think you might be asking about") || 
                    item.message.includes("Would you like me to connect you")) {
                    html += `
                        <div class="messages__item messages__item--context">
                            ${item.message}
                            ${item.suggested_office ? `
                                <div class="office-switch-actions" style="margin-top: 10px; display: flex; gap: 8px;">
                                    <button class="office-switch-yes" onclick="sendMessage('yes')" style="background: #4CAF50; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-weight: 500;">
                                        ✓ Yes, switch to ${item.suggested_office}
                                    </button>
                                    <button class="office-switch-no" onclick="sendMessage('no, continue here')" style="background: #666; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-weight: 500;">
                                        ✗ No, stay here
                                    </button>
                                </div>
                            ` : ''}
                        </div>
                    `;
                } 
                // Check if it's an announcements message
                else if (item.message.includes("📢") && item.message.includes("Announcements")) {
                    html += `
                        <div class="messages__item messages__item--announcement">
                            ${item.message}
                            <button class="tts-button" onclick="speakMessage('${item.message.replace(/'/g, "\\'")}', this)" title="Read aloud">🔊</button>
                        </div>
                    `;
                } 
                // Inline feedback widget message
                else if (item.type === 'feedback_inline') {
                    html += `
                        <div class="messages__item messages__item--visitor">
                            <div class="inline-feedback">
                                <div class="feedback-header">
                                    <strong>Thank you for chatting with us!</strong>
                                    <div style="margin-top:4px;color:#666;">Please rate your experience.</div>
                                </div>
                                <div class="star-rating" aria-label="Star rating">
                                    <span class="star" data-rating="1">★</span>
                                    <span class="star" data-rating="2">★</span>
                                    <span class="star" data-rating="3">★</span>
                                    <span class="star" data-rating="4">★</span>
                                    <span class="star" data-rating="5">★</span>
                                </div>
                                <div class="rating-text" style="display:none;"></div>
                                <div class="comment-section" style="margin-top:8px;">
                                    <textarea name="comment" rows="3" placeholder="Additional comments (optional)" style="width:100%; box-sizing:border-box;"></textarea>
                                </div>
                                <div class="feedback-actions" style="display:flex; gap:8px; justify-content:flex-end; margin-top:8px;">
                                    <button type="button" class="btn-skip">Skip</button>
                                    <button type="button" class="btn-submit" disabled>Submit</button>
                                </div>
                            </div>
                        </div>
                    `;
                } else {
                    html += `
                        <div class="messages__item messages__item--visitor">
                            ${item.message}
                            <button class="tts-button" onclick="speakMessage('${item.message.replace(/'/g, "\\'")}', this)" title="Read aloud">🔊</button>
                        </div>
                    `;
                    // ✅ Show inline suggestions below bot response
                    if (this.suggestionsEnabled() && this.lastInlineBotIndex === index) {
                        // For initial message (index 0), show category buttons
                        if (index === 0 && !this.currentContext && !this.selectedCategoryLabel) {
                            const hasCategories = this.suggestedByCategory && Object.keys(this.suggestedByCategory).length > 0;
                            if (hasCategories) {
                                const cats = Object.keys(this.suggestedByCategory);
                                const categoryButtons = cats.map(cat => 
                                    `<button class=\"suggested-category-inline\" data-category=\"${String(cat)}\">${String(cat)}</button>`
                                ).join('');
                                html += `
                                    <div class=\"inline-suggestions-label\">Suggested topics:</div>
                                    <div class=\"inline-suggestions\">
                                        ${categoryButtons}
                                    </div>
                                `;
                            }
                        } else {
                            // For other messages, show related question suggestions
                            const inline = this.getSuggestionsForCurrent();
                            if (inline && inline.length) {
                                const buttons = inline.map(t => `<button class=\"inline-suggest-btn\" data-msg=\"${String(t).replace(/"/g, '&quot;')}\">${t}</button>`).join('');
                                html += `
                                    <div class=\"inline-suggestions-label\">Related questions:</div>
                                    <div class=\"inline-suggestions\">
                                        ${buttons}
                                    </div>
                                `;
                            }
                        }
                    }
                }
            } else if (item.name === "System") {
                html += `<div class="messages__item messages__item--context">${item.message}</div>`;
            } else {
                html += `<div class="messages__item messages__item--operator message user chatbox__message--user">${item.message}</div>`;
            }
        });

        // ✅ Add typing indicator at the BOTTOM (after all messages)
        html += `
            <!-- Typing Indicator (at bottom) -->
            <div class="chatbox__typing-indicator" id="typing-indicator" style="display: none;">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
                <span class="typing-text">TCC Assistant is typing...</span>
            </div>
        `;

        const chatmessage = document.querySelector('.chatbox__messages');
        chatmessage.innerHTML = html;
        // (Re)bind inline feedback listeners after render
        this.attachInlineFeedbackListeners();
        
        // Update context indicator
        this.updateContextIndicator();
        
        // Re-attach event listeners for suggestion buttons
        this.reattachSuggestionListeners();

        // Enforce suggestions visibility post-render
        this.applySuggestionsVisibility();

        // Bind clicks for settings-driven suggestion items
        document.querySelectorAll('.chatbox__suggestions .suggested-item').forEach(btn => {
            btn.addEventListener('click', () => {
                const text = btn.getAttribute('data-msg') || btn.textContent;
                // Only show inline suggestions after the bot responds
                this.pendingInlineAfterResponse = true;
                this.sendSuggestion(text);
            });
        });
        // Bind inline suggestion clicks
        document.querySelectorAll('.inline-suggestions .inline-suggest-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const text = btn.getAttribute('data-msg') || btn.textContent;
                // Only show inline suggestions after the bot responds
                this.pendingInlineAfterResponse = true;
                this.sendSuggestion(text);
            });
        });

        // Bind clicks for category labels to set context and show category welcome if available
        document.querySelectorAll('.chatbox__suggestions .suggested-category').forEach(btn => {
            btn.addEventListener('click', () => {
                const cat = btn.getAttribute('data-category') || btn.textContent;
                this.currentContext = null; // clear built-in office mapping
                // Show office-specific welcome by label
                this.showOfficeWelcomeByLabel(cat);
                // Render this category's messages below as related questions
                const subBox = document.getElementById('sub-suggestions');
                if (subBox && this.suggestedByCategory && this.suggestedByCategory[cat]) {
                    subBox.innerHTML = '';
                    this.suggestedByCategory[cat].forEach(text => {
                        const b = document.createElement('button');
                        b.textContent = text;
                        b.addEventListener('click', () => this.sendSuggestion(text));
                        subBox.appendChild(b);
                    });
                    // Ensure label reflects related questions
                    const label = document.querySelector('.suggestions-label');
                    if (label) label.textContent = 'Related questions:';
                    // Apply theme color
                    if (this.botSettings && this.botSettings.primary_color) this.applyPrimaryColor(this.botSettings.primary_color);
                }
            });
        });

        // ✅ Bind clicks for INLINE category buttons (below bot response)
        document.querySelectorAll('.inline-suggestions .suggested-category-inline').forEach(btn => {
            btn.addEventListener('click', () => {
                const cat = btn.getAttribute('data-category') || btn.textContent;
                this.currentContext = null; // clear built-in office mapping
                this.selectedCategoryLabel = cat;
                // Show office-specific welcome and inline suggestions will update
                this.showOfficeWelcomeByLabel(cat);
            });
        });

        // Bind click for dynamically created flat suggestion buttons
        document.querySelectorAll('.chatbox__suggestions button[data-msg]').forEach(btn => {
            btn.addEventListener('click', () => {
                const text = btn.getAttribute('data-msg') || btn.textContent;
                this.sendSuggestion(text);
            });
        });

        // Re-apply theme color styles to newly rendered suggestion buttons
        if (this.botSettings && this.botSettings.primary_color) {
            this.applyPrimaryColor(this.botSettings.primary_color);
        }
        
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
                    // Set context and show office-specific welcome if available
                    this.currentContext = category;
                    this.updateContextIndicator();
                    this.showOfficeWelcome(category);
                    this.loadSubSuggestions(category, subSuggestionBox);
                }
            });
        });
    }

    // Check if conversation should end and trigger feedback
    checkForConversationEnd(botResponse) {
        // DISABLED: Only trigger feedback based on user farewell messages
        // This method is kept for compatibility but no longer triggers feedback automatically
        // Feedback is now only triggered by checkForUserFarewellMessage() method
        
        // The original logic has been moved to only trigger on specific user keywords:
        // "thanks", "thank you", "goodbye!", "bye!"
        
        return false; // Never trigger feedback from bot responses
    }

    // Check if user message contains farewell keywords and trigger feedback
    checkForUserFarewellMessage(userMessage) {
        // Use feedback manager's specific keyword detection if available
        if (window.feedbackManager && window.feedbackManager.checkForFarewellTrigger) {
            const result = window.feedbackManager.checkForFarewellTrigger(userMessage);
            console.log('Feedback manager check result:', result);
            return result;
        }

        // Fallback: Include both English and Filipino farewell patterns
        const farewellKeywords = [
            // English patterns
            'thanks', 'thank you', 'goodbye!', 'bye!', 'see you', 'farewell', 'take care', 
            'have a good day', 'have a nice day', 'that\'s all', 'that\'s it', 'nothing else', 
            'all done', 'finished', 'done', 'good night', 'good evening', 'see you later',
            'talk to you later', 'catch you later', 'until next time', 'until we meet again',
            'so long', 'adios', 'ciao',
            
            // Filipino patterns
            'salamat', 'maraming salamat', 'salamat po', 'salamat sa inyo', 'salamat sa tulong',
            'paalam', 'babay', 'ingat', 'mag-ingat ka', 'ingat ka', 'ingat po',
            'hanggang sa muli', 'hanggang sa susunod', 'sige', 'sige na', 'ok na',
            'tapos na', 'wala na', 'yun na yun', 'yun lang', 'ganun lang',
            'magandang gabi', 'magandang araw', 'magandang umaga', 'magandang hapon'
        ];

        // Convert message to lowercase for case-insensitive matching
        const messageLower = userMessage.toLowerCase().trim();
        
        // Check if message contains any of the farewell keywords
        const hasFarewellKeyword = farewellKeywords.some(keyword => 
            messageLower.includes(keyword.toLowerCase())
        );

        console.log('Fallback farewell check for:', userMessage, 'Result:', hasFarewellKeyword);
        return hasFarewellKeyword;
    }

    // Show feedback form when user sends farewell message
    showFeedbackForm() {
        console.log('showFeedbackForm() called - showing inline feedback');
        // Always use inline feedback widget as a bot message
        this.insertInlineFeedbackMessage();
    }

    // Reset feedback state for testing (call this in browser console)
    resetFeedbackState() {
        if (window.feedbackManager) {
            window.feedbackManager.resetFeedbackState();
            console.log('Feedback state reset');
        }
    }

    // Insert inline feedback widget as a bot message
    insertInlineFeedbackMessage() {
        // Prevent duplicate inline feedback if last message is already feedback
        const lastMsg = this.messages[this.messages.length - 1];
        if (lastMsg && lastMsg.type === 'feedback_inline') {
            return;
        }

        const feedbackId = 'fb_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5);
        const feedbackPrompt = {
            name: 'Bot',
            type: 'feedback_inline',
            id: feedbackId,
            message: 'Thank you for chatting with us! Please rate your experience and leave a comment (optional).'
        };
        this.messages.push(feedbackPrompt);
        this.updateChatText();
        this.attachInlineFeedbackListeners();
    }

    // Attach handlers for any inline feedback widgets in the chat
    attachInlineFeedbackListeners() {
        const widgets = document.querySelectorAll('.inline-feedback:not([data-initialized="true"])');
        widgets.forEach((widget) => {
            widget.setAttribute('data-initialized', 'true');
            let currentRating = 0;

            const stars = widget.querySelectorAll('.star');
            const ratingText = widget.querySelector('.rating-text');
            const submitBtn = widget.querySelector('.btn-submit');
            const skipBtn = widget.querySelector('.btn-skip');
            const commentEl = widget.querySelector('textarea[name="comment"]');

            const updateStars = (rating, isHover = false) => {
                stars.forEach((star, index) => {
                    const starRating = index + 1;
                    if (starRating <= rating) {
                        star.classList.add('active');
                        if (isHover) {
                            star.classList.add('hover');
                        } else {
                            star.classList.remove('hover');
                        }
                    } else {
                        star.classList.remove('active', 'hover');
                    }
                });
                const texts = {1: 'Poor', 2: 'Fair', 3: 'Good', 4: 'Very Good', 5: 'Excellent'};
                if (rating > 0) {
                    ratingText.textContent = texts[rating];
                    ratingText.style.display = 'block';
                } else {
                    ratingText.style.display = 'none';
                }
                submitBtn.disabled = rating === 0;
            };

            stars.forEach((star, index) => {
                star.addEventListener('click', () => {
                    currentRating = index + 1;
                    updateStars(currentRating);
                });
                star.addEventListener('mouseenter', () => updateStars(index + 1, true));
            });
            const starContainer = widget.querySelector('.star-rating');
            starContainer.addEventListener('mouseleave', () => updateStars(currentRating));

            const showToast = (message, type = 'info') => {
                if (window.feedbackManager && typeof window.feedbackManager.showToast === 'function') {
                    window.feedbackManager.showToast(message, type);
                    return;
                }
                // minimal fallback
                const toast = document.createElement('div');
                toast.className = `toast toast-${type}`;
                toast.textContent = message;
                document.body.appendChild(toast);
                setTimeout(() => { toast.style.transform = 'translateX(0)'; }, 50);
                setTimeout(() => {
                    toast.style.transform = 'translateX(100%)';
                    setTimeout(() => toast.remove(), 300);
                }, 2500);
            };

            const getSessionId = () => {
                let sessionId = sessionStorage.getItem('chat_session_id');
                if (!sessionId) {
                    sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
                    sessionStorage.setItem('chat_session_id', sessionId);
                }
                return sessionId;
            };

            const submitHandler = async (e) => {
                e.preventDefault();
                if (submitBtn.disabled) return;
                const originalText = submitBtn.textContent;
                submitBtn.disabled = true;
                submitBtn.textContent = 'Submitting...';

                try {
                    const payload = {
                        rating: currentRating,
                        comment: (commentEl.value || '').trim(),
                        user_id: this.user_id,
                        session_id: getSessionId()
                    };
                    const res = await fetch('/api/feedback', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                    const result = await res.json();
                    if (result && result.success) {
                        showToast(result.message || 'Thank you for your feedback!', 'success');
                        // Replace widget content (keep parent node to avoid detaching events on others)
                        widget.innerHTML = '<div style="padding:8px 0;">Thanks for the feedback! ✅</div>';
                    } else {
                        showToast((result && result.message) || 'Something went wrong, please try again.', 'error');
                        submitBtn.disabled = false;
                        submitBtn.textContent = originalText;
                    }
                } catch (err) {
                    console.error('Inline feedback error:', err);
                    showToast('Something went wrong, please try again.', 'error');
                    submitBtn.disabled = false;
                    submitBtn.textContent = originalText;
                }
            };

            const skipHandler = () => {
                // Replace widget content
                widget.innerHTML = '<div style="padding:8px 0; color:#666;">Feedback skipped.</div>';
            };

            submitBtn.addEventListener('click', submitHandler);
            skipBtn.addEventListener('click', skipHandler);
        });
    }
}

// Initialize chatbox when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const chatbox = new Chatbox();
    
    // Make resetFeedbackState available globally for testing
    window.resetFeedbackState = () => chatbox.resetFeedbackState();
});