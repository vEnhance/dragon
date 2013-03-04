#Import some stuff
import os
import zipfile
import ConfigParser
import string
import argparse

from xml.etree.ElementTree import ElementTree
from constants import SHORT_NAME, VERSION_NUMBER, FULL_NAME, GEOGEBRA_XML_LOCATION
from diagram import AsyDiagram, doCompileDiagramObjects, drawDiagram

# Argument parser {{{
parser = argparse.ArgumentParser(
		description = "%s %s, by v_Enhance: %s" %(SHORT_NAME, VERSION_NUMBER, FULL_NAME),
		epilog = "Note: This is, and probably always will be, an unfinished work.  It may not always produce large, in-scale, clearly labelled diagram made with drawing instruments (compass, ruler, protractor, graph paper, carbon paper)."
	)
parser.add_argument("FILENAME",
		action = "store",
		metavar = "FILE",
		help = "The .ggb file to be converted.  Obviously,this argument is required."
		)
#Non-bool arguments
parser.add_argument('--size', '-s',
		action = "store",
		dest = "IMG_SIZE",
		metavar = "SIZE",
		default = "11cm",
		help = "The size of the image to be produce.  Defaults to 11cm."
		)
parser.add_argument('--linescale',
		action = "store",
		dest = "LINE_SCALE_FACTOR",
		metavar = "FACTOR",
		default = 2011,
		help = "Defines the constant by which lines are extended.  The image may break if this is too small, since interesecting lines may return errors.  Default is 2011."
		)
parser.add_argument('--labelscale',
		action = "store",
		dest = "LABEL_SCALE_FACTOR",
		metavar = "FACTOR",
		default = 0.4,
		help = "Defines the constant LSF which is used when labelling points.  This is 0.4 by default."
		)
parser.add_argument('--fontsize',
		action = "store", 
		dest = "FONT_SIZE",
		metavar = "SIZE",
		default = "10pt",
		help = "Default font size, in arbitrary units.  Defaults to \'10pt\'."
		)
parser.add_argument('--config',
		action = "store",
		dest = "CONFIG_FILENAME",
		metavar = "FILENAME",
		default = "",
		help = "If specified, uses the specified .cfg files for this diagram only.  Defaults to FILENAME.cfg"
		)
#Bool arguments
parser.add_argument("--xml",
		action = "store_const",
		dest = "DO_XML_ONLY",
		const = 1,
		default = 0,
		help = "Prints the XML of the input file and exits.  Mainly for debugging"
		)
parser.add_argument('--clip', 
		action = "store_const",
		dest = "CLIP_IMG",
		const = 1,
		default = 0,
		help = "If true, clips the image according to the viewport specified in Geogebra.  Defaults to false."
		)
parser.add_argument('--concise', 
		action = "store_const",
		dest = "CONCISE_MODE",
		const = 1,
		default = 0,
		help = "Turns on concise mode, which shortens the code.  By default, this is turned off."
		)
parser.add_argument('--cse', '--cse5',
		action = "store_const",
		dest = "CSE_MODE", 
		const = 1,
		default = 0,
		help = "Allows the usage of CSE5 whenever possible."
		)
parser.add_argument('--verbose', 
		action = "store_const",
		dest = "CONCISE_MODE",
		const = 0,
		default = 0,
		help = "Turns off concise mode.  This is the default."
		)
parser.add_argument('--nocse',
		action = "store_const",
		dest = "CSE_MODE", 
		const = 1,
		default = 0,
		help = "Forbids the usage of CSE5 except when necessary.  This is the default."
		)
parser.add_argument('--csecolors', 
		action = "store_const",
		dest = "CSE_COLORS",
		const = 1,
		default = 0,
		help = "When using CSE5, use the default pathpen and pointpen (blue/red).  This is off by default."
		)
parser.add_argument('--version',
		action = "version",
		version = "DRAGON %s, by v_Enhance" %VERSION_NUMBER
		)
# }}}

opts = vars(parser.parse_args())
opts['LINE_SCALE_FACTOR'] = float(opts['LINE_SCALE_FACTOR'])
opts['LABEL_SCALE_FACTOR'] = float(opts['LABEL_SCALE_FACTOR'])


if __name__ == "__main__":
	#Get the desired file and parse it
	FILENAME = opts['FILENAME']
	if not "." in FILENAME:
		#Extension isn't given, let's assume it was omitted
		FILENAME += ".ggb"
	elif FILENAME[-1] == ".":
		#Last character is ".", add in "ggb"
		FILENAME += "ggb"
	ggb = zipfile.ZipFile(FILENAME)
	xmlFile = ggb.open(GEOGEBRA_XML_LOCATION)

	#Read configuration file
	config_filename = opts['CONFIG_FILENAME']
	if config_filename.strip() == "":
		config_filename = FILENAME[:FILENAME.find('.')] + '.cfg'
	label_dict = {}
	if os.path.isfile(config_filename):
		config = ConfigParser.RawConfigParser()
		config.optionxform = str # makes names case-sensitive
		config.read(config_filename)
		var_cfg = config.items("var") if config.has_section("var") else {}
		for key, val in var_cfg:
			try:
				opts[string.upper(key)] = eval(val)
			except (NameError, SyntaxError):
				opts[string.upper(key)] = val
		label_cfg = config.items("label") if config.has_section("label") else {}
		for key, val in label_cfg:
			label_dict[key] = "lsf * " + val
	
	# Print XML file only, then exit
	if opts['DO_XML_ONLY']:
		print ''.join(xmlFile.readlines())
		exit()

	#Convert to tree
	ggb_tree = ElementTree()
	ggb_tree.parse(xmlFile)

	#Retrieve the provided values of the viewport {{{
	window_width =	float(ggb_tree.find("euclidianView").find("size").attrib["width"])
	window_height =	float(ggb_tree.find("euclidianView").find("size").attrib["height"])
	xzero = 	float(ggb_tree.find("euclidianView").find("coordSystem").attrib["xZero"])
	yzero = 	float(ggb_tree.find("euclidianView").find("coordSystem").attrib["yZero"])
	xscale = 	float(ggb_tree.find("euclidianView").find("coordSystem").attrib["scale"])
	yscale = 	float(ggb_tree.find("euclidianView").find("coordSystem").attrib["yscale"])

	#Compute the viewport coordinates from this information 
	xmin = -xzero/float(xscale)
	xmax = (window_width - xzero)/float(xscale)
	ymin = -(window_height -yzero)/float(yscale)
	ymax = yzero/float(yscale)
	view = (xmin, xmax, ymin, ymax)
	# }}}

	#Do the construction
	construct_tree = ggb_tree.find("construction")
	theMainDiagram = AsyDiagram()
	doCompileDiagramObjects(construct_tree, theMainDiagram)

	if opts['CLIP_IMG'] == 0:
		print drawDiagram(theMainDiagram, label_dict, opts=opts).replace(u"\u03B1", "alpha")
	else:
		print drawDiagram(theMainDiagram, label_dict, view=view, opts=opts).replace(u"\u03B1", "alpha")

