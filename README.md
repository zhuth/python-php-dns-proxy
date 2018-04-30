# python-php-dns-proxy

This is an renewed version for [DnsProxy](https://github.com/zhuth/DnsProxy).

- Put `resolve.php` on your server. The server may use DDNS.
- Add extra authentication when applicable in order to prevent abuse, e.g. use `.htaccess` and `.htpasswd`.
- For macOS users, rename as you like and put the `.plist` file in `/Library/LaunchDaemons`, then enable it via `launchctl`.
```shell
sudo launchctl load -w info.innovors.dnsproxy
```
You must examine the `.plist` file and change the paths to your actucal position of `dnsproxy.py`.
Python 2.7 is required. `dnslib` and `requests` are required.
