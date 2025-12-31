
// FEATURE 1: Why Score Button & Reasons Panel
const whyScoreBtn = document.getElementById('whyScoreBtn');
const reasonsPanel = document.getElementById('reasonsPanel');

if (whyScoreBtn) {
    whyScoreBtn.addEventListener('click', () => {
        reasonsPanel.classList.toggle('hidden');
    });
}

// Enhance displayResults to handle new features
const oldDisplayResults = window.displayResults;
window.displayResults = function(data) {
    // Call original display function
    oldDisplayResults.call(this, data);
    
    // FEATURE 1: Display reasons for the score
    if (data.reasons && data.reasons.length > 0) {
        const reasonsList = document.getElementById('reasonsList');
        reasonsList.innerHTML = '';
        data.reasons.forEach(reason => {
            const li = document.createElement('li');
            li.textContent = reason;
            reasonsList.appendChild(li);
        });
        // Reset panel to hidden state
        if (reasonsPanel) {
            reasonsPanel.classList.add('hidden');
        }
    }
    
    // FEATURE 2: Agent Timeline (purely visual, already animated via CSS)
    // No additional JS needed - timeline steps animate on results display
    
    // FEATURE 3: Display confidence level
    if (data.confidence) {
        const confidenceValue = document.getElementById('confidenceValue');
        if (confidenceValue) {
            confidenceValue.textContent = data.confidence;
            confidenceValue.setAttribute('data-confidence', data.confidence);
        }
    }
};
