import re

def extract_highlights(essay_text, raw_highlights):
    """Extract start and end indices for quotes in the essay text.
    
    Args:
        essay_text: The full text of the essay.
        raw_highlights: List of dicts with 'quote', 'category', 'reason'.
        
    Returns:
        List of dicts with 'start', 'end', 'category', 'reason', 'quote'.
    """
    if not essay_text or not raw_highlights:
        return []
    
    processed_highlights = []
    
    for rh in raw_highlights:
        quote = rh.get("quote")
        if not quote:
            continue
            
        # Create a regex pattern that ignores whitespace differences
        # Escape special characters in quote, then replace spaces with \s+
        escaped_quote = re.escape(quote)
        # Handle multiple spaces/newlines in the original text by matching \s+
        pattern = escaped_quote.replace(r'\ ', r'\s+')
        
        match = re.search(pattern, essay_text, re.IGNORECASE)
        if match:
            processed_highlights.append({
                "start": match.start(),
                "end": match.end(),
                "category": rh.get("category"),
                "reason": rh.get("reason"),
                "quote": match.group(0) # Use the actual text from the essay
            })
            
    # Sort highlights by start index
    processed_highlights.sort(key=lambda x: x["start"])
    
    # Remove overlaps
    final_highlights = []
    last_end = -1
    
    for h in processed_highlights:
        if h["start"] >= last_end:
            final_highlights.append(h)
            last_end = h["end"]
            
    return final_highlights
