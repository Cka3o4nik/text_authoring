# -*- coding: UTF-8 -*-

import json, re, pdb, random
#from jabber_client import jabberFuncResultWrapMulti
from fileUtils import *
import http_lib#, procUtils

START_ARG = 1
SCRIPT_PATH = FilePathName(SCRIPT_FOLDER)
#DATA_PATH = FilePathName(ARGS.path)#SCRIPT_PATH+'test_data'

WAV_EXT = '.wav'
LAB_EXT = '.lab'
OLD_LAB_EXT = '._lab'
JSON_EXT = '.json'
YAN_EXT = '.yam'

WORK_EXTS = (WAV_EXT, LAB_EXT, OLD_LAB_EXT, JSON_EXT, YAN_EXT)

META_TAGS_SET = set((u'М', u'Ж', u'Р', u'НГ', u'Г', u'НН', u'ПК', u'ИЯ', u'НР'))
META_TAGS_SET.add(u'')

TXT_LABELS = (u'РР', u'СР', u'С', u'КР', u'ШД', u'НП', u'НР', u'Д', u'К', u'М', u'Ш', u'Х')

JSON_GENDERS = {u'М': "Male", u'Ж': "Female", u'Р': "Child"}

AFTER_CORR_BAD_TESTS = (ur'[\\/]',
	 											ur'(?i)[а-я]\*[а-я]',
	 											ur'\*[а-я]+\s',
	 											ur'\s[а-я]+\*',
												ur'(?i)[а-я*+:№\)\]][)(\]\[][а-я*+:№\(\[]',
												ur'[^^][!~][^$]',
												ur'(?i)![а-я]',
												ur'(?i)[а-я]!',
												ur'\([^\(]*~[^\(]*\)',
												ur'(?i)[а-я][a-z]',
												ur'(?i)[a-z][а-я]',
												ur'[А-Я][а-я]',
												ur'[а-я][А-Я]',
												ur'(^|\s)[)(*](\s|$)',
												ur'(^|\s)\)',
												ur'\((\s|$)',
												u'New')

SPEECH_IN_SPEECH = (r'^\(РР ([^\(]*?)\)$', r'\1')
TIMESTAMPS_PATTERN = r'^\d+ \d+'

OPERATOR_CODES = (
	('alisa', 'OAL'),
	('tanya', 'OTA'),
	('anya_sm', 'OAN'),
	('anya', 'OAN'),
	('sergei', 'OSE'),
	('sergey', 'OSE'),
	('georgy', 'OGE'),
	('lyuba', 'OLY'),
	('katya', 'OKA'),
	('inna', 'OIN'),
	('lera', 'OLE'),
	('ira', 'OIR'),
)

#EXPAND_TAGS = ARGS.expand_tags # '--expand-tags' in sys.argv
BAD_DATA_FOLDER = 'Bad data'
#-----------------------------------------------------------------

class TestFailure(Exception): pass

def getBasePathName(src_filename):
#	return FilePathName(src_filename.splitext()[0])
	try:
		return unicode(autoconvert(src_filename).splitext()[0])
	except Exception as ex:
		logExc('Bad filename: %s'%src_filename)
		raise ex

def getBadPath(src_filename, subdir):
	bad_path = autoconvert(src_filename).dirname() + BAD_DATA_FOLDER + subdir
	bad_path.makedirs()
	return bad_path

def getWavLabJSON(src_filename):
	basename = getBasePathName(src_filename)

	wav = FilePathName(basename+WAV_EXT)
	lab = FilePathName(basename+LAB_EXT)
	logOut('lab: %s'%lab, DEBUG)

	json_file = FilePathName(basename+JSON_EXT)
	return wav, lab, json_file


def safe_move_to(src_file, dst_dir):
	if src_file.exists() and unicode(src_file)!=unicode(dst_dir+src_file.basename()):
#		try:
			src_file.move_to(dst_dir)
#		except:
#			pdb.set_trace()

def getWorkFile(src_filename, ext):
	return FilePathName(getBasePathName(src_filename)+ext)

def getWorkFiles(src_filename):
	return [getWorkFile(src_filename, ext) for ext in WORK_EXTS]

def moveWorkFiles(base_pathname, dst_folder):
	for src in getWorkFiles(base_pathname):
		safe_move_to(src, dst_folder)

def replace_while_string_changes(pattern, repl, source, flags=0):
	prev_src = None
	while prev_src != source:
	 	prev_src = source
		source = re_sub(pattern, repl, source, flags)

	return source
	
def convertMeta4JSON(meta_list):
	gender = None
	for meta in meta_list:
		if meta in JSON_GENDERS:
			gender = JSON_GENDERS[meta]
			break

	return {
    "bad_quality_set": u'ПК' in meta_list,
    "gender": gender,
    "harmonic_noise_set": u'Г' in meta_list,
    "native": u'НН' not in meta_list,
    "no_speech_set": u'НР' in meta_list,
    "not_harmonic_noise_set": u'НГ' in meta_list,
    "unknown_lang_set": u'ИЯ' in meta_list
	}

