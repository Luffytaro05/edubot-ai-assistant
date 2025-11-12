// Enhanced Feedback System for EduChat Portal
class FeedbackManager {
    constructor() {
        this.currentRating = 0;
        this.isSubmitting = false;
        this.hasShownFeedback = false; // Track if feedback has been shown in this session
        this.botResponseCount = 0; // Track number of bot responses
        this.minResponsesBeforeFeedback = 2; // Minimum bot responses before showing feedback
        this.lastFeedbackTime = 0; // Timestamp of last feedback shown
        this.feedbackCooldown = 60000; // 60 seconds cooldown between feedback prompts (in milliseconds)
        // Goodbye patterns removed - feedback is now based on bot responses only
        this.goodbyePatterns = []; // Empty array for backwards compatibility
        this.init();
    }

    init() {
        this.createFeedbackForm();
        this.bindEvents();
        // DISABLED: setupMessageListener() - feedback is now controlled manually from app.js
        // this.setupMessageListener();
    }

    createFeedbackForm() {
        // Create feedback form HTML
        const feedbackHTML = `
            <div id="feedback-modal" class="feedback-modal" style="display: none;">
                <div class="feedback-content">
                    <div class="feedback-header">
                        <h3>Thank you for chatting with us!</h3>
                        <p>Please share your experience to help us improve.</p>
                    </div>
                    
                    <form id="feedback-form" class="feedback-form">
                        <div class="rating-section">
                            <label>How would you rate your experience?</label>
                            <div class="star-rating" id="star-rating">
                                <span class="star" data-rating="1">★</span>
                                <span class="star" data-rating="2">★</span>
                                <span class="star" data-rating="3">★</span>
                                <span class="star" data-rating="4">★</span>
                                <span class="star" data-rating="5">★</span>
                            </div>
                            <div class="rating-text" id="rating-text"></div>
                        </div>
                        
                        <div class="comment-section">
                            <label for="feedback-comment">Additional comments (optional)</label>
                            <textarea 
                                id="feedback-comment" 
                                name="comment" 
                                placeholder="Tell us more about your experience..."
                                rows="4"
                            ></textarea>
                        </div>
                        
                        <div class="feedback-actions">
                            <button type="button" id="skip-feedback" class="btn-skip">Skip</button>
                            <button type="submit" id="submit-feedback" class="btn-submit" disabled>
                                Submit Feedback
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        // Add to page
        document.body.insertAdjacentHTML('beforeend', feedbackHTML);
    }

    bindEvents() {
        // Star rating events
        const stars = document.querySelectorAll('.star');
        stars.forEach((star, index) => {
            star.addEventListener('click', () => this.setRating(index + 1));
            star.addEventListener('mouseenter', () => this.hoverRating(index + 1));
        });

        // Rating container events
        const ratingContainer = document.getElementById('star-rating');
        ratingContainer.addEventListener('mouseleave', () => this.resetHover());

        // Form submission
        const form = document.getElementById('feedback-form');
        form.addEventListener('submit', (e) => this.handleSubmit(e));

        // Skip button
        const skipBtn = document.getElementById('skip-feedback');
        skipBtn.addEventListener('click', () => this.hideFeedback());

        // Character count for textarea
        const textarea = document.getElementById('feedback-comment');
        const charCount = document.querySelector('.character-count-feedback');
        if (textarea && charCount) {
            textarea.addEventListener('input', () => {
                const count = textarea.value.length;
                charCount.textContent = `${count}/500`;
                
                // Change color as it approaches limit
                if (count > 450) {
                    charCount.style.color = '#e74c3c';
                } else if (count > 400) {
                    charCount.style.color = '#f39c12';
                } else {
                    charCount.style.color = '#95a5a6';
                }
            });
        }

        // Close modal on outside click
        const modal = document.getElementById('feedback-modal');
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.hideFeedback();
            }
        });
    }

    setRating(rating) {
        this.currentRating = rating;
        this.updateStarDisplay();
        this.updateRatingText();
        this.updateSubmitButton();
    }

    hoverRating(rating) {
        this.updateStarDisplay(rating, true);
    }

    resetHover() {
        this.updateStarDisplay(this.currentRating);
    }

    updateStarDisplay(rating = this.currentRating, isHover = false) {
        const stars = document.querySelectorAll('.star');
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
    }

    updateRatingText() {
        const ratingText = document.getElementById('rating-text');
        const texts = {
            1: 'Poor',
            2: 'Fair', 
            3: 'Good',
            4: 'Very Good',
            5: 'Excellent'
        };
        
        if (this.currentRating > 0) {
            ratingText.textContent = texts[this.currentRating];
            ratingText.style.display = 'block';
        } else {
            ratingText.style.display = 'none';
        }
    }

    updateSubmitButton() {
        const submitBtn = document.getElementById('submit-feedback');
        submitBtn.disabled = this.currentRating === 0;
    }

    async handleSubmit(e) {
        e.preventDefault();
        
        if (this.isSubmitting || this.currentRating === 0) {
            return;
        }

        this.isSubmitting = true;
        const submitBtn = document.getElementById('submit-feedback');
        const originalText = submitBtn.textContent;
        
        try {
            // Update button state
            submitBtn.disabled = true;
            submitBtn.textContent = 'Submitting...';

            // Get form data
            const comment = document.getElementById('feedback-comment').value.trim();
            const user_id = this.getUserId();
            const session_id = this.getSessionId();

            // Prepare data
            const feedbackData = {
                rating: this.currentRating,
                comment: comment,
                user_id: user_id,
                session_id: session_id
            };

            // Submit to backend
            const response = await fetch('/api/feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(feedbackData)
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccessMessage(result.message);
                this.hideFeedback();
            } else {
                this.showErrorMessage(result.message || 'Something went wrong, please try again.');
            }

        } catch (error) {
            console.error('Feedback submission error:', error);
            this.showErrorMessage('Something went wrong, please try again.');
        } finally {
            // Reset button state
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
            this.isSubmitting = false;
        }
    }

    getUserId() {
        // Try to get user ID from various sources
        const userId = localStorage.getItem('user_id') || 
                       sessionStorage.getItem('user_id') || 
                       'guest';
        return userId;
    }

    getSessionId() {
        // Generate or get session ID
        let sessionId = sessionStorage.getItem('chat_session_id');
        if (!sessionId) {
            sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            sessionStorage.setItem('chat_session_id', sessionId);
        }
        return sessionId;
    }

    showSuccessMessage(message) {
        this.showToast(message, 'success');
    }

    showErrorMessage(message) {
        this.showToast(message, 'error');
    }

    showToast(message, type = 'info') {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        // Add styles
        Object.assign(toast.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '12px 20px',
            borderRadius: '4px',
            color: 'white',
            fontWeight: '500',
            zIndex: '10000',
            maxWidth: '300px',
            wordWrap: 'break-word',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            transform: 'translateX(100%)',
            transition: 'transform 0.3s ease'
        });

        // Set background color based on type
        const colors = {
            success: '#28a745',
            error: '#dc3545',
            info: '#17a2b8'
        };
        toast.style.backgroundColor = colors[type] || colors.info;

        // Add to page
        document.body.appendChild(toast);

        // Animate in
        setTimeout(() => {
            toast.style.transform = 'translateX(0)';
        }, 100);

        // Remove after delay
        setTimeout(() => {
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 3000);
    }

    showFeedback() {
        const modal = document.getElementById('feedback-modal');
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        
        // Reset form
        this.currentRating = 0;
        this.updateStarDisplay();
        this.updateRatingText();
        this.updateSubmitButton();
        
        const textarea = document.getElementById('feedback-comment');
        const charCount = document.querySelector('.character-count-feedback');
        if (textarea && charCount) {
            textarea.value = '';
            charCount.textContent = '0/500';
            charCount.style.color = '#95a5a6';
        }
    }

    hideFeedback() {
        const modal = document.getElementById('feedback-modal');
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }

    // Setup message listener - DISABLED: feedback is now based on bot responses only
    // This method is kept for backwards compatibility but does nothing
    setupMessageListener() {
        // Feedback is now triggered by bot responses, not user messages
        // This method is intentionally left empty
        console.log('Feedback listener disabled - feedback now based on bot responses only');
    }

    // Legacy method - kept for backwards compatibility but always returns false
    // Feedback is now based on bot responses, not user messages
    detectGoodbyePattern(message) {
        // Always return false - goodbye patterns are no longer used
        return false;
    }

    // Enhanced feedback form with better messaging
    createFeedbackForm() {
        // Create feedback form HTML
        const feedbackHTML = `
            <div id="feedback-modal" class="feedback-modal" style="display: none;">
                <div class="feedback-content">
                    <div class="feedback-header">
                        <div class="feedback-icon">💬</div>
                        <h3>Thank you for chatting with TCC Assistant!</h3>
                        <p>We'd love to hear about your experience to help us improve our service.</p>
                    </div>
                    
                    <form id="feedback-form" class="feedback-form">
                        <div class="rating-section">
                            <label>How would you rate your experience with TCC Assistant?</label>
                            <div class="star-rating" id="star-rating">
                                <span class="star" data-rating="1" title="Poor">★</span>
                                <span class="star" data-rating="2" title="Fair">★</span>
                                <span class="star" data-rating="3" title="Good">★</span>
                                <span class="star" data-rating="4" title="Very Good">★</span>
                                <span class="star" data-rating="5" title="Excellent">★</span>
                            </div>
                            <div class="rating-text" id="rating-text"></div>
                        </div>
                        
                        <div class="comment-section">
                            <label for="feedback-comment">Tell us more about your experience (optional)</label>
                            <textarea 
                                id="feedback-comment" 
                                name="comment" 
                                placeholder="What did you like? How can we improve? Any suggestions?"
                                rows="4"
                                maxlength="500"
                            ></textarea>
                            <div class="character-count-feedback">0/500</div>
                        </div>
                        
                        <div class="feedback-actions">
                            <button type="button" id="skip-feedback" class="btn-skip">
                                <span>Skip</span>
                            </button>
                            <button type="submit" id="submit-feedback" class="btn-submit" disabled>
                                <span>Submit Feedback</span>
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        // Add to page
        document.body.insertAdjacentHTML('beforeend', feedbackHTML);
    }

