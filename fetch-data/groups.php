<?php
require_once 'fb.php';

$gID = '179249120741';

$response = fb_GET_request($fb, $gID);
$gNode = $response->getGraphObject();

$output = create_output_structure($gNode->getField('name'), 'group', $gID);

$response = fb_GET_request($fb, $gID . '/feed');

$postsEdge = $response->getGraphEdge();

foreach ($postsEdge as $pNode) {
	$pData = create_post_structure($pNode);
	if ($pData) {
		array_push($output['data'], $pData);
	}
}

deliver_json($output);