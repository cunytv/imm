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

    // --- Delete existing resource-collections pairing ---
	
	// get collection refs
	$query = "SELECT collection as value FROM collection_resource WHERE resource = ?;";
	$col_refs = ps_query($query, ['i', $dup_ref]);
	$col_ref = $col_refs[0]['value'];

	// delete collection-resource pairings
	$query = "DELETE FROM collection_resource WHERE resource = ?;";
	ps_query($query, ['i', $dup_ref]);
	echo "Deleted collection_resource entries for ref: $dup_ref\n";

	// delete collections if empty
	if (!empty($col_refs)) {
		$i = 0;
	    foreach ($col_refs as $row) {
	        $col_ref = $row['value'];
			$query = "SELECT collection as value FROM collection_resource WHERE collection = ?;";
			$refs = ps_query($query, ['i', $col_ref]);
			if (empty($refs)) {
				$query = "DELETE FROM collection WHERE ref = ?;";
				ps_query($query, ['i', $col_ref]);
				echo "Deleted empty collection: $col_ref\n";
			}
	    }
	}

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
	$alphanum_path = preg_replace('/[^a-zA-Z0-9]/', '', $full_path);

	// Try YYYYMMDD first
	$re_full = '/(20\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01]))/';
	if (preg_match($re_full, $alphanum_path, $matches)) {
	    $date_str = $matches[1];
	    $date = substr($date_str, 0, 4) . '-' .
	            substr($date_str, 4, 2) . '-' .
	            substr($date_str, 6, 2);
	}
	// Fallback to YYMMDD
	else {
	    $re_short = '/(\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01]))/';

	    if (preg_match($re_short, $alphanum_path, $matches)) {

	        $date_str = $matches[1];

	        $date = '20' . substr($date_str, 0, 2) . '-' .
	                substr($date_str, 2, 2) . '-' .
	                substr($date_str, 4, 2);

	    } else {
	        $date = null;
	    }
	}

	if ($date !== null) {
	    update_field($dup_ref, 12, $date);
	    echo "Updated date field (12) to: $date\n";
	} else {
	    echo "No valid date found in path.\n";
	}

    // --- Update production fields ---
    global $staticsync_mapfolders; // if defined in boot.php
    if (!empty($staticsync_mapfolders) && is_array($staticsync_mapfolders)) {
        foreach ($staticsync_mapfolders as $mapfolder) {
            $match = $mapfolder["match"] ?? '';
            $field = $mapfolder["field"] ?? null;
			$level = $mapfolder["level"] ?? null;

            if ($field === 89 && str_contains($full_path, $match)) {
                $parts = explode('/', $db_path);
                $n = count($parts);
                $show = $parts[$level] ?? null;
				echo "Show: " . $show . "\n";
                update_field($dup_ref, 89, $show);
                echo "Updated production field (89) to: $show\n";
            }
        }
    }
	
    // --- Update filepath tree ---
    $folder = $full_path;
    $path_parts = explode("/", $db_path);
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
	
    // --- Update filepath node ---
	update_field($dup_ref, 92, $db_path);
	
    // --- Update collections ---
	$parent_ref = null;
	$i = 0;
	foreach ($path_parts as $part) {
		$col_name = $path_parts[$i];
		if (is_null($parent_ref)) {
		    $query = "SELECT ref, name FROM collection WHERE name = ? AND parent IS NULL;";
		    $col_ref = ps_query($query, ['s', $col_name]);
		} else {
		    $query = "SELECT ref, name FROM collection WHERE name = ? AND parent = ?;";
		    $col_ref = ps_query($query, ['s', $col_name, 'i', $parent_ref]);
		}
				
		if (empty($col_ref)){
			$fc_categ_ref = create_collection(1, $col_name);
			save_collection($fc_categ_ref, array("parent" => $parent_ref, "type" => 3, "thumbnail_selection_method" => 1));
		} else {
			$fc_categ_ref = $col_ref[0]['ref'];
		}
		
		echo " - " . $fc_categ_ref . " $col_name \n";
		
		if ($i == count($path_parts) - 1){
			add_resource_to_collection($dup_ref, $fc_categ_ref);
		}
		
		$parent_ref = $fc_categ_ref;
		$i++;
	}

    echo "Finished processing duplicate ref: $dup_ref\n";
}
