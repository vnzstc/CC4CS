import mmap, re, os  
import random as rn
from itertools import product
from functools import reduce

types = {}
scalars = {}
arrays = {}
sizes = {}

def pascalCase(inputStr):
    return ''.join(x for x in inputStr.title() if not x.isspace())
    
def replaceStr(filename, regexStr, replacementStr):
	"""This function replaces a line in a file that matches the specified regular expression

		Args: 
			filename (string): the name of the file to be opened
			regexStr (string): a regular expression
			replacementStr (string): the string that is inserted in the file 
	"""
	with open(filename, "r") as file:
		lines = file.readlines()

	for i,line in enumerate(lines):
		# Better to rise an exception if this is never accessed
		if re.match(regexStr, line):
			lines[i] = replacementStr

	with open(filename, "w") as file: 
		file.writelines(lines)  

def getListfromRegex(regexStr, lineStr):
	"""This function finds all possible matches of a regex in a line

		Args:
			regexStr (string): a regular expression
			lineStr (string): the string to be checked 

		Returns:
			list: the list of all matches found
	"""
	return re.findall(regexStr, lineStr)

def searchRegex(regexStr, content):
	return re.search(regexStr, content)

def initializeSizes(variable):
	matched = getSizes(variable)
	
	if matched:
		arrays[variable] = ""

		for element in matched:
			sizes[element] = ""

		return True

	return False

def getSizes(variable):
	"""getSizes retrieves the sizes of an array 

		Args:
			variable (string): an array variable 
	
		Todo:
			* Check of the format of the string 

		Returns:
			list: a list containing the sizes of variable
	"""
	return getListfromRegex(r'\[(.*?)\]', variable)

def parametersFilter(lineStr, targeType, indexType):
	"""
	"""
	global scalars

	tempScalars = []
	matched = getListfromRegex(r'\w+\s\w+(?:\[\w+\]){0,2}', lineStr.decode("utf-8"))


	for i, variable in enumerate(matched):
		index = variable.index(' ')
		varName = variable[index+1:]

		# ------------------------------------
		if variable[:index] == 'TARGET_TYPE':
			types[varName] = targeType
		else:

			types[varName] = indexType
		# ------------------------------------

		if not initializeSizes(varName):
			tempScalars.append(varName)

	scalars = {variable : "" for variable in set(tempScalars) - set(sizes.keys())}

def checkInput(regexStr, inputStr):	
	if not re.match(regexStr, inputStr):
		raise ValueError("Bad input for " + inputStr)
	return True

def askForInput():
	return input('Enter input for '  + '"' + variable + '"' + ': ')

def updateDict(dictionary, key, regex, inputString):
	if checkInput(regex, inputString):
		dictionary[key] = inputString
		return True
	return False

def getParametersFromFile(jsonFileObject, currentType):
	numberOfVariables = len(scalars) + len(sizes) + len(arrays)
	inputs = jsonFileObject[currentType]

	if len(inputs) != numberOfVariables:
		raise ValueError("The parameters file must contain an input for each variable")
	for variable in inputs:
		inputString = inputs[variable]

		if variable in scalars: 
			updateDict(scalars, variable, r'\[\-?\d+,\d+\];[1-9][0-9]*', inputString)
		elif variable in sizes:
			updateDict(sizes, variable, r'\[\-?\d+,\d+\];[1-9][0-9]*', inputString)
		elif variable in arrays:
			updateDict(arrays, variable, r'\[\-?\d+,\d+\]$', inputString)
		else:
			raise ValueError("Variable not found")

def discoverParameters(filename, targeType, indexType):
	"""
		The function opens a .c program and searches for a function with the same name
		Args:
			filename (string): the name of the file under consideration
		Raises:
			ValuesError: if the function is not found
	"""
	file = open(filename + '.c')
	mm = mmap.mmap(file.fileno(), 0, access = mmap.ACCESS_READ)
	matchStr = re.search(str.encode(filename + '\([^\)]*\)(\.[^\)]*\))?', "utf-8"), mm).group(0)

	if matchStr:
		parametersFilter(matchStr, targeType, indexType)
	else:
		raise ValueError("function not found")