    // Public method to trigger feedback form
    triggerFeedback() {
        if (!this.hasShownFeedback) {
            this.showFeedback();
            this.hasShownFeedback = true;
        }
    }

    // Method to check if feedback should be shown after bot response
    // No longer based on goodbye patterns - only based on bot responses
    shouldShowFeedbackAfterBotResponse() {
        // Don't show if already shown in this session
        if (this.hasShownFeedback) {
            return false;
        }
        
        // Check cooldown period
        const now = Date.now();
        if (now - this.lastFeedbackTime < this.feedbackCooldown && this.lastFeedbackTime > 0) {
            return false;
        }
        
        // Increment bot response count
        this.botResponseCount++;
        
        // Show feedback after minimum number of bot responses
        if (this.botResponseCount >= this.minResponsesBeforeFeedback) {
            // Mark as shown, update last feedback time (but don't reset counter in case we want to show again later)
            this.hasShownFeedback = true;
            this.lastFeedbackTime = now;
            return true;
        }
        
        return false;
    }
    
    // Legacy method - kept for backwards compatibility but always returns false
    // Feedback is now based on bot responses, not user farewell messages
    checkForFarewellTrigger(userMessage) {
        // Always return false - goodbye patterns are no longer used
        return false;
    }

    // Reset feedback state (for new sessions)
    resetFeedbackState() {
        this.hasShownFeedback = false;
        this.botResponseCount = 0;
        this.lastFeedbackTime = 0;
    }
    
