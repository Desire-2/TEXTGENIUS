

// Function to scroll the chat messages container to the bottom
function scrollChatToBottom() {
    var chatMessages = document.querySelector('.chat-messages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Event listener to scroll chat messages on page load
window.addEventListener('load', function() {
    scrollChatToBottom();
});

// Event listener to scroll chat messages when new message is added
var chatMessagesContainer = document.querySelector('.chat-messages');
chatMessagesContainer.addEventListener('DOMNodeInserted', function(event) {
    if (event.target.classList.contains('user-message') || event.target.classList.contains('bot-message')) {
        scrollChatToBottom();
    }
});
// Global variables
const messageForm = document.getElementById('message-form');
const fileInput = document.getElementById('file-input');
const messageInput = document.getElementById('message-input');
const chatMessages = document.querySelector('.chat-messages');

// Event listeners
messageForm.addEventListener('submit', sendMessage);
fileInput.addEventListener('change', sendFile);

// Function to send a message
function sendMessage(e) {
    e.preventDefault();

    // Get the user input
    const message = messageInput.value;

    // Create a user message element
    const userMessageElement = createMessageElement('user', message);

    // Add the user message to the chat messages
    chatMessages.appendChild(userMessageElement);

    // Clear the message input field
    messageInput.value = '';

    // Process the user message
    processUserMessage(message);
}

// Function to send a file
function sendFile(e) {
    const file = fileInput.files[0];

    // Check if a file is selected
    if (file) {
        // Create a file message element
        const fileMessageElement = createFileMessageElement(file);

        // Add the file message to the chat messages
        chatMessages.appendChild(fileMessageElement);

        // Process the file
        processFile(file);
    }
}

// Function to create a user or bot message element
function createMessageElement(sender, content) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', sender);

    const messageContent = document.createElement('p');
    messageContent.textContent = content;

    messageElement.appendChild(messageContent);
    return messageElement;
}

// Function to create a file message element
function createFileMessageElement(file) {
    const fileMessageElement = document.createElement('div');
    fileMessageElement.classList.add('message', 'file');

    const fileName = document.createElement('p');
    fileName.textContent = `File: ${file.name}`;

    const fileIcon = document.createElement('i');
    fileIcon.classList.add('fas', 'fa-file');

    fileMessageElement.appendChild(fileIcon);
    fileMessageElement.appendChild(fileName);
    return fileMessageElement;
}

// Function to process the user message
function processUserMessage(message) {
    // Send the user message to the server for processing
    fetch('/process-message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: message })
    })
        .then(response => response.json())
        .then(data => {
            const response = data.response;

            // Create a bot message element
            const botMessageElement = createMessageElement('bot', response);

            // Add a class to the bot message to style it differently
            botMessageElement.classList.add('response');

            // Add the bot message to the chat messages
            chatMessages.appendChild(botMessageElement);

            // Scroll to the bottom of the chat messages
            chatMessages.scrollTop = chatMessages.scrollHeight;
        })
        .catch(error => {
            console.log('Error:', error);
        });
}

// Function to process the file
function processFile(file) {
    // Check the file type
    if (file.type.includes('image')) {
        // Display the image in the chat messages
        displayImage(file);
    } else if (file.type.includes('pdf')) {
        // Process the PDF file
        processPDF(file);
    } else {
        // Handle other file types
        const message = 'Unsupported file type. Please upload an image or PDF file.';
        const botMessageElement = createMessageElement('bot', message);
        chatMessages.appendChild(botMessageElement);
    }
}

// Function to display an image in the chat messages
function displayImage(file) {
    const reader = new FileReader();

    // Read the image file as a data URL
    reader.readAsDataURL(file);

    // Callback function
    reader.onload = function () {
        const imageUrl = reader.result;

        // Create an image element
        const imageElement = document.createElement('img');
        imageElement.classList.add('image');
        imageElement.src = imageUrl;

        // Create a container for the image
        const imageContainer = document.createElement('div');
        imageContainer.classList.add('image-container');
        imageContainer.appendChild(imageElement);

        // Create a message element to hold the image
        const imageMessageElement = document.createElement('div');
        imageMessageElement.classList.add('message', 'image-message');
        imageMessageElement.appendChild(imageContainer);

        // Add the image message to the chat messages
        chatMessages.appendChild(imageMessageElement);

        // Scroll to the bottom of the chat messages
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };
}

// Function to process the PDF file
function processPDF(file) {
    // Send the PDF file to the server for processing
    const formData = new FormData();
    formData.append('file', file);

    fetch('/process-pdf', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            const response = data.response;

            // Create a bot message element
            const botMessageElement = createMessageElement('bot', response);

            // Add a class to the bot message to style it differently
            botMessageElement.classList.add('response');

            // Add the bot message to the chat messages
            chatMessages.appendChild(botMessageElement);

            // Scroll to the bottom of the chat messages
            chatMessages.scrollTop = chatMessages.scrollHeight;
        })
        .catch(error => {
            console.log('Error:', error);
        });
}

