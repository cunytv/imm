<?php

/**
 * Process a duplicate resource: update DB, nodes, and collections.
 *
 * @param string $full_path Full path to the file
 * @param array $duplicates Array of duplicate resource refs (integers)
 */
function process_duplicate_resource(string $full_path, array $duplicates): void
{
    echo "Full path received: $full_path\n";
    echo "Duplicates array: ";
    print_r($duplicates);

    if (empty($duplicates)) {
        echo "No duplicates passed.\n";
        return;
    }

    if (count($duplicates) > 1) {
        echo "More than one duplicate: " . implode(', ', $duplicates) . "\n";
        return;
    }

    $dup_ref = $duplicates[0];
    echo "Processing duplicate ref: $dup_ref\n";

    // --- Update Resource values ---
    $db_path = preg_replace('#^/Volumes#', '', $full_path);
    $query = "UPDATE resource SET file_path = ? WHERE ref = ?;";
    ps_query($query, ['s', $db_path, 'i', $dup_ref]);
    echo "Updated resource file_path to: $db_path\n";

    $db_title = pathinfo($full_path, PATHINFO_FILENAME);
    $query = "UPDATE resource SET field8 = ? WHERE ref = ?;";
    ps_query($query, ['s', $db_title, 'i', $dup_ref]);
    echo "Updated resource title (field8) to: $db_title\n";

    // --- Delete existing resource-collection pairings ---
    $query = "DELETE FROM collection_resource WHERE resource = ?;";
    ps_query($query, ['i', $dup_ref]);
    echo "Deleted collection_resource entries for ref: $dup_ref\n";

    // --- Delete existing resource-node pairings ---
    $nodefields = [8, 12, 89, 91, 92];
    foreach ($nodefields as $field) {
        $query = "DELETE FROM resource_node 
                  WHERE resource = ? 
                  AND node IN (
                      SELECT ref FROM node WHERE resource_type_field = ?
                  );";
        ps_query($query, ['i', $dup_ref, 'i', $field]);
        echo "Deleted resource_node entries for field $field and ref $dup_ref\n";
    }

    // --- Extract date from path ---
    $re = '/\b(\d{4}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])|\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01]))\b/';
    if (preg_match($re, $full_path, $matches)) {
        $date_str = $matches[0];

        if (strlen($date_str) == 8) {
            $date = substr($date_str, 0, 4) . '-' . substr($date_str, 4, 2) . '-' . substr($date_str, 6, 2);
        } else {
            $date = '20' . substr($date_str, 0, 2) . '-' . substr($date_str, 2, 2) . '-' . substr($date_str, 4, 2);
        }

        update_field($dup_ref, 12, $date);
        echo "Updated date field (12) to: $date\n";
    } else {
        echo "No valid date found in path.\n";
        $date = null;
    }

    // --- Update production fields ---
    global $staticsync_mapfolders; // if defined in boot.php
    if (!empty($staticsync_mapfolders) && is_array($staticsync_mapfolders)) {
        foreach ($staticsync_mapfolders as $mapfolder) {
            $match = $mapfolder["match"] ?? '';
            $field = $mapfolder["field"] ?? null;

            if ($field === 89 && str_contains($full_path, $match)) {
                $parts = explode('/', $full_path);
                $n = count($parts);
                $show = $parts[$n - 1] ?? null;
                update_field($dup_ref, 89, $show);
                echo "Updated production field (89) to: $show\n";
            }
        }
    }

    // --- Update filepath tree ---
    $folder = $full_path;
    $path_parts = explode("/", $full_path);
    echo "Original path parts: ";
    print_r($path_parts);

    if (strpos($folder, 'Photos') !== false) {
        $path_parts = array_slice($path_parts, 3, -1);
        echo "Path parts after Photos slice: ";
        print_r($path_parts);
    }

    if (strpos($folder, 'Camera Card Delivery') !== false) {
        $path_parts = array_slice($path_parts, 2, -2);
        echo "Path parts after Camera Card Delivery slice: ";
        print_r($path_parts);
    }

    if (strpos($folder, 'Studio') !== false) {
        $path_parts = array_slice($path_parts, 2, 2);
        if ($date) $path_parts[] = $date;
        echo "Path parts after Studio slice: ";
        print_r($path_parts);
    }

    $path_parts_f = $path_parts;
    $treenodes = touch_category_tree_level($path_parts_f);
    add_resource_nodes($dup_ref, $treenodes);
    echo "Added resource nodes based on path.\n";

    echo "Finished processing duplicate ref: $dup_ref\n";
}
