"""constructs.py
Contains the library of GGB > Asymptote information.
name is a dictionary of name conversions, while the functions perform the actual Asymptote outputting.
Each function has an attribute ggb_return_type, which lists the expected return GGB type of the function.
This can be converted to an asymptote type using the dictionary DICT_ASY_TYPES in constants.py """

from constants import DICT_ASY_TYPES

name = {}
name["midpoint"] = "midpoint"
name["circumcircle"] = "circumcircle"
name["incircle"] = "incircle"
name["incenter"] = "incenter"
name["circumcircle"] = "circumcircle"
name["circumcenter"] = "circumcenter"
name["foot"] = "foot"
name["centroid"] = "centroid"
name["orthocenter"] = "orthocenter"
name["bisectorpoint"] = "bisectorpoint"
name["MarkAngle"] = "anglemark"
name["MarkRightAngle"] = "rightanglemark"
name["length"] = "arclength"

name["IntersectionPoint"] = "IntersectionPoint"
name["IntersectionPoints"] = "IntersectionPoints"
name["CirclebyPoint"] = "CirclebyPoint"
name["CirclebyRadius"] = "CirclebyRadius"
name["Line"] = "Line"
name["Distance"] = "distance"


#Auxiliary functions
def aux_paren(args):
	return "(" + ",".join([str(t) for t in args]) + ")"
def aux_check_sane(args, lmin, lmax):
	assert lmin <= len(args) <= lmax, "%d is not in [%d, %d]" %(len(args), lmin, lmax)
def aux_get_cmd(cmdname, args, lmin=None, lmax=None):
	if lmin is not None and lmax is not None:
		aux_check_sane(args, lmin, lmax)
	return name[cmdname] + aux_paren(args)
def aux_op_join(op_symbol, args):
	return op_symbol.join([str(t) for t in args])


#ARITHMETIC OPERATOR FUNCTIONS
##################################################################
def op_plus(*args, **kwargs):
	return aux_op_join("+", args)
def op_minus(*args, **kwargs):
	return aux_op_join("-", args)
def op_times(*args, **kwargs):
	return aux_op_join("*", ["(%s)" %t for t in args])
def op_divide(*args, **kwargs):
	return aux_op_join("/", ["(%s)" %t for t in args])


#ACTUAL GEOGEBRA FUNCTIONS
#######################################################
def Midpoint(*args, **kwargs):
	if len(args) == 1:
		return aux_get_cmd("midpoint", args)
	else:
		return aux_get_cmd("midpoint", ['--'.join(args)])
Midpoint.ggb_return_type = "point" 

def Circle(*args, **kwargs):
	if len(args) == 2:
		# second = args[1]
		#Determine whether this is an expression or real
		if DICT_ASY_TYPES[kwargs['args_types'][1]] == 'real':
			return aux_get_cmd("CirclebyRadius", args)
		else:
			return aux_get_cmd("CirclebyPoint", args)
	else:
		return aux_get_cmd("circumcircle", args, 3,3)
Circle.ggb_return_type = "point"

#Aw god.  Center of a circle.
def Center(*args, **kwargs):
	aux_check_sane(args, 1, 1)
	w = args[0]
	#Do we really haveee to do this?
	#Because I sure don't want to.
	checkBegin = lambda w, center: w[0:len(name[center])] == name[center]
	
	if checkBegin(w, "incircle"):
		return name["incenter"] + w[w.find('('):]
	elif checkBegin(w, "circumcircle"):
		return name["circumcenter"] + w[w.find('('):]
	
	else:
		#OK, you win.
		apoint = "relpoint(%s, 0)" %w
		bpoint = "relpoint(%s, 0.5)" %w
		return Midpoint(apoint, bpoint, **kwargs)
Center.ggb_return_type = "point"

#Polygons
def Polygon(*args, **kwargs):
	yield '--'.join(args) + '--cycle'
	for i in range(0, len(args)-1):
		yield '%s--%s' %(args[i], args[i+1])
	yield '%s--%s' %(args[-1], args[0])
Polygon.ggb_return_type = "polygon"

def Segment(*args, **kwargs):
	aux_check_sane(args, 2,2)
	return args[0] + "--" + args[1]
Segment.ggb_return_type = "segment"

def Intersect(*args, **kwargs):
	aux_check_sane(args, 2, 3)
	if len(args) == 2:
		if kwargs["num_expected"] == 1:
			return aux_get_cmd("IntersectionPoint", args)
		else:
			#Silly Geogebra
			return [aux_get_cmd("IntersectionPoint", [args[0], args[1], i] ) for i in range(kwargs["num_expected"])]
	else:
		A = args[0]
		B = args[1]
		index = str(int(args[2])-1)
		#Because asymptote indexes as 0,1,... while 
		#geogebra indexs as 1,2,...
		return aux_get_cmd("IntersectionPoint", [A,B,index])
Intersect.ggb_return_type = "point"

