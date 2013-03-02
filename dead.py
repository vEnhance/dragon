#Returns a list of two things:
#A parsed strings, and a list of dependencies
def parseString(s, **kwargs):
	if s[-1] != ']':
		#We're done!
		#Strip trail/lead spaces
		s = s.strip().rstrip()
		#Check if this is a var name
		if s[0] in string.ascii_letters:
			return [s,[s.strip()]]
		else:
			return [s, []]
	else:
		#FML!
		i = s.find('[')
		rawArgsList = []
		#By Murphy's Law, a simple split(',') could easily fail.
		#So we'll do this the hard way
		bracketNest = 0
		queue = ""
		commandNameRaw = s[0:i].strip()
		argumentsRaw = s[i+1:-1]
		for char in argumentsRaw:
			if char == '[':
				bracketNest += 1
				queue += char
			elif char == ']':
				bracketNest -= 1
				queue += char
			elif char == ',' and bracketNest == 0:
				rawArgsList.append(queue)
				queue = ""
			else:
				queue += char
		rawArgsList.append(queue)

		args = []
		depend = []
		for rawArgument in rawArgsList:
			newArgument, newDepend = parseString(rawArgument, **kwargs)
			args.append(newArgument)
			depend += newDepend
		#print depend
		if constructs.__dict__.has_key(commandNameRaw):
			return [constructs.__dict__[commandNameRaw](*args, **kwargs), depend]
			#return [constructs.__dict__[commandNameRaw](*args), list(set(depend))]
			#The list(set(x)) construct kills dups, at the expense of an ordering.
			#Not that we care about an ordering anyways...
		else:
			print "Cannot find command %s" %commandNameRaw
			print "Called with arguments ", 
			print args
			print "Dying..."
			exit()

