<?php

include '/opt/homebrew/var/www/include/boot.php';

$db_link_field = 103;
$file          = $argv[1];

/*
 JSON structure (passed as argument):

 "/DB/FOLDER/PATH" : {
     old_names  : [/FOLDER/PATH/NAME],
     share_link: "https://...",
     files     : ["file.jpg"]
 }
*/

$json    = file_get_contents($file);
$folders = json_decode($json, true);
$unmatched_folders = [];

foreach ($folders as $folder_path => $info)
{
    echo $folder_path . "\n";

    $link = $info['share_link'];

    // Get current folder name
    $parts = explode('/', $folder_path);
    $name  = end($parts);

    $names   = [];
    $names[] = $name;

    // Add old folder names (deduplicated)
    foreach ($info['old_names'] as $old_path) {
        $parts = explode('/', trim($old_path, '/'));
        $name  = end($parts);

        if (!in_array($name, $names, true)) {
            $names[] = $name;
        }
    }

    // Get resource refs for assets in folder
    foreach ($names as $name){
        $query = "SELECT resource AS value FROM collection_resource WHERE collection IN (SELECT ref FROM collection WHERE name = ?);";
        $resource_refs = ps_query($query, ['s', $name], 0);

        if (!empty($resource_refs)) {
            foreach ($resource_refs as $resource_ref) {
                // Create or delete resource_node entry
                if ($link !== null && $link !== '') {
                    $node_ref = set_node(null, $db_link_field, $link, null, null);
					
                    add_resource_nodes($resource_ref['value'], [$node_ref]);
                    echo "Created dropbox link node for resource {$resource_ref['value']}\n";
                } else {
                    $delete_query = "DELETE FROM resource_node WHERE node IN (SELECT ref FROM node WHERE resource_type_field = ?) AND resource = ?;";
                    ps_query($delete_query, ['i', $db_link_field, 'i', $resource_ref['value']]);
                    echo "Deleted dropbox link node for resource {$resource_ref['value']}\n";
                }
            } break;
        }
    }

    if (empty($resource_refs)) {
        $unmatched_folders[$folder_path] = $info;
    }
}

if (!empty($unmatched_folders)) {
    file_put_contents(
        $file,
        json_encode($unmatched_folders, JSON_PRETTY_PRINT)
    );
} else {
    unlink($file);
}