def Line(*args, **kwargs):
	aux_check_sane(args, 2,2)
	first, second = args
	if DICT_ASY_TYPES[kwargs["args_types"][1]] == 'path':
		start =	 "relpoint(%s,0.5-10/lisf)" %second
		end =	 "relpoint(%s,0.5+10/lisf)" %second
		control = "%s-%s+%s" %(start, end, first)
		return name["Line"] + aux_paren( [first, control, 'lisf'] )
	else:
		return name["Line"] + aux_paren( [args[0], args[1], 'lisf'] )
Line.ggb_return_type = "line"

def Ray(*args, **kwargs):
	aux_check_sane(args, 2,2)
	return name["Line"] + aux_paren( [args[0], args[1], 0, 'lisf'] )
Ray.ggb_return_type = "ray"





def AngularBisector(*args, **kwargs):
	aux_check_sane(args, 2,3)
	if len(args) == 2:
		raise ValueError, "Have not implemented angle bisector for two lines yet..."

	else:
		kwargs['args_types'] = ["point", "point"]
		return Line(args[1], name["bisectorpoint"] + aux_paren(args), **kwargs)

AngularBisector.ggb_return_type = "line"





def LineBisector(*args, **kwargs):
	aux_check_sane(args,1,2)
	if len(args) == 2: 
		#Perp Bisector of two points A and B
		kwargs['args_types'] = ["point", "point"]
		return Line(Midpoint(args[0], args[1]), name["bisectorpoint"] + aux_paren(args), **kwargs)

	else: 
		#Perp Bisector of one segment A--B
		#Can we cheat?
		if len(args[0]) == 4 and args[0][1:3] == "--":
			start, end = [args[0][0], args[0][3]]
		else:
			start = "relpoint(%s, 0)" %args[0]
			end = "relpoint(%s, 1)" %args[0]

		kwargs['args_types'] = ["point", "point"]
		return Line(Midpoint(start, end, **kwargs), name["bisectorpoint"] + aux_paren([start, end]), **kwargs)

LineBisector.ggb_return_type = "line"


def OrthogonalLine(*args, **kwargs):
	aux_check_sane(args, 2,2)
	A = "relpoint(%s, 0)" %args[1]
	B = "relpoint(%s, 1)" %args[1]
	P = args[0]
	kwargs['args_types'] = ["point", "point"]
	return Line(P,Foot(P,A,B), **kwargs)
OrthogonalLine.ggb_return_type = "line"


def Vector(*args, **kwargs):
	#Why would you do this?
	return Segment(*args, **kwargs)
Vector.ggb_return_type = "segment"


def Length(*args, **kwargs):
	aux_check_sane(args,1,2)
	if len(args) == 2: #Two points
		return aux_get_cmd("Distance", args)
	elif len(args[0]) == 4 and args[0][1:3] == "--":
		return aux_get_cmd("Distance", [args[0][0], args[0][-1]])
	else: #One segment
		return aux_get_cmd("length", args)
Length.ggb_return_type = "numeric"

def Distance(*args, **kwargs):
	return Length(*args, **kwargs)
Distance.ggb_return_type = "numeric"

def Angle(*args, **kwargs):
	aux_check_sane(args, 3,3)
	A,B,C = args
	return "(abs(dot(unit(%s-%s),unit(%s-%s))) < 1/2011) ? %s%s : %s%s " %(A,B,C,B,name["MarkRightAngle"],aux_paren(args),name["MarkAngle"],aux_paren(args))
#This gives us a more sophisticated angle marker, which makes
#a right angle mark when the angle is roughly 90 degrees
#and a generic mark otherwise.
Angle.ggb_return_type = "angle"

def Mirror(*args, **kwargs):
	aux_check_sane(args, 2, 2)
	#FML.
	first, second = args
	type1 = DICT_ASY_TYPES[kwargs["args_types"][0]]
	type2 = DICT_ASY_TYPES[kwargs["args_types"][1]]
	assert type1 == 'pair', 'LOL idk how to reflect non-points'
	if type2 == 'pair':
		return "2*%s-%s" %(second, first)
	else:
		start =	 "relpoint(%s,0.5-10/lisf)" %second
		end =	 "relpoint(%s,0.5+10/lisf)" %second
		foot =	 "foot(%s,%s,%s)" %(first, start, end)
		return "2*%s-%s" %(foot, first)
def return_first_type(*args, **kwargs):
	return kwargs["args_types"][0]
Mirror.ggb_return_type = return_first_type
		

def Incircle(*args, **kwargs): return aux_get_cmd("incircle", args, 3,3)
def Incenter(*args, **kwargs): return aux_get_cmd("incenter", args, 3,3)
def Foot(*args, **kwargs): return aux_get_cmd("foot", args, 3, 3)
def Orthocenter(*args, **kwargs): return aux_get_cmd("orthocenter", args, 3,3)
def Centroid(*args, **kwargs): return aux_get_cmd("centroid", args, 3,3)
def Circumcenter(*args, **kwargs): return aux_get_cmd("circumcenter", args, 3,3)
Incircle.ggb_return_type = "conic"
Incenter.ggb_return_type = "point"
Foot.ggb_return_type = "point"
Orthocenter.ggb_return_type = "point"
Centroid.ggb_return_type = "point"
Circumcenter.ggb_return_type = "point"
