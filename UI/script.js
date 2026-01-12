/**
 * KIIT Academic Assistant - Frontend Script
 * 
 * Responsibilities:
 * - Manage chat UI interactions
 * - Handle API communication with backend
 * - Render messages and responses
 * - Manage quick action buttons
 */

// =====================================================
// CONFIGURATION & CONSTANTS
// =====================================================

const CONFIG = {
    API_BASE_URL: 'http://localhost:8000/api', // Update with your backend URL
    ENDPOINTS: {
        CHAT: '/chat',
        EXAM_SCHEDULE: '/exam-schedule',
        SYLLABUS: '/syllabus',
        FACULTY_INFO: '/faculty-info',
        REGULATIONS: '/regulations'
    },
    QUICK_ACTIONS: {
        'exam-schedule': {
            label: 'Exam Schedule',
            query: 'What is the exam schedule?'
        },
        'syllabus': {
            label: 'CSE Syllabus',
            query: 'Show me the CSE syllabus'
        },
        'faculty': {
            label: 'Faculty Info',
            query: 'Who are the CSE faculty members?'
        },
        'regulations': {
            label: 'Regulations',
            query: 'What are the academic regulations?'
        }
    }
};

// =====================================================
// DOM ELEMENTS
// =====================================================

const chatContainer = document.getElementById('chatContainer');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const refreshBtn = document.getElementById('refreshBtn');
const typingIndicator = document.getElementById('typingIndicator');
const quickActionBtns = document.querySelectorAll('.quick-btn');

// =====================================================
// STATE MANAGEMENT
// =====================================================

const state = {
    isLoading: false,
    messages: [],
    conversationHistory: []
};

// =====================================================
// INITIALIZATION
// =====================================================

document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
});

function initializeEventListeners() {
    // Send button click
    sendBtn.addEventListener('click', sendMessage);

    // Enter key to send (Shift+Enter for new line)
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Refresh conversation
    refreshBtn.addEventListener('click', resetConversation);

    // Quick action buttons
    quickActionBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const action = e.currentTarget.dataset.action;
            handleQuickAction(action);
        });
    });

    // Auto-adjust textarea height
    userInput.addEventListener('input', autoResizeTextarea);
}

/**
 * Auto-resize textarea based on content
 */
function autoResizeTextarea() {
    userInput.style.height = 'auto';
    userInput.style.height = Math.min(userInput.scrollHeight, 120) + 'px';
}

// =====================================================
// MESSAGE HANDLING
// =====================================================

/**
 * Send message to backend
 */
async function sendMessage() {
    const query = userInput.value.trim();

    if (!query || state.isLoading) {
        return;
    }

    // Add user message to UI
    addMessageToUI('user', query);

    // Clear input
    userInput.value = '';
    userInput.style.height = 'auto';

    // Show typing indicator
    showTypingIndicator();
    setLoadingState(true);

    try {
        // Send request to backend
        const response = await sendChatRequest(query);

        // Hide typing indicator
        hideTypingIndicator();

        // Add assistant response to UI
        addMessageToUI('assistant', response.answer, response.sources);

        // Store in conversation history
        state.conversationHistory.push({
            role: 'user',
            content: query
        });
        state.conversationHistory.push({
            role: 'assistant',
            content: response.answer,
            sources: response.sources
        });

    } catch (error) {
        hideTypingIndicator();
        addMessageToUI('assistant', `Error: ${error.message}. Please check if the backend is running.`);
    } finally {
        setLoadingState(false);
        userInput.focus();
    }
}

/**
 * Send chat request to backend API
 * 
 * @param {string} query - User query
 * @returns {Promise<{answer: string, sources: string[]}>}
 */
async function sendChatRequest(query) {
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.CHAT}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                query: query
            })
        });

        if (!response.ok) {
            throw new Error(`Server responded with status ${response.status}`);
        }

        const data = await response.json();

        // Validate response format
        if (!data.answer) {
            throw new Error('Invalid response format from backend');
        }

        return {
            answer: data.answer,
            sources: data.sources || []
        };

    } catch (error) {
        console.error('API Error:', error);
        throw new Error(error.message || 'Failed to connect to backend');
    }
}

