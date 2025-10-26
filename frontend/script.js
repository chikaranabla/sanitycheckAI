// Get DOM elements
const uploadForm = document.getElementById('uploadForm');
const startChatBtn = document.getElementById('startChatBtn');
const sendMessageBtn = document.getElementById('sendMessageBtn');
const chatInput = document.getElementById('chatInput');
const newSessionBtn = document.getElementById('newSessionBtn');
const retryBtn = document.getElementById('retryBtn');

const uploadSection = document.getElementById('uploadSection');
const loadingSection = document.getElementById('loadingSection');
const chatSection = document.getElementById('chatSection');
const errorSection = document.getElementById('errorSection');

const chatMessages = document.getElementById('chatMessages');
const protocolName = document.getElementById('protocolName');
const errorMessage = document.getElementById('errorMessage');

// Global state
let currentSessionId = null;

// Section display management
function showSection(section) {
    uploadSection.style.display = 'none';
    loadingSection.style.display = 'none';
    chatSection.style.display = 'none';
    errorSection.style.display = 'none';
    
    section.style.display = 'block';
}

// Upload form submission
uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const protocolFile = document.getElementById('protocolFile').files[0];
    
    if (!protocolFile) {
        showError('Please select a protocol file.');
        return;
    }
    
    // Show loading
    showSection(loadingSection);
    
    try {
        // Create FormData
        const formData = new FormData();
        formData.append('protocol_file', protocolFile);
        
        // API request
        const response = await fetch('/api/chat/start', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Server error occurred');
        }
        
        const result = await response.json();
        
        // Store session ID
        currentSessionId = result.session_id;
        
        // Update protocol name
        protocolName.textContent = `Protocol: ${result.protocol_name}`;
        
        // Clear chat messages
        chatMessages.innerHTML = '';
        
        // Add initial AI message
        addMessage('assistant', result.message);
        
        // Show chat section
        showSection(chatSection);
        
        // Focus on input
        chatInput.focus();
        
    } catch (error) {
        console.error('Error:', error);
        showError(error.message || 'An error occurred while starting the chat session.');
    }
});

