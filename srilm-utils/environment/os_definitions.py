# -*- coding: UTF-8 -*-

import os, sys
#from fileUtils import *

strFILENAME_ENCODING = sys.getfilesystemencoding()
SYS_ENC = sys.getdefaultencoding()
strSTDOUT_ENC = sys.stdout.encoding or "utf8"

if False:#False #True
	print('sys.getdefaultencoding    = ' + SYS_ENC)
	print('sys.getfilesystemencoding = ' + strFILENAME_ENCODING)
	print('sys.stdin.encoding        = ' + sys.stdin.encoding)
	print('sys.stdout.encoding       = ' + strSTDOUT_ENC)

os_type_is_nt = os.name == 'nt'
if os_type_is_nt:
	OS_OUTPUT_ENCODING = 'cp1251'
	#OS_EXCEPTION_ENCODING = 'CP1251'
	TERMINAL_CLEAR_CMD = lambda: os.system('cls')
else:
	OS_OUTPUT_ENCODING = 'utf8'
	TERMINAL_CLEAR_CMD = lambda: os.system('clear')

strFS_ENCODING = OS_OUTPUT_ENCODING
