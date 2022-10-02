# Downloads all interesting hrefs from a webpage

import functools
import os
import re
import urllib
from pathlib import Path
import asyncio
from typing import Callable, List
import argparse
import functools

import httpx
import aiofiles
import aiofiles.os


GET_KWARGS = {
    # 'auth': ('user', 'password'),
    'headers': {
        'User-Agent': 'httpx/python'
    }
}
"""Additions arguments for requests."""



async def download_href(base_url: str, href: str, http: httpx.AsyncClient, downloading_semaphore: asyncio.Semaphore) -> str:
    """Downloads the (relative or absolute) `href`, i.e. saves it to a file if it doesn't exist yet.
    If the `href` is relative, it is interpreted relative to `base_url`.
    Downloading is limited by the `downloading_semaphore`."""

    # Make the link absolute
    href = urllib.parse.urljoin(base_url, href)

    # Get filename (last part of the URL)
    filename = href.split('/')[-1]

    # Check if file is already downloaded
    if await aiofiles.os.path.exists(filename):
        print(f"File {filename} already exists, skipping")
        return
    
    async with downloading_semaphore:
        print(f'Downloading {href}')
        web_file_response = await http.get(href, **GET_KWARGS)
    web_file_response.raise_for_status()  # Raise exception if status code is not 2xx

    # Save the file to the filesystem
    print(f'Saving {href} to {filename}')
    async with aiofiles.open(filename, 'wb+') as file:
        await file.write(web_file_response.content)


def is_interesting_filetype(href: str, filetypes: List[str]) -> bool:
    """Returns whether the `href` has one of the filetypes mentioned in `filetypes`,
    i.e. whether the href should be downloaded."""

    return any(href.endswith(filetype) for filetype in filetypes)


async def get_interesting_links_in_page(url: str, http: httpx.AsyncClient, filetypes: List[str]) -> List[str]:
    """
    Returns all (absolute and relative) links in the page at `url`
    that have one of the filetypes mentioned in `filetypes`.
    """

    # Get the webpage
    response = await http.get(url, **GET_KWARGS, follow_redirects=True)
    response.raise_for_status()  # Raise exception if status code is not 2xx
    webpage = response.text

    # regex that finds href in a tag
    href_regex = re.compile(r'href=[\"\'](.*?)[\"\']')

    # Search for all hrefs in the webpage
    hrefs = href_regex.findall(webpage)

    # Filter out the hrefs that are not interesting
    hrefs = [href for href in hrefs if is_interesting_filetype(href=href, filetypes=filetypes)]

    return hrefs


async def switch_to_download_dir(download_dir: Path):
    """Switches to the download directory `download_dir`,
    so we don't have to care about the path when downloading."""

    # Create download directory if it not exists yet
    await aiofiles.os.makedirs(download_dir, exist_ok=True)

    # Change into download directory, so we don't have to specify the full path when downloading
    os.chdir(download_dir)


def parse_args() -> argparse.Namespace:
    """Parses the command line arguments."""

    parser = argparse.ArgumentParser(
        description='Downloads all interesting hrefs from a webpage',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('url', type=str, help='URL to the webpage to download hrefs from')
    parser.add_argument('--download_dir', type=Path, default=Path('./downloads'),
        help='Directory to save the downloaded files in')
    parser.add_argument('--filetypes', type=str, default=['.mp4', '.pdf', '.txt', '.zip'], nargs='+',
        help='Filetypes that should be downloaded')

    return parser.parse_args()


async def main(args: argparse.Namespace):
    await switch_to_download_dir(args.download_dir)

    async with httpx.AsyncClient() as http:
        hrefs = await get_interesting_links_in_page(url=args.url, http=http, filetypes=args.filetypes)

        # Fetch all hrefs concurrently
        # To avoid an unintentional DoS attack, we limit the number of concurrent downloads to 10
        downloading_semaphore = asyncio.Semaphore(10)
        download_href_partial: Callable = functools.partial(
            download_href,
            http=http, downloading_semaphore=downloading_semaphore, base_url=args.url
        )
        results = await asyncio.gather(*[download_href_partial(href=href) for href in hrefs])
    
    print(list(results))
    


if __name__ == '__main__':
    asyncio.run(main(parse_args()))
