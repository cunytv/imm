#!/usr/bin/env python3

def print_media_dict():
    # Print the titles and their abbreviations
    print(f"Media ID Dictionary")  # Header
    print('-' * 50)  # Separator
    for title, abbreviation in shows.items():
        print(f"{title:<40} {abbreviation}")

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