def splitScalarInput(rangeStr):
	"""
		This function takes in input the string that contains the ranges and the number of values to generate
		and divides it by the semicolon

		Args:
			rangeStr (string): the string that contains the range 

		Returns:
			tuple: The first element is the range and the second is the number of values
	"""
	currentInput = rangeStr.split(';')
	vaRange = eval(currentInput[0])
	vaNum = int(currentInput[1])

	return (vaRange, vaNum)

def genRandomList(rangeMin, rangeMax, elementNum, varType):
	lst = [round(rn.uniform(rangeMin, rangeMax), 3) for _ in range(elementNum)]

	if varType != "float":
		return [int(element) for element in lst]

	return lst

def generateList(lst):
	for variable in lst:
		currentTuple = splitScalarInput(lst[variable])
		lst[variable] = genRandomList(currentTuple[0][0], currentTuple[0][1], currentTuple[1], types[variable])

	return lst

def listCreator():
	generateList(scalars)
	generateList(sizes)

def createHeader():
	"""
		This function creates the output file.
		Returns the object that rappresents the file
	"""
	basic = "#ifndef VALUES\n#define VALUES\n"

	output = open('values.h', 'w+')
	output.write(basic)

	return output

def closeHeader(fileObject):
	fileObject.write("#endif")
	fileObject.close()

def removeLastOccurence(character, string):
	k = string.rfind(character)
	string = string[:k] + "" + string[k+1:]
	return string

def writeArray(headerFile, value, varType, arraySizes):
	arrayRange = eval(value)
	elementNum = reduce(lambda x, y: x*y, arraySizes)

	toWrite = "{"

	for i in range(0, arraySizes[0]):
		arrayValues = genRandomList(arrayRange[0], arrayRange[1], elementNum, varType)
		try:
			for j in range(0, arraySizes[1]):
				if j == 0:
					toWrite += "{"
				toWrite += str(arrayValues[j]) + ","
			toWrite = removeLastOccurence(',', toWrite)
			toWrite += "},"	
		
		except Exception as e:
				toWrite += str(arrayValues[i]) + ","

	toWrite = removeLastOccurence(',', toWrite)
	toWrite += "};\n"

	headerFile.write(toWrite)

def writeVariables(combination, headerFile):
	"""
		This function writes variables in the output file.
	"""
	cont = 0
	currentSizeValues = {}

	for key, value in scalars.items():
		pos = combination[cont]
		headerFile.write("\t" + types[key] + " " + key + " = " + str(value[pos]) + ";\n")
		cont += 1

	for key,value in sizes.items():
		pos = combination[cont]
		headerFile.write("\tenum{" + key + " = " + str(value[pos]) + "};\n")	
		currentSizeValues.update({key : value[pos]})
		cont += 1

	for key, value in arrays.items():
		matched = getSizes(key)
		currentSizes = [currentSizeValues[element] for element in matched]
		headerFile.write("\t" + types[key] + " " + key + " = ")
		writeArray(headerFile, value, types[key], currentSizes)
		
def generateHeaders():
	""" 
		This function generates combinations of the values of previously calculated lists.
		Combines indexes and then accesses by index, the correspondent list, to get the value.
		Furthermore, for each header a directory is created 
	"""
	counts = [len(singleList) for singleList in list(scalars.values()) + list(sizes.values())]
	iterate = [range(length) for length in counts]
	fileIndex = 0

	# Includes directory creation 
	os.makedirs("includes")
	# Change working directory
	os.chdir("includes")

	for combination in product(*iterate):
		# For each combination will be generated 10 random array
		for index in range(1):
			# Creates the directory in which the header will be placed 
			dirName = "values_" + str(fileIndex)						
			
			os.makedirs(dirName)
			headerFile = createHeader()
			writeVariables(combination, headerFile)
			closeHeader(headerFile)

			# Moves the file in the above created directory  
			os.rename("values.h", dirName + "/values.h")
				
		fileIndex += 1

	# Return to the previous directory
	os.chdir('..')