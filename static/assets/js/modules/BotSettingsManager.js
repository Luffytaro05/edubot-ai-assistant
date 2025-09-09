/**
 * BotSettingsManager - Manages chatbot configuration settings
 * Extends BaseManager for common CRUD operations and localStorage persistence
 */
class BotSettingsManager extends BaseManager {
    constructor() {
        super('botSettings');
        this.initializeDefaultSettings();
    }

    /**
     * Initialize default bot settings
     */
    initializeDefaultSettings() {
        if (this.getAll().length === 0) {
            const defaultSettings = {
                // General Settings
                'bot-name': 'EduChat Assistant',
                'bot-language': 'en',
                'bot-timezone': 'UTC',
                'bot-status': 'active',
                'welcome-message': 'Hello! I\'m EduChat Assistant, your AI-powered guide to university information. How can I help you today?',
                'response-delay': 1,
                'max-response-length': 500,

                // Appearance Settings
                'theme': 'default',
                'primary-color': '#3b82f6',
                'secondary-color': '#64748b',
                'accent-color': '#10b981',
                'font-family': 'Inter',
                'font-size': 'medium',

                // Behavior Settings
                'typing-indicator': true,
                'suggestions': true,
                'auto-scroll': true,
                'sound-notifications': false,
                'temperature': 0.7,
                'max-tokens': 150,
                'context-window': 'medium',
                'fallback-message': 'I\'m sorry, I don\'t understand. Could you please rephrase your question or contact human support?',
                'escalate-unknown': true,

                // Integration Settings
                'webhook-url': '',
                'webhook-enabled': false,

                // Advanced Settings
                'cache-duration': 30,
                'rate-limit': 60,
                'input-sanitization': true,
                'rate-limiting': true,
                'session-timeout': false,
                'log-level': 'info',
                'conversation-logging': true,
                'performance-monitoring': true
            };

            this.saveSettings(defaultSettings);
        }
    }

    /**
     * Get all bot settings
     * @returns {Object} Object containing all settings
     */
    getSettings() {
        const settings = this.getAll();
        if (settings.length === 0) {
            this.initializeDefaultSettings();
            return this.getAll()[0] || {};
        }
        return settings[0] || {};
    }

    /**
     * Save bot settings
     * @param {Object} settings - The settings to save
     * @returns {Object} Result object with success status and message
     */
    saveSettings(settings) {
        try {
            // Validate required settings
            if (!settings['bot-name'] || settings['bot-name'].trim() === '') {
                return { success: false, message: 'Bot name is required' };
            }

            if (!settings['welcome-message'] || settings['welcome-message'].trim() === '') {
                return { success: false, message: 'Welcome message is required' };
            }

            // Validate numeric settings
            if (settings['response-delay'] && (settings['response-delay'] < 0 || settings['response-delay'] > 10)) {
                return { success: false, message: 'Response delay must be between 0 and 10 seconds' };
            }

            if (settings['max-response-length'] && (settings['max-response-length'] < 100 || settings['max-response-length'] > 2000)) {
                return { success: false, message: 'Max response length must be between 100 and 2000 characters' };
            }

            if (settings['max-tokens'] && (settings['max-tokens'] < 50 || settings['max-tokens'] > 500)) {
                return { success: false, message: 'Max tokens must be between 50 and 500' };
            }

            if (settings['temperature'] && (settings['temperature'] < 0 || settings['temperature'] > 1)) {
                return { success: false, message: 'Temperature must be between 0 and 1' };
            }

            if (settings['cache-duration'] && (settings['cache-duration'] < 5 || settings['cache-duration'] > 1440)) {
                return { success: false, message: 'Cache duration must be between 5 and 1440 minutes' };
            }

            if (settings['rate-limit'] && (settings['rate-limit'] < 10 || settings['rate-limit'] > 1000)) {
                return { success: false, message: 'Rate limit must be between 10 and 1000 requests per minute' };
            }

            // Validate URL if provided
            if (settings['webhook-url'] && settings['webhook-url'].trim() !== '') {
                try {
                    new URL(settings['webhook-url']);
                } catch {
                    return { success: false, message: 'Invalid webhook URL format' };
                }
            }

            // Get existing settings and merge with new ones
            const existingSettings = this.getSettings();
            const updatedSettings = { ...existingSettings, ...settings };
            updatedSettings.updatedAt = new Date().toISOString();

            // Save to localStorage
            this.save([updatedSettings]);

            return { success: true, message: 'Settings saved successfully' };
        } catch (error) {
            console.error('Error saving settings:', error);
            return { success: false, message: 'Failed to save settings' };
        }
    }

