import requests
import re
import os
import urllib.request
import getpass
import pprint
import logging

from clint.textui import progress
from hurry.filesize import size

# Config
debug = 1
pp = pprint.PrettyPrinter(indent=4)
logging.basicConfig(level=logging.DEBUG)
# Change to your directory!
DIRNAME = '/home/tk5149/AbletonPacks/'
USERNAME = input('Username:')
PASSWORD = getpass.getpass()
URL = 'https://www.ableton.com/en/login/'
PACKS = 'https://www.ableton.com/en/packs/'

################## LOCAL FUNCTIONS #################

def _download_file(url, filename):
    r = requests.get(url, stream=True)
    with open(filename, 'wb') as f:
        total_length = int(r.headers.get('content-length'))
        for chunk in progress.bar(r.iter_content(chunk_size=1024), expected_size=(total_length/1024) + 1):
            if chunk:
                f.write(chunk)
                f.flush()

with requests.Session() as c:

    c.keep_alive = False
    c.get(URL)
    cookies = c.cookies
    csrftoken = cookies['csrftoken']
    login_data = dict(username=USERNAME, password=PASSWORD, next='/en/account/', csrfmiddlewaretoken=csrftoken)
    r = c.post(URL, data = login_data, headers={"Referer": "https://www.ableton.com/", 'user-agent': 'my-app/0.0.1'})

    if int(r.status_code) == 200:
        print("### Status code:",r.status_code,"Logged in successfully! ###")
    else:
        print("### Wrong credentials - status code:",r.status_code," ###")

    page = c.get(PACKS)
    page_source_code = page.text
    p = re.compile('http://cdn2-downloads\.ableton.com.*?\.alp', re.IGNORECASE)
    m_all = p.findall(page_source_code)

    if debug == 1: print("### Changing folder to \""+DIRNAME+"\" ###")
    os.chdir(DIRNAME)

    for match in m_all:
        pack_name = re.match('.+/([A-Za-z0-9-_\.]+\.alp)', match)
        pack_name = pack_name.group(1)
        alpurl = re.sub(r" &amp; ", "%20&%20", match)
        category = re.sub(r" &amp; ", "_", match)
        category = re.match('^http.+\/livepacks\/(.*?)\/', category)
        category_name = category.group(1)

        # if debug == 1: print("{}{}{}{}".format("/",category_name,"/",pack_name))

        file_path = DIRNAME+category_name+"/"+pack_name
        remote_file = urllib.request.urlopen(alpurl)
        remote_file_size = remote_file.headers['Content-Length']

        if int(remote_file_size) <= 10485760:
            if os.path.exists(file_path) and os.access(file_path, os.R_OK):
                f = open(file_path, "rb")
                file_size_on_disk = len(f.read())
                print("Pack",pack_name,"already exists")
                f.close()

                if int(remote_file_size) != int(file_size_on_disk):
                    print("Remote file",pack_name,"seems to be newer than local file (",size(int(remote_file_size)),"compared to",size(int(file_size_on_disk)),")")
                    _download_file(alpurl,pack_name)
                    print("Moving pack_name to \""+category_name+"\" folder")
                    os.rename(pack_name, category_name+"/"+pack_name)
                    print("Downloading complete")
            else:
                if int(remote_file_size) > 1:
                    print("Pack",pack_name,"does not exist! Downloading...")
                    if not os.path.exists(category_name):
                        print("Creating folder \""+category_name+"\"")
                        os.makedirs(category_name)
                    _download_file(alpurl,pack_name)
                    print("Moving pack_name to (",category_name,") folder")
                    os.rename(pack_name, category_name+"/"+pack_name)
                    print("Downloading complete ")

