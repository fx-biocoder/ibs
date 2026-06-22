<?php
date_default_timezone_set("America/Argentina/Buenos_Aires");

require_once 'helpers/ibs_service.php';

if (isset($_GET['page']) && $_GET['page']) {
	$file = 'phpfiles/'.$_GET['page'].'.php';
	if (file_exists($file)) {
		require_once $file;
	} else {
		require_once 'phpfiles/404.php';
	}
} else {
	require_once 'phpfiles/home.php';
}
?>