    /**
     * Reset settings to default values
     * @returns {Object} Result object with success status and message
     */
    resetSettings() {
        try {
            // Clear existing settings
            this.save([]);
            
            // Reinitialize with default settings
            this.initializeDefaultSettings();
            
            return { success: true, message: 'Settings reset to default successfully' };
        } catch (error) {
            console.error('Error resetting settings:', error);
            return { success: false, message: 'Failed to reset settings' };
        }
    }

    /**
     * Get a specific setting value
     * @param {string} key - The setting key
     * @returns {*} The setting value or null if not found
     */
    getSetting(key) {
        const settings = this.getSettings();
        return settings[key] || null;
    }

    /**
     * Update a specific setting
     * @param {string} key - The setting key
     * @param {*} value - The new value
     * @returns {Object} Result object with success status and message
     */
    updateSetting(key, value) {
        try {
            const settings = this.getSettings();
            settings[key] = value;
            settings.updatedAt = new Date().toISOString();

            this.save([settings]);
            return { success: true, message: 'Setting updated successfully' };
        } catch (error) {
            console.error('Error updating setting:', error);
            return { success: false, message: 'Failed to update setting' };
        }
    }

    /**
     * Get settings by category
     * @param {string} category - The category to filter by
     * @returns {Object} Object containing settings for the specified category
     */
    getSettingsByCategory(category) {
        const settings = this.getSettings();
        const categorySettings = {};

        const categoryMappings = {
            'general': ['bot-name', 'bot-language', 'bot-timezone', 'bot-status', 'welcome-message', 'response-delay', 'max-response-length'],
            'appearance': ['theme', 'primary-color', 'secondary-color', 'accent-color', 'font-family', 'font-size'],
            'behavior': ['typing-indicator', 'suggestions', 'auto-scroll', 'sound-notifications', 'temperature', 'max-tokens', 'context-window', 'fallback-message', 'escalate-unknown'],
            'integrations': ['webhook-url', 'webhook-enabled'],
            'advanced': ['cache-duration', 'rate-limit', 'input-sanitization', 'rate-limiting', 'session-timeout', 'log-level', 'conversation-logging', 'performance-monitoring']
        };

        const keys = categoryMappings[category] || [];
        keys.forEach(key => {
            if (settings.hasOwnProperty(key)) {
                categorySettings[key] = settings[key];
            }
        });

        return categorySettings;
    }

    /**
     * Export settings to JSON
     * @returns {string} JSON string of all settings
     */
    exportSettings() {
        try {
            const settings = this.getSettings();
            return JSON.stringify(settings, null, 2);
        } catch (error) {
            console.error('Error exporting settings:', error);
            return null;
        }
    }

    /**
     * Import settings from JSON
     * @param {string} jsonData - JSON string of settings
     * @returns {Object} Result object with success status and message
     */
    importSettings(jsonData) {
        try {
            const settings = JSON.parse(jsonData);
            
            if (typeof settings !== 'object' || settings === null) {
                return { success: false, message: 'Invalid settings format' };
            }

            const result = this.saveSettings(settings);
            return result;
        } catch (error) {
            console.error('Error importing settings:', error);
            return { success: false, message: 'Failed to import settings' };
        }
    }

