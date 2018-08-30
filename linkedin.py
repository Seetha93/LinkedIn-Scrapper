import sys
import subprocess
import requests
import xlsxwriter
import config
from bs4 import BeautifulSoup
import json, threading
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class LinkedIn:
	def __init__(self):
		# self.client = requests.Session()

		# HOMEPAGE_URL = 'https://www.linkedin.com'
		# LOGIN_URL = 'https://www.linkedin.com/uas/login-submit'

		# html = self.client.get(HOMEPAGE_URL).content
		# soup = BeautifulSoup(html, "html.parser")
		# csrf = soup.find(id="loginCsrfParam-login")['value']

		# login_information = {
		#     'session_key': config.linkedin['username'],
		#     'session_password': config.linkedin['password'],
		#     'loginCsrfParam': csrf,
		# }

		self.headers = {'Csrf-Token':'ajax:7736867257193100830'}
		self.cookies = self.authenticate()
		
		self.results = []

		# self.client.post(LOGIN_URL, data=login_information)

		# self.driver = webdriver.Chrome()
		# self.driver.get('https://www.linkedin.com/')
		# self.driver.find_element_by_xpath('//*[@id="login-email"]').send_keys(config.linkedin['username'])
		# self.driver.find_element_by_xpath('//*[@id="login-password"]').send_keys(config.linkedin['password'])
		# self.driver.find_element_by_xpath('//*[@id="login-submit"]').click()
		# time.sleep(5)

	## Function to authenticate for search results page
	def authenticate(self):
	    try:
	        session = subprocess.Popen(['python', 'login.py'], stdout=subprocess.PIPE).communicate()[0].replace("\n","")
	        print "[Info] Connecting with linkedin"  
	        if len(session) == 0:
	            sys.exit("[Error] Unable to login to LinkedIn.com")
	        print "[Info] Obtained new session: %s" % session
	        cookies = dict(li_at=session)
	    except Exception, e:
	        sys.exit("[Fatal] Could not authenticate to linkedin. %s" % e)
	    return cookies

	#	Input : Name of the customer from customer.csv
	#	The goal of this function is to get the search results based on the name and filter the results 
	#	based on location (indiana). 
	def search(self, name):
		# Fetch the initial page to get results/page counts
	    url = "https://www.linkedin.com/voyager/api/search/cluster?count=40&guides=List(v-%%3EPEOPLE,facetGeoRegion-%%3Ear%%3A0)&keywords=%s&origin=FACETED_SEARCH&q=guided&start=0" % name
	    
	    self.cookies['JSESSIONID'] = 'ajax:7736867257193100830'
	    self.cookies['X-RestLi-Protocol-Version'] = '2.0.0' 

	    r = requests.get(url, cookies=self.cookies, headers=self.headers)
	    content = json.loads(r.text)
	    data_total = content['paging']['total']
	    
	    # Calculate pages off final results at 40 results/page
	    pages = data_total / 40
	    if data_total % 40 == 0:
	        # Becuase we count 0... Subtract a page if there are no left over results on the last page
	        pages = pages - 1 
	    if pages == 0: 
	        pages = 1
	    
	    print "[Info] %i Results Found" % data_total
	    if data_total > 1000:
	        pages = 24
	        print "[Notice] LinkedIn only allows 1000 results. Refine keywords to capture all data"
	    print "[Info] Fetching %i Pages" % pages
	    print
	    results = []
		
	    for p in range(pages):
	        # Request results for each page using the start offset
	        url = "https://www.linkedin.com/voyager/api/search/cluster?count=40&guides=List()&keywords=%s&origin=GLOBAL_SEARCH_HEADER&q=guided&searchId=1489295486936&start=%i" % (name, p*40)
	        url = "https://www.linkedin.com/voyager/api/search/cluster?count=40&guides=List(v-%%3EPEOPLE,facetGeoRegion-%%3Ear%%3A0)&keywords=%s&origin=FACETED_SEARCH&q=guided&start=%i" % (name, p*40)
	        
	        r = requests.get(url, cookies=self.cookies, headers=self.headers)
	        content = r.text.encode('UTF-8')
	        content = json.loads(content)
	        # print "[Info] Fetching page %i with %i results" % (p+1,len(content['elements'][0]['elements']))
	        for c in content['elements'][0]['elements']:
	            try:
	               	if c['hitInfo']['com.linkedin.voyager.search.SearchProfile']['headless'] == False:
	                    try:
	                        data_industry = c['hitInfo']['com.linkedin.voyager.search.SearchProfile']['industry']
	                    except:
	                        data_industry = ""  

	                    if( 'indiana' in c['hitInfo']['com.linkedin.voyager.search.SearchProfile']['location'].lower()):
		                    results.append({
		                    	'first_name' :  c['hitInfo']['com.linkedin.voyager.search.SearchProfile']['miniProfile']['firstName'], 
		                    	'last_name': c['hitInfo']['com.linkedin.voyager.search.SearchProfile']['miniProfile']['lastName'], 
		                    	'location' : c['hitInfo']['com.linkedin.voyager.search.SearchProfile']['location'], 
		                    	'occupation' :  c['hitInfo']['com.linkedin.voyager.search.SearchProfile']['miniProfile']['occupation'],
		                    	'url' : "https://www.linkedin.com/in/%s" % c['hitInfo']['com.linkedin.voyager.search.SearchProfile']['miniProfile']['publicIdentifier']
		                    })
	            except:
	            	continue
	            
	    return results    

	#	The aim of this function is to :
	#		1. Open browser
	#		2. Sign into a valid login account
	def start_driver(self):
		self.driver = webdriver.Chrome()
		self.driver.get('https://www.linkedin.com/')
		self.driver.find_element_by_xpath('//*[@id="login-email"]').send_keys(config.linkedin['username'])
		self.driver.find_element_by_xpath('//*[@id="login-password"]').send_keys(config.linkedin['password'])
		self.driver.find_element_by_xpath('//*[@id="login-submit"]').click()
		time.sleep(5)

	
	#	Input : Linkedin url
	#	The goal of this function is to scrap the data from the url passed and return 
	#	Number of jobs, Current Company, Current Position data as an object.
	#	Also this function makes use of the browser opened using selenium to load the page(
	#	to avoid captcha issues.Its almost a hack for now)
	def get_profile_data(self, url):
		number_of_companies = 0
		current_position = []
		current_company = []
		job_start_date = ''

		# res = self.client.get(url)
		self.driver.get(url)
		html = self.driver.find_element_by_tag_name('html')
		html.send_keys(Keys.END)
		time.sleep(10)
		soup = BeautifulSoup(self.driver.page_source, 'html')
		positions = soup.findAll('li', {'class' : 'pv-position-entity'})
		hidden_position = soup.find('button', {'class' : 'pv-profile-section__see-more-inline'})
		print hidden_position
		hidden_positions = 0
		if hidden_position is not None:
			hidden_positions = int(hidden_position.text.split("Show")[1].split("more")[0])
		print len(positions)
		print hidden_positions

		if len(positions) > 0:
			# number_of_companies = len(positions) + hidden_positions
			number_of_companies = len(positions) + hidden_positions
			current_position = positions[0].find('h3').text
			current_company = positions[0].find('h4').text.split("Company Name")[1]
			date_field = positions[0].find('h4', {'class': 'pv-entity__date-range'})
			if date_field is not None:
				job_start_date = date_field.findAll('span')[1].text.split(u'\u2013')[0]
			# print {
			# 	'no_of_jobs' : number_of_companies, 
			# 	'current_position' : current_position,
			# 	'current_company': current_company,
			# 	'job_start_date': job_start_date
			# }
			# print "******"
		
		        

		return {
					'no_of_jobs' : number_of_companies, 
					'current_position' : current_position,
					'current_company': current_company,
					'job_start_date': job_start_date
				}

	# Function to close the browser
	def logout(self):
		self.driver.close()