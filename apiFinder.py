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

def outputAPIs(apiCalls):
	print("API RESULTS ARE")
	htmlFile = open('output.html', 'w')
	jsonFile = open("output.json", "w")
	apiCalls = findPathVariables(apiCalls)
	for apiResult in apiCalls:
		print(apiResult.toString())
	jsonFile.write(json.dumps(apiCalls, cls=APICallEncoder))
	#jsonObj = json.JSONDecoder().decode(apiCalls)
	#print(jsonObj)
	#pickle.dump(apiCalls, open("output.json", "wb"))


def createWebDriver():
	theURL=''
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
	profile.set_preference("extensions.firebug.DBG_STARTER", True);

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
	profile.set_preference("extensions.firebug.netexport.pageLoadedTimeout", 15000)
	profile.set_preference("extensions.firebug.netexport.timeout", 10000)

	profile.set_preference("extensions.firebug.netexport.defaultLogDir", os.getcwd()+"/nextexport")

	profile.update_preferences();

	browser = webdriver.Firefox(firefox_profile=profile)
	return browser

def openURL(url):
	browser = createWebDriver()
	theURL = url
	time.sleep(5)
	#browser = webdriver.Chrome();
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

	time.sleep(15) #wait for the page to load
	html = browser.page_source
	browser.quit()
	return html

def findPathVariables(apiList):
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

def isInternal(url, baseUrl):
	if url.startswith("/"):
		return baseUrl+url
	if tldextract.extract(baseUrl).domain == tldextract.extract(url).domain:
		return url
	return None



#Returns a list of all internal URLs on a page as long
#as they are either relative URLs or contain the current domain name
def findInternalURLs(bsObj, currentUrl, allFoundURLs):
	newUrls = []
	baseUrl = urlparse(currentUrl).scheme+"://"+urlparse(currentUrl).netloc
	#Finds all links that begin with a "/"
	for link in bsObj.findAll("a"):
		if 'href' in link.attrs:
			#baseUrl, urlInPage = parseUrl(link.attrs)
			url = link.attrs['href']
			#It's an internal URL and we haven't found it already
			url = isInternal(url, baseUrl)
			if url is not None and url not in newUrls and url not in allFoundURLs:
				newUrls.append(url)
				allFoundURLs.append(url)
	return allFoundURLs, newUrls


def getContentType(headers):
	for header in headers:
		if header["name"] == "Content-Type":
			return header["value"]

#Get rid of all the current har files
def setup():
	harDir = "nextexport";
	files = os.listdir(harDir)
	for singleFile in files:
		if "har" in singleFile:
			os.remove(harDir+"/"+singleFile)

def getAllHarFiles(harDir="nextexport"):
	files = os.listdir(harDir)
	harFiles = []
	for filename in files:
		if "har" in filename:
			harFiles.append(harDir+"/"+filename)
	return harFiles

def readHarFile(harPath):
	f = codecs.open(harPath, "rb")
	harTxt = f.read().decode("utf-8", "replace")
	harObj = json.loads(harTxt)
	return harObj

def getSingleHarFile(harDir="nextexport"):
	#f = open("nextexport/"+files[0], 'rb')
	harFiles = getAllHarFiles(harDir)
	if len(harFiles) < 1:
		return None
	#Get last harFile in the directory
	harFile = getAllHarFiles(harDir)[len(harFiles)-1]
	return readHarFile(harFile)


def parseEntry(entry, searchString=None):
	url = entry["request"]["url"]
	method = entry["request"]["method"]
	params = dict()
	urlObj = urlparse(url)
	base = urlObj.scheme+"://"+urlObj.netloc
	mimeType = None
	responseSize = 0
	if "content" in entry["response"] and "mimeType" in entry["response"]["content"]:
		
		if searchString is not None:
			if "text" not in entry["response"]["content"] or searchString not in entry["response"]["content"]["text"]:
				return None

		contentType = entry["response"]["content"]["mimeType"]
		responseSize = entry["response"]["content"]["size"]
		contentTypesRecorded = ["text/html", "application/json", "application/xml"]
		if contentType is None:
			return None
		elif contentType.lower() in contentTypesRecorded:
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
	apiCall = APICall(url, base, urlObj.path, mimeType, method, params, responseSize)
	return apiCall



def scanHarfile(harObj, apiCalls = [], searchString=None, removeParams=False):
	#Store the api call objects here
	entries = harObj["log"]["entries"]
	for entry in entries:
		call = parseEntry(entry, searchString=searchString)
		if call is not None:
			call.addToList(apiCalls, removeParams)
	return apiCalls

def parseMultipleHars(directory):
	apiCalls = []
	harPaths = getAllHarFiles(directory)
	for harPath in harPaths:
		print("Parsing file: "+harPath)
		harObj = readHarFile(harPath)
		if removeParams in args.o:
			apiCalls = scanHarfile(harObj, apiCalls=apiCalls, removeParams=True)
		else:
			apiCalls = scanHarfile(harObj, apiCalls=apiCalls)
	return apiCalls

#Performs a recursive crawl of a site, searching for APIs
def crawlingScan(url, apiCalls = [], allFoundURLs = [], removeParams=False):
	try:
		print("Scanning URL: "+url)
		html = openURL(url)
		bsObj = BeautifulSoup(html, "lxml")
		harObj = getSingleHarFile()
		apiCalls = scanHarfile(harObj, apiCalls=apiCalls, removeParams=removeParams)
		allFoundURLs, newUrls = findInternalURLs(bsObj, url, allFoundURLs)
		for newUrl in newUrls:
			crawlingScan(newUrl, apiCalls, allFoundURLs)
	except (KeyboardInterrupt, SystemExit):
		print("Stopping crawl")
		outputAPIs(apiCalls)
		exit(1)
	return apiCalls


#Clean up any existing har files
setup()

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

#Search for text found within a particular API
if args.s:
	if not args.u:
		print("Must provide URL.")
		sys.exit(1)
	print("Searching "+args.u+" for \""+args.s+"\"")
	openURL(args.u)
	harObj = getSingleHarFile()
	apiCalls = scanHarfile(harObj, searchString=args.s)


#Scan for all APIs
elif not args.d:
	#Move recursively through the site
	if "removeParams" in args.o:
		apiCalls = crawlingScan(args.u, removeParams=True)
	else:
		apiCalls = crawlingScan(args.u)
	

else:
	print("Parsing existing directory of har files")
	apiCalls = parseMultipleHars(args.d)

outputAPIs(apiCalls)


