"""Test the sanitization logic on the repeated sample"""
import re

def sanitize_live_text(raw_text, prev_text=None):
    """Simulates the on_live_text sanitization logic"""
    try:
        if not raw_text:
            return None

        s = raw_text.strip()
        if not s:
            return None

        # remove control tokens
        s = re.sub(r"\binstructions\[LiveCaptions\]\s*\d+\b", "", s, flags=re.IGNORECASE)
        s = re.sub(r"\s+", " ", s).strip()

        # collapse repeated consecutive words
        s = re.sub(r"\b(\w+)(?:\s+\1\b){2,}", r"\1", s, flags=re.IGNORECASE)

        # extract last complete sentence
        sentences = re.split(r'(?<=[.!?])\s+', s)
        if sentences:
            complete_sentences = [sent for sent in sentences if re.search(r'[.!?]$', sent)]
            if complete_sentences:
                s = complete_sentences[-1]
            else:
                s = sentences[-1]
                if len(s) > 100:
                    s = s[:100].rsplit(' ', 1)[0]

        # token-based similarity check
        if prev_text:
            prev_tokens = set(prev_text.lower().split())
            curr_tokens = set(s.lower().split())
            
            if curr_tokens:
                overlap = len(prev_tokens & curr_tokens) / len(curr_tokens)
                
                if overlap > 0.6:
                    new_words = curr_tokens - prev_tokens
                    if len(new_words) < 5:
                        return None  # skip incremental update
            
            if prev_text.lower() in s.lower() or s.lower() in prev_text.lower():
                if abs(len(s) - len(prev_text)) < 20:
                    return None

        s = s.strip()
        if not s or len(s) < 3:
            return None

        return s

    except Exception as e:
        print(f"Error: {e}")
        return None


# Test with the user's repeated sample
sample = """no, but creativity, I guess, yeah, it's it doesn't have to be consistent like, I mean, it's creative, right? It's a storyno, but creativity, I guess, yeah, it's it doesn't have to be consistent like, I mean, it's creative, right? It's a story butno, but creativity, I guess, yeah, it's it doesn't have to be consistent like I mean it's creative, right? It's a story. But if, youno, but creativity, I guess, yeah, it's it doesn't have to be consistent like I mean it's creative, right? It's a story. But if, you giveno, but creativity, I guess, yeah, it's it doesn't have to be consistent. Like, I mean, it's creative, right? It's a story. But if you give it likeno, but creativity, I guess, yeah, it's it doesn't have to be consistent. Like, I mean, it's creative, right? It's a story. But if you give it like a hardno, but creativity, I guess, yeah, it's it doesn't have to be consistent. Like, I mean, it's creative, right? It's a story. But if you give it like a hard mathno, but creativity, I guess, yeah, it's it doesn't have to be consistent like, I mean, it's creative, right? It's a story, but if you give it like a hard math problem likeno, but creativity, I guess, yeah, it's it doesn't have to be consistent like, I mean, it's creative, right? It's a story, but if you give it like a hard math problem like andno, but creativity, I guess, yeah, it's it doesn't have to be consistent like, I mean, it's creative, right? It's a story. But if you give it like a hard math problem like and that's not, possibleno, but creativity, I guess, yeah, it's it doesn't have to be consistent like, I mean, it's creative, right? It's a story. But if you give it like a hard math problem like and that's not, possible tono, but creativity I guess, yeah, it's it doesn't have to be consistent like I mean it's creative, right? It's a story. But if you give it like a hard math problem like and that's not possible to solve butno, but creativity I guess, yeah, it's it doesn't have to be consistent like I mean it's creative, right? It's a story. But if you give it like a hard math problem like and that's not possible to solve but you don'tno, but creativity I guess, yeah, it's it doesn't have to be consistent like I mean it's creative, right? It's a story. But if you give it like a hard math problem like and that's not possible to solve but you don't giveno, but creativity, I guess, yeah, it's it doesn't have to be consistent like, I mean, it's creative, right? It's a story. But if you give it like a hard math problem like and that's not possible to solve, but you don't give it"""

print("Testing sanitizer on repeated sample:\n")
print("=" * 80)

# Simulate incremental updates (split the sample into chunks)
lines = sample.split("no, but creativity")
prev = None
update_count = 0

for i, line in enumerate(lines):
    if not line.strip():
        continue
    
    # reconstruct the line
    text = "no, but creativity" + line
    
    result = sanitize_live_text(text, prev)
    
    if result:
        update_count += 1
        print(f"\nUpdate #{update_count}:")
        print(f"  Input length: {len(text)} chars")
        print(f"  Output: {result[:150]}{'...' if len(result) > 150 else ''}")
        prev = result
    else:
        print(f"\nSkipped (incremental/duplicate)")

print("\n" + "=" * 80)
print(f"\nTotal updates shown: {update_count} out of {len([l for l in lines if l.strip()])} inputs")
print("\nExpected: Only 1-2 substantial updates instead of 14+ repeated lines")
