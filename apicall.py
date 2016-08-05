from statistics import mean
import requests
import time
import json
import html


class APICall:

	def __init__(self, originalUrl, base, path, encodingType, method, params, size, content):
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
		htmlVal = "<div class=\"apicall\">"
		htmlVal += "<b>URL:</b>"+self.base+self.path
		htmlVal += "<table><tr><td>Key</td><td>Value(s)</td></tr>"
		for key, vals in self.params.items():
			htmlVal += "<tr><td>"+key+"</td>"
			htmlVal += "<td>"+str(vals)+"</td></tr>"
		htmlVal += "</table><p>"
		htmlVal += "<b>Example:</b> "+self.originalUrl+"</br>"
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
			print("URL: "+str(self.base)+str(self.path)+"/"+",".join(self.pathParams))
		else:
			print("URL: "+str(self.base)+str(self.path))
		print("METHOD: "+self.method)
		if len(self.returnSizes) > 0:
			print("AVG RESPONSE SIZE: "+str(int(mean(self.returnSizes))))
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
