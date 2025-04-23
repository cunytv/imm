#!/usr/bin/env python3
from difflib import SequenceMatcher

def print_media_dict():
    # Print the titles and their abbreviations
    print(f"Media ID Dictionary")  # Header
    print('-' * 50)  # Separator
    for title, abbreviation in shows.items():
        print(f"{title:<40} {abbreviation}")

# Full show name similarity (not between codes)
def check_similarity(s):
    match_tuple = (None, 0) # show name, ratio

    for key, value in shows.items():
        similarity = SequenceMatcher(None, s, key).ratio()
        if similarity > match_tuple[1]:
            match_tuple = (key, similarity)

    if match_tuple[1] > 0.5:
        return match_tuple[0]
    else:
        return 'No Show'

# Takes code and return show name
def get_full_show_name(s):
    name = None
    for key, value in shows.items():
        if value == s:
            name = key
            return name
    return 'No Show'

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
    "CUNY TV Presents Film":       "CNTVPR",
    "CUNY Uncut":                  "CNNT",
    "CUNY Laureates":              "CNLR",
    "EdCast":                      "EDCA",
    "Graduate Center Presents":    "GCPR",
    "Italics":                     "ITAL",
    "Keeping Relevant":            "KPRL",
    "LATiNAS":                     "LTNS",
    "Let It Rip":                  "LTRP",
    "New York Times Close Up":     "NYTCU",
    "Nueva York":                  "NUEV",
    "One to One":                  "OTOO",
    "Shades of US":                "SHUS",
    "Sustainability Matters":       "STMT",
    "Theater All the Moving Parts": "THMP",
    "Urban U":                     "URBN"
}
