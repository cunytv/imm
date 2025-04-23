<?php

$shows = [
    "A Slice of NY" => "SLNY",
    "Arts in the City" => "AITC",
    "Asian American Life" => "AALF",
    "Black America" => "BLAM",
    "Bob Herbert’s OP-ED" => "OPED",
    "Book It" => "BKIT",
    "Cafe con Felo" => "CFFL",
    "City Cinematheque" => "CCT",
    "City Works" => "CTWR",
    "Conversations with Jim Zirin" => "CNJZ",
    "CUNY Forum" => "CFOR",
    "CUNY TV Presents Film" => "CNTVPR",
    "CUNY Uncut" => "CNNT",
    "CUNY Laureates" => "CNLR",
    "EdCast" => "EDCA",
    "Graduate Center Presents" => "GCPR",
    "Italics" => "ITAL",
    "Keeping Relevant" => "KPRL",
    "LATiNAS" => "LTNS",
    "Let It Rip" => "LTRP",
    "New York Times Close Up" => "NYTCU",
    "Nueva York" => "NUEV",
    "One to One" => "OTOO",
    "Shades of US" => "SHUS",
    "Sustainability Matters" => "STMT",
    "Theater All the Moving Parts" => "THMP",
    "Urban U" => "URBN"
];

function print_media_dict($shows) {
    global $shows;
    echo "Media ID Dictionary\n";
    echo str_repeat('-', 50) . "\n";
    foreach ($shows as $title => $abbreviation) {
        printf("%-40s %s\n", $title, $abbreviation);
    }
}

function check_similarity($input) {
    global $shows;
    $bestMatch = null;
    $highestRatio = 0;

    foreach ($shows as $title => $abbr) {
        similar_text($input, $title, $percent);
        if ($percent > $highestRatio) {
            $highestRatio = $percent;
            $bestMatch = $title;
        }
    }

    if ($highestRatio > 0.5){
        return $bestMatch;
    } else {
        return 'No Show';
    }
}

function get_full_show_name($code) {
    global $shows;
    foreach ($shows as $title => $abbr) {
        if ($abbr === $code) {
            return $title;
        }
    }
    return 'No Show';
}

// Example usage
// print_media_dict($shows);
 echo check_similarity("American Life") . "\n";
// echo get_full_show_name($shows, "AITC") . "\n";
