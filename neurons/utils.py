import re


# doesn't check all possible cases since Memgraph also runs some checks (comment checks etc)
def generate_patterns_for_terms(terms):
    patterns = []
    for term in terms:
        lower_term = term.lower()
        # Escape term for regex pattern
        escaped_term = re.escape(lower_term)
        # Basic term
        patterns.append(escaped_term)

        # With spaces between each character
        patterns.append(r'\s*'.join(escaped_term))

        # Unicode escape sequences (basic example)
        unicode_pattern = ''.join([f'\\u{ord(char):04x}' for char in lower_term])
        patterns.append(unicode_pattern)

        # Mixed case variations to catch case obfuscation
        mixed_case_variations = [f'[{char.lower()}{char.upper()}]' for char in lower_term]
        patterns.append(''.join(mixed_case_variations))

        # Detecting comments that might hide portions of malicious queries
        # This is a simplistic approach and might need refinement
        patterns.append(f'/{escaped_term}|{escaped_term}/')

    return patterns


def is_potentially_malicious(query, terms):
    # Normalize the query by lowercasing (maintaining original for comment checks)
    normalized_query = query.lower()

    # Generate patterns for the given terms, including obfuscation-resistant versions
    write_patterns = generate_patterns_for_terms(terms)

    # Compile regex patterns to detect any of the write operations
    pattern = re.compile('|'.join(write_patterns), re.IGNORECASE)

    # Check if the normalized query matches any of the patterns
    if pattern.search(normalized_query):
        return True  # Query is potentially malicious or not read-only

    return False  # Query passed the check