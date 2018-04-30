<?php
header('Content-Type: application/json');
$domain = $_GET['domain'];
$ip = dns_get_record($domain, +$_GET['type']);
if ($ip && $ip[0]['host'] != $domain) {
	$ip[] = array('host'=>$domain, 'ip'=>$ip[0]['host'], 'type'=>'CNAME', 'ttl'=>$ip[0]['ttl'], 'class'=>$ip[0]['class']);
}
echo json_encode($ip);
