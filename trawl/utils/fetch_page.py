import os
import certifi
import httpx
from urllib.parse import urlparse

def fetch_page(url: str, verify: bool | str | None = None) -> str:
    env_verify = os.getenv("HTTPX_VERIFY")
    if env_verify is not None:
        if env_verify.lower() in {"false", "0", "no", "off"}:
            verify = False
        else:
            verify = env_verify

    if verify is None:
        verify = certifi.where()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
    }

    try:
        r = httpx.get(url=url, timeout=30, headers=headers, verify=verify)
        r.raise_for_status()
        return r.text

    except httpx.ConnectError:
        try:
            r = httpx.get(url=url, timeout=30, headers=headers, verify=False)
            r.raise_for_status()
            return r.text
        except Exception:
            return ""

    except httpx.HTTPStatusError:
        return ""

    except httpx.TimeoutException:
        return ""   

    except Exception:
        return ""