class CallStats(object): pass
re_call_stats = CallStats()
re_call_stats.pattern_requests = 0
re_call_stats.cache_hits = 0

#RE_global_storage = {}
#def get_compiled_pattern(pattern, flags=0):
#	re_call_stats.pattern_requests += 1
#
#	pattern_key = pattern+str(flags)
#	pattern_RE = RE_global_storage.get(pattern_key)
#	if not pattern_RE:
#		pattern_RE = re.compile(pattern, flags) 
#		RE_global_storage[pattern_key] = pattern_RE
#	else:
#		re_call_stats.cache_hits += 1
#
#	return pattern_RE


#@handleExceptionDecor
def getText(lab, pattern=None, group=None, flags=0):
	lab_text = cat(lab).strip('\r\n')#.decode('utf8')
	try:
		lab_text = lab_text.decode('utf8')
	except:
		raise TestFailure(u'Invalid lab %s encoding. Text: [%r]!'%(lab, lab_text))
		

	if not pattern:
		return lab_text

	try:
		res = re_extract(pattern, lab_text)
		if group:
			res =  res[group-1]
	except:
		logOut(u'File [%s] does not contain regex [%s] group %s!'%(lab, pattern, group), logger_name = TEST_ERRORS)
		res = None

	return res


def get_text_only(markup):
	#Фильтруем исходный текст
#	logVar('txt', txt)
	txt = re_sub(ur'(?m)^\d+ \d+ +(.+)', ur'\1', markup)
	txt = replace_while_string_changes(ur'(?m)^[А-Я]*_[А-Я]*', ur'', txt)
	txt = replace_while_string_changes(ur'\(\S+ ([^()]+)\)', ur'\1', txt)

	txt = re_sub(ur'\(\S+(.*?)\)', ur'\1', txt)
	txt = re_sub(ur'\(\S+', u' ',txt)

	txt = re_sub(ur'\*(.+?)\*', ur'\1',txt)
	txt = re_sub(ur'№\S+№=(\S+)', ur'\1',txt)
	txt = re_sub(ur'[;":+!№)-]', u'',txt)
	txt = re_sub(ur' +', u' ',txt)

	return txt.strip()


def getLabTextOnly(lab):
	return get_text_only(getText(lab))
								

def re_sub(find, replace, source, flags=0):	
	find_RE = get_compiled_pattern(find, flags)
	return re.sub(find_RE, replace, source)


def correctText(text):	
	for lbl in TXT_LABELS:
		text = re_sub(ur"(\s?)([/\\])%s(.*?)\2(\s?)"%lbl, ur"\1(%s\3)\4"%lbl, text)

	text = text.replace(u'#', u'№')
	text = text.replace(u'~', u'!')
	return text


#@handleExceptionDecor
def txtMatches(text, regexp, flags=re.U):
	res = re_extract(regexp, autoconvert_u(text))
	return res!=None



#@procUtils.threadFunctionLocker
def yaspell_(str, lang='ru'):
	useCache = True
	r = None
	attempt = 0
	while r==None:
		r = page_cacher.get_page(YSPELL_URL, {'text':str.encode('utf8'), 'lang':lang}, fUseCache=useCache)
		attempt += 1

		try:
			r = json.loads(r)
		except:
			logOut('Attempt %d. Using HTTP cache: %s'%(attempt, useCache))
			logErr('HTTP response processing error. Data: %s'%r)
			r = None
			useCache = False
			if 2<attempt:
				logErr('check spelling made 3 attempts to download data. Supposing serious network problems.')
				logOut('Current proxy: %s. Waiting for operator resolution...'%proxies)
				raw_input('Press Enter to retry: ')
				attempt = 0

	for word, replacement in [(x['word'], (x['s'] + [''])[0]) for x in r if x['code'] <3]:
		if replacement:
			str = str.replace(word, replacement)

	return str
		

REF = 'ref'
HYP = 'hyp'
def parse_hyp_file(fname):
	res = {}
	txt = fname.cat()
	for hyp in txt.split('\n\n')[4:]:
		lines = hyp.decode('utf8').split('\n')
		if len(lines)>5:
			it = {}
			it[REF] = ' '.join(lines[3].split()[1:])
			it[HYP] = ' '.join(lines[4].split()[1:])
			filename = lines[1].split()[1][1:-1]
			filename = filename.replace('/', '_') 
			res[filename] = it

	return res


def replace_op_codes(txt):
	for src, repl in OPERATOR_CODES:
#		txt = re_sub(src, repl, txt, re.I, re.U)
		txt = txt.lower().replace(src, repl)

	return txt
#-----------------------------------------------------------------


TEST_ERRORS = 'TST_ERR'
