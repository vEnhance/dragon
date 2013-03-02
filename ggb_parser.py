"""ggb_parser.py
The aim of this file is to take an expression in GGB language, e.g. "Length[Segment[A,B]]/2" and
convert it into the corresponding asymptote code.  At the same time, the return value should also
give a list of _dependencies_; that is, a list of variables which are invoked, so that Dragon will
known later that it should declare these variables for the definition to work."""

import constructs as module_constructs
from constants import INFIX_OPERATOR_DICT, STRING_TYPE
import string

class RPSToken():
	"""Generic token class.
	Represents parens, operators, functions, and objects."""
	token_type = ""
	needed_attr = []
	def __init__(self, **kwargs):
		if not all([kwargs.has_key(req) for req in self.needed_attr]):
			raise KeyError, "Token of type %s requires attributes %s, given %s" %(self.token_type, self.needed_attr, kwargs.keys())
		for key in kwargs.keys():
			setattr(self, key, kwargs[key])
	def __repr__(self):
		return self.token_type

class RPSFunction(RPSToken): 
	token_type = "function"
	def __repr__(self):
		return "%s.%d" %(self.name, self.number_args)

class RPSPrefixFunction(RPSFunction):
	function_type = "prefix"
	needed_attr = ["name"]
	number_args = 0 #change this pretty soon... 
	prec = 999

class RPSInfixOperator(RPSFunction):
	function_type = "infix"
	number_args = 2
	needed_attr = []
	def __init__(self, op, **kwargs):
		for key in kwargs.keys():
			setattr(self, key, kwargs[key])
		self.name = INFIX_OPERATOR_DICT[op]['name']
		self.prec = INFIX_OPERATOR_DICT[op]['prec']

class RPSObject(RPSToken):
	token_type = "object"
	is_constant = 0
	needed_attr = ["ggb_type", "constructor", "is_in_diagram"]
	def __repr__(self):
		return self.constructor
class RPSLeftParen(RPSToken): token_type = "("
class RPSRightParen(RPSToken): token_type = ")"


def isFunc(s):
	return module_constructs.__dict__.has_key(s)

def get_tokens_from_string(s):
	"""Produce tokens from a raw GGB string s"""
	tokens = []
	cocoon = ""
	EOF = ";"
	for char in s + EOF:
		if char in "()[]+-*/,;":
			#If queue is nonempty, write it to tokens.
			if cocoon.strip() != "":
				tokens.append(cocoon.strip())
			#If the last thing is a (, check if implicit multiply
			if len(tokens) > 0:
				if not isFunc(tokens[-1]) and not (tokens[-1] in "+-*/") and char == "(":
					tokens.append("*")
			#Append special char to tokens
			tokens.append(char)
			#Reset queue
			cocoon = ""
		elif char == " " and cocoon.strip() == "":
			#Ignore extraneous spaces
			pass
		else:
			#Add to queue
			cocoon += char
	#OK, don't need that EOF anymore.
	tokens.pop()
	return tokens

def ShuntingYard(string_tokens, **kwargs):
	"""Converts a prefix/infix string expression into a list of instances 'Token'
	sorted in Reverse Polish notation.
	Return value: [list[tokens] of tokens, list[label] of dependencies]"""
	outputQueue = []
	stack = []
	deps = []
	function_nargs_tracker = []
	
	for string_token in string_tokens:
		#print "Processing %s..." %string_token

		if string_token in "([":
			stack.append(RPSLeftParen())
			
		elif string_token in ")]":
			while stack[-1].token_type != "(":
				assert stack[-1].token_type == "function", stack[-1]
				outputQueue.append(stack.pop())
			stack.pop() #Remove the left paren
			if len(stack) > 0:
				if stack[-1].token_type == "function":
					if stack[-1].function_type == "prefix":
						outputQueue.append(stack.pop())
						outputQueue[-1].number_args = function_nargs_tracker.pop()

		elif string_token in ",":
			#Separator
			while stack[-1].token_type != "(":
				stack_top = stack.pop()
				assert stack_top.token_type == "function", "%s is not a function" %stack_top
				assert stack_top.function_type == "infix", "%s is not infix" %stack_top
				outputQueue.append(stack_top)
			function_nargs_tracker[-1] += 1
			
		elif isFunc(string_token):
			#This is a prefix function from constructs
			curr_rps_token = RPSPrefixFunction(name = string_token)	
			stack.append(curr_rps_token)
			function_nargs_tracker.append(1)

		elif INFIX_OPERATOR_DICT.has_key(string_token):
			#This is an infix operator.
			curr_rps_token = RPSInfixOperator(op = string_token)
			if len(stack) > 0:
				while stack[-1].token_type == "function":
					if stack[-1].function_type == "infix" and curr_rps_token.prec <= stack[-1].prec:
						outputQueue.append(stack.pop())
					else:
						break
					if len(stack) <= 0: break
			stack.append(curr_rps_token)

		elif any( [char in string.ascii_letters + "_ " for char in string_token] ):
			#This is a varname
			deps.append(string_token)

			#curr_ggb_type = "point"
			if not kwargs['ref_dict'].has_key(string_token):
				print "FATAL ERROR"
				print "\"%s\" is neither a recorded GGB command or the name of a previous object." %string_token
				print "You are on your own.  Good luck."
				exit()

			curr_ggb_type = kwargs['ref_dict'][string_token].ggb_obj_type

			curr_rps_token = RPSObject(ggb_type = curr_ggb_type, constructor = string_token, is_constant = 0, is_in_diagram = 1)
			outputQueue.append(curr_rps_token)

		elif all( [char in '1234567890. ' for char in string_token] ):
			#This is a real.
			curr_rps_token = RPSObject(ggb_type = "numeric", constructor = string_token, is_constant = 1, is_in_diagram = 0)
			outputQueue.append(curr_rps_token)

		else:
			#idk
			raise TypeError, "Dragon's shunting yard doesn't know how to handle token %s" %string_token

	while len(stack) > 0:
		assert stack[-1].token_type == "function", stack.token_type
		assert stack[-1].function_type == "infix", stack.token_type
		outputQueue.append(stack.pop())

	return [outputQueue, deps]

def parse_string(s, **kwargs):
	token_set, deps = ShuntingYard(get_tokens_from_string(s), **kwargs)
	stack = []

	for token in token_set:
		if token.token_type == "object":
			stack.append(token)
		elif token.token_type == "function":
			args_token = reversed([stack.pop() for t in range(token.number_args)])
			args_string = []
			args_types = []
			for arg in args_token:
				args_string.append(arg.constructor)
				args_types.append(arg.ggb_type)
			curr_func = getattr(module_constructs, token.name)
			res_constructor = curr_func(*args_string, args_types = args_types, **kwargs)
			if token.function_type == "prefix":
				theType = curr_func.ggb_return_type
				if type(theType) == STRING_TYPE:
					res_type = theType
				else:
					res_type = theType(*args_string, args_types = args_types, **kwargs)
			else:
				#QQ
				assert len(args_types) == 2, "Infix called with num arguments %s" %str(args_types)
				if args_types[0] == 'numeric':
					res_type = args_types[1]
				elif args_types[1] == 'numeric':
					res_type = args_types[0]
				else:
					res_type = args_types[0]
			stack.append( RPSObject(is_constant = 0, is_in_diagram = 0, ggb_type = res_type, constructor = res_constructor) ) 
	final_result = stack[0]
	if kwargs['num_expected'] == 1:
		return [final_result.constructor, deps]
	else:
		return [[blah for blah in final_result.constructor], deps]
