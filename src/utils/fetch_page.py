import httpx

def fetch_page(url):
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
    }
    r = httpx.get(url=url, timeout=10, headers=headers)
    return r.text