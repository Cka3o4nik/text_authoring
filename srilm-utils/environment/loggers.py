# -*- coding: UTF-8 -*-

import os, os.path as op, time, socket, inspect

from loggers_console import *
from os_definitions import *
from logging import handlers

PC_NAME = socket.gethostname()
if os_type_is_nt:
	dfltLOG_SUBFOLDER = 'logs\\' 
else:
	dfltLOG_SUBFOLDER = 'logs/'

SCRIPT_FILENAME = sys.argv[0]
DEFAULT_LOG_FILENAME = 'srilm-utils' # op.basename(SCRIPT_FILENAME)
SCRIPT_FOLDER = '' # op.dirname(SCRIPT_FILENAME)
defaultLOG_FOLDER = op.join(SCRIPT_FOLDER, dfltLOG_SUBFOLDER)

FILE_ONLY_LOGGER = 'FileOnlyLogger'

def configureFileLogger(astrLogFilename=DEFAULT_LOG_FILENAME, minLogLevel=logging.INFO, fileLogLevel=INFO, logger_name = DEFAULT_LOGGER_NAME, astrLogFolder=defaultLOG_FOLDER):
	configureDefaultLogger(minLogLevel)
	logger = logging.getLogger(logger_name)
	
	try:
	  os.mkdir(astrLogFolder)#os.path.join(os.getcwd(), astrLogFolder)
	except:
	  pass
	
	# create file handler and set level to debug
	fh = logging.FileHandler(u'%s%s_%s.log'%(astrLogFolder, astrLogFilename, time.strftime('%Y-%m-%d_%H-%M-%S')))
	fh.setLevel(fileLogLevel)#logging.NOTSET
	
	# add formatter to fh
	fh.setFormatter(formatter)
	
	# add handlers to logger
	logger.addHandler(fh)

	addHandlerTo(FILE_ONLY_LOGGER, fh)
	return fh


def configureRotatingFileLogger(astrLogFilename=DEFAULT_LOG_FILENAME, backup_count=10, minLogLevel=INFO, fileLogLevel=INFO, logger_name = DEFAULT_LOGGER_NAME, astrLogFolder=defaultLOG_FOLDER):
	configureDefaultLogger(minLogLevel)
	logger = logging.getLogger(logger_name)
	
	try:
	  os.mkdir(astrLogFolder)
	except:
	  pass
	
	log_filename = '%s%s.log'%(astrLogFolder, astrLogFilename)
	#print 'log_filename: ', log_filename

	# create file handler and set level to debug
	fh = logging.handlers.RotatingFileHandler(log_filename, backupCount=backup_count) 
	fh.setLevel(fileLogLevel)
	
	fh.doRollover()

	# add formatter to fh
	fh.setFormatter(formatter)
	
	# add handlers to logger
	logger.addHandler(fh)

	addHandlerTo(FILE_ONLY_LOGGER, fh)
	return fh


def configureMidnightRotatingFileLogger(astrLogFilename=DEFAULT_LOG_FILENAME, minLogLevel=INFO, fileLogLevel=INFO, logger_name = DEFAULT_LOGGER_NAME):
	configureDefaultLogger(minLogLevel)
	logger = logging.getLogger(logger_name)
	
	try:
	  os.mkdir(defaultLOG_FOLDER)
	except:
	  pass
	
	# create file handler and set level to debug
	fh = logging.handlers.TimedRotatingFileHandler('%s%s.log'%(defaultLOG_FOLDER, astrLogFilename), 'midnight') 
	fh.setLevel(fileLogLevel)
	
	fh.doRollover()

	# add formatter to fh
	fh.setFormatter(formatter)
	
	# add handlers to logger
	logger.addHandler(fh)

	addHandlerTo(FILE_ONLY_LOGGER, fh)
	return fh


#def logFuncName(astrMsg='', level = INFO, logger_name = DEFAULT_LOGGER_NAME):
#	logger = logging.getLogger(logger_name)
#	logOut('%s%s'%(getCaller(logger), astrMsg), level, logger_name)


def whoami():
	return inspect.stack()[1][3]

def get_printable_vector(vec, separator=', '):
	return separator.join(('%1.2g'%elem for elem in vec))

def get_printable_vector_log_record(msg, vec, separator=', '):
	return msg%get_printable_vector(vec, separator)

def log_out_num_vector(msg, vec, logLevel = INFO, separator=', ', logger_name = DEFAULT_LOGGER_NAME):
	logger = logging.getLogger(logger_name)
	if not logger.isEnabledFor(DEBUG):
		return

	message = get_printable_vector_log_record(msg, vec, separator)
	logOut(message, logLevel, logger_name)
	return message


def log_out_dict(msg, dic, logLevel = DEBUG, logger_name = DEFAULT_LOGGER_NAME):
	dict_list = ('%s: %s'%pair for pair in dic.items())
	logOut(msg%', '.join(dict_list), logLevel, logger_name)
#	logOut(msg+': '+get_printable_vector(vec))

def log_out_str_vector(msg, vec, logLevel = DEBUG, logger_name = DEFAULT_LOGGER_NAME):
	logOut(msg%' '.join((str(elem) for elem in vec)), logLevel, logger_name)

log_out_vector = log_out_num_vector

#logger = None
# create logger
#logger = logging.getLogger(DEFAULT_LOGGER_NAME)#'my_logger'

# create formatter
#formatter = logging.Formatter(MSG_FORMAT, DATE_FORMAT) # %m-%d

#if __name__ != 'main':
#  configureDefaultLogger()
