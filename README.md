# webdownloader

Ever needed to download all PDFs/MP4s/ZIPs linked on a webpage,
for example for downloading lecture notes?

webdownloader is a command line tool wrriten in Python/asyncio that does exactly that.


## Install requirements

    $ pip install -r requirements.txt


## Usage

    usage: webdownloader.py [-h] [--download_dir DOWNLOAD_DIR] [--filetypes FILETYPES [FILETYPES ...]] url

    Downloads all interesting hrefs from a webpage

    positional arguments:
    url                   URL to the webpage to download hrefs from

    optional arguments:
    -h, --help            show this help message and exit
    --download_dir DOWNLOAD_DIR
                            Directory to save the downloaded files in (default: downloads)
    --filetypes FILETYPES [FILETYPES ...]
                            Filetypes that should be downloaded (default: ['.mp4', '.pdf', '.txt', '.zip'])