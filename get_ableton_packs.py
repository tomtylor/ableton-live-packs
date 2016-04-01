import requests
import re
import os
import sys
import urllib
import getpass

from clint.textui import progress

def download_file(url, filename):
	r = requests.get(url, stream=True)
	with open(filename, 'wb') as f:
		total_length = int(r.headers.get('content-length'))
		for chunk in progress.bar(r.iter_content(chunk_size=1024), expected_size=(total_length/1024) + 1): 
			if chunk:
				f.write(chunk)
				f.flush()

with requests.Session() as c:

	# Change to your destination!
	DIRNAME = '/Volumes/DATA/AbletonPacks/'
	USERNAME = raw_input('Username:')
	PASSWORD = getpass.getpass()
	URL = 'https://www.ableton.com/en/login/'
	PACKS = 'https://www.ableton.com/en/packs/'

	c.get(URL)
	cookies = c.cookies
	csrftoken = cookies['csrftoken']
	login_data = dict(username=USERNAME, password=PASSWORD, next='/en/account/', csrfmiddlewaretoken=csrftoken)
	r = c.post(URL, data = login_data, headers={"Referer": "https://www.ableton.com/", 'user-agent': 'my-app/0.0.1'})
	
	# print r.status_code
	# if(int(r.status_code) == 200):
	# 	print "Status code:",r.status_code,"Logged in successfully!"
	# else:
	# 	print "Wrong credentials - status code:",r.status_code
	# sys.exit()
	
	page = c.get(PACKS)
	page_source_code = page.text
	p = re.compile('http://cdn2-downloads\.ableton.com.*?\.alp', re.IGNORECASE)
	m_all = p.findall(page_source_code)
	
	print "\n###"
	print "Changing folder to '"+DIRNAME+"'"; 
	print "###\n"
	os.chdir(DIRNAME);

	i = 0
	for match in m_all:

		i += 1
		
		pack_name = re.match('.+/([A-Za-z0-9-_\.]+\.alp)', match)
		pack_name = pack_name.group(1)
		alpurl = re.sub(r" &amp; ", "%20&%20", match)
		category = re.sub(r" &amp; ", "_", match)
		category = re.match('^http.+\/livepacks\/(.*?)\/', category)
		category_name = category.group(1)
		
		file_path = DIRNAME+category_name+"/"+pack_name
		
		remote_file = urllib.urlopen(alpurl)
		remote_file_meta = remote_file.info()
		remote_file_size = remote_file_meta.getheaders("Content-Length")[0]
		
		if os.path.exists(file_path) and os.access(file_path, os.R_OK):
			f = open(file_path, "rb")
			file_size_on_disk = len(f.read())
			print "Pack",pack_name,"already exists"
			f.close()

			if int(remote_file_size) != int(file_size_on_disk):
				print "Remote file (",remote_file_size,") seems to be newer than the local file (",file_size_on_disk,")"
				print "Downloading file",pack_name
				download_file(alpurl,pack_name)
				print "Moving pack_name to "+category_name
				os.rename(pack_name, category_name+"/"+pack_name)	
				print "Done replacing\n"
		else:
			if int(remote_file_size) > 1:
				print "Pack",pack_name,"does not exist! Downloading..."
				if not os.path.exists(category_name):
					print "Creating folder "+category_name+"\n"
					os.makedirs(category_name)
				download_file(alpurl,pack_name)
				print "Moving pack_name to "+category_name
				os.rename(pack_name, category_name+"/"+pack_name)	
				print "Done creating\n"