    // Method to be called when bot responds
    onBotResponse() {
        // Check if feedback should be shown after this bot response
        if (this.shouldShowFeedbackAfterBotResponse()) {
            // Show feedback after a short delay
            setTimeout(() => {
                this.showFeedback();
                this.hasShownFeedback = true;
            }, 1500);
        }
    }
}

// Initialize feedback manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.feedbackManager = new FeedbackManager();
    
    // Add manual trigger for testing (remove in production)
    window.testFeedback = () => {
        window.feedbackManager.triggerFeedback();
    };
    
    // Add test function for Filipino patterns
    window.testFilipinoPatterns = () => {
        const testMessages = [
            'salamat po',
            'maraming salamat',
            'paalam',
            'ingat po',
            'tapos na',
            'wala na',
            'yun lang',
            'magandang gabi',
            'sige na',
            'ok na'
        ];
        
        console.log('Testing Filipino patterns:');
        testMessages.forEach(msg => {
            const result = window.feedbackManager.checkForFarewellTrigger(msg);
            console.log(`"${msg}" -> ${result ? '✅ TRIGGERS' : '❌ NO TRIGGER'}`);
        });
    };
    
    // Add keyboard shortcut for testing (Ctrl+Shift+F)
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.shiftKey && e.key === 'F') {
            e.preventDefault();
            window.feedbackManager.triggerFeedback();
        }
    });
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FeedbackManager;
}
