# -*- coding: UTF-8 -*-

import sys, logging, traceback

from os_definitions import *
from logging import NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL

DEFAULT_LOGGER_NAME = 'DFLT'

MSG_FORMAT  = '%(asctime)s %(name)s %(levelname)s %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# create formatter
formatter = logging.Formatter(MSG_FORMAT, DATE_FORMAT)

LOG_BASE_CLASS = logging.getLoggerClass()
DEFAULT_LOGGER_CALLED = False
#*********************************************************************
class SkaLogger(LOG_BASE_CLASS):
	def __init__(self, astrName):
	  LOG_BASE_CLASS.__init__(self, astrName)
	   
	def logVar(self, aValueObj, astrAddData=''):
#    strMsg = 'logVar %s%s: %s'%(astrAddData, aValueObj.__name__, aValueObj)
	  logVar(aValueObj, astrAddData)
#*********************************************************************

class SelfLogging:
	
	def cfgLoggerParams(self, minLogLevel=INFO):
	  cfgConsoleLoggerParams(self.log_source, minLogLevel)

	def logOut(self, msg, level=INFO):
	  logOut(msg, level, self.log_source)
	
	def logDebug(self, msg):
	  logDebug(msg, self.log_source)
	
def addHandlerTo(logger_name, handler):
	logger = logging.getLogger(logger_name)
	logger.addHandler(handler)

def cfgConsoleLoggerList(log_names, minLogLevel=INFO):
	for log_name in log_names:
	  cfgConsoleLoggerParams(log_name, minLogLevel)

def cfgLoggerList(log_names, minLogLevel=INFO):
	for log_name in log_names:
	  cfgCommonLoggerParams(log_name, minLogLevel)


def cfgCommonLoggerParams(logger_name, minLogLevel=INFO):
	logger = logging.getLogger(logger_name)
	logger.setLevel(minLogLevel)

#	print("logger [%s] id: %d"%(logger_name, id(logger)))
#	print("min log level set to: %s"%minLogLevel)


def cfgConsoleLoggerParams(logger_name, minLogLevel=INFO):
	# вроде это не нужно...
	cfgCommonLoggerParams(logger_name, DEBUG)
	
	# create console handler and set level to debug
	ch = logging.StreamHandler()
	ch.setLevel(minLogLevel)
	
	# add formatter to ch
	ch.setFormatter(formatter)

#	print 'adding console handler to %s'%logger_name
	addHandlerTo(logger_name, ch)



def configureDefaultLogger(minLogLevel=INFO):
	global DEFAULT_LOGGER_CALLED
	if DEFAULT_LOGGER_CALLED:
	  logDbg("configureDefaultLogger was already called! Do not call it second time - it'll add duplicate channel handler.")
	  return

	cfgConsoleLoggerParams(DEFAULT_LOGGER_NAME, minLogLevel)
	DEFAULT_LOGGER_CALLED = True
	
	

def logOut(astrMsg, level = INFO, logger_name = DEFAULT_LOGGER_NAME):
	logger = logging.getLogger(logger_name)
	try:
	  #print 'before encoding: Msg[r]: %r'%astrMsg
	  #astrMsg = astrMsg.encode('utf-8') if isinstance(astrMsg, unicode) else astrMsg
	  #print 'Msg[r]: %r'%astrMsg
	  logger.log(level, astrMsg)
	except:
	  print 'Logger exception caught trying to log out message: %r!!!'%astrMsg
	
	
#def logInfoNamed(astrMsg, logger_name):
#  logOut(astrMsg, INFO, logger_name)

def logDbg(astrMsg, logger_name = DEFAULT_LOGGER_NAME, caller=None):
	logger = logging.getLogger(logger_name)
	if not logger.isEnabledFor(DEBUG):
		return

	caller = caller if caller else getCallerName(logger_name)
	logOut(caller+u': '+astrMsg, DEBUG, logger_name)
	#traceback.print_stack()
	 
def logInfo(astrMsg, logger_name = DEFAULT_LOGGER_NAME):
	logOut(astrMsg, INFO, logger_name)
	
def logFuncName(astrMsg='', level = INFO, logger_name = DEFAULT_LOGGER_NAME):
	logOut(u'%s%s'%(getCallerName(logger_name), astrMsg), level, logger_name)

def logErr(astrMsg, logger_name = DEFAULT_LOGGER_NAME):
	logOut(u'function %s: %s'%(getCallerName(logger_name), astrMsg), ERROR, logger_name)
	
#      except pywin32.error, details:
#        exc_class = sys.exc_info()[0]
#        logOut('Received data: %s'%cmd)
#        strExcData = 'Exception type %s handled while executing command. Details: %s'%(exc_class, details)
#        logOut(strExcData)
#        strExcData.decode('cp1251')


def get_exception_info():
	return traceback.format_exc(10).decode(OS_OUTPUT_ENCODING)


def logExc(astrMsg='exception', logger_name = DEFAULT_LOGGER_NAME):
	msg = astrMsg+u'\n'+get_exception_info()
	logOut(msg, CRITICAL, logger_name)
	return msg


def logExcAsErr(astrMsg='', logger_name = DEFAULT_LOGGER_NAME):
	last_type, last_value, tb = sys.exc_info()
	exc = traceback.format_exception_only(last_type, last_value)
#	str_exc = exc[-1].decode(OS_OUTPUT_ENCODING)#(''.join())#
	str_exc = (''.join(exc)).decode(OS_OUTPUT_ENCODING)##

#	print 'str_exc: ', str_exc
#	msg = u"%s  %s\n%s"%(getCallerName(logger_name), astrMsg, str_exc)
	msg = u'%s\n%s'%(astrMsg, str_exc)
	logOut(msg, ERROR, logger_name)
	return msg


def getCallerName(logger_name):
	return unicode(logging.getLogger(logger_name).findCaller())

def logOutLen(astrMsg, data, level = INFO, logger_name = DEFAULT_LOGGER_NAME):
	return logOut('%s length: %d'%(astrMsg, len(data)), level, logger_name)

def logVar(aValueObj, astrAddData='', lvl=INFO, logger_name=DEFAULT_LOGGER_NAME):
#  print '%s%s: %s'%
#    logger.logVar(aValueObj, astrAddData)
#  print '\n%s'%strMsg
#  strMsg = unicode(strMsg) # , "CP1251"
	strMsg = '%s%r. Variable type: %s'%(astrAddData, aValueObj, type(aValueObj)) # logVar 
	caller = getCallerName(logger_name)
	logOut(strMsg, lvl, logger_name)


logging.setLoggerClass(SkaLogger)

#logger = None
# create logger
#logger = logging.getLogger(DEFAULT_LOGGER_NAME)#'my_logger'

# create formatter
#formatter = logging.Formatter(MSG_FORMAT, DATE_FORMAT) # %m-%d

#if __name__ != 'main':
#  configureDefaultLogger()
