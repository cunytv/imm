<?php

include 'cunymediaids.php';

// global vars
// fixed
$private_key = "61f7477d9cdad97ad99295ca7a2de2967172f866f1b21e1ee83ee570da999e87";
$user = "admin";
$url = "http://resourcespace/api/";
$remote_fc_id = 540; // Remote footage featured collection ID
$path_tree_field_id = 91; // ID for path tree field type 
$prod_title_field_id = 89;
$remote_node_id = 43395; // Remote footage parent node ID for path tree

// user input
$searchDir = '';
$dropboxLink = '';

// code generated
$resource_fp = '';
$resource_id = 0;
$alternative_fps = [];
$showcode = '';

// deprecated
// Determines if file is av media
// filter out .dstore type files
function isMediaFile($filePath) {
    // Get number of streams
    $nbStreamsCommand = "ffprobe -loglevel quiet " . escapeshellarg($filePath) . " -show_entries format=nb_streams -of default=nw=1:nk=1";
    $nbStreamsOutput = trim(shell_exec($nbStreamsCommand));
    // Get stream duration
    $durationCommand = "ffprobe -loglevel quiet " . escapeshellarg($filePath) . " -show_entries stream=duration -of default=nw=1:nk=1";
    $durationOutput = trim(shell_exec($durationCommand));
	// Split the string into an array by newlines, and get first instance
	$durationOutput = explode("\n", $durationOutput);
	$durationOutput = $durationOutput[0];
	
    $nbStreams = canCastToNum($nbStreamsOutput) ? (int)$nbStreamsOutput : 0;
    $duration = canCastToNum($durationOutput) ? (float)$durationOutput : 0;

    if ($nbStreams >= 1 && $duration > 0) {
        return true;
    }
}

// Above function super slow, consider using this
function isDSStore($filePath) {
    return basename($filePath) === '.DS_Store';
}

// Determines if a string can be cast to float
function canCastToNum($s) {
    return is_numeric($s);	
}

// finds windowmp4 files
// edit so that it only picks one, and has the other one be an alternative file
function findWindowMp4Files($directory) {
	global $resource_fp, $alternative_fps;
    $matches = [];

    $iterator = new RecursiveIteratorIterator(
        new RecursiveDirectoryIterator($directory, RecursiveDirectoryIterator::SKIP_DOTS)
    );

    foreach ($iterator as $file) {
        if ($file->isFile() && !isDSStore($file->getPathname())) {
            // Case-insensitive check for 'window.mp4' at the end of the filename
            if (preg_match('/window\.mp4$/i', $file->getFilename())) {
                $matches[] = $file->getPathname();
            }
        }
    }

	if (count($matches) > 1) {
	    $resource_fp = $matches[0];
	    $alternative_fps = array_slice($matches, 1);
	} elseif (count($matches) === 1) {
	    $resource_fp = $matches[0];
	}
		
}

//
function findAllFiles($directory) {
	global $alternative_fps;
    $files = [];

    $directoryIterator = new RecursiveDirectoryIterator($directory, RecursiveDirectoryIterator::SKIP_DOTS);

    // Skip directories named "access"
    $filterIterator = new RecursiveCallbackFilterIterator($directoryIterator, function ($current, $key, $iterator) {
        if ($iterator->hasChildren() && $current->isDir()) {
            return $current->getFilename() !== 'access';
        }
        return true;
    });

    $iterator = new RecursiveIteratorIterator($filterIterator);

    foreach ($iterator as $file) {
        if ($file->isFile() && !isDSStore($file->getPathname())) {
            $files[] = $file->getPathname();
        }
    }

    $alternative_fps = array_merge($files, $alternative_fps);

}


function extractShowCode($d){
	global $showcode;
	
	$parts = explode('/', rtrim($d, '/'));
	$second_last_dir = $parts[count($parts) - 2];

	// Extract letters before the first number
	if (preg_match('/^([A-Za-z]+)/', $second_last_dir, $matches)) {
	    $showcode = $matches[1];
	} else {
	    echo "No letters before numbers found." . PHP_EOL;
		$showcode = 'NOSHOW';
	}
	
}

