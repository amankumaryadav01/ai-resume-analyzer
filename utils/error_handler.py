def safe_error_message(error: Exception) -> str:
    """Return a user-friendly error message without exposing internals."""
    message = str(error).strip()

    if not message:
        return "Something went wrong. Please try again."

    if "GROQ_API_KEY" in message:
        return "Groq API key is missing or invalid. Please check your .env file."

    if "RateLimit" in message or "rate_limit" in message.lower():
        return "AI service rate limit reached. Please wait and try again."

    if "timeout" in message.lower():
        return "The AI service took too long to respond. Please try again."

    if "JSON" in message:
        return "The AI returned an unexpected response. Please try again."

    return f"Something went wrong: {message}"
