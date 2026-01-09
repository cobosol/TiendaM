// static/js/chatbot_http.js - VERSIÓN CON PROTECCIÓN BOOTSTRAP

// ==========================================
// VARIABLES GLOBALES
// ==========================================

let userInput, chatMessages, chatContainer, chatButton, sendButton, typingIndicator;
let minimizeButton, closeButton;
let isChatOpen = false;
let isAuthenticated = false;
let currentUser = null;
let chatHistory = [];
let authModalInstance = null;
let userId = generateUserId();

function generateUserId() {
    const randomArray = new Uint32Array(2);
    window.crypto.getRandomValues(randomArray);
    return 'user_' + Array.from(randomArray).map(n => n.toString(36)).join('').substr(0, 9);
}
        
// ==========================================
// VERIFICACIÓN DE BOOTSTRAP
// ==========================================

function checkBootstrap() {
    if (typeof bootstrap === 'undefined') {
        console.error('❌ Bootstrap no está cargado. No se pueden usar modales.');
        return false;
    }
    console.log('✅ Bootstrap está disponible');
    return true;
}

// ==========================================
// FUNCIONES DE INICIALIZACIÓN
// ==========================================

function initializeChatElements() {
    console.log('🔄 Inicializando elementos del chat...');
    
    chatButton = document.getElementById('open-chat');
    chatContainer = document.getElementById('chat-container');
    minimizeButton = document.getElementById('minimize-chat');
    closeButton = document.getElementById('close-chat');
    chatMessages = document.getElementById('chat-messages');
    userInput = document.getElementById('user-input');
    sendButton = document.getElementById('send-btn');
    typingIndicator = document.getElementById('typing-indicator');
    
    console.log('✅ Elementos del DOM inicializados');
}

function initializeAuthComponents() {
    console.log('🔄 Inicializando componentes de autenticación...');
    
    // Verificar que Bootstrap esté disponible
    if (!checkBootstrap()) {
        console.warn('⚠️ No se puede inicializar el modal sin Bootstrap');
        return;
    }
    
    const modalElement = document.getElementById('authModal');
    if (modalElement) {
        authModalInstance = new bootstrap.Modal(modalElement);
        console.log('✅ Modal de autenticación inicializado');
        
        setupAuthModalEvents();
        
        modalElement.addEventListener('hidden.bs.modal', function() {
            resetAuthForm();
        });
    } else {
        console.error('❌ No se encontró el elemento authModal');
    }
}

function setupAuthModalEvents() {
    const authSubmit = document.getElementById('auth-submit');
    if (authSubmit) {
        authSubmit.addEventListener('click', handleAuthSubmit);
    }
    
    const authUsername = document.getElementById('auth-username');
    const authPassword = document.getElementById('auth-password');
    
    if (authUsername) {
        authUsername.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                handleAuthSubmit();
            }
        });
    }
    
    if (authPassword) {
        authPassword.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                handleAuthSubmit();
            }
        });
    }
}

function setupChatEventListeners() {
    console.log('🔄 Configurando event listeners del chat...');
    
    // --- CORRECCIÓN IMPLEMENTADA: Manejador directo para abrir el chat ---
    if (chatButton) {
        chatButton.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            toggleChat(true);
        });
    }

    // Listener delegado en el documento para cerrar al hacer clic fuera
    document.addEventListener('click', function(e) {
        // Cerrar chat al hacer clic fuera, pero no si es dentro del botón de abrir
        if (isChatOpen && 
            chatContainer && 
            !chatContainer.contains(e.target) && 
            !e.target.closest('#open-chat')) {
            toggleChat(false);
        }
    });
    
    // Event listeners para botones dentro del chat
    if (minimizeButton) {
        minimizeButton.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleChat(false);
        });
    }
    
    if (closeButton) {
        closeButton.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleChat(false);
        });
    }
    
    if (sendButton) {
        sendButton.addEventListener('click', function(e) {
            e.stopPropagation();
            sendMessage();
        });
    }
    
    if (userInput) {
        userInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.stopPropagation();
                sendMessage();
            }
        });
    }
}

function initializeChatState() {
    if (chatContainer) chatContainer.style.display = 'none';
    if (chatButton) chatButton.style.display = 'block';
    if (typingIndicator) typingIndicator.style.display = 'none';
}

