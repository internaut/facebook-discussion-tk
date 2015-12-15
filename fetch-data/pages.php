<?php
require_once 'fb.php';

if (!$fbAccessToken) {
	redirect_to('login.php');
}

$output = [];

function comments_from_post($pNode, &$data) {
	$commentCount = $pNode->getField('comment_count');
	$commentsEdge = $pNode->getField('comments');
	
	if (!$data) {
		return;
	}
	
	$refetch = false;
	if (!$commentsEdge && $pNode && !is_null($commentCount) && $commentCount > 0) {
		$cID = $pNode->getField('id');
		if ($cID) {
			$response = fb_GET_request($cID . '/comments', 'message,from{name},created_time,updated_time,comments,comment_count');
			$commentsEdge = $response->getGraphEdge();
			$refetch = true;
		}
	}
	
	if (!$commentsEdge) {
		return;
	}
	
	foreach ($commentsEdge as $cNode) {
		$cData = create_post_structure($cNode);
		if (is_null($cData)) {
			continue;
		}
		
		comments_from_post($cNode, $cData);
		
		array_push($data['comments'], $cData);
	}
}

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
			
			// now go through the comments
			comments_from_post($pNode, $pData);
			
			// add it to the overall output
			if ($pData) {
				array_push($pOutput['data'], $pData);
			}
		}
	} while ($postsEdge = $fb->next($postsEdge));

	$output[$pLabel] = $pOutput;
}

deliver_json($output);