// Send message
async function sendMessage() {
    const message = chatInput.value.trim();
    
    if (!message || !currentSessionId) {
        return;
    }
    
    // Add user message to UI
    addMessage('user', message);
    
    // Clear input
    chatInput.value = '';
    
    // Disable input while processing
    chatInput.disabled = true;
    sendMessageBtn.disabled = true;
    
    try {
        // Create form data
        const formData = new FormData();
        formData.append('session_id', currentSessionId);
        formData.append('message', message);
        
        // API request
        const response = await fetch('/api/chat/message', {
            method: 'POST',
            body: formData  // FormData will automatically set correct Content-Type
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            console.error('Server error:', errorData);
            throw new Error(errorData.detail || 'Server error occurred');
        }
        
        const result = await response.json();
        console.log('Message sent successfully:', result);
        
        // Add AI response
        addMessage('assistant', result.message, result);
        
        // Re-enable input
        chatInput.disabled = false;
        sendMessageBtn.disabled = false;
        chatInput.focus();
        
    } catch (error) {
        console.error('Error:', error);
        addMessage('system', `Error: ${error.message}`);
        chatInput.disabled = false;
        sendMessageBtn.disabled = false;
    }
}

// Send message button click
sendMessageBtn.addEventListener('click', sendMessage);

// Enter key to send
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// Add message to chat
function addMessage(role, content, data = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}-message`;
    
    // Create message content
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Format content (convert markdown-style formatting)
    let formattedContent = escapeHtml(content);
    
    // Convert **bold** to <strong>
    formattedContent = formattedContent.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    
    // Convert line breaks
    formattedContent = formattedContent.replace(/\n/g, '<br>');
    
    contentDiv.innerHTML = formattedContent;
    messageDiv.appendChild(contentDiv);
    
    // Add image if present
    if (data && data.image_url) {
        const imageDiv = document.createElement('div');
        imageDiv.className = 'message-image';
        
        const img = document.createElement('img');
        img.src = data.image_url;
        img.alt = 'Setup Image';
        img.className = 'setup-image';
        img.onerror = function() {
            this.style.display = 'none';
            const errorText = document.createElement('p');
            errorText.textContent = 'Image not available';
            errorText.className = 'image-error';
            imageDiv.appendChild(errorText);
        };
        
        imageDiv.appendChild(img);
        messageDiv.appendChild(imageDiv);
    }
    
    // Add checkpoints if present
    if (data && data.checkpoints) {
        const checkpointsDiv = createCheckpointsDisplay(data.checkpoints);
        messageDiv.appendChild(checkpointsDiv);
    }
    
    // Add action indicator if present
    if (data && data.action) {
        const actionDiv = document.createElement('div');
        actionDiv.className = 'message-action';
        
        let actionText = '';
        if (data.action === 'photo_taken') {
            actionText = '📷 Photo captured and analyzed';
        } else if (data.action === 'protocol_executed') {
            actionText = '✅ Protocol execution started';
        }
        
        if (actionText) {
            actionDiv.innerHTML = `<em>${actionText}</em>`;
            messageDiv.appendChild(actionDiv);
        }
    }
    
    // Add timestamp
    const timestampDiv = document.createElement('div');
    timestampDiv.className = 'message-timestamp';
    timestampDiv.textContent = new Date().toLocaleTimeString();
    messageDiv.appendChild(timestampDiv);
    
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Create checkpoints display
function createCheckpointsDisplay(checkpointsData) {
    const container = document.createElement('div');
    container.className = 'checkpoints-container';
    
    const title = document.createElement('h4');
    title.textContent = 'Verification Results';
    container.appendChild(title);
    
    // Overall result
    const overallResult = checkpointsData.overall_result;
    const isPass = overallResult === 'pass';
    
    const overallDiv = document.createElement('div');
    overallDiv.className = `overall-result ${overallResult}`;
    overallDiv.innerHTML = `
        <span class="overall-result-icon">${isPass ? '✅' : '❌'}</span>
        <span>${isPass ? 'All checks passed' : 'Some checks failed'}</span>
    `;
    container.appendChild(overallDiv);
    
    // Checkpoints list
    const checkpointsList = document.createElement('div');
    checkpointsList.className = 'checkpoints-list';
    
    if (checkpointsData.checkpoints && checkpointsData.checkpoints.length > 0) {
        checkpointsData.checkpoints.forEach(checkpoint => {
            const item = createCheckpointItem(checkpoint);
            checkpointsList.appendChild(item);
        });
    }
    
    container.appendChild(checkpointsList);
    
    return container;
}

// Create checkpoint item
function createCheckpointItem(checkpoint) {
    const div = document.createElement('div');
    div.className = `checkpoint-item ${checkpoint.result}`;
    
    const icon = checkpoint.result === 'pass' ? '✅' : '❌';
    
    div.innerHTML = `
        <div class="checkpoint-icon">${icon}</div>
        <div class="checkpoint-content">
            <div class="checkpoint-description">
                <span class="checkpoint-id">#${checkpoint.id}</span>
                ${escapeHtml(checkpoint.description)}
            </div>
            ${checkpoint.details ? `
                <div class="checkpoint-details">
                    ${escapeHtml(checkpoint.details)}
                </div>
            ` : ''}
        </div>
    `;
    
    return div;
}

// Show error
function showError(message) {
    errorMessage.innerHTML = `
        <p><strong>Error Message:</strong></p>
        <p>${escapeHtml(message)}</p>
    `;
    showSection(errorSection);
}

// Retry button
retryBtn.addEventListener('click', () => {
    showSection(uploadSection);
});

// New session button
newSessionBtn.addEventListener('click', () => {
    if (confirm('Are you sure you want to start a new session? Current conversation will be lost.')) {
        currentSessionId = null;
        uploadForm.reset();
        showSection(uploadSection);
    }
});

// HTML escape
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initial state: show upload section
showSection(uploadSection);