function createResource(){
	global $private_key, $user, $url, $resource_id;
	
	$data = [
	    'user' => $user,
	    'function' => 'create_resource',
	    'resource_type' => 3, // 3 = video
		'archive' => 0, // 0 = active
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
	    if (canCastToNum($curl_response)) { // Expected result is an int
			$resource_id = $curl_response;
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

// this uses the upload_multipart function
function uploadFile(){
	global $private_key, $user, $url, $resource_fp, $resource_id;

	$data = [
	    'user' => $user,
	    'function' => 'upload_multipart',
	    'ref' => $resource_id,
	    'no_exif' => true,
	    'revert' => false,
	];

	$sign = hash('sha256', $private_key . http_build_query($data));
	$data['sign'] = $sign;
	$postdata = [
	    'query' => http_build_query($data),
	    'sign' => $sign,
	    'user' => $user,
	    'file' => new CURLFile($resource_fp), # IMPORTANT: this wasn't part of the signature!
	];

	$curl = curl_init($url);
	curl_setopt($curl, CURLOPT_HTTPHEADER, ['Content-Type: multipart/form-data']);
	curl_setopt($curl, CURLOPT_POST, 1);
	curl_setopt($curl, CURLOPT_POSTFIELDS, $postdata);
	curl_setopt($curl, CURLOPT_RETURNTRANSFER, 1 );
	
	# Retry loop
	$maxRetries = 3;
	$attempt = 0;

	while ($attempt < $maxRetries) {
	    $attempt++;
		echo " - Uploading resource " . basename($resource_fp) . PHP_EOL;
	    $curl_response = curl_exec($curl);
		$curl_error = curl_error($curl);
		$http_code = curl_getinfo($curl, CURLINFO_HTTP_CODE);
	    if ($http_code == '204') { // Expected code if success
			return;
	    } else {
	        echo "Attempt #$attempt failed.\n";
			echo "cURL Error: " . $curl_error . "\n";
		    echo "Response Body: ";
		    print_r($curl_response);
	        sleep(1); // Optional: wait a second before retrying
	    }
	}

}

function uploadAltFiles(){
	global $alternative_fps;
	
	for ($i = 0; $i < count($alternative_fps); $i++) {
	    if (file_exists($alternative_fps[$i])) {
	        uploadAltFile($alternative_fps[$i]);
	    } else {
	        echo " - File not found" . PHP_EOL;
	    }
	}
	
}

function uploadAltFile($fp){
	global $private_key, $user, $url, $resource_id;
	
	$data = [
	    'user' => $user,
	    'function' => 'add_alternative_file',
	    'resource' => $resource_id,
	    'name' => basename($fp),
		'file' => $fp,
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
		echo " - Uploading alt file " . basename($fp) . PHP_EOL;
	    $curl_response = curl_exec($curl);
		$curl_error = curl_error($curl);
	    if (canCastToNum($curl_response)) { // Expected result is an int
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
	}
	
	addResourceToCollection($ec_id);
		
}

function addResourceToCollection($coll){
	global $private_key, $user, $url, $resource_id;

	$data = [
	    'user' => $user,
	    'function' => 'add_resource_to_collection',
	    'resource' => $resource_id,
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

function saveCollection($ref){
	global $private_key, $user, $url, $remote_fc_id;

	$coldata = [];
	$coldata['type'] = 3; // 3 = featured collection
	$coldata['parent'] = $remote_fc_id;
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

function createCollection(){
	global $private_key, $user, $url, $showcode;
	
	$data = [
	    'user' => $user,
	    'function' => 'create_collection',
	    'name' => $showcode,
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

// Checks if FC exists
function doesFCExist($arr){
	global $showcode;
	
	$found = false;
	$found_id = false;

	foreach ($arr as $item) {
	    if (isset($item['name']) && $item['name'] === $showcode) {
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

// Retrieve existing remote Featured Collections
function getFCs() {
    global $private_key, $user, $url, $remote_fc_id;

    $params = [
        "user"    => $user,
        "function"=> "get_featured_collections",
        "parent"  => $remote_fc_id
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


function set_title(){
	global $private_key, $user, $url, $resource_id, $resource_fp;

	$title = basename($resource_fp);
	$title_upper = strtoupper($title);
	$title_s = explode('_WINDOW.MP4', $title_upper)[0];

	$data = [
		    'user' => $user,
		    'function' => 'update_field',
		    'resource' => $resource_id,
			'field' => 8, // type field ID for Title
			'value' => $title_s,
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
	
}

function set_asset_type(){
	global $private_key, $user, $url, $resource_id;

	$data = [
	    'user' => $user,
	    'function' => 'update_field',
	    'resource' => $resource_id,
		'field' => 88, // type field ID for Asset Type
		'value' => 'Remote',
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
	
}

// use archive file path to construct tiger video file path
function set_file_path(){
	global $private_key, $user, $url, $resource_id, $resource_fp, $showcode;
	
	$tiger_fp = '/Volumes/TigerVideo/Camera Card Delivery/' . $showcode . '/' . preg_split("/_WINDOW\.mp4/i", basename($resource_fp))[0];
	//$tiger_fp = str_replace(' ', '%20', $tiger_fp);
	
	$data = [
	    'user' => $user,
	    'function' => 'update_field',
	    'resource' => $resource_id, 
		'field' => 92, // type ID for file path
		'value' => $tiger_fp,
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
	
}

function set_production_title(){
	global $private_key, $user, $url, $resource_id, $showcode, $prod_title_field_id;

	$showname = get_full_show_name($showcode);
	echo $showname . "\n";

	$nodes = get_nodes($prod_title_field_id); // type field ID for production title
	$node_id = does_node_exist($nodes, $showname); // returns 0 if no match found
	echo $node_id . "\n";
	
	if ($node_id == 0){
		$node_id = set_node($showname, $prod_title_field_id);
	}
	echo $node_id . "\n";
	
	add_resource_to_nodes([$node_id]);
}

function create_field_tree(){
	global $remote_node_id, $showcode, $path_tree_field_id;
	$nodes = get_nodes($path_tree_field_id, $remote_node_id); // type field ID for file tree
	$node_id = does_node_exist($nodes, $showcode); // returns 0 if no match found
	
	if ($node_id == 0){
		$node_id = set_node($showcode, $path_tree_field_id, $remote_node_id);
	}
	
	add_resource_to_nodes([$remote_node_id, $node_id]);
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

function get_nodes($ref, $parent=null){
	global $private_key, $user, $url, $resource_id, $remote_node_id;
	
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

// make more modular
function add_resource_to_nodes($nodearray){
	global $private_key, $user, $url, $resource_id; 
	
	$nodestring = implode(',', $nodearray);

	$data = [
	    'user' => $user,
	    'function' => 'add_resource_nodes',
	    'resource' => $resource_id,
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
	//print_r($curl_response);
	
}

function set_dropbox_link(){
	global $private_key, $user, $url, $resource_id, $dropboxLink;

	$data = [
	    'user' => $user,
	    'function' => 'update_field',
	    'resource' => $resource_id,
		'field' => 103, // type field ID for Title
		'value' => $dropboxLink,
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
	
}


// Path to search
//need to pass directory with objects at the end... less to recurse but is this a good idea? consider changing, in case archive structure changes in the future

if ($argc > 1) {
    $searchDir  = $argv[1];
    echo "Processing dir: $searchDir\n";
    if ($argc > 2) {
    	$dropboxLink = $argv[2];
    }
} else {
    echo "No filename provided.\n";
    die();
}

findWindowMp4Files($searchDir);
//findAllFiles($searchDir);
extractShowCode($searchDir);
createResource();
uploadFile();
//uploadAltFiles();
checkandCreateFC();
set_title();
set_asset_type();
set_file_path();
set_production_title();
create_field_tree();
set_dropbox_link();


echo "Resource ID: " . $resource_id . PHP_EOL;
echo "Show code: " . $showcode . PHP_EOL;

//uploadFile();


