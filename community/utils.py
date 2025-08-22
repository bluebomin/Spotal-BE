from urllib.parse import urlparse, unquote
from typing import Union

def s3_key_from_url(url: str, bucket: Union[str, None] = None) -> str:
    p = urlparse(url)
    path = unquote(p.path.lstrip("/"))
    if bucket:
        parts = path.split("/", 1)
        if parts and parts[0] == bucket and len(parts) > 1:
            return parts[1]
    return path
    
