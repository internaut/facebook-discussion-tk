<?php
require_once 'fb.php';

if (!$fbAccessToken) {
	redirect_to('login.php');
}

$output = [];

foreach ($CONF_PAGE_IDS as $pLabel => $pConf) {
	list($pID, $postsSince, $postsUntil) = $pConf;

	$response = fb_GET_request($pID);
	$pgNode = $response->getGraphObject();

	$pOutput = create_output_structure($pgNode->getField('name'), 'page', $pID);
	
	$extraParams = [];
	if ($postsSince) {
		array_push($extraParams, 'since=' . strtotime($postsSince));
	}
	if ($postsUntil) {
		array_push($extraParams, 'until=' . strtotime($postsUntil));
	}

	$response = fb_GET_request($pID . '/feed', $requestsPagePostFields, $requestsDefaultLimit, $extraParams);
	$postsEdge = $response->getGraphEdge();

	do {
		foreach ($postsEdge as $pNode) {	// for each post of the page
			$pData = create_post_structure($pNode);
			if ($pData) {
				array_push($pOutput['data'], $pData);
			}
			
			// now go through the comments
			var_dump($pNode->getField('comments'));
		}
	} while ($postsEdge = $fb->next($postsEdge));

	$output[$pLabel] = $pOutput;
}

deliver_json($output);