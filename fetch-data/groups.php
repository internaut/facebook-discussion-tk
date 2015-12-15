<?php
require_once 'fb.php';

if (!$fbAccessToken) {
	redirect_to('login.php');
}

$output = [];

foreach ($CONF_GROUP_IDS as $gLabel => $gConf) {
	list($gID, $postsSince, $postsUntil) = $gConf;

	$response = fb_GET_request($gID);
	$gNode = $response->getGraphObject();

	$gOutput = create_output_structure($gNode->getField('name'), 'group', $gID);

	$extraParams = [];
	if ($postsSince) {
		array_push($extraParams, 'since=' . strtotime($postsSince));
	}
	if ($postsUntil) {
		array_push($extraParams, 'until=' . strtotime($postsUntil));
	}

	$response = fb_GET_request($gID . '/feed', $requestsGroupPostFields, $requestsDefaultLimit, $extraParams);
	$postsEdge = $response->getGraphEdge();

	do {
		foreach ($postsEdge as $pNode) {
			$pData = create_post_structure($pNode);
			if ($pData) {
				array_push($gOutput['data'], $pData);
			}
		}
	} while ($postsEdge = $fb->next($postsEdge));
	
	$output[$gLabel] = $gOutput;
}

deliver_json($output);