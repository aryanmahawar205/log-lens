import os
import random
import datetime

# Reuse some variables from generate_validation.py for simplicity if needed, but we can just write a standalone script.
DATASETS_DIR = "validation/datasets/enterprise/"
os.makedirs(DATASETS_DIR, exist_ok=True)

IPS = [f"192.168.1.{i}" for i in range(1, 20)] + ["8.8.8.8", "1.1.1.1", "10.0.0.5"]
METHODS = ["GET", "POST", "HEAD", "PUT", "DELETE"]
URLS = ["/index.html", "/api/data", "/login", "/dashboard", "/images/logo.png", "/about"]
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Googlebot/2.1 (+http://www.google.com/bot.html)",
    "python-requests/2.25.1"
]

def generate_apache_combined(dt, ip, method, url, status, bytes_sent, referer, ua):
    ts = dt.strftime("%d/%b/%Y:%H:%M:%S +0000")
    return f'{ip} - - [{ts}] "{method} {url} HTTP/1.1" {status} {bytes_sent} "{referer}" "{ua}"'

def generate_nginx(dt, ip, method, url, status, bytes_sent, referer, ua):
    ts = dt.strftime("%d/%b/%Y:%H:%M:%S +0000")
    # nginx default combined is basically the same as apache combined in most setups, we'll use slightly different time format if needed, but standard is fine
    return f'{ip} - - [{ts}] "{method} {url} HTTP/1.1" {status} {bytes_sent} "{referer}" "{ua}"'

def generate_iis(dt, ip, method, url, status, bytes_sent, referer, ua, latency):
    d = dt.strftime("%Y-%m-%d")
    t = dt.strftime("%H:%M:%S")
    return f"{d} {t} 10.0.0.1 {method} {url} - 80 - {ip} {ua.replace(' ', '+')} {referer.replace(' ', '+')} {status} 0 0 {latency}"

START_DATE = datetime.datetime.now() - datetime.timedelta(days=180)

# Generate 20 files spanning months
for file_idx in range(1, 21):
    num_lines = random.randint(500, 2000)
    current_time = START_DATE + datetime.timedelta(days=file_idx * 9) # spread over ~180 days

    server_type = random.choice(["apache", "nginx", "iis"])
    filename = f"{server_type}_access_{file_idx:02d}.log"
    filepath = os.path.join(DATASETS_DIR, filename)

    lines = []

    # IIS needs headers
    if server_type == "iis":
        lines.append("#Software: Microsoft Internet Information Services 10.0")
        lines.append("#Version: 1.0")
        lines.append(f"#Date: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("#Fields: date time s-ip cs-method cs-uri-stem cs-uri-query s-port cs-username c-ip cs(User-Agent) cs(Referer) sc-status sc-substatus sc-win32-status time-taken")

    for _ in range(num_lines):
        ip = random.choice(IPS)
        method = random.choice(METHODS)
        url = random.choice(URLS)
        status = random.choice([200, 200, 200, 404, 301, 500])
        bytes_sent = random.randint(500, 50000)
        referer = "-"
        ua = random.choice(USER_AGENTS)
        latency = random.randint(10, 500)

        # Anomalies
        rand = random.random()
        if rand < 0.05: # attack
            url = "/index.php?id=1+UNION+SELECT+1,2,3--"
            ua = "sqlmap/1.5.2"
        elif rand < 0.10: # recon
            url = "/.env"
            status = 404
        elif rand < 0.15: # 500 spike
            status = 500

        if server_type == "apache":
            lines.append(generate_apache_combined(current_time, ip, method, url, status, bytes_sent, referer, ua))
        elif server_type == "nginx":
            lines.append(generate_nginx(current_time, ip, method, url, status, bytes_sent, referer, ua))
        elif server_type == "iis":
            lines.append(generate_iis(current_time, ip, method, url, status, bytes_sent, referer, ua, latency))

        current_time += datetime.timedelta(seconds=random.randint(1, 60))

    with open(filepath, "w") as f:
        f.write("\n".join(lines))

print("Enterprise dataset generated.")
