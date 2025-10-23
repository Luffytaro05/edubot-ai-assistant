# Suggested Topics Hide/Show Fix

## Issue Summary
The chatbot's **suggested questions and suggested topics** were remaining visible even after users started chatting. They should only appear in the initial state and when the conversation is reset.

## Problem Identified
In `static/app.js`, the `updateChatText()` function was **always rendering** the greeting message and suggested topics at the top of the chat, regardless of whether the user had sent any messages.

### Code Location
- **File:** `static/app.js`
- **Function:** `updateChatText()` (line 1944)
- **Template HTML:** `templates/base.html` (lines 515-629)

## Changes Made

### Before (Lines 1944-1986)
```javascript
updateChatText() {
    const welcome = (this.botSettings && this.botSettings.welcome_message) ? this.botSettings.welcome_message : "Hi there! I'm your TCC Connect assistant. How can I help you today?";
    const showSuggestions = this.suggestionsEnabled();

    // Greeting and suggestions were ALWAYS rendered
    let html = `
        <div class="chatbox__greeting">
            <p>${welcome}</p>
        </div>
        ${showSuggestions ? `<div class=\"suggestions-label\">Suggested topics:</div>` : ''}
        ${showSuggestions ? `<div class=\"chatbox__suggestions\">${suggestedContent}</div>` : `<div class=\"chatbox__suggestions\" style=\"display:none\"></div>`}
        ...
    `;
```

### After (Lines 1944-1991)
```javascript
updateChatText() {
    const welcome = (this.botSettings && this.botSettings.welcome_message) ? this.botSettings.welcome_message : "Hi there! I'm your TCC Connect assistant. How can I help you today?";
    const showSuggestions = this.suggestionsEnabled();

    // ✅ Only show greeting and main suggestions when there are NO messages
    const hasMessages = this.messages.length > 0;

    // Greeting and suggestions now only show when chat is empty
    let html = `
        ${!hasMessages ? `
        <div class="chatbox__greeting">
            <p>${welcome}</p>
        </div>
        ` : ''}
        ${!hasMessages && showSuggestions ? `<div class=\"suggestions-label\">Suggested topics:</div>` : ''}
        ${!hasMessages && showSuggestions ? `<div class=\"chatbox__suggestions\">${suggestedContent}</div>` : `<div class=\"chatbox__suggestions\" style=\"display:none\"></div>`}
        ...
    `;
```

## How It Works Now

### 1️⃣ **Initial State (No Messages)**
- ✅ Greeting message is **visible**
- ✅ "Suggested topics:" label is **visible**
- ✅ Suggested topic buttons are **visible** (Admission Office, Registrar Office, ICT Office, etc.)

### 2️⃣ **After User Sends First Message**
- ❌ Greeting message **disappears**
- ❌ "Suggested topics:" label **disappears**
- ❌ Suggested topic buttons **disappear**
- ✅ Only chat messages remain visible

### 3️⃣ **When User Clicks Reset**
- The `resetContext()` function clears the messages array
- `updateChatText()` is called again
- Since `this.messages.length === 0`, greeting and suggestions **reappear**

### 4️⃣ **When User Clicks Clear History**
- The `clearHistory()` function clears all messages
- `updateChatText()` is called again
- Greeting and suggestions **reappear**

## Benefits
✅ **Cleaner UI:** Chat area is not cluttered with initial suggestions during conversation  
✅ **Better UX:** Users can focus on the conversation without distractions  
✅ **Consistent Behavior:** Suggestions only appear when relevant (initial state or after reset)  
✅ **No Breaking Changes:** All existing functionality remains intact  

## Testing Recommendations
1. ✅ Open chatbot - verify greeting and suggested topics appear
2. ✅ Click a suggested topic or type a message - verify they disappear
3. ✅ Click the "Reset Conversation" button - verify they reappear
4. ✅ Click the "Clear History" button - verify they reappear
5. ✅ Close and reopen chatbot - verify behavior is consistent

## Files Modified
- `static/app.js` - Updated `updateChatText()` function

## Files Unchanged
- `templates/base.html` - No changes needed (static HTML is replaced by JavaScript)

---

**Status:** ⚠️ **SUPERSEDED by INLINE_SUGGESTIONS_IMPLEMENTATION.md**  
**Date:** October 16, 2025  
**Issue Type:** UI/UX Enhancement

---

## ⚠️ UPDATE

This fix has been **superseded** by a better implementation. See `INLINE_SUGGESTIONS_IMPLEMENTATION.md` for the current implementation where:
- Suggestions now appear **BELOW bot responses** (not at the top)
- Better user experience with inline contextual suggestions
- Cleaner chat interface

