<?php
require_once 'fb.php';

$helper = $fb->getRedirectLoginHelper();

$loginUrl = $helper->getLoginUrl(BASE_URL . '/login-callback.php');

echo '<a href="' . $loginUrl . '">Log in with Facebook!</a>';

require_once 'done.php';