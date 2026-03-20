<?php
global $shows;

$shows = [
    "A Slice of NY" => "SLNY",
    "Arts in the City" => "AITC",
    "Asian American Life" => "AALF",
    "Association for a Better New York" => "ABNY",
    "Black America" => "BLAM",
    "Board of Trustees" => "BOT",
    "Bob Herbert’s OP-ED" => "OPED",
    "Book It" => "BKIT",
    "Cafe con Felo" => "CFFL",
    "City Cinematheque" => "CCT",
    "City Works" => "CTWR",
    "Conversations with Jim Zirin" => "CNJZ",
    "CUNY Forum" => "CFOR",
    "CUNY TV Presents" => "CNTVPR",
    "CUNY Uncut" => "CNNT",
    "CUNY Laureates" => "CNLR",
    "CUNY Specials" => "SPEC",
    "EdCast" => "EDCA",
    "Frame By Frame" => "FRBF",
    "Graduate Center Presents" => "GCPR",
    "Italics" => "ITAL",
    "Keeping Relevant" => "KPRL",
    "LATiNAS" => "LTNS",
    "Laura Flanders Show" => "LFFR",
    "Let It Rip" => "LTRP",
    "New York Times Close Up" => "NYTCU",
    "Nueva York" => "NUEV",
    "One to One" => "OTOO",
    "Shades of US" => "SHUS",
    "Sustainability Matters" => "STMT",
    "Theater All the Moving Parts" => "ATMP",
    "Urban U" => "URBN",
    "Special" => "SPEC"
];

$aliases = [
    "Conversations w/ Jim Zirin" => "Conversations with Jim Zirin"
];

function print_media_dict() {
    global $shows;

    echo "Media ID Dictionary\n";
    echo str_repeat("-", 50) . "\n";

    foreach ($shows as $title => $abbr) {
        printf("%-40s %s\n", $title, $abbr);
    }
}

function similarity_ratio($a, $b) {
    similar_text(strtolower($a), strtolower($b), $percent);
    return $percent / 100;
}

function check_similarity($s) {
    global $shows, $aliases;

    $best_match = null;
    $best_ratio = 0;

    foreach ($shows as $key => $value) {
        $ratio = similarity_ratio($s, $key);
        if ($ratio > $best_ratio) {
            $best_ratio = $ratio;
            $best_match = $key;
        }
    }

    foreach ($aliases as $key => $value) {
        $ratio = similarity_ratio($s, $key);
        if ($ratio > $best_ratio) {
            $best_ratio = $ratio;
            $best_match = $value;
        }
    }

    if ($best_ratio > 0.5) {
        return $best_match;
    } else {
        return "No Show";
    }
}

function get_full_show_name($code) {
    global $shows;

    foreach ($shows as $name => $abbr) {
        if ($abbr === $code) {
            return $name;
        }
    }

    return "No Show";
}

function get_show_code($s) {
    global $shows;

    $show_name = check_similarity($s);

    if ($show_name !== "No Show") {
        return $shows[$show_name];
    }

    return "Invalid string. No show name match.";
}

function is_code_in_dict($s) {
    global $shows;

    $codes = array_map('strtoupper', array_values($shows));
    return in_array(strtoupper($s), $codes);
}

function codes_string_contains($s) {
    global $shows;

    $matches = [];
    $s = strtoupper($s);

    foreach ($shows as $value) {
        if (strpos($s, strtoupper($value)) !== false) {
            $matches[] = $value;
        }
    }

    return $matches;
}

function shows_string_contains($s) {
    global $shows, $aliases;

    $matches = [];
    $s = strtolower($s);

    foreach ($shows as $key => $value) {
        if (strpos($s, strtolower($key)) !== false) {
            $matches[] = $key;
        }
    }

    foreach ($aliases as $key => $value) {
        if (strpos($s, strtolower($key)) !== false) {
            $matches[] = $value;
        }
    }

    return $matches;
}

?>
