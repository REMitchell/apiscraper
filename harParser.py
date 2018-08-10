import os
import codecs
import json 
from urllib.parse import urlparse, parse_qs
import pprint
from apicall import APICall

class HarParser():

    def __init__(self, harPath, searchString=None, removeParams=False):
        self.harPath = harPath
        self.searchString = searchString
        self.contentTypesRecorded = ["text/html", "application/json", "application/xml"]
        self.removeParams = removeParams

    def getAllHarFiles(self):
        files = os.listdir(self.harPath)
        harFiles = []
        for filename in files:
            if "har" in filename:
                harFiles.append(self.harPath+"/"+filename)
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
            text = entry["response"]["content"]["text"]
            context = None
            if self.searchString is not None:
                if self.searchString not in text:
                    return None
                #Set the search string, with some surrounding context in the apiCall 
                start = entry["response"]["content"]["text"].index(self.searchString)
                end = start + len(self.searchString) + 50
                start = 0 if start < 50 else start-50
                context = text[start:end]

            contentType = entry["response"]["content"]["mimeType"]
            responseSize = entry["response"]["content"]["size"]

            content = text
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
                if "params" in entry["request"]["postData"]:
                    paramList = entry["request"]["postData"]["params"]
                    for param in paramList:
                        if param['name'] not in params:
                            params[param['name']] = []
                        params[param['name']].append(param['value'])
                elif "text" in entry["request"]["postData"]:
                    paramList = entry["request"]["postData"]["text"]
            apiCall = APICall(url, base, urlObj.path, mimeType, method, params, responseSize, content, searchContext=context)
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
        for harPath in harPaths:
            print("Parsing file: "+harPath)
            harObj = self.readHarFile(harPath)
            apiCalls = self.scanHarfile(harObj, apiCalls=apiCalls)
        return apiCalls