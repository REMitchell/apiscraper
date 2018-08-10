import urllib
from urllib.parse import urlparse, parse_qs
import sys
import re
import os
from random import shuffle
from bs4 import BeautifulSoup

from apicall import APICall, APICallEncoder, APIWriter
from harParser import HarParser
from browser import Browser

class APIFinder:

	def __init__(self, url=None, harDirectory=None, searchString=None, removeParams=False, count=1, cookies=None):
		self.url = url
		self.harDirectory = harDirectory
		self.searchString = searchString
		self.removeParams = removeParams
		self.count = count
		self.browser = None
		self.cookies = cookies
		
	def start(self):
		if self.count > 1 and self.url is None:
			print("Cannot provide page count with no URL given")
			exit(1)
		if self.removeParams and self.url is None:
			print("WARNING: Must have Internet connection to remove unneeded parameters")

		#Scan for all APIs
		if self.url:
			os.makedirs(self.harDirectory,exist_ok=True)
			self.deleteExistingHars()
			self.browser = Browser("chromedriver/chromedriver", "browsermob-proxy-2.1.4/bin/browsermob-proxy", self.harDirectory, cookies=self.cookies)
			if self.searchString is not None:
				print("Searching URL "+self.url+" for string "+self.searchString)
			#Move recursively through the site
			apiCalls = self.crawlingScan(self.url)
			
		#Scan directory of har files
		else:
			print("Parsing existing directory of har files")
			harParser = HarParser(self.harDirectory, self.searchString, self.removeParams)
			apiCalls = harParser.parseMultipleHars()

		if self.browser is not None:
			self.browser.close()

		return apiCalls

	def openURL(self, url):
		return self.browser.get(url) #load the url in Chrome

	def getDomain(self, url):
		return urlparse(url).netloc.lstrip('www.')

	def isInternal(self, url, baseUrl):
		if url.startswith("/"):
			return baseUrl+url
		if self.getDomain(baseUrl) == self.getDomain(url):
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
	def deleteExistingHars(self):
		files = os.listdir(self.harDirectory)
		for singleFile in files:
			if "har" in singleFile:
				os.remove(self.harDirectory+"/"+singleFile)


	#Performs a recursive crawl of a site, searching for APIs
	def crawlingScan(self, url, apiCalls = [], allFoundURLs = []):
		self.count = self.count - 1
		if self.count < 0:
			return

		harParser = HarParser(self.harDirectory, searchString=self.searchString, removeParams=self.removeParams)

		#If uncommented, will return as soon as a matching call is found
		#if self.searchString is not None and len(apiCalls) > 0:
		#	return apiCalls
		try:
			print("Scanning URL: "+url)
			html = self.openURL(url)
			if html is not None:
				bsObj = BeautifulSoup(html, "lxml")

				harObj = harParser.getSingleHarFile()
				apiCalls = harParser.scanHarfile(harObj, apiCalls=apiCalls)

				allFoundURLs, newUrls = self.findInternalURLs(bsObj, url, allFoundURLs)
				shuffle(newUrls)
				
				for newUrl in newUrls:
					self.crawlingScan(newUrl, apiCalls, allFoundURLs)
		
		except (KeyboardInterrupt, SystemExit):
			print("Stopping crawl")
			self.browser.close()
			apiWriter = APIWriter(apiCalls)
			apiWriter.outputAPIs()
			exit(1)
		return apiCalls
