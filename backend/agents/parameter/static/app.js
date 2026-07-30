document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const typingIndicator = document.getElementById('typing-indicator');
    const pulse = document.querySelector('.pulse');
    const statusText = document.getElementById('session-status');
    const stateShape = document.getElementById('state-shape');
    const stateParams = document.getElementById('state-params');

    let sessionId = null;
    let isProcessing = false;

    // Helper to scroll to bottom
    const scrollToBottom = () => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    // Helper to add a message to chat
    const appendMessage = (content, sender, isStatus = false) => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message ${isStatus ? 'status-message' : ''}`;
        
        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        bubble.textContent = content;
        
        messageDiv.appendChild(bubble);
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    };

    // Update UI state
    const setProcessing = (processing) => {
        isProcessing = processing;
        messageInput.disabled = processing;
        sendButton.disabled = processing;
        
        if (processing) {
            typingIndicator.classList.remove('hidden');
            pulse.classList.add('active');
            statusText.textContent = 'Thinking...';
            scrollToBottom();
        } else {
            typingIndicator.classList.add('hidden');
            pulse.classList.remove('active');
            statusText.textContent = sessionId ? 'Active Session' : 'Idle';
            messageInput.focus();
        }
    };

    // Update sidebar state
    const updateSidebarState = (shape, parameters) => {
        if (shape) {
            stateShape.textContent = shape;
        }

        if (parameters && Object.keys(parameters).length > 0) {
            stateParams.innerHTML = '';
            for (const [key, value] of Object.entries(parameters)) {
                const li = document.createElement('li');
                li.innerHTML = `<span class="param-name">${key}</span><span class="param-val">${value}</span>`;
                stateParams.appendChild(li);
            }
        } else {
            stateParams.innerHTML = '<li class="empty-params">None collected</li>';
        }
    };

    // API Call wrapper
    const makeApiCall = async (endpoint, payload) => {
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Network response was not ok');
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            appendMessage(`Error: ${error.message}. Try again.`, 'assistant');
            setProcessing(false);
            return null;
        }
    };

    // Handle Form Submit
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const message = messageInput.value.trim();
        if (!message || isProcessing) return;

        // Clear input and append user message
        messageInput.value = '';
        appendMessage(message, 'user');
        setProcessing(true);

        let endpoint, payload;

        if (!sessionId) {
            // Start a new session
            endpoint = '/start';
            payload = { message: message };
        } else {
            // Continue existing session
            endpoint = '/continue';
            payload = { session_id: sessionId, message: message };
        }

        const data = await makeApiCall(endpoint, payload);

        if (data) {
            if (data.status === 'waiting') {
                // Ongoing dialogue
                sessionId = data.session_id;
                appendMessage(data.reply, 'assistant');
                // We don't have the current state in the response for 'waiting', 
                // but the prompt is asked. We can assume the shape from earlier.
            } else if (data.shape && data.parameters) {
                // Completed
                sessionId = null; // Reset session
                updateSidebarState(data.shape, data.parameters);
                appendMessage(`Success! Gathered all parameters for ${data.shape}.`, 'assistant', true);
                
                // Show a summary of parameters
                const paramSummary = Object.entries(data.parameters)
                    .map(([k, v]) => `${k}: ${v}`)
                    .join(', ');
                appendMessage(`Final configuration: ${paramSummary}`, 'assistant');
                
                // Prompt for next action
                setTimeout(() => {
                    appendMessage("What would you like to create next?", 'assistant');
                }, 1000);
            }
        }

        setProcessing(false);
    });
});