// ==========================================
// FUNCIONES DEL CHAT
// ==========================================

function toggleChat(show) {
    if (show) {
        if (chatContainer) {
            chatContainer.style.display = 'block';
            chatContainer.classList.add('show');
        }
        if (chatButton) {
            chatButton.style.display = 'none';
        }
        isChatOpen = true;
        
        // Ocultar notificación al abrir el chat
        hideAvatarNotification();

        setTimeout(() => {
            if (userInput) userInput.focus();
        }, 300);
    } else {
        if (chatContainer) {
            chatContainer.classList.remove('show');
            setTimeout(() => {
                chatContainer.style.display = 'none';
            }, 300);
        }
        if (chatButton) {
            chatButton.style.display = 'block';
        }
        isChatOpen = false;
    }
}

function appendMessage(message, isUser = false, sender = null) {
    if (!chatMessages) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.classList.add(isUser ? 'message-user' : 'message-bot');
    
    if (sender && !isUser) {
        /* messageDiv.innerHTML = `<div class="fw-bold">${sender}</div>${message}`; */
        const safeSender = encodeForHTML(sender);
        const safeMessage = encodeForHTML(message);
        messageDiv.innerHTML = `<div class="fw-bold">${safeSender}</div>${safeMessage}`;
    } else {
        messageDiv.textContent = message;
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    chatHistory.push({
        message: message,
        isUser: isUser,
        timestamp: new Date().toISOString()
    });
}
function encodeForHTML(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}
function showTypingIndicator() {
    if (typingIndicator) {
        typingIndicator.style.display = 'block';
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }
}

function hideTypingIndicator() {
    if (typingIndicator) {
        typingIndicator.style.display = 'none';
    }
}

function getCSRFToken() {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, 10) === 'csrftoken=') {
                cookieValue = decodeURIComponent(cookie.substring(10));
                break;
            }
        }
    }
    return cookieValue;
}

// ==========================================
// FUNCIÓN PRINCIPAL PARA ENVIAR MENSAJES
// ==========================================

