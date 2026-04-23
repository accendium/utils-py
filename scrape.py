import sys
import os
import pyperclip
import requests
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor


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


TEXT_COPY = """Parse the following images and output them into code blocks. Examples should go under an "Examples" section and problems under "Problems." Code blocks should be in the order: {order}. At the bottom have a section "Micro" which has a code block of a command to open all the files in micro **in order** ("micro first.cpp second.cpp third.cpp...") top to bottom in the order described here. A section should look like this minimal schema:

**Examples**

```cpp
// code goes here
```

```cpp
// another code example here
```"""


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


def copy_template_prompt(names: list[str]) -> None:
    copy = TEXT_COPY.format(order=", ".join(names))
    pyperclip.copy(copy)
    print(f"Copied the following to clipboard:\n\n {copy}")


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <page_url>")
        raise SystemExit(1)

    names: list[str] = []
    image_urls = [img for img in get_image_urls(sys.argv[1]) if "favicon" not in img]
    with ThreadPoolExecutor(8) as ex:
        for image_url, ok in zip(image_urls, ex.map(download_image, image_urls)):
            if ok:
                names.append(image_url.rsplit("/", 1)[-1].rsplit(".", 1)[0])
    copy_template_prompt(names)


if __name__ == "__main__":
    main()
