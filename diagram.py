import ggb_parser
from constants import DICT_ASY_TYPES, LINE_STYLE, LINE_WT, STRING_TYPE, DEPEND_THRESHOLD
from constants import SHORT_NAME, VERSION_NUMBER, CSE_CONCISE_TRANSLATE


class GGBObject():
	"""GGBObject Class
	Each item in Geogebra (point, circle, etc.) gets created a GGBObject instance,
	in which all of its attributes are stored.
	Some particular attributes:
		visible: denotes whether the object should be visible in the final diagram.  Defaults to 1.
		depend: denotes whether the object is referenced in another command, and hence needs to be declared.  Defaults to 0.
		label: the label of the object.
		color: the color the object should be drawn.  This applies to paths.
		thick: specifies the object should be drawn with linewidth(x).
		style: dashed, dotted, linestyle("4 4"), etc.
		ggb_obj_type: the geogebra object type; e.g. "segment", "conic"
		asy_obj_type: the object type that should be declared; e.g. "pair", "path", etc.
		needs_label: whether the object should be labelled in the actual diagram.
		needs_pen: 1 if any of the attributes {color, thick, style} are not the default values, and 0 otherwise.
	"""
	def __init__(self, **kwargs):
		for key in kwargs.keys():
			setattr(self, key, kwargs[key])

	def __repr__(self):
		return "%s = %s" %(self.label, self.constructor)

	#Attributes, and their default values
	visible = 1
	depend = 0
	label = "A"
	constructor = "(0,0)"
	color = None #Specify as RGB floats [.2, .4, .1]
	thick = None #linewidth for some reason seems to be 0.8, 1.2, 1.6... huh.
	style = None #dashed, etc.
	ggb_obj_type = "point"
	asy_obj_type = "pair" #path, pen, ...?

	needs_pen = 0
	needs_label = 0


class AsyDiagram():
	"""AsyDiagram Class
	This is basically just a container for GGBObjects in
	the diagram currently being created"""

	objectList = [] #List of labels to mantain construction order.
	toLabelList = [] #List of labels of objects which require labelling on the actual output.
	objectDict = {} #Label : GGBObject instance dictionary for all objects in diagram.

	text_dict = {} #List of text objects

	def has_key(self, key):
		return self.objectDict.has_key(key)

	def __getitem__(self, label):
		return self.objectDict[label]

	def __setitem__(self, label, obj):
		self.objectDict[label] = obj
		self.objectList.append(label)