async function sendMessage() {
    if (!userInput) return;
    
    const message = userInput.value.trim();
    if (!message) return;

    // Detectar comandos de autenticación
    const lowerMessage = message.toLowerCase();
    if (lowerMessage.includes('login') || 
        lowerMessage.includes('iniciar sesión') || 
        lowerMessage.includes('autenticar') ||
        lowerMessage.includes('mi cuenta') ||
        lowerMessage.includes('mis datos')) {
        
        appendMessage(message, true);
        userInput.value = '';
        
        if (!isAuthenticated) {
            appendMessage('Te mostraré el formulario de autenticación...', false, '👩 Iris');
            setTimeout(showAuthModal, 1000);
        } else {
            appendMessage(`Ya estás autenticado como ${currentUser.nombre}. ¿En qué más puedo ayudarte?`, false, '👩 Iris');
        }
        return;
    }

    // Detectar comando de logout
    if (lowerMessage.includes('logout') || 
        lowerMessage.includes('cerrar sesión') || 
        lowerMessage.includes('salir')) {
        
        appendMessage(message, true);
        userInput.value = '';
        
        if (isAuthenticated) {
            await logoutUser();
        } else {
            appendMessage('No hay ninguna sesión activa.', false, '👩 Iris');
        }
        return;
    }

    // Mensaje normal
    appendMessage(message, true);
    userInput.value = '';
    showTypingIndicator();

    try {
        let endpoint = 'https://chatbot.cobosis.com/assistant/api/chat/';

        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
            },
            mode: 'cors',
            body: JSON.stringify({ 
                message: message,
                history: chatHistory.slice(-5),
                user_id: userId,
                include_analysis: false
            })
        });

        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status} - ${response.statusText}`);
        }

        const data = await response.json();
        
        if (!data.success) {
            appendMessage('⚠️ ' + data.message, false);
        } else {
            appendMessage(data.response, false, '👩 Iris');
            
            // Verificar si la respuesta sugiere necesidad de autenticación
            const authKeywords = [
                'autenticar', 'iniciar sesión', 'necesito que te autentiques', 
                'acceder a tus datos', 'login', 'credenciales', 'usuario y contraseña',
                'para ver esta información', 'área personal'
            ];
            
            const needsAuth = authKeywords.some(keyword => 
                data.response.toLowerCase().includes(keyword.toLowerCase())
            );
            
            if (needsAuth && !isAuthenticated) {
                setTimeout(() => showAuthModal(), 500);
            }
        }
    } catch (error) {
        console.error('❌ Error:', error);
        appendMessage('❌ Error de conexión. Intenta más tarde.', false);
    } finally {
        hideTypingIndicator();
    }
}

// ==========================================
// FUNCIONES DE AUTENTICACIÓN
// ==========================================

function showAuthModal() {
    console.log('🔧 Intentando mostrar modal de autenticación...');
    
    // Verificar Bootstrap primero
    if (!checkBootstrap()) {
        appendMessage('Error: No se puede mostrar el formulario de autenticación. Recarga la página.', false, '👩 Iris');
        return;
    }
    
    const modalElement = document.getElementById('authModal');
    if (!modalElement) {
        console.error('❌ Elemento authModal no encontrado');
        return;
    }
    
    if (!authModalInstance) {
        authModalInstance = new bootstrap.Modal(modalElement);
    }
    
    // Resetear el formulario
    const authForm = document.getElementById('auth-form');
    const authSuccess = document.getElementById('auth-success');
    const authError = document.getElementById('auth-error');
    
    if (authForm) authForm.classList.remove('d-none');
    if (authSuccess) authSuccess.classList.add('d-none');
    if (authError) authError.classList.add('d-none');
    
    // Limpiar campos
    const usernameField = document.getElementById('auth-username');
    const passwordField = document.getElementById('auth-password');
    if (usernameField) usernameField.value = '';
    if (passwordField) passwordField.value = '';
    
    // Mostrar el modal
    try {
        authModalInstance.show();
        console.log('✅ Modal mostrado exitosamente');
        
        setTimeout(() => {
            if (usernameField) usernameField.focus();
        }, 500);
        
    } catch (error) {
        console.error('❌ Error al mostrar modal:', error);
    }
}

async function authenticateUser(username, password) {
    try {
        console.log('🔐 Intentando autenticar usuario:', username);
        
        const response = await fetch('/chatbot/api/chatbot/auth/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
            },
            body: JSON.stringify({
                action: 'login',
                username: username,
                password: password
            })
        });
        
        const data = await response.json();
        console.log('📨 Respuesta de autenticación:', data);
        
        if (data.status === 'success') {
            isAuthenticated = true;
            currentUser = data.user;
            return { success: true, user: data.user };
        } else {
            return { success: false, error: data.message };
        }
    } catch (error) {
        console.error('❌ Error de autenticación:', error);
        return { success: false, error: 'Error de conexión con el servidor' };
    }
}

async function logoutUser() {
    try {
        const response = await fetch('/chatbot/api/chatbot/auth/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
            },
            body: JSON.stringify({
                action: 'logout'
            })
        });
        
        isAuthenticated = false;
        currentUser = null;
        appendMessage('Sesión cerrada correctamente.', false, '👩 Iris');
        
    } catch (error) {
        console.error('❌ Error al cerrar sesión:', error);
    }
}

async function handleAuthSubmit() {
    console.log('🔄 Procesando formulario de autenticación...');
    
    const username = document.getElementById('auth-username').value;
    const password = document.getElementById('auth-password').value;
    const authError = document.getElementById('auth-error');
    
    if (!username || !password) {
        showAuthError('Por favor, completa todos los campos');
        return;
    }
    
    const submitButton = document.getElementById('auth-submit');
    submitButton.disabled = true;
    submitButton.innerHTML = '<i class="bi bi-arrow-repeat spinner"></i> Autenticando...';
    
    const result = await authenticateUser(username, password);
    
    if (result.success) {
        console.log('✅ Autenticación exitosa');
        
        document.getElementById('auth-form').classList.add('d-none');
        document.getElementById('auth-success').classList.remove('d-none');
        authError.classList.add('d-none');
        
        setTimeout(() => {
            if (authModalInstance) {
                authModalInstance.hide();
            }
            
            submitButton.disabled = false;
            submitButton.innerHTML = '<i class="bi bi-box-arrow-in-right me-1"></i>Iniciar Sesión';
            
            appendMessage(`¡Bienvenido ${result.user.nombre}! Ahora puedo ayudarte con tus datos personales.`, false, '👩 Iris');
            
        }, 1500);
        
    } else {
        console.log('❌ Error de autenticación:', result.error);
        
        submitButton.disabled = false;
        submitButton.innerHTML = '<i class="bi bi-box-arrow-in-right me-1"></i>Iniciar Sesión';
        
        showAuthError(result.error || 'Error de autenticación');
        
        document.getElementById('auth-password').value = '';
    }
}

function showAuthError(message) {
    const authError = document.getElementById('auth-error');
    const authErrorText = document.getElementById('auth-error-text');
    
    if (authError && authErrorText) {
        authErrorText.textContent = message;
        authError.classList.remove('d-none');
        authError.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

function resetAuthForm() {
    const usernameField = document.getElementById('auth-username');
    const passwordField = document.getElementById('auth-password');
    const authError = document.getElementById('auth-error');
    const authForm = document.getElementById('auth-form');
    const authSuccess = document.getElementById('auth-success');
    const submitButton = document.getElementById('auth-submit');
    
    if (usernameField) usernameField.value = '';
    if (passwordField) passwordField.value = '';
    if (authError) authError.classList.add('d-none');
    if (authForm) authForm.classList.remove('d-none');
    if (authSuccess) authSuccess.classList.add('d-none');
    
    if (submitButton) {
        submitButton.disabled = false;
        submitButton.innerHTML = '<i class="bi bi-box-arrow-in-right me-1"></i>Iniciar Sesión';
    }
}

function setupAvatarEffects() {
    const chatAvatar = document.getElementById('open-chat');
    
    if (chatAvatar) {
        // Solo efectos visuales, no listeners de clic
        chatAvatar.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.1)';
        });
        
        chatAvatar.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
        
        // Mostrar notificación después de 10 segundos de inactividad
        setTimeout(() => {
            showAvatarNotification();
        }, 10000);
    }
}

// Mostrar notificación en el avatar
function showAvatarNotification() {
    const notification = document.querySelector('.chat-notification');
    if (notification && !isChatOpen) {
        notification.style.display = 'block';
        
        // Parpadear la notificación
        let intervalId = setInterval(() => {
            // Detener si el chat se abre
            if (isChatOpen) {
                clearInterval(intervalId);
                notification.style.opacity = '1';
                notification.style.display = 'none';
                return;
            }
            notification.style.opacity = notification.style.opacity === '0.5' ? '1' : '0.5';
        }, 1000);
        notification.dataset.intervalId = intervalId; // Guardar ID para limpieza
    }
}

// Ocultar notificación cuando se abre el chat
function hideAvatarNotification() {
    const notification = document.querySelector('.chat-notification');
    if (notification) {
        notification.style.display = 'none';
        const intervalId = notification.dataset.intervalId;
        if (intervalId) {
            clearInterval(parseInt(intervalId));
            notification.dataset.intervalId = '';
        }
    }
}


// ==========================================
// INICIALIZACIÓN PRINCIPAL
// ==========================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 DOM cargado, inicializando chatbot...');
    
    // Verificar dependencias críticas
    if (typeof bootstrap === 'undefined') {
        console.error('❌ BOOTSTRAP NO ESTÁ CARGADO. El modal de autenticación no funcionará.');
    }
    
    initializeChatElements();
    initializeAuthComponents();
    setupChatEventListeners();
    initializeChatState();
    setupAvatarEffects();

    // Estado inicial
    if (chatContainer) chatContainer.style.display = 'none';
    if (typingIndicator) typingIndicator.style.display = 'none';
    
    console.log('✅ Chatbot completamente inicializado');
});

// ==========================================
// COMANDOS DE DEPURACIÓN
// ==========================================

window.debugChat = {
    showModal: function() {
        if (!checkBootstrap()) {
            console.error('❌ No se puede mostrar modal: Bootstrap no disponible');
            return;
        }
        showAuthModal();
    },
    testAuth: function() {
        if (userInput) {
            userInput.value = 'login';
            sendMessage();
        }
    },
    checkStatus: function() {
        console.log('🔧 Estado del chatbot:');
        console.log('- Bootstrap disponible:', typeof bootstrap !== 'undefined');
        console.log('- userInput:', !!userInput);
        console.log('- isAuthenticated:', isAuthenticated);
        console.log('- authModalInstance:', !!authModalInstance);
    }
};

console.log('🔧 Comandos de depuración: debugChat.showModal(), debugChat.checkStatus()');