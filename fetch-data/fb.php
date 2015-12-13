<?php
require_once 'vendor/autoload.php';

require_once 'conf.php';


if(!session_id()) {
    session_start();
}

$fb = new Facebook\Facebook([
  'app_id' => APP_ID,
  'app_secret' => APP_SECRET,
  'default_graph_version' => 'v2.2',
]);