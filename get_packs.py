import requests
import re
import sys
import os
import getpass
import pprint
import logging

from clint.textui import progress
from hurry.filesize import size
from urllib.request import urlopen

# Config
debug = 0
pp = pprint.PrettyPrinter(indent=4)
logging.basicConfig(level=logging.DEBUG)
# Change to your directory!
DIR_NAME = "/home/tk5149/Downloads/AbletonPacks/"
USERNAME = input('Username:')
PASSWORD = getpass.getpass()
URL = 'https://www.ableton.com/en/login/'
PACKS = 'https://www.ableton.com/en/packs/'


################## LOCAL FUNCTIONS #################

def _download_file(url, filename):
    r = requests.get(url, stream=True)
    with open(filename, 'wb') as f:
        total_length = int(r.headers.get('content-length'))
        for chunk in progress.bar(r.iter_content(chunk_size=1024), expected_size=(total_length / 1024) + 1):
            if chunk:
                f.write(chunk)
                f.flush()


with requests.Session() as c:
    c.keep_alive = False
    c.get(URL)
    cookies = c.cookies
    csrftoken = cookies['csrftoken']
    login_data = dict(username=USERNAME, password=PASSWORD,
                      next='/en/account/', csrfmiddlewaretoken=csrftoken)
    r = c.post(URL, data=login_data, headers={
               "Referer": "https://www.ableton.com/", 'user-agent': 'my-app/0.0.1'})

    if int(r.status_code) == 200:
        print("### Status code:", r.status_code, "Logged in successfully! ###")
    else:
        print("### Wrong credentials - status code:", r.status_code, " ###")

    page = c.get(PACKS)
    page_source_code = page.text
    p = re.compile("https*?://cdn-downloads.ableton.com.*?.alp", re.IGNORECASE)
    m_all = p.findall(page_source_code)

    # pp.pprint(m_all)
    # print(len(m_all))
    # sys.exit()

    if debug == 1:
        print("### Changing folder to \"" + DIR_NAME + "\" ###")
    os.chdir(DIR_NAME)

    for match in m_all:
        pack_name = re.match(".+/([A-Za-z0-9-_.]+.alp)", match)
        pack_name = pack_name.group(1)
        alp_url = re.sub(r" &amp; ", "%20&%20", match)
        category = re.sub(r" &amp; ", "_", match)
        category = re.match('^http.+/livepacks/(.*?)/', category)
        category_name = category.group(1)

        if debug == 1:
            print("{}{}{}{}".format("/", category_name, "/", pack_name))

        file_path = DIR_NAME + category_name + "/" + pack_name
        remote_file = urlopen(alp_url)
        remote_file_size = remote_file.headers['Content-Length']

        if int(remote_file_size) <= 10485760:
            if int(remote_file_size) > 0:
                if os.path.exists(file_path) and os.access(file_path, os.R_OK):
                    stat_info = os.stat(file_path)
                    file_size_on_disk = stat_info.st_size
                    print("Pack", pack_name, "already exists")

                    if int(remote_file_size) != int(file_size_on_disk):
                        print("Remote file", pack_name, "seems to be newer than local file (", size(int(remote_file_size)),
                              "compared to", size(int(file_size_on_disk)), ")")
                        _download_file(alp_url, pack_name)
                        print("Moving pack_name to \"" +
                              category_name + "\" folder")
                        os.rename(pack_name, category_name + "/" + pack_name)
                        print("Downloading complete")
                else:
                    if int(remote_file_size) > 1:
                        print("Pack", pack_name,
                              "does not exist! Downloading...")
                        if not os.path.exists(category_name):
                            print("Creating folder \"" + category_name + "\"")
                            os.makedirs(category_name)
                        _download_file(alp_url, pack_name)
                        print("Moving pack_name to (", category_name, ") folder")
                        os.rename(pack_name, category_name + "/" + pack_name)
                        print("Downloading complete ")