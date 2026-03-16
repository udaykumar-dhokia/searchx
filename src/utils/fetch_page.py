import os

import certifi
import httpx

def fetch_page(url: str, verify: bool | str | None = None) -> str:
    """Fetch the HTML content of a web page using HTTP GET.

    Args:
        url (str): The URL of the web page to fetch.
        verify (bool|str|None): SSL verification settings.
            - None (default): uses `certifi` bundle for verification.
            - False: disables SSL verification (not recommended).
            - str: path to a CA bundle file.

    Returns:
        str: The HTML content of the page.

    Raises:
        httpx.RequestError: If the request fails due to network issues or invalid URL.
        httpx.TimeoutException: If the request takes longer than the specified timeout.
    """

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
    r = httpx.get(url=url, timeout=30, headers=headers, verify=verify)
    return r.text