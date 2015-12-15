<!doctype html>

<html lang="de">
<head>
  <meta charset="utf-8">
</head>

<body>

<h1>Collect data from Facebook</h1>

<p>
<?php
if ($userNode) {
	echo 'Logged in as ' . $userNode->getName();
} else {
	echo 'Not logged in';
}
?>
</p>