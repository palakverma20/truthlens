def danger_score(text):
    """
    Calculate danger score and provide reasons for the score.
    Returns: (score, reasons, confidence)
    """
    score = 0
    reasons = []
    
    # Check for urgency language
    urgency_words = ["!", "now", "immediately", "urgent", "asap", "quickly", "hurry"]
    if any(word in text.lower() for word in urgency_words):
        score += 20
        if "!" in text:
            reasons.append("Uses excessive exclamation marks")
        if any(w in text.lower() for w in ["now", "immediately", "urgent", "asap"]):
            reasons.append("Uses urgency language")
    
    # Check for social pressure
    social_words = ["everyone", "share", "forward", "tell your friends", "don't miss"]
    if any(word in text.lower() for word in social_words):
        score += 20
        reasons.append("Applies social pressure or viral tactics")
    
    # Check for financial language
    financial_words = ["money", "transfer", "payment", "invest", "prize", "claim", "reward", "free"]
    if any(word in text.lower() for word in financial_words):
        score += 15
        if "transfer" in text.lower() or "payment" in text.lower():
            reasons.append("Mentions monetary transactions")
        if "free" in text.lower() or "prize" in text.lower():
            reasons.append("Promises unrealistic rewards")
    
    # Check for authority impersonation
    auth_words = ["bank", "police", "government", "official", "urgent action required"]
    if any(word in text.lower() for word in auth_words):
        score += 15
        reasons.append("Impersonates authority or official entity")
    
    # Check for emotional triggers
    emotional_words = ["scared", "angry", "worried", "shocked", "devastated", "heartbroken"]
    if any(word in text.lower() for word in emotional_words):
        score += 10
        reasons.append("Uses emotional manipulation language")
    
    # Determine confidence level
    if score >= 60:
        confidence = "High"
    elif score >= 30:
        confidence = "Medium"
    else:
        confidence = "Low"
    
    score = min(score, 100)
    
    # If no reasons found, provide a generic one
    if not reasons:
        reasons = ["Message appears to use standard communication patterns"]
    
    return score, reasons, confidence


def calculate_mood(score):
    """
    Calculate AI Mood badge based on risk score.
    Returns: (emoji, label, color_class)
    """
    if score <= 25:
        return "😐", "Calm Analysis", "mood-calm"
    elif score <= 50:
        return "🤔", "Mixed Signals", "mood-mixed"
    elif score <= 75:
        return "⚠️", "High Pressure", "mood-high"
    else:
        return "🚨", "Manipulative Tone", "mood-manipulative"
