#!/usr/bin/env python3
from difflib import SequenceMatcher

# Create a dictionary from the provided list
shows = {
    "A Slice of NY":              "SLNY",
    "Arts in the City":           "AITC",
    "Asian American Life":         "AALF",
    "Black America":               "BLAM",
    "Bob Herbert’s OP-ED":        "OPED",
    "Book It":                     "BKIT",
    "Cafe con Felo":               "CFFL",
    "City Cinematheque":           "CCT",
    "City Works":                  "CTWR",
    "Conversations with Jim Zirin": "CNJZ",
    "CUNY Forum":                  "CFOR",
    "CUNY TV Presents":       "CNTVPR",
    "CUNY Uncut":                  "CNNT",
    "CUNY Laureates":              "CNLR",
    "CUNY Specials":               "SPEC",
    "EdCast":                      "EDCA",
    "Frame By Frame":               "FRBF",
    "Graduate Center Presents":    "GCPR",
    "Italics":                     "ITAL",
    "Keeping Relevant":            "KPRL",
    "LATiNAS":                     "LTNS",
    "Laura Flanders Show":         "LFFR",
    "Let It Rip":                  "LTRP",
    "New York Times Close Up":     "NYTCU",
    "Nueva York":                  "NUEV",
    "One to One":                  "OTOO",
    "Shades of US":                "SHUS",
    "Sustainability Matters":       "STMT",
    "Theater All the Moving Parts": "ATMP",
    "Urban U":                     "URBN",
    "Special":                      "SPEC"
}

def print_media_dict():
    # Print the titles and their abbreviations
    print(f"Media ID Dictionary")  # Header
    print('-' * 50)  # Separator
    for title, abbreviation in shows.items():
        print(f"{title:<40} {abbreviation}")

# Returns full show name to which string is most similar
def check_similarity(s):
    match_tuple = (None, 0) # show name, ratio

    for key, value in shows.items():
        similarity = SequenceMatcher(None, s.lower(), key.lower()).ratio()
        if similarity > match_tuple[1]:
            match_tuple = (key, similarity)

    if match_tuple[1] > 0.5:
        return match_tuple[0]
    else:
        return 'No Show'

# Takes code and returns show name
def get_full_show_name(s):
    name = None
    for key, value in shows.items():
        if value == s:
            name = key
            return name
    return 'No Show'

# Takes show name and returns code
def get_show_code(s):
    show_name = check_similarity(s)
    if show_name != "No Show":
        return shows[show_name]
    else:
        return "Invalid string. No show name match."

def is_code_in_dict(s):
    return s.upper() in (code.upper() for code in shows.values())

def codes_string_contains(s):
    matches = [value for value in shows.values() if value in s.upper()]
    return matches

def shows_string_contains(s):
    matches = []
    s = s.lower()
    for word in shows:
        word_lower = word.lower()
        if word_lower in s:
            matches.append(word)

    return matches

