<?php
require_once 'fb.php';

if (!$fbAccessToken) {
	redirect_to('login.php');
}

$output = collect_posts($CONF_GROUP_IDS, 'feed');

deliver_json($output);
