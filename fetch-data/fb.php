<?php
require_once 'vendor/autoload.php';

require_once 'conf.php';

$requestsDefaultLimit = 100;
$requestsGroupPostFields = 'message,from{first_name,last_name},story,created_time,updated_time,comments';
$requestsPagePostFields = 'message,from{name},story,created_time,updated_time,comments{message,from{name},created_time,comment_count}';	// somehow "from{first_name,last_name}" does not work here

function redirect_to($path) {
	header('Location: ' . BASE_URL . '/' . $path);
	exit;
}

function create_output_structure($name, $type, $fbId) {
	return [
	    'meta' => [
	    	'name' => $name,
	    	'type' => $type,
	    	'fb_id' => $fbId,
	    	'date' => strftime('%Y-%m-%d %H:%M:%S'),
		],
		'data' => [],
	];
}

function create_post_structure($pNode) {
	$msg = $pNode->getField('message');
	if (is_null($msg)) {
		return null;
	}
	
	$fromName = null;
	if ($pNode->getField('from') && is_object($pNode->getField('from')) && $pNode->getField('from')->getField('first_name') && $pNode->getField('from')->getField('last_name')) {
		$fromName = $pNode->getField('from')->getField('first_name') . ' ' . $pNode->getField('from')->getField('last_name');
	} else if ($pNode->getField('from') && is_object($pNode->getField('from')) && $pNode->getField('from')->getField('name')) {
		$fromName = $pNode->getField('from')->getField('name');
	} else if ($pNode->getField('story')) {
		$p = explode(' ', $pNode->getField('story'));
		if (count($p) >= 2) {
			$fromName = implode(' ', [$p[0], $p[1]]);
		}
	}
	
	$time = null;
	if ($pNode->getField('updated_time')) {
		$timeObj = $pNode->getField('updated_time');
	} else {
		$timeObj = $pNode->getField('created_time');	
	}
	if ($timeObj) {
		$time = $timeObj->format('Y-m-d H:i:s');
	}

	return [
		'date' => $time,
		'from' => $fromName,
		'message' => $msg,
		'comments' => [],	// nested array of comments consisting of post structure
	];
}

function deliver_json($data) {
	header('Content-Type: application/json; charset=utf-8');
	echo json_encode($data);
}

function fb_GET_request($path, $fields=null, $limit=null, $addParams=[]) {
	global $fb;
	
	$params = $addParams;

	if ($fields) {
		array_push($params, 'fields=' . $fields);
	}

	if (!is_null($limit)) {
		array_push($params, 'limit=' . $limit);
	}

	$paramsStr = '';
	if (count($params) > 0) {
		$paramsStr = '?' . implode('&', $params);
	}

	$requestURL = '/' . $path . $paramsStr;

	// Send the request to Graph
	try {
		$response = $fb->get($requestURL);
	} catch(Facebook\Exceptions\FacebookResponseException $e) {
	  // When Graph returns an error
	  echo 'Graph returned an error: ' . $e->getMessage();
	  exit;
	} catch(Facebook\Exceptions\FacebookSDKException $e) {
	  // When validation fails or other local issues
	  echo 'Facebook SDK returned an error: ' . $e->getMessage();
	  exit;
	}
	
	return $response;
}


if(!session_id()) {
    session_start();
}

$fbAccessToken = isset($_SESSION['facebook_access_token']) ? $_SESSION['facebook_access_token'] : null;

$fb = new Facebook\Facebook([
  'app_id' => APP_ID,
  'app_secret' => APP_SECRET,
  'default_graph_version' => 'v2.5',
]);

$userNode = null;
if ($fbAccessToken) {
	$fb->setDefaultAccessToken($fbAccessToken);
	
	$response = fb_GET_request('me');
	$userNode = $response->getGraphUser();
}