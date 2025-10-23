class BotSettingsManager {
    constructor() {
        this.endpoints = {
            get: '/api/bot/settings',
            update: '/api/bot/settings/update',
            reset: '/api/bot/settings/reset'
        };
        this.cache = null;
        this.init();
    }

    async init() {
        await this.loadSettings();
        this.bindUI();
    }

    transformCustomPayload(custom) {
        const transformed = {};
        if (custom.hasOwnProperty('botName')) transformed.bot_name = String(custom.botName || '').trim();
        if (custom.hasOwnProperty('welcomeMessage')) transformed.welcome_message = String(custom.welcomeMessage || '');
        if (custom.hasOwnProperty('responseTimeout')) transformed.response_timeout = parseInt(custom.responseTimeout || 30, 10);
        if (custom.hasOwnProperty('showTypingIndicator')) transformed.show_typing_indicator = !!custom.showTypingIndicator;
        if (custom.hasOwnProperty('showSuggestedQuestions')) transformed.show_suggested_questions = !!custom.showSuggestedQuestions;
        if (custom.hasOwnProperty('tone')) transformed.tone_of_voice = String(custom.tone || 'Professional');
        if (custom.hasOwnProperty('customGreetings')) transformed.custom_greetings = String(custom.customGreetings || '');
        if (custom.hasOwnProperty('primaryColor')) transformed.primary_color = String(custom.primaryColor || '#3B82F6');
        if (custom.hasOwnProperty('confidenceThreshold')) {
            const ct = parseFloat(custom.confidenceThreshold);
            transformed.confidence_threshold = isNaN(ct) ? 0.7 : (ct > 1 ? ct / 100.0 : ct);
        }
        if (custom.hasOwnProperty('botAvatar')) transformed.bot_avatar = String(custom.botAvatar || '');
        return transformed;
    }

    getEl(id) {
        return document.getElementById(id);
    }

    readForm() {
        const suggestedMessages = this.collectSuggestedMessages();
        return {
            bot_name: this.getEl('bot-name')?.value?.trim() || '',
            bot_avatar: this.getEl('bot-avatar-url')?.value || (this.cache?.bot_avatar || '/static/images/bot-icon.png'),
            welcome_message: this.getEl('welcome-message')?.value || '',
            response_timeout: parseInt(this.getEl('response-timeout')?.value || 30, 10),
            show_typing_indicator: !!document.querySelector('#show-typing-indicator')?.checked,
            show_suggested_questions: !!document.querySelector('#show-suggested-questions')?.checked,
            tone_of_voice: (document.querySelector('input[name="tone"]:checked')?.value || 'Professional'),
            custom_greetings: this.getEl('custom-greetings')?.value || '',
            primary_color: this.getEl('primary-color')?.value || '#3B82F6',
            confidence_threshold: this.normalizeConfidence(this.getEl('confidence-threshold')?.value),
            suggested_messages: suggestedMessages,
            office_specific_messages: this.collectOfficeMessages(),
        };
    }

    normalizeConfidence(value) {
        const v = parseFloat(value || '0.7');
        if (v > 1) return v / 100.0;
        if (v < 0) return 0.0;
        return v;
    }

    collectOfficeMessages() {
        // Example: extend later to read dynamic key-value UI
        const items = document.querySelectorAll('.office-message-item');
        const map = {};
        items.forEach(item => {
            const label = item.querySelector('label')?.textContent?.trim();
            const value = item.querySelector('textarea')?.value || '';
            if (label) map[label] = value;
        });
        return map;
    }

    collectSuggestedMessages() {
        const list = [];
        document.querySelectorAll('.category-group').forEach(group => {
            // Prefer the editable title text so renamed categories are saved
            const titleEl = group.querySelector('.category-header .editable-title');
            const titleText = titleEl ? (titleEl.textContent || '').trim() : '';
            const category = titleText || group.getAttribute('data-category') || 'General';
            const messages = [];
            group.querySelectorAll('.category-message .editable-content').forEach(span => {
                const text = span.textContent.trim();
                if (text) messages.push(text);
            });
            if (messages.length) list.push({ category, messages });
        });
        return list;
    }

    async loadSettings() {
        try {
            const res = await fetch(this.endpoints.get);
            const data = await res.json();
            this.cache = data || {};
            this.populateForm(this.cache);
        } catch (e) {
            console.error('Failed to load settings', e);
            if (window.toast) toast.error('Failed to load settings');
        }
    }

    populateForm(settings) {
        if (!settings) return;
        const el = (id) => this.getEl(id);
        if (el('bot-name')) el('bot-name').value = settings.bot_name || 'TCC Assistant';
        if (el('welcome-message')) el('welcome-message').value = settings.welcome_message || '';
        if (el('response-timeout')) {
            el('response-timeout').value = parseInt(settings.response_timeout ?? 30, 10);
            const slider = el('response-timeout');
            const label = document.getElementById('timeout-value');
            if (label) label.textContent = `Current: ${slider.value}s`;
        }
        const typingCb = document.getElementById('show-typing-indicator');
        if (typingCb) typingCb.checked = !!settings.show_typing_indicator;
        const suggestedCb = document.getElementById('show-suggested-questions');
        if (suggestedCb) suggestedCb.checked = !!settings.show_suggested_questions;

        if (settings.tone_of_voice) {
            const radio = document.querySelector(`input[name="tone"][value="${settings.tone_of_voice}"]`);
            if (radio) radio.checked = true;
        }

        if (el('custom-greetings')) el('custom-greetings').value = settings.custom_greetings || '';
        if (el('primary-color')) {
            el('primary-color').value = settings.primary_color || '#3B82F6';
            const summary = document.getElementById('summary-color');
            if (summary) summary.textContent = el('primary-color').value;
            this.applyTheme(el('primary-color').value);
        }

        if (el('confidence-threshold')) {
            const ct = typeof settings.confidence_threshold === 'number' ? Math.round(settings.confidence_threshold * 100) : 70;
            el('confidence-threshold').value = ct;
            const label = document.getElementById('confidence-value');
            if (label) label.textContent = `${ct}%`;
            const summary = document.getElementById('summary-confidence');
            if (summary) summary.textContent = `${ct}%`;
        }

        const summaryName = document.getElementById('summary-bot-name');
        if (summaryName && el('bot-name')) summaryName.textContent = el('bot-name').value;
    }

    bindUI() {
        const saveBtn = document.querySelector('[onclick="saveSettings()"]');
        const resetBtn = document.querySelector('[onclick="resetSettings()"]');
        if (saveBtn) saveBtn.addEventListener('click', (e) => { e.preventDefault(); this.saveSettings(); });
        if (resetBtn) resetBtn.addEventListener('click', (e) => { e.preventDefault(); this.resetSettings(); });

        const color = this.getEl('primary-color');
        if (color) color.addEventListener('change', (e) => this.applyTheme(e.target.value));
    }

    applyTheme(color) {
        if (!color) return;
        document.documentElement.style.setProperty('--primary-color', color);
    }

    async saveSettings(customPayload = null) {
        try {
            const payload = customPayload ? this.transformCustomPayload(customPayload) : this.readForm();
            const res = await fetch(this.endpoints.update, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (res.ok && data.success) {
                if (window.toast) toast.success(data.message || 'Settings saved');
                this.cache = { ...this.cache, ...payload };
            } else {
                if (window.toast) toast.error(data.message || 'Failed to save settings');
            }
            return data;
        } catch (e) {
            console.error('Save settings failed', e);
            if (window.toast) toast.error('Failed to save settings');
            return { success: false };
        }
    }

    async resetSettings() {
        try {
            const res = await fetch(this.endpoints.reset, { method: 'POST' });
            const data = await res.json();
            if (res.ok && data.success) {
                if (window.toast) toast.success(data.message || 'Settings reset to default');
                await this.loadSettings();
            } else {
                if (window.toast) toast.error(data.message || 'Failed to reset settings');
            }
            return data;
        } catch (e) {
            console.error('Reset settings failed', e);
            if (window.toast) toast.error('Failed to reset settings');
            return { success: false };
        }
    }
}

window.BotSettingsManager = BotSettingsManager;