/**
 * Handle quick action button clicks
 * 
 * @param {string} action - Action key
 */
function handleQuickAction(action) {
    const actionConfig = CONFIG.QUICK_ACTIONS[action];
    if (actionConfig) {
        userInput.value = actionConfig.query;
        autoResizeTextarea();
        userInput.focus();
        // Optionally auto-send
        // sendMessage();
    }
}

// =====================================================
// UI RENDERING
// =====================================================

/**
 * Add message to chat UI
 * 
 * @param {string} role - 'user' or 'assistant'
 * @param {string} content - Message content
 * @param {Array<string>} sources - Optional sources/references
 */
function addMessageToUI(role, content, sources = []) {
    const messageEl = document.createElement('div');
    messageEl.className = `message ${role}`;

    // Avatar
    const avatarEl = document.createElement('div');
    avatarEl.className = 'message-avatar';
    
    if (role === 'user') {
        avatarEl.innerHTML = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>';
    } else {
        avatarEl.innerHTML = '<svg viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 2" stroke="white" stroke-width="2" fill="none"/></svg>';
    }

    // Content wrapper
    const contentEl = document.createElement('div');
    contentEl.className = 'message-content';

    // Message bubble
    const bubbleEl = document.createElement('div');
    bubbleEl.className = 'message-bubble';
    bubbleEl.textContent = content;

    contentEl.appendChild(bubbleEl);

    // Sources (if provided)
    if (sources && sources.length > 0 && role === 'assistant') {
        const sourceEl = document.createElement('div');
        sourceEl.className = 'message-source';
        sourceEl.innerHTML = `<strong>Source:</strong> ${sources.join(', ')}`;
        contentEl.appendChild(sourceEl);
    }

    // Timestamp
    const timeEl = document.createElement('div');
    timeEl.className = 'message-time';
    timeEl.textContent = getFormattedTime();
    contentEl.appendChild(timeEl);

    messageEl.appendChild(avatarEl);
    messageEl.appendChild(contentEl);

    chatContainer.appendChild(messageEl);

    // Scroll to bottom
    scrollToBottom();
}

/**
 * Show typing indicator
 */
function showTypingIndicator() {
    typingIndicator.classList.add('active');
    scrollToBottom();
}

/**
 * Hide typing indicator
 */
function hideTypingIndicator() {
    typingIndicator.classList.remove('active');
}

/**
 * Get formatted time string
 * 
 * @returns {string}
 */
function getFormattedTime() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    return `${hours}:${minutes}`;
}

/**
 * Scroll chat container to bottom
 */
function scrollToBottom() {
    setTimeout(() => {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }, 0);
}

// =====================================================
// STATE & CONTROL
// =====================================================

/**
 * Set loading state
 * 
 * @param {boolean} isLoading
 */
function setLoadingState(isLoading) {
    state.isLoading = isLoading;
    userInput.disabled = isLoading;
    sendBtn.disabled = isLoading;
    quickActionBtns.forEach(btn => btn.disabled = isLoading);
}

/**
 * Reset conversation
 */
function resetConversation() {
    // Clear all messages
    chatContainer.innerHTML = `
        <div class="welcome-section">
            <div class="book-icon">
                <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
                    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
                </svg>
            </div>
            <h2 class="welcome-title">Hello! I'm your KIIT Academic Counselor</h2>
            <p class="welcome-text">I can help with syllabus queries, regulations, and subject information.</p>
        </div>
    `;

    // Reset state
    state.messages = [];
    state.conversationHistory = [];
    userInput.value = '';
    userInput.style.height = 'auto';
    hideTypingIndicator();
    setLoadingState(false);
    userInput.focus();

    scrollToBottom();
}

// =====================================================
// EXPORT FOR DEBUGGING (Optional)
// =====================================================

// Expose state and functions for debugging in console if needed
window.ChatApp = {
    state,
    sendMessage,
    resetConversation,
    config: CONFIG
};
