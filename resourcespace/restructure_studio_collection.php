<?php

$private_key = "61f7477d9cdad97ad99295ca7a2de2967172f866f1b21e1ee83ee570da999e87";
$user = "admin";
$url = "http://resourcespace/api/";

$path_tree_field_id = 91; // ID for path tree field type 
$studio_node_id = 51022; // Studio footage parent node ID for path tree

function isCurrentCollectionAlreadyDate($cc){
    $d = DateTime::createFromFormat('Y-m-d', $cc);
    return $d && $d->format('Y-m-d') === $cc;
}

function extractDate($t){
	global $date;
	
	$re8 = '/^(\d{4}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01]))/'; //YYYYMMDD
	$re6 = '/(\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01]))/'; //YYMMDD

	if (preg_match($re8, $t, $m)) {
		$date = (string) $m[1];
		$date = substr($date, 0, 4) . '-' . substr($date, 4, 2) . '-' . substr($date, 6, 2);
	}
	elseif (preg_match($re6, $t, $m)) {
		    $date = $m[1];
			$date = '20' . $date;
			$date = substr($date, 0, 4) . '-' . substr($date, 4, 2) . '-' . substr($date, 6, 2);
	} else {
			$date = 'NODATE';
	}
}

// Retrieve existing remote Featured Collections
function getFCs() {
    global $private_key, $user, $url, $show_fc_ref;

    $params = [
        "user"    => $user,
        "function"=> "get_featured_collections",
        "parent"  => $show_fc_ref
    ];

    $query = http_build_query($params);
    $sign = hash("sha256", $private_key . $query);

    // Retry loop
    $maxRetries = 3;
    $attempt = 0;

    while ($attempt < $maxRetries) {
        $attempt++;
        $response = file_get_contents("http://resourcespace/api/?" . $query . "&sign=" . $sign);
        $http_code = '';

        if (isset($http_response_header)) {
            $status_line = $http_response_header[0];
            preg_match('{HTTP\/\S*\s(\d{3})}', $status_line, $match);
            $http_code = $match[1] ?? null;

            if ($http_code == '200') { // Success
                return $response;
            } else {
                echo "Attempt #$attempt failed.\n";
                echo "Response Body: ";
                print_r($response);
                sleep(1); // Wait before retrying
            }
        }
    }

}

// Checks if FC exists
function doesFCExist($arr){
	global $date;
	
	$found = false;
	$found_id = false;

	foreach ($arr as $item) {
	    if (isset($item['name']) && $item['name'] === $date) {
	        $found = true;
			$found_id = $item['ref'];
	        break;
	    }
	}
	
    return [
        'found' => $found,
        'found_id' => intval($found_id)
    ];
}

// Determines if a string can be cast to float
function canCastToNum($s) {
    return is_numeric($s);	
}

function createCollection(){
	global $private_key, $user, $url, $date;
	
	$data = [
	    'user' => $user,
	    'function' => 'create_collection',
	    'name' => $date,
	];

	$query = http_build_query($data);
	$sign = hash("sha256", $private_key . $query);
	$data['sign'] = $sign;

	$postdata = array();
	$postdata['query'] = http_build_query($data);
	$postdata['sign'] = $sign;
	$postdata['user'] = $user;

	$curl = curl_init($url);
	curl_setopt( $curl, CURLOPT_HEADER, "Content-Type:application/x-www-form-urlencoded" );
	curl_setopt( $curl, CURLOPT_POST, 1);
	curl_setopt( $curl, CURLOPT_POSTFIELDS, $postdata);
	curl_setopt( $curl, CURLOPT_RETURNTRANSFER, 1 );	
	
	# retry loop
	$maxRetries = 3;
	$attempt = 0;

	while ($attempt < $maxRetries) {
	    $attempt++;
	    $curl_response = curl_exec($curl);
		$curl_error = curl_error($curl);
	    if (canCastToNum($curl_response)) { // Expected result is an int
			return intval($curl_response);
	    } else {
	        echo "Attempt #$attempt failed.\n";
			echo "cURL Error: " . $curl_error . "\n";
		    echo "Response Body: ";
		    print_r($curl_response);
	        sleep(1);
	    }
	}
		
}

