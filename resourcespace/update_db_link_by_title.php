<?php

include '/opt/homebrew/var/www_test/include/boot.php';

$db_link_field = 103;
//$file = '/Users/libraryad/Documents/remote_share_links.json';
$file = $argv[1];

$json = file_get_contents($file);
$links = json_decode($json, true);

foreach ($links as $key => $value) {
	$name = $key;
	$link = $value;
	
	$query = 'select ref as value from resource where field8 = ' . $name . ' ;';
	$query = "SELECT ref AS value FROM resource WHERE field8 = ?;";
	$resource_ref = ps_value($query, ['s', $name], 0);
	echo $resource_ref . "\n";
	
	// create node and resource_node entries
	if ($link !== null && $link !== '') {
		$node_ref = set_node(null, $db_link_field, $link, null, null);
		add_resource_nodes($resource_ref, [$node_ref]);
		echo "Created dropbox link node for resource" . $resource_ref . "\n";
	} else { // or delete resource_node entry
		$query = "DELETE FROM resource_node WHERE node IN (SELECT ref FROM node WHERE resource_type_field = ?) AND resource = ?;";
		ps_query($query, ['i', $db_link_field, 'i', $resource_ref]);
		echo "Deleted dropbox link node for resource" . $resource_ref . "\n";
	}
}
