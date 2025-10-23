# Change Password Function Fix - Feedback & Usage Pages

## Problem Identified

The "Change Password" button was **not working** on the Feedback and Usage Statistics pages in the Admin Interface. The form would submit but nothing would happen.

### Root Cause

There were **two separate `DOMContentLoaded` event listeners** in each file:

1. **First listener**: Initialized `authManager` 
2. **Second listener**: Set up the change password form handler

This caused a **race condition** where:
- The second `DOMContentLoaded` might execute before or after the first one
- The form handler tried to access `authManager.getToken()` but `authManager` might not be initialized yet
- Multiple event listeners can execute in unpredictable order

#### feedback.html (Before - BROKEN):
```javascript
// First DOMContentLoaded (line 409)
document.addEventListener('DOMContentLoaded', async function() {
    authManager = new AuthManager();
    // ... initialization
});

// Second DOMContentLoaded (line 491) - SEPARATE!
document.addEventListener('DOMContentLoaded', function() {
    const changePasswordForm = document.getElementById('changePasswordForm');
    changePasswordForm.addEventListener('submit', async function(e) {
        const token = authManager.getToken(); // ❌ May be undefined!
        // ...
    });
});
```

---

## Solution Implemented

### Files Modified

1. **templates/feedback.html**
2. **templates/usage.html**

### Changes Made

**Consolidated all initialization into a single `DOMContentLoaded` listener** and created a separate `setupChangePasswordForm()` function that's called after `authManager` is initialized.

#### After (Fixed):

```javascript
// Single DOMContentLoaded
document.addEventListener('DOMContentLoaded', async function() {
    authManager = new AuthManager();
    if (!authManager.checkAuth()) {
        window.location.href = '/admin/index';
        return;
    }

    // ... other initialization
    
    // Setup change password form handler AFTER authManager is ready
    setupChangePasswordForm();  // ✅ Called after authManager initialized
});

// Separate function for form setup
function setupChangePasswordForm() {
    const changePasswordForm = document.getElementById('changePasswordForm');
    if (changePasswordForm) {
        changePasswordForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // ... validation ...
            
            try {
                const token = authManager.getToken(); // ✅ Works now!
                if (!token) {
                    showToast('Please login again', 'error');
                    return;
                }

                const response = await fetch('/api/auth/change-password', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        currentPassword: currentPassword,
                        newPassword: newPassword
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    showToast('Password changed successfully!', 'success');
                    closeChangePasswordModal();
                } else {
                    showToast(data.message || 'Failed to change password', 'error');
                }
            } catch (error) {
                console.error('Error changing password:', error);
                showToast('An error occurred while changing password', 'error');
            }
        });
    }
}
```

---

## How It Works Now

### Initialization Flow:

1. **Page Loads** → Single `DOMContentLoaded` event fires
2. **AuthManager Initialized** → `authManager = new AuthManager()`
3. **Authentication Check** → Verifies user is logged in
4. **Other Managers Initialized** → `usageStatsManager`, charts, etc.
5. **Form Handler Setup** → `setupChangePasswordForm()` is called
6. **Form Ready** → Change password form is now fully functional

### Change Password Flow:

1. **User clicks "Change Password"** → Modal opens
2. **User fills form** → Current password, new password, confirm
3. **Form validates**:
   - New password ≥ 8 characters
   - New password matches confirmation
   - New password ≠ current password
4. **Form submits** → Calls `authManager.getToken()` (now available!)
5. **API Request** → Sends to `/api/auth/change-password` with JWT token
6. **Success** → Shows success toast, closes modal
7. **Error** → Shows error toast with specific message

---

## Testing the Fix

### To verify the change password is working:

#### On Feedback Page:

1. Login to Admin Interface
2. Navigate to **Feedback** page (`/feedback`)
3. Click **user avatar** in top-right corner
4. Click **"Change Password"** from dropdown
5. Fill in the form:
   - Current Password: (your current password)
   - New Password: (min 8 characters)
   - Confirm New Password: (must match)
6. Click **"Change Password"** button
7. ✅ Verify:
   - Success toast appears: "Password changed successfully!"
   - Modal closes automatically
   - Password is actually changed (try logging out and back in with new password)

#### On Usage Statistics Page:

Repeat the same steps on the **Usage Statistics** page (`/usage`)

### Test Error Scenarios:

1. **Short password** (< 8 chars):
   - ✅ Should show: "Password must be at least 8 characters long"

2. **Passwords don't match**:
   - ✅ Should show: "New passwords do not match"

3. **New password same as current**:
   - ✅ Should show: "New password must be different from current password"

4. **Wrong current password**:
   - ✅ Should show: "Current password is incorrect" (from backend)

---

## Benefits of This Fix

### Before (Multiple DOMContentLoaded):

```javascript
// ❌ PROBLEMS:
// 1. Race condition - which runs first?
// 2. Unpredictable execution order
// 3. Form handler may access uninitialized authManager
// 4. Hard to debug timing issues

document.addEventListener('DOMContentLoaded', async function() {
    authManager = new AuthManager(); // Async operation
});

document.addEventListener('DOMContentLoaded', function() {
    // This might run before authManager is ready!
    setupForm(); 
});
```