function saveCollection($ref){
	global $private_key, $user, $url, $show_fc_ref;

	$coldata = [];
	$coldata['type'] = 3; // 3 = featured collection
	$coldata['parent'] = $show_fc_ref;
	$coldata['force_featured_collection_type'] = 0; // set to 1 only if root folder
	$coldata['thumbnail_selection_method'] = 1; // 1 = most popular img

	$data = [
	    'user' => $user,
	    'function' => 'save_collection',
	    'ref' => $ref,
		'coldata' => $coldata,
	];

	$query = http_build_query($data);
	$sign = hash("sha256", $private_key . $query);
	$data['sign'] = $sign;

	$postdata = array();
	$postdata['query'] = http_build_query($data);
	$postdata['sign'] = $sign;
	$postdata['user'] = $user;

	$curl = curl_init($url);
	curl_setopt( $curl, CURLOPT_HEADER, "Content-Type:application/x-www-form-urlencoded" );
	curl_setopt( $curl, CURLOPT_POST, 1);
	curl_setopt( $curl, CURLOPT_POSTFIELDS, $postdata);
	curl_setopt( $curl, CURLOPT_RETURNTRANSFER, 1 );
	
	# Retry loop
	$maxRetries = 3;
	$attempt = 0;

	while ($attempt < $maxRetries) {
	    $attempt++;
	    $curl_response = curl_exec($curl);
		$curl_error = curl_error($curl);
	    if ($curl_response) { // Expected result is true
			return;
	    } else {
	        echo "Attempt #$attempt failed.\n";
			echo "cURL Error: " . $curl_error . "\n";
		    echo "Response Body: ";
		    print_r($curl_response);
	        sleep(1);
	    }
	}
	
}

function addResourceToCollection($coll){
	global $private_key, $user, $url, $resource_ref;

	$data = [
	    'user' => $user,
	    'function' => 'add_resource_to_collection',
	    'resource' => $resource_ref,
		'collection' => $coll,
	];

	$query = http_build_query($data);
	$sign = hash("sha256", $private_key . $query);
	$data['sign'] = $sign;

	$postdata = array();
	$postdata['query'] = http_build_query($data);
	$postdata['sign'] = $sign;
	$postdata['user'] = $user;

	$curl = curl_init($url);
	curl_setopt( $curl, CURLOPT_HEADER, "Content-Type:application/x-www-form-urlencoded" );
	curl_setopt( $curl, CURLOPT_POST, 1);
	curl_setopt( $curl, CURLOPT_POSTFIELDS, $postdata);
	curl_setopt( $curl, CURLOPT_RETURNTRANSFER, 1 );
	
	# Retry loop
	$maxRetries = 3;
	$attempt = 0;

	while ($attempt < $maxRetries) {
	    $attempt++;
	    $curl_response = curl_exec($curl);
		$curl_error = curl_error($curl);
	    if ($curl_response) { // Expected result is true
			return;
	    } else {
	        echo "Attempt #$attempt failed.\n";
			echo "cURL Error: " . $curl_error . "\n";
		    echo "Response Body: ";
		    print_r($curl_response);
	        sleep(1);
	    }
	}
	
}


function checkandCreateFC(){
	$fcs = getFCs();
	$fcs = json_decode($fcs, true);
	$result = doesFCExist($fcs);
	$exist_collection = $result['found'];
	$ec_id = $result['found_id'];
	
	if (!$exist_collection){
		$ec_id = createCollection();
		saveCollection($ec_id);
		echo "Created Featured Collection " . $ec_id . PHP_EOL;	
	} else {
		echo "Featured Collection Exists " . $ec_id . PHP_EOL;
	}
	
	addResourceToCollection($ec_id);
		
}

function get_nodes($ref, $parent=null){
	global $private_key, $user, $url;
	
	$params = [
	    'user' => $user,
	    'function' => 'get_nodes',
	    'ref' => $ref, 
	    'parent' => $parent,
	];

	$query = http_build_query($params);

	$sign=hash("sha256",$private_key . $query);
	$response = file_get_contents("http://resourcespace/api/?" . $query . "&sign=" . $sign);

	return $response;
	
}

