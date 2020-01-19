# -*- coding: UTF-8 -*-

import sys
#from loggers import *

def getArgsCmd(params_start_idx=1):
	params=sys.argv[params_start_idx:]
	return params[0]+'(%s)'%', '.join(params[1:])

def getTxtArgsCmd(params_start_idx=1):
#	func_args = ''
#	if 1 < len(params):
#		spr = '", r"'
#		func_args = r'"%s"'%spr.join(cmd_args[arg_start_index+1:])
	
	params=sys.argv[params_start_idx:]
	strParams = ''
	if 1<len(params):
		strParams = 'ur"%s"'%('", ur"'.join(params[1:]))

	strCmd = params[0]+'(%s)'%strParams
	print(" Command to execute: ", strCmd)
	return strCmd
#	eval(sys.argv[1]+'(%s)'%', '.join(sys.argv[2:]))

def execImportCmd(cmd_args, afImported):
	arg_start_index = 1
	
	module_name = None
	if not afImported:
		module_name = cmd_args[arg_start_index]
		exec('from %s import *'%module_name)
		arg_start_index += 1

#	if not afImported and module_name:
#		module = sys.modules[module_name]
#		if not hasattr(module, 'init'):
#			configureDefaultLogger()
#		else:

#		if hasattr(module, 'init'):
#			init()

	return eval(getTxtArgsCmd(cmd_args[arg_start_index:]))

fIsMain = __name__ == '__main__'
if fIsMain:
	execImportCmd(sys.argv, not fIsMain)
