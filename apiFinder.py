import urllib
from urllib.parse import urlparse, parse_qs
import tldextract
import sys
import re
import os
import time
import datetime
from browsermobproxy import Server
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
import selenium
import json
import codecs
from bs4 import BeautifulSoup
import time
import argparse
from apicall import APICall, APICallEncoder

class ApiFinder:

	browser = None

	def __init__(self, url, directory, searchString, removeParams, crawlApis):
		self.url = url
		self.directory = directory
		self.searchString = searchString
		self.removeParams = removeParams
		self.crawlApis = crawlApis
		self.contentTypesRecorded = ["text/html", "application/json", "application/xml"]
		self.browser = None

	def start(self):
		if self.crawlApis and self.url is None:
			print("Cannot crawl APIs in directory mode")
			exit(1)
		if self.removeParams and self.urls is None:
			print("WARNING: Must have Internet connection to remove unneeded parameters")
		#Scan for all APIs
		if self.url:
			if self.searchString is not None:
				print("Searching URL "+self.url+" for string "+self.searchString)
			#Move recursively through the site
			apiCalls = self.crawlingScan(self.url)
			
		#Scan directory of har files
		else:
			print("Parsing existing directory of har files")
			apiCalls = self.parseMultipleHars()

		self.outputAPIs(apiCalls)
		if self.browser is not None:
			self.browser.quit()

	def outputAPIs(self, apiCalls):
		print("API RESULTS ARE")
		jsonFile = open("output.json", "w")
		apiCalls = self.findPathVariables(apiCalls)
		for apiResult in apiCalls:
			print(apiResult.toString())
		self.outputHTML(apiCalls)
		jsonFile.write(json.dumps(apiCalls, cls=APICallEncoder))
		return

	def outputHTML(self, apiCalls):
		f = codecs.open("html_template.html", "r")
		template = f.read()
		templateParts = template.split("CALLSGOHERE")
		open('output.html', 'w').close()
		htmlFile = open('output.html', 'a')
		htmlFile.write(templateParts[0])
		for apiCall in apiCalls:
			htmlFile.write(apiCall.toHTML())
		htmlFile.write(templateParts[1])
		htmlFile.close()


	def createWebDriver(self):
		if self.browser:
			return self.browser
		fireBugPath = 'extensions/firebug-2.0.16.xpi'
		netExportPath = 'extensions/netExport-0.9b7.xpi'
		fireStarterPath = 'extensions/fireStarter-0.1a6.xpi'

		profile = webdriver.firefox.firefox_profile.FirefoxProfile();

		profile.add_extension(fireBugPath);
		profile.add_extension(netExportPath);
		profile.add_extension(fireStarterPath);

		#firefox preferences
		profile.set_preference("app.update.enabled", False)  
		profile.native_events_enabled = True
		profile.set_preference("webdriver.log.file", os.getcwd()+"/log.txt")
		#profile.set_preference("extensions.firebug.DBG_STARTER", True);

		profile.set_preference("extensions.firebug.currentVersion", "2.0.16")
		profile.set_preference("extensions.firebug.addonBarOpened", True)
		profile.set_preference("extensions.firebug.addonBarOpened", True)
		profile.set_preference("extensions.firebug.consoles.enableSite", True)						  

		profile.set_preference("extensions.firebug.console.enableSites", True)
		profile.set_preference("extensions.firebug.script.enableSites", True)
		profile.set_preference("extensions.firebug.net.enableSites", True)
		profile.set_preference("extensions.firebug.previousPlacement", 1)
		profile.set_preference("extensions.firebug.allPagesActivation", "on")
		profile.set_preference("extensions.firebug.onByDefault", True)
		profile.set_preference("extensions.firebug.defaultPanelName", "net")

		#set net export preferences
		profile.set_preference("extensions.firebug.netexport.alwaysEnableAutoExport", True)
		profile.set_preference("extensions.firebug.netexport.autoExportToFile", True)
		profile.set_preference("extensions.firebug.netexport.saveFiles", True)

		profile.set_preference("extensions.firebug.netexport.autoExportToServer", False)
		profile.set_preference("extensions.firebug.netexport.Automation", True)
		profile.set_preference("extensions.firebug.netexport.showPreview", False)
		#profile.set_preference("extensions.firebug.netexport.pageLoadedTimeout", 15000)
		#profile.set_preference("extensions.firebug.netexport.timeout", 10000)
		
		profile.set_preference("extensions.firebug.netexport.defaultLogDir", os.getcwd()+"/nextexport")
		##profile.set_preference("extensions.firebug.net.logLimit", 1000)
		profile.update_preferences();

		self.browser = webdriver.Firefox(firefox_profile=profile)
		self.browser.get("https://www.mozilla.org/en-US/")
		self.setup()
		time.sleep(5)
		return self.browser

	def openURL(self, url):
		browser = self.createWebDriver()
		try:
			browser.get(url) #load the url in firefox
		except WebDriverException as e:
			print("Error getting URL: "+url)
			print(format(e))
		time.sleep(3) #wait for the page to load
		browser.execute_script("window.scrollTo(0, document.body.scrollHeight/5);")
		time.sleep(1) #wait for the page to load
		browser.execute_script("window.scrollTo(0, document.body.scrollHeight/4);")
		time.sleep(1) #wait for the page to load
		browser.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
		time.sleep(1) #wait for the page to load
		browser.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
		time.sleep(1) #wait for the page to load
		browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")

		time.sleep(10) #wait for the page to load
		html = browser.page_source
		return html

	def findPathVariables(self, apiList):
		digits = re.compile('\d')
		for i in range(0,len(apiList)):
			for j in range(i+1, len(apiList)):
				paths1 = apiList[i].path.split('/')
				paths2 = apiList[j].path.split('/')
				if len(paths1) == len(paths2) and len(paths1) > 3:
					if paths1[:-1] == paths2[:-1]:
						paths1end = paths1[len(paths1)-1]
						paths2end = paths2[len(paths2)-1]
						if ('.' not in paths1end and '.' not in paths1end) or (digits.search(paths1end) and digits.search(paths2end)):
							#We can assume that they're the same API
							apiList[i].pathParams.add(paths1end)
							apiList[i].pathParams.add(paths2end)
							apiList[i].path = '/'.join(paths1[:-1])
							#Remove this later
							apiList[j].path = ''
		return [api for api in apiList if api.path != '']

	def isInternal(self, url, baseUrl):
		if url.startswith("/"):
			return baseUrl+url
		if tldextract.extract(baseUrl).domain == tldextract.extract(url).domain:
			return url
		return None


	def findInternalURLsInText(self, text, currentUrl, allFoundURLs):
		newUrls = []
		regex = re.compile(r'(https?://[\w]+\.)(com|org|biz|net)((/[\w]+)+)(\.[a-z]{2,4})?(\?[\w]+=[\w]+)?((&[\w]+=[\w]+)+)?', re.ASCII)

		matches = re.finditer(regex, text)

		for match in matches:
			print(str(match.group()))

	#Returns a list of all internal URLs on a page as long
	#as they are either relative URLs or contain the current domain name
	def findInternalURLs(self, bsObj, currentUrl, allFoundURLs):
		newUrls = []
		baseUrl = urlparse(currentUrl).scheme+"://"+urlparse(currentUrl).netloc
		#Finds all links that begin with a "/"
		for link in bsObj.findAll("a"):
			if 'href' in link.attrs:
				#baseUrl, urlInPage = parseUrl(link.attrs)
				url = link.attrs['href']
				#It's an internal URL and we haven't found it already
				url = self.isInternal(url, baseUrl)
				if url is not None and url not in newUrls and url not in allFoundURLs:
					newUrls.append(url)
					allFoundURLs.append(url)
		return allFoundURLs, newUrls


	def getContentType(self,headers):
		for header in headers:
			if header["name"] == "Content-Type":
				return header["value"]

	#Get rid of all the current har files
	def setup(self):
		files = os.listdir(self.directory)
		for singleFile in files:
			if "har" in singleFile:
				os.remove(self.directory+"/"+singleFile)

	def getAllHarFiles(self):
		files = os.listdir(self.directory)
		harFiles = []
		for filename in files:
			if "har" in filename:
				harFiles.append(self.directory+"/"+filename)
		return harFiles

	def readHarFile(self, harPath):
		f = codecs.open(harPath, "rb")
		harTxt = f.read().decode("utf-8", "replace")
		harObj = json.loads(harTxt)
		return harObj

	def getSingleHarFile(self):
		#f = open("nextexport/"+files[0], 'rb')
		harFiles = self.getAllHarFiles()
		if len(harFiles) < 1:
			return None
		#Get last harFile in the directory
		harFile = self.getAllHarFiles()[len(harFiles)-1]
		return self.readHarFile(harFile)


	def parseEntry(self, entry):
		url = entry["request"]["url"]
		method = entry["request"]["method"]
		params = dict()
		urlObj = urlparse(url)
		base = urlObj.scheme+"://"+urlObj.netloc
		mimeType = None
		responseSize = 0
		if "content" in entry["response"] and "mimeType" in entry["response"]["content"] and "text" in entry["response"]["content"]:
			if self.searchString is not None:
				if "text" not in entry["response"]["content"] or self.searchString not in entry["response"]["content"]["text"]:
					return None

			contentType = entry["response"]["content"]["mimeType"]
			responseSize = entry["response"]["content"]["size"]
			print("url is: "+url)
			content = entry["response"]["content"]["text"]
			if contentType is None:
				return None
			elif contentType.lower() in self.contentTypesRecorded:
				mimeType = contentType.lower()
			elif contentType.lower() == "application/gzip":
				print("GZIP ENTRY:\n"+entry)
			else:
				return None

			if method == "GET":
				params = parse_qs(urlObj.query, keep_blank_values=True)
			elif method == "POST":
				paramList = entry["request"]["postData"]["params"]
				if paramList is not None:
					for param in paramList:
						if param['name'] not in params:
							params[param['name']] = []
						params[param['name']].append(param['value'])
				elif entry["request"]["postData"]["text"] is not None:
					paramList = entry["request"]["postData"]["text"]
			apiCall = APICall(url, base, urlObj.path, mimeType, method, params, responseSize, content)
			return apiCall



	def scanHarfile(self,harObj, apiCalls = []):
		#Store the api call objects here
		entries = harObj["log"]["entries"]
		for entry in entries:
			call = self.parseEntry(entry)
			if call is not None:
				call.addToList(apiCalls, removeUnneededParams=self.removeParams)
		return apiCalls

	def parseMultipleHars(self):
		apiCalls = []
		harPaths = self.getAllHarFiles()
		print(harPaths)
		for harPath in harPaths:
			print("Parsing file: "+harPath)
			harObj = self.readHarFile(harPath)
			apiCalls = self.scanHarfile(harObj, apiCalls=apiCalls)
		return apiCalls

	#Performs a recursive crawl of a site, searching for APIs
	def crawlingScan(self, url, apiCalls = [], allFoundURLs = []):
		if self.searchString is not None and len(apiCalls) > 0:
			return apiCalls
		try:
			print("Scanning URL: "+url)
			html = self.openURL(url)
			bsObj = BeautifulSoup(html, "lxml")
			harObj = self.getSingleHarFile()
			apiCalls = self.scanHarfile(harObj, apiCalls=apiCalls)
			allFoundURLs, newUrls = self.findInternalURLs(bsObj, url, allFoundURLs)
			for newUrl in newUrls:
				self.crawlingScan(newUrl, apiCalls, allFoundURLs)
		except (KeyboardInterrupt, SystemExit):
			print("Stopping crawl")
			self.outputAPIs(apiCalls)
			exit(1)
		return apiCalls


#Clean up any existing har files
#setup()

parser = argparse.ArgumentParser()
parser.add_argument("-u", help="Target URL", nargs='?')
parser.add_argument("-d", help="Target directory", nargs='?')
parser.add_argument("-s", help="Search term", nargs='?')
parser.add_argument("-o", help="Optional (removeParams, crawlApis)", nargs='+')
args = parser.parse_args()

if not (args.u or args.d):
	print("Need to provide either a URL or search directory. Use -h for help")
	sys.exit(1)


apiCalls = None
removeParams = False
crawlApis = False

if args.d is None:
	args.d = "nextexport"

if args.o is not None:
	if "removeParams" in args.o:
		removeParams = True
	if "crawlApis" in args.o:
		crawlApis = True

finder = ApiFinder(args.u, args.d, args.s, removeParams, crawlApis)

finder.start()



