<?php

include '/opt/homebrew/var/www/include/boot.php';

$db_link_field = 103;
$file = $argv[1];

// json structure, passed as argument, is
// "/DB/FOLDER/PATH" : {
//							id:
//                          old_names: [/FOLDER/PATH/NAME],
//							share_link: $https://,
//							files: {filehash: {"name": file.jpg, "old_names": [file.jpg], "deleted": bool}}
//						}

$json = file_get_contents($file);
$folders = json_decode($json, true);
$unmatched_titles = [];

foreach ($folders as $folder_path => $info) {
	echo $folder_path . "\n";
	
	$link = $info['share_link'];
	
	// Get potential names
	$parts = explode('/', $folder_path);
	$name = end($parts);

	$names = []; 
	$names[] = $name;
	
	foreach ($info['old_names'] as $old_path) {
	    $parts   = explode('/', trim($old_path, '/'));
	    $name = $parts[count($parts) - 1];

		if (!in_array($name, $names, true)) {
		    $names[] = $name;
		}
	}
	
	// Get resource ref
	foreach ($names as $name){		
		$query = "SELECT ref AS value FROM resource WHERE field8 = ?;";
		$resource_ref = ps_value($query, ['s', $name], 0);
		
		if ($resource_ref != 0) {
			// Create node and resource_node entry or delete resource_node entry
			if ($link !== null && $link !== '') {
				$node_ref = set_node(null, $db_link_field, $link, null, null);
				add_resource_nodes($resource_ref, [$node_ref]);
				echo "Created dropbox link node for resource " . $resource_ref . "\n";
			} else {
				$query = "DELETE FROM resource_node WHERE node IN (SELECT ref FROM node WHERE resource_type_field = ?) AND resource = ?;";
				ps_query($query, ['i', $db_link_field, 'i', $resource_ref]);
				echo "Deleted dropbox link node for resource " . $resource_ref . "\n";
			}
			
		    break;
		}
	}

    if ($resource_ref == 0) {
		echo "Resource not found with title " . $names[0] . "\n";
        $unmatched_titles[$folder_path] = $info;
    }
}

if (!empty($unmatched_titles)) {
    file_put_contents(
        $file,
        json_encode($unmatched_titles, JSON_PRETTY_PRINT)
    );
} else {
    unlink($file);
}