def doCompileDiagramObjects(tree, diagram):
	for xml_geo_obj in list(tree):
		#Cases:commands,expressions,elements
		if xml_geo_obj.tag == "command":
			#Decompress args
			cmd_name = xml_geo_obj.attrib["name"]
			cmd_input_obj = xml_geo_obj.find("input")
			cmd_output_obj = xml_geo_obj.find("output")
			num_output = len(cmd_output_obj.keys())
			num_args = len(cmd_input_obj.keys())
			args = [ cmd_input_obj.attrib['a%d' %i] for i in range(0, num_args) ]

			if cmd_name == 'Point':
				#Bail out
				continue

			#Convert to geogebra
			ggb_command = "%s[%s]" %(cmd_name, ','.join(args))
			#Parse it!
			constructor, deps = ggb_parser.parse_string(ggb_command, num_expected=num_output, ref_dict = diagram.objectDict)

			if type(constructor) == STRING_TYPE:
				constructor_array = [constructor]
			else:
				constructor_array = list(constructor)
				#Polygons... -___-

			#Get output
			try:
				for i in range(0, num_output):
					label = cmd_output_obj.attrib['a%d' %i]
					diagram[label] = GGBObject(constructor = constructor_array[i], label=label)
			except IndexError:
				#Whine and exit
				print ggb_command
				print cmd_output_obj
				exit()

			for label in deps:
				if diagram.has_key(label):
					diagram[label].depend += 1
				else:
					print "/* WARNING: No object has label %s */" %label

		elif xml_geo_obj.tag == "expression":
			#Dependencies may or may not be screwed over now.
			label = xml_geo_obj.attrib["label"]
			exp = xml_geo_obj.attrib["exp"]
			#print "/* Expression %s = %s */" %(label, exp)
			if exp[0] == exp[-1] == "\"":
				# This is text.
				parsedExp = exp
			else:
				parsedExp = ggb_parser.parse_string(exp, num_expected=1, ref_dict = diagram.objectDict)[0]
			diagram[label] = GGBObject(constructor = parsedExp, label=label)
			diagram[label].depend += 1
			#^ Explicitly defined reals are almost always dependencies: this program isn't exactly bug free.

		elif xml_geo_obj.tag == "element":
			ggb_type = xml_geo_obj.attrib['type']	
			label = xml_geo_obj.attrib["label"]
			if DICT_ASY_TYPES.has_key(ggb_type):
				asy_type = DICT_ASY_TYPES[ggb_type]
			elif ggb_type == "polygon":
				diagram[xml_geo_obj.attrib["label"]].visible = 0
				#Polygons are silly.  SKIP.
				continue
			elif ggb_type == "text": #OH please no...
				#Get the attributes we need
				text_label = label
				text_content = diagram.objectDict[label].constructor
				xml_startpoint_obj = xml_geo_obj.find("startPoint")
				x_coord = xml_startpoint_obj.attrib['x']
				y_coord = xml_startpoint_obj.attrib['y']

				#Add this to a dict just for texts, assuming visible
				if xml_geo_obj.find("show").attrib["object"] == "true":
					diagram.text_dict[text_label] = {"text" : text_content, "x" : x_coord, "y" : y_coord}

				#Delete this from the diagram
				del diagram.objectDict[label]
				diagram.objectList.remove(label)
				continue
			else:
				print "/* WARNING: Dragon does not know how to handle type %s */" %ggb_type
				continue
				#Cross fingers here!

			
			if diagram.has_key(label):
				#OK, so just slap on attributes, later.
				diagram[label].asy_obj_type = asy_type
				diagram[label].ggb_obj_type = ggb_type
					
			else:
				#Oh, free object?
				if ggb_type == "point":
					x_coord = xml_geo_obj.find('coords').attrib['x']
					y_coord = xml_geo_obj.find('coords').attrib['y']
					diagram[label] = GGBObject(label = label, asy_obj_type = asy_type, constructor = "(%s, %s)" %(x_coord,y_coord) )
				elif ggb_type == "numeric":
					val = xml_geo_obj.find('value').attrib['val']
					diagram[label] = GGBObject(label = label, visible = 0, asy_obj_type = asy_type, constructor = val)
					diagram[label].depend += 1
				else:
					print "PANIC: Dragon cannot handle free object of type %s" %ggb_type
					print "Dying..."
					exit()

			#OK, attributes now...
			if xml_geo_obj.find("show") == None:
				#lol no show?
				#Moving on...
				continue

			if xml_geo_obj.find("show").attrib["object"] == "true":
				diagram[label].visible = 1
				if asy_type == "path":
					colorArray = []
					for c in 'rgb':
						colorArray.append(int(xml_geo_obj.find("objColor").attrib[c])/256.0)
					thick = int(xml_geo_obj.find("lineStyle").attrib["thickness"])
					style = int(xml_geo_obj.find("lineStyle").attrib["type"])

					if sum(colorArray) > 0:
						diagram[label].color = 'rgb(%.1f,%.1f,%.1f)' %tuple(colorArray)
						diagram[label].needs_pen = 1
					if thick != 2:
						diagram[label].thick = 'linewidth(%s)' %LINE_WT[thick]
						diagram[label].needs_pen = 1
					if style != 0:
						diagram[label].style = LINE_STYLE[style]
						diagram[label].needs_pen = 1
				#Paths are pretty configurable ._.
			else:
				diagram[label].visible = 0

			if xml_geo_obj.find("show").attrib["label"] == "true" and diagram[label].visible == 1 and diagram[label].ggb_obj_type != "angle":
				diagram.toLabelList.append(label)
				diagram[label].needs_label = 1
				diagram[label].depend += 1

			diagram[label].label = label


		else:
			#cry
			print "Karl is angry\nKarl does not recognize tag %s" %xml_geo_obj.tag
			print xml_geo_obj.__dict__
			exit()


def clean_string(s):
	return s.replace("'", "_prime")
def restore_string(s):
	return s.replace("_prime", r"\'")

