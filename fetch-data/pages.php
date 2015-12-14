<?php
require_once 'fb.php';

if (!$fbAccessToken) {
	redirect_to('login.php');
}

$pID = '';

$response = fb_GET_request($pID);
$pgNode = $response->getGraphObject();

$output = create_output_structure($pgNode->getField('name'), 'page', $pID);

$response = fb_GET_request($pID . '/posts');

$postsEdge = $response->getGraphEdge();

foreach ($postsEdge as $pNode) {
	$pData = create_post_structure($pNode);
	if ($pData) {
		array_push($output['data'], $pData);
	}
}

deliver_json($output);