### After (Single DOMContentLoaded + Sequential Setup):

```javascript
// ✅ ADVANTAGES:
// 1. Predictable execution order
// 2. Guaranteed authManager is ready before form setup
// 3. Clear initialization sequence
// 4. Easy to understand and maintain

document.addEventListener('DOMContentLoaded', async function() {
    authManager = new AuthManager();
    // ... wait for initialization ...
    setupChangePasswordForm(); // Called after authManager ready
});

function setupChangePasswordForm() {
    // authManager is guaranteed to be initialized here
}
```

---

## Best Practices Applied

### ✅ Single Initialization Point

Instead of multiple `DOMContentLoaded` listeners, use one initialization function that orchestrates all setup in the correct order.

### ✅ Explicit Function Calls

Rather than relying on event listener order, explicitly call setup functions when their dependencies are ready:

```javascript
document.addEventListener('DOMContentLoaded', async function() {
    // Step 1: Initialize core dependencies
    authManager = new AuthManager();
    
    // Step 2: Initialize dependent systems
    usageStatsManager = new UsageStatsManager();
    
    // Step 3: Setup UI components that need managers
    setupChangePasswordForm(); // ✅ Knows authManager is ready
});
```

### ✅ Separation of Concerns

By extracting `setupChangePasswordForm()` into its own function:
- Code is more readable
- Function can be tested independently
- Clear responsibility boundary
- Easier to maintain

---

## Related Code Structure

This fix brings **feedback.html** and **usage.html** in line with other admin pages that already follow this pattern:

### ✅ dashboard.html (Already correct):
```javascript
document.addEventListener('DOMContentLoaded', async function() {
    authManager = new AuthManager();
    usageStatsManager = new UsageStatsManager();
    await initializeDashboard();
    setupEventListeners();
});
```

### ✅ Now feedback.html and usage.html follow the same pattern:
```javascript
document.addEventListener('DOMContentLoaded', async function() {
    authManager = new AuthManager();
    // ... other initialization ...
    setupChangePasswordForm(); // ✅ Sequential setup
});
```

---

## Summary of All Fixes

### Issue 1: Logout Not Working (Previous Fix)
- **Problem**: `authManager` scoped inside `DOMContentLoaded`
- **Solution**: Declared `authManager` as global variable

### Issue 2: showToast Not Defined (Previous Fix)
- **Problem**: `showToast()` function missing
- **Solution**: Added `showToast()` function definition

### Issue 3: Change Password Not Working (This Fix)
- **Problem**: Multiple `DOMContentLoaded` listeners causing race condition
- **Solution**: Consolidated into single listener with sequential setup

---

## Impact

✅ **Change Password works on Feedback page**
✅ **Change Password works on Usage Statistics page**
✅ **Proper validation and error messages**
✅ **No race conditions**
✅ **Predictable initialization order**
✅ **Consistent pattern across all admin pages**
✅ **Better code maintainability**

---

---

## Additional Fix: Missing Modal CSS

### Third Issue Discovered

After fixing the initialization sequence, the change password modal still wouldn't appear when clicking the button. The modal HTML was present but invisible.

### Root Cause

The **modal CSS was completely missing** from both `feedback.html` and `usage.html`. While the dashboard.html had the proper modal styling, these files were missing:

- `.modal-overlay` - The dark background overlay
- `.modal-container` - The white modal box
- `.modal-header`, `.modal-body`, `.modal-footer` - Modal structure
- `.form-control`, `.password-input-group` - Form styling
- `.btn`, `.btn-primary`, `.btn-secondary` - Button styles
- Animation styles for fade-in and slide-up effects

Without these CSS rules, when `openChangePasswordModal()` set `display: flex`, the modal had no visual styling and remained invisible.

### Solution

Added the complete modal CSS (200+ lines) to both files, copied from dashboard.html:

```css
/* Change Password Modal Styles */
.modal-overlay {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    z-index: 9999;
    align-items: center;
    justify-content: center;
    animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

.modal-container {
    background: white;
    border-radius: 12px;
    width: 90%;
    max-width: 500px;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
    animation: slideUp 0.3s ease;
}

/* ... and all other modal styles ... */
```

This CSS provides:
- **Modal overlay**: Dark semi-transparent background covering the page
- **Modal container**: White centered box with rounded corners and shadow
- **Animations**: Smooth fade-in for overlay, slide-up for modal
- **Form styling**: Input fields, password toggle buttons, labels
- **Button styling**: Primary (blue) and secondary (gray) buttons
- **Responsive design**: Works on mobile and desktop

---

## Date Fixed
October 10, 2025

## Complete Fix Summary
- **Fix 1**: AuthManager scope (global variable)
- **Fix 2**: showToast function definition  
- **Fix 3**: Consolidated DOMContentLoaded and sequential initialization
- **Fix 4**: Added complete modal CSS styling (200+ lines)

