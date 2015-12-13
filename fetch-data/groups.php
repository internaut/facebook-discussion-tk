<?php
require_once 'fb.php';

if (!isset($_SESSION['facebook_access_token']) || !$_SESSION['facebook_access_token']) {
	header('Location: ' . BASE_URL . '/login.php');
	exit;
}

$fb->setDefaultAccessToken($_SESSION['facebook_access_token']);

try {
  $response = $fb->get('/me');
  $userNode = $response->getGraphUser();
} catch(Facebook\Exceptions\FacebookResponseException $e) {
  // When Graph returns an error
  echo 'Graph returned an error: ' . $e->getMessage();
  exit;
} catch(Facebook\Exceptions\FacebookSDKException $e) {
  // When validation fails or other local issues
  echo 'Facebook SDK returned an error: ' . $e->getMessage();
  exit;
}

echo '<pre>';
echo 'Logged in as ' . $userNode->getName() . "\n";

echo "fetching group posts...\n";

$request = $fb->request(
  'GET',
  '/55259308085/feed'
);

// Send the request to Graph
try {
  $response = $fb->getClient()->sendRequest($request);
} catch(Facebook\Exceptions\FacebookResponseException $e) {
  // When Graph returns an error
  echo 'Graph returned an error: ' . $e->getMessage();
  exit;
} catch(Facebook\Exceptions\FacebookSDKException $e) {
  // When validation fails or other local issues
  echo 'Facebook SDK returned an error: ' . $e->getMessage();
  exit;
}

$edge = $response->getGraphEdge();

foreach ($edge as $node) {
	var_dump($node);
}

echo '</pre>';