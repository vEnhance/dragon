#CONSTANTS.py
"""constants.py
Some constants.
"""

SHORT_NAME = "DRAGON"
FULL_NAME = "Displays Readable Asymptote from GeoGebra Output Names"
VERSION_NUMBER = "0.0.9.6"

CSE_CONCISE_TRANSLATE = {}
CSE_CONCISE_TRANSLATE["IntersectionPoint"] = "IP"
CSE_CONCISE_TRANSLATE["IntersectionPoints"] = "IPs"
CSE_CONCISE_TRANSLATE["CirclebyPoint"] = "CP"
CSE_CONCISE_TRANSLATE["CirclebyRadius"] = "CR"
CSE_CONCISE_TRANSLATE["Line"] = "L"
CSE_CONCISE_TRANSLATE["Distance"] = "d"

GOOD_LUCK = "You are on your own.  Good luck!"


#Things that might occasionally want to be changed
DICT_ASY_TYPES = {
	'point' : 'pair',
	'segment' : 'path',
	'conic' : 'path',
	'numeric' : 'real',
	'angle': 'path',
	'line' : 'path',
	'ray' : 'path'
	}
#Don't include polygon here

LINE_STYLE = {
	0 : None, #Default
	10 : 'linetype("4 4")', 
	15 : 'dashed',
	20 : 'dotted',
	25 : 'dashdotted',
	30 : 'linetype("8 4 0 4")',
	}
LINE_WT = {
	1: 0.6,
	2: None, #This is default
	3: 1.0,
	4: 1.2,
	5: 1.4,
	6: 1.6,
	7: 1.8
	}


#The following CAN be modified, but I can't think of why, one would want to
STRING_TYPE = type('string')
DEPEND_THRESHOLD = 1 #min number of refs before pair name is assigned.
#This is here because I was an idiot and thought DEPEND_THRESHOLD > 1 would work.
#It doesn't.
GEOGEBRA_XML_LOCATION = "geogebra.xml"
INFIX_OPERATOR_DICT = {
		"+" : {"name": "op_plus", "prec": 5},
		"-" : {"name": "op_minus", "prec": 5},
		"*" : {"name": "op_times", "prec": 7},
		"/" : {"name": "op_divide", "prec": 7}
		}

