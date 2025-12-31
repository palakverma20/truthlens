// THEME TOGGLE
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    document.body.setAttribute('data-theme', savedTheme);
}

function toggleTheme() {
    const currentTheme = document.body.getAttribute('data-theme') || 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    document.body.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

const themeToggle = document.getElementById('themeToggle');
if (themeToggle) {
    themeToggle.addEventListener('click', toggleTheme);
}

// Initialize theme on page load
initTheme();

const messageInput = document.getElementById('messageInput');
const charCount = document.getElementById('charCount');
const analyzeBtn = document.getElementById('analyzeBtn');
const loadingState = document.getElementById('loadingState');
const resultsSection = document.getElementById('resultsSection');
const errorState = document.getElementById('errorState');
const errorMessage = document.getElementById('errorMessage');

// Character counter
messageInput.addEventListener('input', () => {
    charCount.textContent = messageInput.value.length;
});

// Analyze button click
analyzeBtn.addEventListener('click', async () => {
    const text = messageInput.value.trim();
    
    if (!text) {
        showError('Please enter a message to analyze.');
        return;
    }
    
    if (text.length > 5000) {
        showError('Message exceeds 5000 character limit.');
        return;
    }
    
    analyzeBtn.disabled = true;
    showLoading();
    hideResults();
    hideError();
    
    try {
        // Set request timeout to 35 seconds (backend timeout is 30s)
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 35000);
        
        const response = await fetch('https://truthlens-backend-dgxw.onrender.com/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text }),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Analysis failed');
        }
        
        const data = await response.json();
        displayResults(data);
        hideLoading();
    } catch (error) {
        console.error('Error:', error);
        if (error.name === 'AbortError') {
            showError('Request took too long. Please try again.');
        } else {
            showError('Error analyzing message: ' + error.message);
        }
        hideLoading();
    } finally {
        analyzeBtn.disabled = false;
    }
});

function showLoading() {
    loadingState.classList.remove('hidden');
}

function hideLoading() {
    loadingState.classList.add('hidden');
}

function hideResults() {
    resultsSection.classList.add('hidden');
}

function showError(message) {
    errorMessage.textContent = message;
    errorState.classList.remove('hidden');
}

function hideError() {
    errorState.classList.add('hidden');
}

function displayResults(data) {
    const score = data.score || 0;
    
    // Trim text if too long (show summary)
    const truncateText = (text, maxLength = 200) => {
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    };
    
    // Display all results immediately
    document.getElementById('explanationText').textContent = data.explanation;
    document.getElementById('emotionText').textContent = truncateText(data.emotion);
    document.getElementById('logicText').textContent = truncateText(data.logic);
    document.getElementById('patternText').textContent = truncateText(data.pattern);
    
    // Update risk meter with smooth animation
    const riskFill = document.getElementById('riskFill');
    const riskScore = document.getElementById('riskScore');
    const riskDescription = document.getElementById('riskDescription');
    
    // Animate the fill
    riskFill.style.width = '0%';
    riskScore.textContent = '0';
    
    // Force reflow to trigger animation
    void riskFill.offsetWidth;
    
    riskFill.style.width = score + '%';
    riskScore.textContent = score;
    
    // Risk level description with color coding
    let riskLevel = 'Low Risk';
    let riskColor = 'var(--accent-green)';
    if (score > 60) {
        riskLevel = 'High Risk';
        riskColor = 'var(--accent-red)';
    } else if (score > 30) {
        riskLevel = 'Medium Risk';
        riskColor = 'var(--accent-cyan)';
    }
    riskDescription.textContent = riskLevel;
    riskScore.style.color = riskColor;
    
    // Display mood badge if available
    if (data.mood) {
        const moodBadge = document.getElementById('moodBadge');
        const moodEmoji = document.getElementById('moodEmoji');
        const moodLabel = document.getElementById('moodLabel');
        
        moodEmoji.textContent = data.mood.emoji;
        moodLabel.textContent = data.mood.label;
        
        // Update mood class
        moodBadge.className = 'mood-badge ' + data.mood.class;
        
        // Show badge with animation
        moodBadge.classList.remove('hidden');
        
        // Add tooltip text
        moodBadge.title = 'AI Mood: Summarizes the overall tone and manipulation level of the message';
    }
    
    // Show results section with animation
    resultsSection.classList.remove('hidden');
    
    // Trigger animation by forcing reflow
    setTimeout(() => {
        resultsSection.offsetHeight;
    }, 10);
}

