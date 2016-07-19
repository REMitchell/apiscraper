from statistics import mean

class APICall:

	def __init__(self, originalUrl, base, path, encodingType, method, params, headers, size):
		self.originalUrl = originalUrl
		self.base = base
		self.path = path
		self.encodingType = encodingType
		self.method = method
		#Dictionary of key, [list of values] pairs
		self.params = params
		self.headers = headers
		size = int(size)
		if size is not None and size > 0:
			self.returnSizes = [size]
		else:
			self.returnSizes = []

	#Adds the API call to the list if it does not exist yet. If the call does
	#exist in the list, integrates any new parameters found
	def addToList(self, apiCalls):
		for call in apiCalls:
			if self.base == call.base and self.path == call.path:
				call.returnSizes = call.returnSizes + self.returnSizes
				#The calls are the same, make sure to add all the 
				for key, vals in self.params.items():
					if call.params[key] is None:
						call.params[key] = vals
					else:
						#Add all the values together
						call.params[key] = list(set(call.params[key] + self.params[key]))
				return apiCalls
		#Has not been found in the current list, simply append it
		apiCalls.append(self)
		return apiCalls

	#def removeUneccessaryParameters():

	def toString(self):
		cellSize = 40
		print("\n"+cellSize*"-")
		print("URL: "+str(self.base)+str(self.path))
		if len(self.returnSizes) > 0:
			print("AVG RESPONSE SIZE: "+str(int(mean(self.returnSizes))))
		if len(self.params) > 0:
			print("|  KEY"+" "*(cellSize-5)+"|  VALUE"+" "*(cellSize-7)+"|")
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
				
