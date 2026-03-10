import sys
import os
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import requests


IMAGE_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".svg",
    ".bmp",
    ".ico",
    ".tif",
    ".tiff",
    ".avif",
)


def looks_like_image(url: str) -> bool:
    path = urlparse(url).path.lower()
    return path.endswith(IMAGE_EXTENSIONS)


class ImageParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url
        self.images: list[str] = []
        self.seen: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for attr_name, value in attrs:
            if not value:
                continue

            if attr_name in {"src", "data-src", "href", "poster"}:
                self.add_url(value)
            elif attr_name in {"srcset", "data-srcset"}:
                for item in value.split(","):
                    self.add_url(item.strip().split(" ")[0])

    def add_url(self, value: str) -> None:
        absolute_url = urljoin(self.base_url, value.strip())
        if looks_like_image(absolute_url) and absolute_url not in self.seen:
            self.seen.add(absolute_url)
            self.images.append(absolute_url)


def get_image_urls(page_url: str) -> list[str]:
    response = requests.get(page_url, timeout=15)
    response.raise_for_status()

    parser = ImageParser(page_url)
    parser.feed(response.text)
    return parser.images


def download_image(url: str, output: str = "output") -> bool:
    print(f"Downloading {url}")
    try:
        res = requests.get(url, timeout=15, stream=True)
        res.raise_for_status()

        parsed = urlparse(url)
        filename = parsed.path.rsplit("/", 1)[-1] or "image"

        if not any(filename.lower().endswith(ext) for ext in IMAGE_EXTENSIONS):
            filename += ".jpg"
        
        os.makedirs(output, exist_ok=True)
        filepath = os.path.join(output, filename)

        with open(filepath, "wb") as f:
            for chunk in res.iter_content(8192):
                if chunk:
                    f.write(chunk)
        print(f"Downloaded {filename} from {url} to {output}")
        return True
    except Exception as e:
        print(f"Failed to download image from {url}: {e}")
        return False


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scrape.py <page_url>")
        raise SystemExit(1)

    for image_url in get_image_urls(sys.argv[1]):
        download_image(image_url)


if __name__ == "__main__":
    main()