function set_node($name, $field, $parent=null){
	global $private_key, $user, $url;

	$data = [
	    'user' => $user,
	    'function' => 'set_node',
	    'ref' => 'NULL',
		'resource_type_field' => $field,
		'name' => $name,
		'parent' => $parent,
	];

	$query = http_build_query($data);
	$sign = hash("sha256", $private_key . $query);
	$data['sign'] = $sign;

	$postdata = array();
	$postdata['query'] = http_build_query($data);
	$postdata['sign'] = $sign;
	$postdata['user'] = $user;

	$curl = curl_init($url);
	curl_setopt( $curl, CURLOPT_HEADER, "Content-Type:application/x-www-form-urlencoded" );
	curl_setopt( $curl, CURLOPT_POST, 1);
	curl_setopt( $curl, CURLOPT_POSTFIELDS, $postdata);
	curl_setopt( $curl, CURLOPT_RETURNTRANSFER, 1 );

	$curl_response = curl_exec($curl);
	$curl_error = curl_error($curl);

	print_r($curl_error);
	//print_r($curl_response);
	
	return $curl_response;
}

// make more modular
function add_resource_to_nodes($nodearray){
	global $private_key, $user, $url, $resource_ref; 
	
	$nodestring = implode(',', $nodearray);

	$data = [
	    'user' => $user,
	    'function' => 'add_resource_nodes',
	    'resource' => $resource_ref,
		'nodestring' => $nodestring,
	];

	$query = http_build_query($data);
	$sign = hash("sha256", $private_key . $query);
	$data['sign'] = $sign;

	$postdata = array();
	$postdata['query'] = http_build_query($data);
	$postdata['sign'] = $sign;
	$postdata['user'] = $user;

	$curl = curl_init($url);
	curl_setopt( $curl, CURLOPT_HEADER, "Content-Type:application/x-www-form-urlencoded" );
	curl_setopt( $curl, CURLOPT_POST, 1);
	curl_setopt( $curl, CURLOPT_POSTFIELDS, $postdata);
	curl_setopt( $curl, CURLOPT_RETURNTRANSFER, 1 );

	$curl_response = curl_exec($curl);
	$curl_error = curl_error($curl);

	print_r($curl_error);	
}

function does_node_exist($nodes, $string){	
	$nodes = json_decode($nodes, true);
	$match_id = 0;

	foreach ($nodes as $node) {
	    if (isset($node["name"]) && $node["name"] === $string) {
	        $match_id = $node["ref"];
	        break;
	    }
	}
	return $match_id;
}

function create_field_tree(){
	global $studio_node_id, $date, $path_tree_field_id, $show_fc_name;
	
	echo "Date: " . $date . PHP_EOL;
	
	$nodes = get_nodes($path_tree_field_id, $studio_node_id); // nodes under Studio
	$show_node_id = does_node_exist($nodes, $show_fc_name); // get show node
		
	$nodes = get_nodes($path_tree_field_id, $show_node_id); // nodes under Show
	$node_id = does_node_exist($nodes, $date); // get date node
		
	if ($node_id == 0){
		$node_id = set_node($date, $path_tree_field_id, $show_node_id);
	}
	
	add_resource_to_nodes([$studio_node_id, $show_node_id, $node_id]);
}

// Path to your JSON file
$file = '/Users/libraryad/Desktop/col690.json';

// Read the file contents
$json = file_get_contents($file);

// Decode JSON to associative array
$data = json_decode($json, true);

// Check if decoding worked
if ($data === null) {
    echo "Failed to decode JSON.\n";
    exit;
}

$studio_fc_ref = 690; //Studio level collection
$date = 0;

// Loop through each item
foreach ($data as $item) {

	$resource_ref = $item['resource_ref'];
	$title = $item['resource_title'];
	$current_fc_name = $item['collection_name']; //Studio/Show/X level collection
	$show_fc_name = $item['parent_name'];
	$show_fc_ref = $item['parent_ref']; //Studio/Show level collection

	echo "Resource ref: " . $resource_ref . "\n";
	echo "Resource title: " . $title . "\n";
	echo "Collection: " . $current_fc_name . "\n";
	echo "Parent Name: " . $show_fc_name . "\n";
	echo "Parent Ref: " . $show_fc_ref . "\n";
	echo "***\n";


	if (isCurrentCollectionAlreadyDate($current_fc_name)) {
    	echo "Collection is already a date.\n";
    	exit(1); // exit with code 1
	}

	extractDate($title);
	checkandCreateFC();
	create_field_tree();
	
	exit(1);
}