    /**
     * Validate settings
     * @param {Object} settings - The settings to validate
     * @returns {Object} Result object with success status and validation errors
     */
    validateSettings(settings) {
        const errors = [];

        // Required fields
        if (!settings['bot-name'] || settings['bot-name'].trim() === '') {
            errors.push('Bot name is required');
        }

        if (!settings['welcome-message'] || settings['welcome-message'].trim() === '') {
            errors.push('Welcome message is required');
        }

        // Numeric validations
        if (settings['response-delay'] !== undefined && (settings['response-delay'] < 0 || settings['response-delay'] > 10)) {
            errors.push('Response delay must be between 0 and 10 seconds');
        }

        if (settings['max-response-length'] !== undefined && (settings['max-response-length'] < 100 || settings['max-response-length'] > 2000)) {
            errors.push('Max response length must be between 100 and 2000 characters');
        }

        if (settings['max-tokens'] !== undefined && (settings['max-tokens'] < 50 || settings['max-tokens'] > 500)) {
            errors.push('Max tokens must be between 50 and 500');
        }

        if (settings['temperature'] !== undefined && (settings['temperature'] < 0 || settings['temperature'] > 1)) {
            errors.push('Temperature must be between 0 and 1');
        }

        if (settings['cache-duration'] !== undefined && (settings['cache-duration'] < 5 || settings['cache-duration'] > 1440)) {
            errors.push('Cache duration must be between 5 and 1440 minutes');
        }

        if (settings['rate-limit'] !== undefined && (settings['rate-limit'] < 10 || settings['rate-limit'] > 1000)) {
            errors.push('Rate limit must be between 10 and 1000 requests per minute');
        }

        // URL validation
        if (settings['webhook-url'] && settings['webhook-url'].trim() !== '') {
            try {
                new URL(settings['webhook-url']);
            } catch {
                errors.push('Invalid webhook URL format');
            }
        }

        return {
            success: errors.length === 0,
            errors: errors
        };
    }

    /**
     * Get settings statistics
     * @returns {Object} Statistics object
     */
    getStats() {
        const settings = this.getSettings();
        const stats = {
            totalSettings: Object.keys(settings).length,
            categories: {
                general: 0,
                appearance: 0,
                behavior: 0,
                integrations: 0,
                advanced: 0
            },
            lastUpdated: settings.updatedAt || null
        };

        // Count settings by category
        Object.keys(settings).forEach(key => {
            if (key.includes('bot-') || key.includes('welcome') || key.includes('response')) {
                stats.categories.general++;
            } else if (key.includes('theme') || key.includes('color') || key.includes('font')) {
                stats.categories.appearance++;
            } else if (key.includes('indicator') || key.includes('suggestions') || key.includes('temperature')) {
                stats.categories.behavior++;
            } else if (key.includes('webhook') || key.includes('integration')) {
                stats.categories.integrations++;
            } else if (key.includes('cache') || key.includes('rate') || key.includes('log')) {
                stats.categories.advanced++;
            }
        });

        return stats;
    }

    /**
     * Check if a setting is enabled
     * @param {string} key - The setting key
     * @returns {boolean} True if the setting is enabled, false otherwise
     */
    isEnabled(key) {
        const value = this.getSetting(key);
        return value === true || value === 'true' || value === 'enabled' || value === 'active';
    }

    /**
     * Get theme configuration
     * @returns {Object} Theme configuration object
     */
    getThemeConfig() {
        const settings = this.getSettings();
        return {
            theme: settings['theme'] || 'default',
            primaryColor: settings['primary-color'] || '#3b82f6',
            secondaryColor: settings['secondary-color'] || '#64748b',
            accentColor: settings['accent-color'] || '#10b981',
            fontFamily: settings['font-family'] || 'Inter',
            fontSize: settings['font-size'] || 'medium'
        };
    }

    /**
     * Get behavior configuration
     * @returns {Object} Behavior configuration object
     */
    getBehaviorConfig() {
        const settings = this.getSettings();
        return {
            typingIndicator: this.isEnabled('typing-indicator'),
            suggestions: this.isEnabled('suggestions'),
            autoScroll: this.isEnabled('auto-scroll'),
            soundNotifications: this.isEnabled('sound-notifications'),
            temperature: parseFloat(settings['temperature']) || 0.7,
            maxTokens: parseInt(settings['max-tokens']) || 150,
            contextWindow: settings['context-window'] || 'medium',
            fallbackMessage: settings['fallback-message'] || 'I\'m sorry, I don\'t understand.',
            escalateUnknown: this.isEnabled('escalate-unknown')
        };
    }
}
