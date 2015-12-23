<?php
define('APP_ID', '...');
define('APP_SECRET', '...');
define('BASE_URL', 'http://example.com/some/path');
define('CHUNK_PER_DAYS', 14);
define('SLEEP_PER_CHUNK_SEC', 1);
define('SEC_PER_DAY', 60*60*24);

// get IDs from: http://lookup-id.com/
// add as: '<LABEL>' => [<FB-ID>, '<STARTDATE>', '<ENDDATE>'],
$CONF_GROUP_IDS = [
	'berlin_kostenlos' => [179249120741, '2015-12-10', '2015-12-15'],
	'berlin_veranstaltungen' => [597696046982625, '2015-12-10', '2015-12-15'],
];

$CONF_PAGE_IDS = [
	'some_page' => [12345, '2015-12-01', '2015-12-31'],
];