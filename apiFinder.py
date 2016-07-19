import urllib
from urllib.parse import urlparse, parse_qs
import tldextract
import sys
import re
import os
import subprocess
import hashlib
import time
import datetime
from browsermobproxy import Server
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
import selenium
import json
import codecs
from bs4 import BeautifulSoup

from apicall import APICall




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
	profile.set_preference("webdriver.log.file", "/Users/ryan/Documents/apiFinder/log.txt")
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

	profile.set_preference("extensions.firebug.netexport.defaultLogDir", "/Users/ryan/Documents/apiFinder/nextexport")

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

	time.sleep(10) #wait for the page to load
	html = browser.page_source
	browser.quit()
	return html

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
	harDir = "/Users/ryan/Documents/apiFinder/nextexport";
	files = os.listdir(harDir)
	for singleFile in files:
		if "har" in singleFile:
			os.remove(harDir+"/"+singleFile)

def getHarFile(files):
	for singleFile in files:
		if "har" in singleFile:
			return singleFile

def readHarfile():
	print("Readng .har file")
	harDir = "/Users/ryan/Documents/apiFinder/nextexport";
	files = os.listdir(harDir)
	print("Number of files is: "+str(len(files)))
	#f = open("nextexport/"+files[0], 'rb')
	harFile = "nextexport/"+getHarFile(files)
	f = codecs.open(harFile, "rb")
	#b'\x80abc'.decode("utf-8", "replace")
	harTxt = f.read().decode("utf-8", "replace")
	harObj = json.loads(harTxt)
	return harObj

#Use a global APICall list for this. If the same API call is found, 
#add the new values to the parameter list 
def parseCall(url, encodingType, method, size=0):
	urlObj = urlparse(url)
	params = parse_qs(urlObj.query, keep_blank_values=True)
	#(path, encodingType, method, params, headers):
	base = urlObj.scheme+"://"+urlObj.netloc
	apiCall = APICall(url, base, urlObj.path, encodingType, method, params, url, size)
	return apiCall

def searchHarfile(harObj, searchString):
	apiCalls = []
	entries = harObj["log"]["entries"]
	for entry in entries:
		if entry["response"] is not None and entry["response"]["content"] is not None and entry["response"]["content"]["text"] is not None:
			text = entry["response"]["content"]["text"]
			if searchString in text:
				url = entry["request"]["url"]
				method = entry["request"]["method"]
				contentType = entry["response"]["content"]["mimeType"]
				#(path, encodingType, method, params, headers)
				parseCall(url, contentType, method).addToList(apiCalls)

	return apiCalls

def scanHarfile(harObj, apiCalls = []):
	#Store the api call objects here
	entries = harObj["log"]["entries"]
	for entry in entries:
		url = entry["request"]["url"]
		method = entry["request"]["method"]
		if entry["response"]["content"] is not None and entry["response"]["content"]["mimeType"] is not None: 
			contentType = entry["response"]["content"]["mimeType"]
			responseSize = entry["response"]["content"]["size"]
			print("Response size is: "+str(responseSize))
			if contentType is None:
				print("No header for response "+str(url))
			elif contentType.lower() == "application/json":
				print(url)
				print(method)
				print("Content Type: "+str(contentType))
				parseCall(url, "json", method, responseSize).addToList(apiCalls)

			elif contentType.lower() == "application/xml":
				print(url)
				print(method)
				print("Content Type: "+str(contentType))
				parseCall(url, "xml", method, responseSize).addToList(apiCalls)
		else:
			print("No headers in response")

	return apiCalls

#Performs a recursive crawl of a site, searching for APIs
def crawlingScan(url, apiResults = [], allFoundURLs = []):
	try:
		print("Scanning URL: "+url)
		html = openURL(url)
		bsObj = BeautifulSoup(html, "lxml")
		harObj = readHarfile()
		apiResults = scanHarfile(harObj, apiResults)
		allFoundURLs, newUrls = findInternalURLs(bsObj, url, allFoundURLs)
		for newUrl in newUrls:
			crawlingScan(newUrl, apiResults, allFoundURLs)
	except (KeyboardInterrupt, SystemExit):
		print("Stopping crawl")
		print(str(len(apiResults))+" calls found")
		for apiCall in apiResults:
			apiCall.toString()
		sys.exit(1)
		os._exit(1)
	return apiResults


#Clean up any existing har files
setup()

#Usage: 
#$python3 http://example.com search searchTerm
#$python3 http://example.com scan
#python3 https://map.crossfit.com scan
usage = '''
USAGE:
python apiFinder.py search <url> <search term>" 
python apiFinder.py scan <url>
	'''
if len(sys.argv) < 2:
	usage = "Need some more arguments there!"+usage
	print(usage)
	sys.exit(0)


apiResults = None
#Scan for all APIs
if sys.argv[1].lower() == "scan":
	#Move recursively through the site
	if sys.argv[2] == None:
		print("Must provide URL."+usage)
		sys.exit(1)
	apiResults = crawlingScan(sys.argv[2])
	

#Search for text found within a particular API
elif sys.argv[1].lower() == "search":
	if sys.argv[2] is None:
		print("Must provide URL."+usage)
		sys.exit(1)
	if sys.argv[3] is None:
		print("Must provide search string."+usage)
		sys.exit(1)
	print("Searching URL for \""+sys.argv[3]+"\"")
	openURL(sys.argv[2])
	harObj = readHarfile()
	apiResults = searchHarfile(harObj, sys.argv[3])

else:
	print("Unknown function "+str(sys.argv[1])+usage)
	sys.exit(1)


print("API RESULTS ARE")
for apiResult in apiResults:
	print(apiResult.toString())

