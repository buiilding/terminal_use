import google.generativeai as genai

def count_tokens(model: genai.GenerativeModel, text: str) -> int:
    """
    Counts the number of tokens in a given text using the provided Gemini model.
    
    As a fallback, it will estimate the token count based on character count.
    """
    try:
        # The count_tokens method returns a CountTokensResponse object
        response = model.count_tokens(text)
        return response.total_tokens
    except Exception as e:
        print(f"Could not count tokens using the API: {e}")
        print("Falling back to a rough character-based approximation.")
        # As a rough fallback, one token is approximately 4 characters.
        return len(text) // 4 