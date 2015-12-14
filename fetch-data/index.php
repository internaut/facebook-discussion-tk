<?php
require_once 'fb.php';

if (!$fbAccessToken) {
	redirect_to('login.php');
}

require_once 'html_header.php';
?>

<p>Collect data as JSON:</p>

<ul>
	<li><a href="groups.php">Public Groups</a></li>
	<li><a href="pages.php">Public Pages</a></li>
</ul>

<?php
require_once 'html_footer.php';