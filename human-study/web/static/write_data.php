<?php
header('Access-Control-Allow-Origin: evlabwebapps.mit.edu/*');
// get the data from the POST message
$post_data = json_decode(file_get_contents('php://input'), true);
// $post_data = $_POST;
$data = $post_data['filedata'];
$name = $post_data['filename'];
// the directory must be writable by the server
$fname = "../results/{$name}.json"; 
// write the file to disk
file_put_contents($fname, $data);
echo($fname)
?>