def drawDiagram(diagram, label_locations = {}, opts = {}, view = None):
	CONCISE_MODE = opts['CONCISE_MODE']
	CSE_MODE = opts['CSE_MODE']
	out_asy_code = ""
	if CONCISE_MODE == 0:
		out_asy_code += "/* %s %s \nHomemade Script by v_Enhance. */\n\n" %(SHORT_NAME, VERSION_NUMBER)
	out_asy_code += """mport olympiad; import cse5; size(%(IMG_SIZE)s); real lsf=%(LABEL_SCALE_FACTOR).4f; real lisf=%(LINE_SCALE_FACTOR).1f; defaultpen(fontsize(%(FONT_SIZE)s));"""  %opts
	if CONCISE_MODE == 1:
		out_asy_code.replace("; ", "\n") # Add newlines

	if view is not None:
		out_asy_code += " real xmin=%.2f; real xmax=%.2f; real ymin=%.2f; real ymax=%.2f;" %view
	if CSE_MODE == 1 and opts['CSE_COLORS'] == 0:
		out_asy_code += " pathpen=black; pointpen=black;"
	out_asy_code += "\n"

	if CONCISE_MODE == 0:
		out_asy_code += "\n"

	#Declare pairs, paths, etc. which are dependencies
	if CONCISE_MODE == 1:
		#Assemble lists of all dependencies
		concise_depend_declare_dict = {}
		for label in diagram.objectList:
			curr_obj = diagram[label]
			if curr_obj.depend >= DEPEND_THRESHOLD: 
				curr_asy_obj_type = curr_obj.asy_obj_type
				concise_depend_declare_dict[curr_asy_obj_type] = concise_depend_declare_dict.get(curr_asy_obj_type, []) + [label]
			else:
				pass
		
		for generic_asy_obj_type in concise_depend_declare_dict.keys():
			out_asy_code += "%s %s; " %(generic_asy_obj_type, ', '.join(concise_depend_declare_dict[generic_asy_obj_type]))
		out_asy_code += "\n"
	else:
		#We'll just shout them out as we go.
		pass

	#Actually create objects!
	#Not drawing: this is only those that need to have a reference
	if CONCISE_MODE == 0:
		out_asy_code += "/* Initialize Objects */\n"

	for label in diagram.objectList:
		curr_obj = diagram[label]
		if curr_obj.depend >= DEPEND_THRESHOLD or curr_obj.needs_label:
			if CONCISE_MODE == 0:
				out_asy_code += "%s %s = %s;\n" %(curr_obj.asy_obj_type, label, curr_obj.constructor)
			else:
				out_asy_code += "%s = %s; " %(label, curr_obj.constructor)
		else:
			pass
	
	out_asy_code += "\n"
	if CONCISE_MODE == 0:
		out_asy_code += "/* Draw objects */\n"

	#DRAW EVERYTHING
	#First, decide how to dot points and draw paths
	if CSE_MODE == 0:
		dotCmd = "dot"
		drawCmd = "draw"
	elif CONCISE_MODE == 0:
		dotCmd = "Drawing"
		drawCmd = "Drawing"
	else:
		dotCmd = "D"
		drawCmd = "D"
	#Main loop
	for label in diagram.objectList:
		curr_obj = diagram[label]
		if curr_obj.depend < DEPEND_THRESHOLD:
			obj_repr = curr_obj.constructor # If object wasn't declared earlier
		else:
			obj_repr = label # Already declared -- refer to by name
		if curr_obj.visible == 0:
			pass #Don't draw invisible objects
		else:
			#Figure out how to draw depending on whether path, pair, or other type.
			if curr_obj.asy_obj_type == "pair":
				out_asy_code += "%s(%s);" %(dotCmd, obj_repr)
				out_asy_code += "\n" if CONCISE_MODE == 0 else " "
			elif curr_obj.asy_obj_type == "path":
				if not curr_obj.needs_pen:
					out_asy_code += "%s(%s);" %(drawCmd, obj_repr)
					out_asy_code += "\n" if CONCISE_MODE == 0 else " "
				else:
					#Create a pen
					penProps = [blah for blah in [curr_obj.color, curr_obj.thick, curr_obj.style] if blah != None]
					if CONCISE_MODE == 0:
						pen = ' + '.join(penProps)
						out_asy_code += "%s(%s, %s);\n" %(drawCmd, obj_repr, pen)
					else:
						pen = '+'.join(penProps)
						out_asy_code += "%s(%s, %s); " %(drawCmd, obj_repr, pen)
			elif curr_obj.asy_obj_type == "real":
				#Sorry, idk how to draw a real number.</sarc>
				continue
			else:
				print "Type %s from object %s is not recognized" %(curr_obj.asy_obj_type, curr_obj)
				print "Dying..."
				exit()
	

	#Setup label commands.
	if CSE_MODE == 0 and CONCISE_MODE == 0:
		label_cmd_name = "label"
	elif CONCISE_MODE == 1:
		label_cmd_name = "MP"
	else:
		label_cmd_name = "MarkPoint"
	
	out_asy_code += "\n"
	if CONCISE_MODE == 0:
		out_asy_code += "/* Label points */\n"

	# If concise, change the long CSE commands to the abbreviations
	for long_name in CSE_CONCISE_TRANSLATE:
		out_asy_code.replace(long_name, CSE_CONCISE_TRANSLATE[long_name])
	
	#Finally, before the last labelling, clean up apostrophes and such
	out_asy_code = clean_string(out_asy_code)

	#Label each object
	for label in diagram.objectList:
		curr_obj = diagram[label]
		if not curr_obj.needs_label:
			pass
		else:
			where = label_locations.get(label, "lsf * dir(45)")
			if CSE_MODE == 0:
				out_asy_code += "%s(\"$%s$\", %s, %s);" %(label_cmd_name, label, clean_string(label), where)
			else:
				out_asy_code += "%s(\"%s\", %s, %s);" %(label_cmd_name, label, clean_string(label), where)
			out_asy_code += "\n" if CONCISE_MODE == 0 else " "	
	
	#Print the texts
	for text_label in diagram.text_dict.keys():
		text = diagram.text_dict[text_label]["text"]
		x = diagram.text_dict[text_label]["x"]
		y = diagram.text_dict[text_label]["y"]
		if CSE_MODE == 1:
			if text[0] == "$" and text[-1] == "$": text = text[1:-1]
		out_asy_code += "%s(%s, (%s,%s));" %(label_cmd_name, text, x,y)
		out_asy_code += "\n" if CONCISE_MODE == 0 else " "	

	#Viewports	
	if view != []:
		if CONCISE_MODE == 0:
			out_asy_code += "\n/* Clip the image */ \n"
		out_asy_code += "clip((xmin,ymin)--(xmin,ymax)--(xmax,ymax)--(xmax,ymin)--cycle);"
	return out_asy_code

