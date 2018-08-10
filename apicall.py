from statistics import mean
import requests
import time
import json
import html
import re
import codecs

class APICall:

	def __init__(self, originalUrl, base, path, encodingType, method, params, size, content, searchContext=None):
		self.originalUrl = originalUrl
		self.base = base.rstrip("/")
		self.path = path.rstrip("/")
		self.encodingType = encodingType
		self.method = method
		#Dictionary of key, [list of values] pairs
		self.params = params
		self.pathParams = set()
		size = int(size)
		if size is not None and size > 0:
			self.returnSizes = [size]
		else:
			self.returnSizes = []
		self.unneededKeys = []
		self.content = content
		self.searchContext = searchContext

	def __json__(self):
		jsonDict = {"original":self.originalUrl, "base":self.base, "path":self.path}
		jsonDict["encodingType"] = self.encodingType
		jsonDict["method"] = self.method
		jsonDict["params"] = self.params
		jsonDict["pathParams"] = list(self.pathParams)
		jsonDict["responseSizes"] = 0 if len(self.returnSizes) == 0 else int(mean(self.returnSizes))
		jsonDict["content"] = self.content
		return jsonDict

	def toHTML(self):
		htmlVal = "<div class=\"apicall "+self.encodingType.split("/")[1]+"\">"
		htmlVal += "<b>URL:</b>"+self.base+self.path
		htmlVal += "<br><b>METHOD:</b> "+self.method
		if len(self.params) > 0:
			htmlVal += "<table><tr><td><b>Key</b></td><td><b>Value(s)</b></td></tr>"
			for key, vals in self.params.items():
				htmlVal += "<tr><td>"+key+"</td>"
				htmlVal += "<td>"+str(vals)+"</td></tr>"
			htmlVal += "</table><p>"
		htmlVal += "<br><b>Example:</b> <a href=\""+self.originalUrl+"\ target=\"_blank\">"+self.originalUrl+"</a></br>"
		htmlVal += "<textarea class=\"content\">"
		htmlVal += html.escape(self.content, quote=True)
		htmlVal += "</textarea></div>"
		return htmlVal

	def removeUnneededParameters(self):
		# params is a dict of [string:string], not [string:list<string>]
		# need to convert
		params = dict()
		for key, value in self.params.items():
			params[key] = value[0]
		str(self.base)+str(self.path)
		#get baseline
		baseline = requests.get(str(self.base)+str(self.path), params=params).text
		for key in params.keys():
			newParams = dict(params)
			del newParams[key]
			testText = requests.get(str(self.base)+str(self.path), params=newParams).text
			if testText == baseline:
				self.unneededKeys.append(key)
				del self.params[key]

	#Adds the API call to the list if it does not exist yet. If the call does
	#exist in the list, integrates any new parameters found
	def addToList(self, apiCalls, removeUnneededParams=False):
		for call in apiCalls:
			if self.path == call.path and self.base == call.base:
				call.returnSizes = call.returnSizes + self.returnSizes
				for unneededKey in call.unneededKeys:
					#Remove all the unneeded keys we've found in the parent already
					if unneededKey in self.params:
						del self.params[unneededKey]

				if removeUnneededParams:
					self.removeUnneededParameters()

				#The calls are the same, make sure to add all the params together
				for key, vals in self.params.items():
					if key not in call.params:
						call.params[key] = vals
					else:
						#Add all the values together
						call.params[key] = list(set(call.params[key] + self.params[key]))
				return apiCalls
		#Has not been found in the current list, simply append it
		if removeUnneededParams:
			self.removeUnneededParameters()
		apiCalls.append(self)
		return apiCalls

	#def removeUneccessaryParameters():

	def toString(self):
		cellSize = 40
		print("\n"+cellSize*"-")
		if len(self.pathParams) > 0:
			print("URL: "+str(self.base)+str(self.path)+"/\nPATH PARAMS: "+",".join(self.pathParams))
		else:
			print("URL: "+str(self.base)+str(self.path))
		print("METHOD: "+self.method)
		if len(self.returnSizes) > 0:
			print("AVG RESPONSE SIZE: "+str(int(mean(self.returnSizes))))
		if self.searchContext:
			print("SEARCH TERM CONTEXT: "+self.searchContext+"\n")
		if len(self.params) > 0:
			print("|  KEY"+" "*(cellSize-5)+"|  VALUE(S)"+" "*(cellSize-10)+"|")
			for key, vals in self.params.items():
				keySpace = cellSize - len(key)
				if vals[0] == "":
					print("|"+key+" "*keySpace+"|(blank)        |")
				else:
					valStr = ""
					for value in vals:
						valStr = value+","
					#Remove final comma
					valStr = valStr[:len(valStr)-1]
					valLength = len(valStr)
					while valLength > cellSize:
						print("|"+" "*cellSize+"|"+valStr[:cellSize]+"|")
						valStr = valStr[cellSize:]
						valLength = len(valStr)
					valSpace = cellSize - valLength
					print("|"+key+" "*keySpace+"|"+valStr+" "*valSpace+"|")
				print("--"+"--"*cellSize+"-")

class APICallEncoder(json.JSONEncoder):
	def default(self, obj):
		if hasattr(obj, '__json__'):
			return obj.__json__()
		return json.JSONEncoder.default(self, obj)

class APIWriter():
	def __init__(self, apiCalls):
		self.apiCalls = apiCalls
		self.apiCalls = self.findPathVariables()
		
	def outputAPIs(self):
		print("API RESULTS ARE")
		jsonFile = open("output.json", "w")
		for apiResult in self.apiCalls:
			print(apiResult.toString())
		self.outputHTML()
		jsonFile.write(self.outputJSON())
		return

	def outputJSON(self):
		return json.dumps(self.apiCalls, cls=APICallEncoder)

	def outputHTML(self):
		f = codecs.open("html_template.html", "r")
		template = f.read()
		templateParts = template.split("CALLSGOHERE")
		open('output.html', 'w').close()
		htmlFile = open('output.html', 'a')
		htmlFile.write(templateParts[0])
		for apiCall in self.apiCalls:
			htmlFile.write(apiCall.toHTML())
		htmlFile.write(templateParts[1])
		htmlFile.close()
	
	def isPathVar(self, var):
		if '.' in var:
			return False
		numDigs = sum(c.isdigit() for c in var)
		if float(numDigs) / float(len(var)) > .5:
			return True		
		return False

	def findPathVariables(self):
		'''
		Experimental feature to identify variables in paths and group similar API calls
		'''
		digits = re.compile('\d')
		for i in range(0,len(self.apiCalls)):
			for j in range(i+1, len(self.apiCalls)):
				paths1 = self.apiCalls[i].path.split('/')
				paths2 = self.apiCalls[j].path.split('/')
				if len(paths1) == len(paths2) and len(paths1) > 3:
					if paths1[:-1] == paths2[:-1]:
						print("Paths match to the last item:")
						paths1end = paths1[len(paths1)-1]
						paths2end = paths2[len(paths2)-1]
						if self.isPathVar(paths1end) and self.isPathVar(paths2end):
							#We can assume that they're the same API
							print("APIs are the same")
							self.apiCalls[i].pathParams.add(paths1end)
							self.apiCalls[i].pathParams.add(paths2end)
							#self.apiCalls[i].path = '/'.join(paths1[:-1])
							#Remove this later
							self.apiCalls[j].path = ''
		return [api for api in self.apiCalls if api.path != '']
