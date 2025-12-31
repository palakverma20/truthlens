def emotion_agent(text, model):
    prompt = f"""
    You are helping a child.
    Does this message try to scare or anger people?
    Message: {text}
    Answer simply.
    """
    return model.generate_content(prompt).text

def logic_agent(text, model):
    prompt = f"""
    Is this message using unfair thinking tricks?
    Explain like I am 10.
    Message: {text}
    """
    return model.generate_content(prompt).text

def pattern_agent(text, model):
    prompt = f"""
    Does this message look like common fake or misleading messages?
    Look for big claims, no sources, urgency.
    Message: {text}
    """
    return model.generate_content(prompt).text

def explain_agent(emotion, logic, pattern, model):
    prompt = f"""
    Combine these findings and explain kindly:
    Emotion: {emotion}
    Logic: {logic}
    Pattern: {pattern}
    """
    return model.generate_content(prompt).text
