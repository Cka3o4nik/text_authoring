#!/usr/bin/python
# -*- coding: UTF-8 -*-

import math, shelve, io, contextlib, re, itertools as it
from ctypes import c_char_p, c_double, cdll
import procUtils as pu
from multiprocessing import Process, Pool, Queue, Manager

from fileUtils import *
from launcher import getTxtArgsCmd, getArgsCmd
import pdb

ln_10 = math.log(10)
line_log_threshold = 100000

if os_type_is_nt:
	PUBLIC = FilePathName('//192.168.77.2/Public')
	#SRILM_PATH = ShellCmd(PUBLIC+'Workdata/SRILM/built/cygwin')
	SRILM_PATH = ShellCmd(PUBLIC+'Workdata/SRILM/built/cygwin_c')
else:	
	PUBLIC = FilePathName('/mnt/public')
	#SRILM_PATH = PUBLIC+'Workdata/SRILM/built/cygwin-build'
	SRILM_PATH = ShellCmd()

SHARE = PUBLIC+'share/m.frolov'
SCRIPT_PATH = FilePathName(SCRIPT_FOLDER)
TEXT_BASE_PATH = SHARE+'speech_texts'
#TEXT_BASE_PATH =SCRIPT_PATH

nNG_WORDS_IDX = nPROB_IDX = 0
nLM_WORDS_IDX = 1
nBOW_IDX = -1
nSTATS_IDX = -1

strSRILM_BOL = '<s>'
strSRILM_EOL = '</s>'

strLFDC_BOL = '!ENTER'
strLFDC_EOL = '!EXIT'

DEFAULT_COUNTS_FILE = 'ngram.count'
DEFAULT_MODEL_FILE = 'lang.model'

LM_KEY = 'Top 5000 LM'
#TOP_5K_LM_FILENAME = 'Top 5000 LM'


import datetime as dt
def time_print(str):
	print(('%s  %s'%(dt.datetime.now().strftime(DATE_FORMAT), str)))

def parse_srilm_lm_iterator(srilm_lm):
	dict = set()
	for i, line in enumerate(srilm_lm.xcat()):		
		if i%line_log_threshold == 0:
			#logOut('Lines processed: {0:n}'.format(i)
			print('{0}\tLM file lines read: {1:g}'.format(dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), i))
		
		line = line.strip('\r\n')
		line_data = line.split('\t')
		ldata_len = len(line_data)
		if ldata_len < 2:
			continue

		prob = float(line_data[nPROB_IDX])
		words = parse_split_ngram(line_data[nLM_WORDS_IDX])
		if 2 < ldata_len:
			bow = float(line_data[-1])
		else:
			bow = None
		
		#print 'Line: ', line
		#logDbg('Words: [%s], prob: %s, bow: %s'%(' '.join(words), prob, bow))
		yield words, prob, bow


def srilm_ng_count_iterator(srilm_ngc):
	for i, line in enumerate(srilm_ngc.xcat()):
		if i%line_log_threshold == 0:
			logOut('Lines processed: %d'%i)
		
		line = line.strip('\r\n')
		line_data = line.split('\t')
		#ldata_len = len(line_data)

		#if ldata_len < :
		#	continue

		count = int(line_data[nSTATS_IDX])
		words = parse_split_ngram(line_data[nNG_WORDS_IDX])
		
		#print 'Line: ', line
		#print 'Stats: ', stats, 'words: [%s]'%', '.join(words)
		
		yield words, count


def parse_srilm_lm_iter(lm_filename, stats=None, flt=lambda w, c, p, b: True):
	for ngram, prob, bow in parse_srilm_lm_iterator(lm_filename):
		if not flt(ngram, count, prob, bow):
			continue

		key = str(ngram)
		#logDbg('model key: %s'%key)
		
		if stats:
			count = stats[key]
			#logDbg('stat data: %s, prob: %s'%(stats[key], prob))
		else:
			count = 0

		yield ngram, count, prob, bow


def get_srilm_ng_count_D(ngc_file):
	#logFuncName()
	stats = {1: 0., 2: 0.}

	for ngram, count in srilm_ng_count_iterator(ngc_file):
		#logDbg('Stats key: %s'%key)
		ngram_len = len(ngram)
		if ngram_len < 3:
			stats[ngram_len] += count

	D = stats[1]/(stats[1] + 2*stats[2])
	logOut('D: %f'%D)
	return D


class SRILM_LM_Converter:
	
	def __init__(self):
		self.stats = None
		
	def parse_srilm_lm_iter(self, lm_filename, stats=None, flt=lambda w, c, p, b: True):
		for ngram, prob, bow in self.parse_srilm_lm_iterator(lm_filename):
			key = str(ngram)
			
			#logDbg('model key: %s'%key)
			
			if stats:
				count = stats[key]
				#logDbg('stat data: %s, prob: %s'%(stats[key], prob))
			else:
				count = 0

			if not flt(ngram, count, prob, bow):
				continue

			yield ngram, count, prob, bow


	def parse_srilm_lm_iterator(self, srilm_lm):
		dict = set()
		for i, line in enumerate(srilm_lm.xcat()):		
			if i%line_log_threshold == 0:
				#logOut('Lines processed: {0:n}'.format(i)
				print('{0}\tLM file lines read: {1:g}'.format(dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), i))
			
			line = line.strip('\r\n')
			line_data = line.split('\t')
			ldata_len = len(line_data)
			if ldata_len < 2:
				continue

			prob = float(line_data[nPROB_IDX])
			words = self.parse_split_ngram(line_data[nLM_WORDS_IDX])
			if 2 < ldata_len:
				bow = float(line_data[-1])
			else:
				bow = None
			
			#print 'Line: ', line
			#logDbg('Words: [%s], prob: %s, bow: %s'%(' '.join(words), prob, bow))
			yield words, prob, bow


	def parse_split_ngram(self, str_data):
		str_data = str_data.strip()
		return tuple(str_data.split(' '))
		#return str_data.split(' ')


	def parse_srilm_ng_count(self, ngc_path):
		res = {}

		for words, stats in srilm_ng_count_iterator(ngc_path):
			key = str(words)
			logDbg('Stats key: %s'%key)
			res[key] = stats

		return res


	def convert_srilm_ng_count_direct(self, ngc_file):
		logFuncName()
		stats = {}

		for ngram, count in srilm_ng_count_iterator(ngc_file):
			key = str(ngram)
			#logDbg('Stats key: %s'%key)
			stats[key] = count
			self.add_ngram_to_db(ngram, count)

		return stats

#def parse_srilm_lm_iter(self, lm_filename, stats=None):
#	return parse_srilm_lm_iter(lm_filename, stats)


	def parse_srilm_lm(self, lm_filename, stats=None, afConvert=True, filter=lambda w, c, p, b: True, stop_condition=lambda w, c, p, b: False):
		logFuncName()

		ngram_dict = {}
		for ngram, count, prob, bow in self.parse_srilm_lm_iter(lm_filename, stats, filter):
			if stop_condition(ngram, count, prob, bow):
				break

			key = str(ngram)
			logDbg('model key: %s'%key)
			
			if afConvert:
				self.add_ngram_to_db(ngram, count, prob, bow)

#			if filter(ngram, count, prob, bow):
			n = len(ngram)
			dict_n = ngram_dict.setdefault(n, [])
			#dict_n[ngram] = (count, prob, bow)
			dict_n.append((ngram, count, prob, bow))

		return ngram_dict


	def convert_srilm_lm_direct(self, lm_filename, stats=None, order=100):
		logFuncName()
		
		lm_filename = autoconvert(lm_filename)
		ngram_dict = self.parse_srilm_lm(lm_filename, stats, False, lambda w, c, p, b: len(w)<=order, lambda w, c, p, b: order<len(w))

		for n, dict_n in ngram_dict.items():
			logOut('Adding %d-grams to dictionary'%n)
			#ngram_dict[n]
			for i, (ngram, count, prob, bow) in enumerate(dict_n):
				self.add_ngram_to_db(ngram, count)
				if i%line_log_threshold == 0:
					logOut('Ngrams processed: %d'%i)

		for n, dict_n in ngram_dict.items():
			logOut('Setting %d-gram probabilities/bows'%n)
			for i, ngram_data in enumerate(dict_n):
				self.add_ngram_to_db(*ngram_data)
				if i%line_log_threshold == 0:
					logOut('Ngrams processed: %d'%i)

		return ngram_dict

	
	def load_filter_5000(self):
		self.filter_db = {}
		self.filter_list = load_filter_5000()


	def filter_5000(self, ngram, c, p, b):
		return filter_5000(self.filter_list, self.filter_db, ngram, c, p, b)


	def filter_5000_dictionary_by_lm(self, lm_filename, stats=None):
		logFuncName()

		src_dict = r'anya\dic.txt'
		#src_dict = r'anya\dictUsed_full.txt'
		#src_dict = r'anya\phones.txt'

		dict_file = self.text_base_path + src_dict
		filter_list = [line.strip('\n') for line in dict_file.xcat()]
		#logOut('Filter: %s'%filter_list)

		filter = lambda ngram, c, p, b: ' '.join(ngram) in filter_list
		ngram_dict = {}

		for i, (ngram, count, prob, bow) in enumerate(self.parse_srilm_lm_iter(lm_filename, stats)):
			n = len(ngram)
			if n>1:# or i>30000
				break

			if list(filter(ngram, count, prob, bow)):
				dict_n = ngram_dict.setdefault(n, {})
				dict_n[ngram] = (count, prob, bow)

		# save new dictionary to file for Anya
		flt_dict = r'anya\dictUsed_filtered.txt'
		with open((self.text_base_path + flt_dict).to_fs(), 'w') as filtered_dict_file:
			filtered_dict_file.writelines([ngram[0]+'\n' for ngram in list(ngram_dict[1].keys())])

		ngram_dict[1][('pau',)] = (0, 0, None)
		for n, dict_n in ngram_dict.items():
			logOut('Adding %d-grams to dictionary'%n)
			#ngram_dict[n]
			for i, (ngram, (count, prob, bow)) in enumerate(dict_n.items()):
				self.add_ngram_to_db(ngram, count)
				if i%line_log_threshold == 0:
					logOut('Ngrams processed: %d'%i)

		for n, dict_n in ngram_dict.items():
			logOut('Setting %d-gram probabilities/bows'%n)
			for i, (ngram, (count, prob, bow)) in enumerate(dict_n.items()):
				self.add_ngram_to_db(ngram, count, prob, bow)
				if i%line_log_threshold == 0:
					logOut('Ngrams processed: %d'%i)

		return ngram_dict


	def convert_srilm_lm_Top_5000(self, lm_filename, stats=None):
		logFuncName()

		src_dict = r'anya\dictUsed_filtered.txt'

		dict_file = self.text_base_path + src_dict
		filter_list = [line.strip('\n') for line in dict_file.xcat()]

		#logOut('Filter: %s'%filter_list)

		ngram_dict = {}

		for i, (ngram, count, prob, bow) in enumerate(self.parse_srilm_lm_iter(lm_filename, stats)):
			n = len(ngram)
			if n>2:# or i>30000
				break

			if self.filter(ngram, count, prob, bow):
				dict_n = ngram_dict.setdefault(n, {})
				dict_n[ngram] = (count, prob, bow)

		self.prepare_conversion()
		for n, dict_n in ngram_dict.items():
			logOut('Adding %d-grams to dictionary'%n)
			#ngram_dict[n]
			for i, (ngram, (count, prob, bow)) in enumerate(dict_n.items()):
				self.add_ngram_to_db(ngram, count)
				if i%line_log_threshold == 0:
					logOut('Ngrams added to dictionary: %d'%i)

		for n, dict_n in ngram_dict.items():
			logOut('Setting %d-gram probabilities/bows'%n)
			for i, (ngram, (count, prob, bow)) in enumerate(dict_n.items()):
				self.add_ngram_to_db(ngram, count, prob, bow)
				if i%line_log_threshold == 0:
					logOut('Ngram probabilities exported: %d'%i)
		
		self.cleanup_after_conversion()
		return ngram_dict
	

	def convert(self, ngram_N, model_path, filter=lambda n, c, p, b: True):
		#self.prepare_conversion(ngram_N, model_path)

		self.ngram_N = ngram_N 
		self.model_path = model_path

		srilm_ngc = model_path + DEFAULT_COUNTS_FILE
		srilm_lm = model_path + DEFAULT_MODEL_FILE	

		text_file = self.text_base_path+'joint.txt'

		#create_lm_cmd = (SRILM_PATH+'ngram-count').to_fs(), '-order', unicode(ngram_N), '-text', '%s'%text_file, '-write', \
		#		'%s'%srilm_ngc, '-lm', '%s'%srilm_lm
		#launch(create_lm_cmd, True)

		#dict, model, stats = convert_all_memory()
		#print 'Dict len: ', len(dict), 'LM size: ', len(model), 'Stats list size: ', len(stats)

		stats = None
		#stats = self.convert_srilm_ng_count_direct(srilm_ngc)		
		
		#ngram_dict = self.convert_srilm_lm_direct(srilm_lm, stats)
		
		#self.fill_all_lm_ngrams(ngram_N, ngram_dict)

		self.start(srilm_lm, filter)

		#self.cleanup_after_conversion(ngram_N, model_path)
		logOut('Conversion finished')
	

	def start(self, lm_filename, filter):
		self.flt = filter
		self.convert_srilm_lm_Top_5000(lm_filename, self.stats)
		logOut('db created')


	def prepare_conversion(self): return

	def cleanup_after_conversion(self): return

	def fill_all_lm_ngrams(self, max_n, ngram_dict):
		logFuncName()

		words = ngram_dict[1]
		known_ngrams = ngram_dict[max_n]

		logDbg('words: [%s]'%str(words))

		#word_list = [w[0] for w in words]
		all_ngrams = it.product([w[0] for w in words], repeat=max_n)
		for i, ngram in enumerate(all_ngrams):
			if ngram in known_ngrams:
				continue

			if i%line_log_threshold == 0:
				logOut('Missing ngrams processed: %d'%i)
			
			str_ngram = str(ngram)
			logDbg('Creating missing ngram [%s] probability...'%str_ngram)
			
			i = 2
			bow = 0
			n_igrams = ngram_dict[max_n-1] # getting n-1-gram list
			# discounted p(a_z) = bow(a_) * p(_z)
			a_ = ngram[:-1] # getting n-1 word/phoneme prefix
			_z = list(ngram[1:])
			t_z = tuple(_z)
			while t_z not in n_igrams:
				if not len(_z):
					logErr('Ngram [%s] suffix _z has reduced to an empty stirng'%str_ngram)
					break

				cur_bow = n_igrams.get(a_, (None,))[nBOW_IDX]
				if cur_bow:
					bow += cur_bow

				a_ = tuple(_z[:-1]) # getting n-i word/phoneme prefix
				_z.pop(0) # popping first word/phoneme to get n-i suffix
				t_z = tuple(_z)
				n_igrams = ngram_dict[max_n-i] # getting n-i-gram list
				i += 1
			else:
				prob = n_igrams[t_z][nPROB_IDX]
				cur_bow = n_igrams[a_][nBOW_IDX]
				if cur_bow!=None:
					bow += cur_bow
				#else:
				#	logErr('Ngram [%s] has no bow! Skipping...'%str(ngram))

				prob += bow

			self.add_ngram_to_db(ngram, 0, prob, bow)


	def convert_mem(self):
		for ngram in dict:
			str_ngram = str(ngram)	
			count = stats[str_ngram]
			prob = model[str_ngram][nBOW_IDX]
			if not prob:
				prob = model[str_ngram][nPROB_IDX]

			self.add_ngram_to_db(ngram, count, prob, bow)


	def convert_all_memory(self):
		dict, model = parse_srilm_lm(srilm_lm)
		stats = parse_srilm_ng_count(srilm_ngc)
		return dict, model, stats

	def convert_all_direct(self):
		stats = convert_srilm_ng_count_direct()
		self.convert_srilm_lm_direct(stats)

	def add_ngram_to_db(self, ngram, count, prob=None, bow=None): return


def lm_list_2_dict_converter(lm_records):
	lm_dict = {}
	for i, (ngram, count, prob, bow) in enumerate(lm_records):
		n = len(ngram)
		lst = lm_dict.setdefault (n, [])
		lst.append((ngram, count, prob, bow))
		lm_dict[n] = lst

		if i%line_log_threshold == 0:
			logOut('Ngrams added to dictionary: {0:g}'.format(i))

	return lm_dict


def load_dict_from_db():
	
	logOut('Loading db...')
	db = shelve.open('top_5000.db')
	#db = bsddb.btopen('top_5000.bdb')
	logOut('Obtaining result dict...')
	res = db[LM_KEY]
	logOut('Copying dict -> BSD db...')
	db2[LM_KEY] = res
	logOut('Closing db...')
	db.close ()
	return res

def dict_2_ARPA_converter(lm_dict, lm_file):
	#lm_dict = lm_list_2_dict_converter(lm_records)
	with open(lm_file, 'w') as f:
		
		f.write('\\data\\\n') 
		for n, ngram_list in lm_dict.items():
			f.write('ngram %d=%d\n'%(n, len(ngram_list))) 

		for n, ngram_list in lm_dict.items():
			f.write('\n\n\\%d-grams:\n'%n)
			logOut('Sorting %d-grams...'%n)
			ngram_list.sort(lambda x, y: cmp(x[0], y[0]))

			for i, (ngram, count, prob, bow) in enumerate(ngram_list):
				if i%line_log_threshold == 0:
					logOut('Ngrams written to file: {0:g}'.format(i))

				ng = (word.decode('cp1251').encode('utf8') for word in ngram)
				bow = '' if not bow else bow
				f.write('%s\t%s\t%s\n'%(prob, ' '.join(ng), bow))

def dict_2_LFDC_converter(ngram_N, lm_dict, lfdc_file):
	conv = SRILM_LM_LFDC_Converter()
	conv.ngram_N = ngram_N
	conv.prepare_conversion()

	for n, ngram_list in lm_dict.items():
		if n>ngram_N:
			continue

		logOut('Adding %d-grams...'%n)
		logDbg('N-grams type: %s'%type(ngram_list))
		for i, (ngram, count, prob, bow) in enumerate(ngram_list):
			if i%line_log_threshold == 0:
				logOut('{0:d}-grams added: {1:g}'.format(n, i))

			conv.add_ngram_to_db(ngram, count)


	for n, ngram_list in lm_dict.items():
		if n>ngram_N:
			continue

		logOut('Setting %d-gram probs...'%n)
		for i, (ngram, count, prob, bow) in enumerate(ngram_list):
			if i%10000 == 0:
				logOut('{0:d}-grams converted: {1:g}'.format(n, i))

			#ng = (word.decode('cp1251').encode('utf8') for word in ngram)
			#bow = '' if bow==None else bow
			logDbg('N-gram: [%s, %s, %s, %s]'%(ngram, count, prob, bow))
			bow = None if n == ngram_N else bow
			conv.add_ngram_to_db(ngram, count, prob, bow)

	conv.cleanup_after_conversion(str(lfdc_file))

def srilm_lm_2_LFDC(ngram_N, lm_file, out_path):
	converter = SRILM_LM_MP_Converter(flt_proc_count=1)
	lm_dict = converter.convert_srilm_lm_direct(lm_file, None, ngram_N)
	dict_2_LFDC_converter(ngram_N, lm_dict, autoconvert(out_path) + 'LFDC.dat')

def srilm_lm_importer(lm_filename, input_ng_cpb_queue, stats=None):
	iter = parse_srilm_lm_iter(lm_filename, stats)
	#map(input_ng_cpb_queue.put, iter)
	for i, (ngram, count, prob, bow) in enumerate(iter):
		if 2<len(ngram):
			break

		input_ng_cpb_queue.put((ngram, count, prob, bow))

	input_ng_cpb_queue.put(None)


def load_filter_5000():
	#src_dict = TEXT_BASE_PATH + 'anya'+'dictUsed_filtered.txt'
	src_dict = TEXT_BASE_PATH + 'anya'+'echo_words_5000kw_misha.txt'

	filter_list = [line.strip('\n') for line in src_dict.xcat()]

	print(('Filter dictionary size: %d'%len(filter_list)))
	return filter_list


def filter_5000(filter_list, filter_db, ngram, c, p, b):
	#values = [word in filter_list in filter_list for word in ngram]
	tests = [filter_db.setdefault(w, w in filter_list) for w in ngram]
	return all(tests)

def lm_filter(flt, filter_db, input_ng_cpb_queue, output_ng_cpb_queue):
	logFuncName()
	
	filter_list = load_filter_5000()

	task = input_ng_cpb_queue.get()
	#while True: pass
	while task:
		#print('Received task: %s'%str(task))
		#print 'FFW: ', filter_list[2].decode('cp1251')
		#print 'filter checking for task FW', task[0][0].decode('cp1251')
		if flt(filter_list, filter_db, *task):
			print('filter passed')
			print('Task %s passed filter and queued to export'%str(task.decode('cp1251')))
			output_ng_cpb_queue.put(task)

		task = input_ng_cpb_queue.get()
	
	output_ng_cpb_queue.put(None)


class SRILM_LM_MP_Converter(SRILM_LM_Converter):

	def __init__(self, flt_proc_count=1):
		SRILM_LM_Converter.__init__(self)
		self.flt_proc_count = flt_proc_count


	def srilm_lm_importer(self, input_ng_cpb_queue):
		#input_ng_cpb_queue = self.input_ng_cpb_queue
		iter = self.parse_srilm_lm_iter(self.lm_filename, self.stats)
		list(map(input_ng_cpb_queue.put, iter))
		input_ng_cpb_queue.put(None)


	def lm_filter(self):
		task = self.input_ng_cpb_queue.get()
		while task:
			ngram = task[0]
			#print('Processing ngram [ %s ]...'%' '.join(ngram))
			if self.flt(*task):
				#if ngram[0] == '<s>':
				#	print('Ngram [ %s ] added'%str(ngram))

				self.output_ng_cpb_queue.put(task)
			#else:
			#	print('Ngram [ %s ] not added'%str(task))

			task = self.input_ng_cpb_queue.get()
		
		self.output_ng_cpb_queue.put(None)


	def lm_db_saver(self):
		self.prepare_conversion()
		
		output_ng_cpb_queue = self.output_ng_cpb_queue

		task = output_ng_cpb_queue.get()
		task_list = []
		
		#db = shelve.open('top_5000.db', writeback=True)
		db[LM_KEY] = []

		i = 0
		while task:
			if i%line_log_threshold == 0:
				logOut('Ngrams added to dictionary: {0:g}'.format(i))
				#db.sync()

			#ngram, count, prob, bow = task
			#self.add_ngram_to_db(ngram, count)
			self.add_ngram_to_db(*task)
			task_list.append(task)
			
			#if 7860000<i:
			#	db.sync()
	
			task = output_ng_cpb_queue.get()
			#db[LM_KEY].append(task)
			i += 1

		logOut('Saving ngrams to db...')
		db[LM_KEY] = task_list
		db.close()

		#for i, task in enumerate(task_list):
		#	self.add_ngram_to_db(*task)
		#	if i%10000 == 0:
		#		logOut('Ngram probabilities set: %d'%i)

		self.cleanup_after_conversion()#, flt_proc_count


	def start(self, lm_filename, flt):
		self.lm_filename = lm_filename
		self.flt = flt
		
		mgr = Manager()
		#mgr.start()
		
		self.load_filter_5000()

		filter_db = mgr.dict()
		
		# Очередь распарсенных из модели SRILMа данных (ngram, count, prob, bow)
		input_ng_cpb_queue = Queue(300000)
		#input_ng_cpb_queue = mgr.Queue()
		self.input_ng_cpb_queue = input_ng_cpb_queue
		
		# Выходная очередь данных для экспорта в БД/LFDC
		output_ng_cpb_queue = Queue()
		#output_ng_cpb_queue = mgr.Queue()
		self.output_ng_cpb_queue = output_ng_cpb_queue
		
		
		lm_importer = Process(target=self.srilm_lm_importer, args=(input_ng_cpb_queue, ))
		#lm_importer = Process(target=srilm_lm_importer, args=(lm_filename, input_ng_cpb_queue, ))
		lm_importer.start()
	
		#filter_pool = Pool(processes=self.flt_proc_count)
		#filter_pool.apply_async(lm_filter, (filter_5000, input_ng_cpb_queue, output_ng_cpb_queue))
		#filter_pool.apply_async(self.lm_filter)

		proc_list = []
		for i in range(self.flt_proc_count):
			#filter = Process(target=lm_filter, args=(filter_5000, filter_db, input_ng_cpb_queue, output_ng_cpb_queue))
			flt_proc = Process(target=self.lm_filter)
			flt_proc.start()
			proc_list.append(flt_proc)
		
		self.lm_db_saver()

		logOut('db created')
		[proc.terminate() for proc in proc_list]

		
class SRILM_LM_LFDC_Converter:

	def __init__(self, flt_proc_count=1):
		self.text_base_path = TEXT_BASE_PATH

		
	def parse_split_ngram(self, str_data):
		str_data = str_data.strip().replace(strSRILM_BOL, strLFDC_BOL)
		str_data = str_data.replace(strSRILM_EOL, strLFDC_EOL)
		
		return tuple(str_data.split(' '))


	# add ngram to LFDC interface 
	def add_ngram_to_db(self, ngram, count, prob=None, bow=None):
		n = len(ngram)
		str_ngram = ' '.join(ngram)
		
		c_words = [c_char_p(word) for word in ngram]
		c_words.append(None)

		c_ngram = (c_char_p * n)(*c_words)		

		if prob == None:
			logDbg('Adding ngram [%s] with count: %s'%(str_ngram.decode('cp1251'), count))
			self.lfdc_dll.AddNgramIntoStructure(n, c_ngram)
			return

		ln_prob = prob*ln_10
		ln_bow = bow*ln_10 if bow!=None else None

		logDbg('CorrectNgramData call for [%s] with count: %s, prob: %f, bow: %s'%(str_ngram, count, ln_prob, ln_bow))
		try:
			self.lfdc_dll.CorrectNgramData(n, c_ngram, count, c_double(ln_prob))
			if ln_bow!=None:
				logDbg('Set bow for n=%d [%s] with count: %s, prob: %f, bow: %s'%(n, str_ngram, count, ln_prob, ln_bow))
				try:
					self.lfdc_dll.CorrectNgramData(n+1, c_ngram, count, c_double(ln_bow))
				except:
					logOut('Tried to set bow for n=%d [%s] with count: %s, prob: %f, bow: %s'%(n, str_ngram, count, ln_prob, ln_bow))
					sys.exit(-1)
		except:
			logExc("CorrectNgramData call failed")
	

	def prepare_conversion(self):
		self.lfdc_dll = cdll.LngFileData
		self.lfdc_dll.LoadingLFDC(self.ngram_N)

	def cleanup_after_conversion(self, lfdc_file):
		#lfdc_file = str(self.model_path+'LFDC_%s.dat'%os.getpid())
		self.lfdc_dll.OutputDataFile(lfdc_file)
		logOut('Model saved to LFDC binray file')

		self.lfdc_dll.UnloadLFDC()

		launch(('DataVisual.exe', lfdc_file, str(lfdc_file+'.txt')))


	def load_filter_5000(self):
		self.filter_db = {}
		self.filter_list = load_filter_5000()


	def filter_5000(self, ngram, c, p, b):
		#value_list = [word in self.filter_list for word in ngram]
		value_list = [self.filter_db.setdefault(word, word in self.filter_list) for word in ngram]
		return all(value_list)


def get_srilm_cmd_for(cmd, *add_params):
	res_cmd = SRILM_PATH+cmd
	res_cmd.extend_args(*add_params)
	return res_cmd

def launch_srilm_cmd_for(afWait, stdindata, cmd, *add_params):
	add_params = [str(el) for el in add_params]
	shell_cmd = get_srilm_cmd_for(cmd, *add_params)
	#logOut('shell_cmd: [%s]'%shell_cmd)
	shell_cmd.launch(afWait, stdindata)

def get_counts_filename_for(src_filename):
	if src_filename!='-':
		res = src_filename+COUNTS_EXT 
	else:
		res = DEFAULT_COUNTS_FILE

	return res


def get_create_srilm_ng_counts_cmd(src_filename):
	cmd = ShellCmd(CREATE_STAT_CMD_TMPL)
	cmd.extend_args('-text', src_filename, '-write', get_counts_filename_for(src_filename))
	return cmd

def ng_count(afWait=True, input_text=None, *add_args):
	cmd = ShellCmd(CREATE_STAT_CMD_TMPL)
	#cmd.append_arg('-tolower')
	cmd.extend_args(*add_args)
	return cmd.launch(afWait, input_text)

def create_srilm_lm(counts_filename, afWait=True, input_text=None, *add_args):
	add_args.extend(('-read', counts_filename))
	ng_count(afWait, input_text, *add_args)


#def create_srilm_ng_counts_stdin(cnts_fname, input_text):
#	cmd = ShellCmd(CREATE_STAT_CMD_TMPL)
#	cmd.extend(('-text', '-', '-write', cnts_fname))
#	logOut('Starting ngram-count for [%s]'%' '.join(cmd))
#	return ProcMgmt.startThread(launch, cmd, True, stdindata=input_text)
#	#return ProcMgmt.startThread(eval, 'pass')

def th_launch_ngram_count(count_list, thread_list, input_text):
	counts_fname = get_worker_counts_filename(len(thread_list))
	logOut('input_text len: %d'%len(input_text))
	th = create_srilm_ng_counts_stdin(counts_fname, input_text)
	count_list.append(counts_fname) 
	thread_list.append(th)

def create_srilm_ng_counts_th(src_filename, afWait=False):
	cmd = get_create_srilm_ng_counts_cmd(src_filename)
	logDbg('Starting ngram-count for %s'%cmd)
	return ProcMgmt.startThread(launch, cmd, True)

def thrd_srilm_ng_counts_collector(src_queue):
	while True:
		src_filename = src_queue.get()
		cmd = get_create_srilm_ng_counts_cmd(src_filename)
		logDbg('Starting ngram-count for %s'%cmd)
		launch(cmd, True)

def ng_counts_merge(count_files, counts_res=DEFAULT_COUNTS_FILE):
	args = ['-write', counts_res]
	args.extend(count_files)
	launch_srilm_cmd_for(True, None, 'ngram-merge', *args)

def ng_counts_merge_reduce(count_files):
	bulk_size = 1000
	block_count = len(count_files)/bulk_size
	for i in range(block_count):
		block = count_files[i*bulk_size:(i+1)*bulk_size]
		if 0<i:
			block.append('ngram.count_%d'%i)

		logOut('Starting %d-th ngram-merge'%i)
		ng_counts_merge(count_files, 'ngram.count_%d'%(i+1))

def get_worker_counts_filename(worker_idx):
	return 'ngram.count_%d'%worker_idx

def thrd_srilm_ng_counts_merger(worker_idx, src_queue):
	count_files = []
	bulk_size = 1000
	try:
		for i in range(bulk_size):
			count_files.append(src_queue.get())
	except:
		pass

	logOut('Starting %d-th ngram-merger'%worker_idx)
	ng_counts_merge(count_files, get_worker_counts_filename(worker_idx))


def ng_counts_merge_parallel(count_files):
	worker_list = []
	src_queue = Queue()
	for fname in count_files:
		src_queue.put(fname)

	for i in range(3):
		worker = create_proc_worker(ProcMgmt.md.Process, thrd_srilm_ng_counts_merger, i, src_queue)
		worker_list.append(worker)
		
	count_files = []
	for i, worker in enumerate(worker_list):
		worker.join()
		count_files.append(get_worker_counts_filename(i))
		
	logOut('Starting last ngram-merge!')
	ng_counts_merge(count_files)

def make_big_lm(order, counts_file, model_file, vocab_file, tmp_path):
	name = 'py_big_lm'
	gtflags = []		
	
	#logOut('Reading counts...')
	logOut('Starting get-gt-counts...')
	with counts_file.open() as count_data:
		#logOut('Counts len is %d'%len(count_data))
		launch_srilm_cmd_for(True, count_data, 'get-gt-counts', 'out='+tmp_path+name, 'max=20', 'maxorder=%s'%order)
			
	logOut('make-gt-discounts cycle...')
	gtn_mins = [0, 1, 1, 2, 2, 2, 2, 2, 2, 2]
	gtn_maxs = [7 for i in range(10)]
	for n in range(1, order+1):
		logOut('n=%d'%n)
		name_gtn = tmp_path+'%s.gt%d'%(name, n)
		gtflags.extend(('-gt%d'%n, name_gtn))
		launch_srilm_cmd_for(True, None, 'make-gt-discounts', 'min=%d'%gtn_mins[n], 'max=%d'%gtn_maxs[n], name_gtn+'counts', '>', name_gtn)

	#contexts = '%s.contexts'%name
	# merge gathered statistics with data collected from src_filename
	#create_srilm_ng_counts('-', True, count_data, '-text', src_filename, '-write', contexts, '-read-with-mincounts', '-trust-totals', '-meta-tag __meta__', *gtflags)

	logOut('Starting ngram-count...')
	with open(counts_file) as count_data:
		create_srilm_lm('-', True, count_data, '-vocab', vocab_file, '-read-with-mincounts', '-lm', model_file, '-meta-tag', '__meta__', *gtflags)

def find_source_files(src_path, file_mask):
	logOut('Searching for source files %s in [%s]:'%(file_mask, src_path))
	src_list = FilePathName(src_path).search(file_mask)
	logOut('Sources found: %d'%len(src_list))
	logDbg('src_list: '+str (src_list))
	return [fname for fname in src_list if not fname.isdir()]

def create_split_ng_counts(ngram_N, src_path, file_mask):
	src_list = find_source_files(src_path, file_mask)	
	logOut('Starting ngram-count for sources...')

	#src_queue = Queue()
	thread_list = []
	count_list = []
	input_text=''
	for fname in src_list:
	#	src_queue.put(fname)
		for i, line in enumerate(xcat(fname)):
			if i%int (1e6) == 0:
				logOut('%d lines read'%i)

			input_text += line#'\n'.join(f.readlines(1e4))
			#input_text += f.read(int (1e8))
			if 3e8<len(input_text):
				logOut('Block read. starting counts calculation...')
				th_launch_ngram_count(count_list, thread_list, input_text)
				input_text = ''

		th_launch_ngram_count(count_list, thread_list, input_text)
	
	logOut("Waiting for ngram-count's finish...")
	[th.join() for th in thread_list]
	
	#thread_dict = {}
	#thread_limit = 30
	#ProcMgmt.thPoolProcess(4, thrd_srilm_ng_counts_collector, (src_queue))

	#count_list = [get_counts_filename_for(fname) for fname in src_list]
	return count_list


def create_lm_multicounts(ngram_N, src_path, file_mask, dst_path, vocab_file, tmp_path):
	src_path = FilePathName(src_path)
	dst_path = FilePathName(dst_path)
	count_list = create_split_ng_counts(ngram_N, src_path, file_mask)
	logOut('Starting ngram-merge for [%s]...'%' '.join(count_list))
	ng_counts_merge(count_list)
	#ng_counts_merge_parallel(count_list)
	
	#make_big_lm(ngram_N, src_path+DEFAULT_COUNTS_FILE,  dst_path+'py_lang.model', vocab_file, tmp_path)
	
	#logOut('Starting ngram-count for sources...')
#ng_count(True, input_text, '-vocab', vocab_file, '-text', '-', '-lm', dst_path+DEFAULT_MODEL_FILE)

	with open(counts_file) as count_data:
		create_srilm_lm('-', True, count_data, '-vocab', vocab_file, '-read-with-mincounts', '-lm', model_file, '-meta-tag', '__meta__', *gtflags)


def create_lm_1_op(ngram_N, src_path, file_mask, dst_path, vocab_file):
	src_list = find_source_files(src_path, file_mask)	
	ngc_proc = ng_count(False, None, '-vocab', vocab_file, '-text', '-', '-write', dst_path+DEFAULT_COUNTS_FILE, '-lm', dst_path+DEFAULT_MODEL_FILE)
	
	i = 0
	input_text = ''
	logOut("Reading sources piped to ngram-count's stdin...")
	for fname in src_list:
		for line in xcat(fname):
			if i%int (1e5) == 0:
				logOut('%g lines read'%i)

			#line = line.decode('utf8').lower().encode('utf8')
			#print line
			#input_text += line#'\n'.join(f.readlines(1e4))
			ngc_proc.stdin.write(line+'\n')			
			i += 1
	
	logOut("Closing stdin...")
	ngc_proc.stdin.close()
	logOut("Waiting for  ngram-count finish...")
	ngc_proc.wait()


def create_ngram_stats(order, src_path, file_mask, dst_path, tmp_path, prev_stats=None):
	'create_ngram_stats arguments: order, src_path, file_mask, dst_path, tmp_path, prev_stats'

	def create_new_ng_count_process():
		s_counts_file_idx = str(len(ngc_stats_proc_lst))
		counts_fname = tmp_path+(DEFAULT_COUNTS_FILE+'_'+s_counts_file_idx)
		ngc_args = [False, None, '-order', str(order), '-text', '-', '-sort', '-write', counts_fname.to_fs()]
		if prev_stats:
			ngc_args.extend(('-read', str(prev_stats)))

		ngc_stats_proc = ng_count(*ngc_args)
		ngc_stats_proc_lst.append(ngc_stats_proc)
		return ngc_stats_proc, counts_fname

	tmp_path = FilePathName(tmp_path)
	dst_path = FilePathName(dst_path)
	src_list = find_source_files(src_path, file_mask)	
	ngc_stats_proc_lst = []
	count_files = []
	
	
	i = 0
	input_text = ''
	logOut("Reading sources piped to ngram-count for statistics...")
	ngc_stats_proc = None
	BLOCK_SIZE = 1e8
	cur_block_len = BLOCK_SIZE+1

	input_len = 0
	for fname in src_list:
		for line in fname.xcat():
			if i%int (1e6) == 0:
				logOut('%g lines read'%i)

			#line = line.decode('utf8').lower().encode('utf8')
			#print line
			if BLOCK_SIZE < cur_block_len:
				logDbg('Block of %g bytes read. Starting new ngram-count process...'%cur_block_len)
				if ngc_stats_proc:
					ngc_stats_proc.stdin.close()

				cur_block_len = 0
				ngc_stats_proc, counts_fname = create_new_ng_count_process()
				count_files.append(counts_fname)

			cur_block_len += len(line)
			ngc_stats_proc.stdin.write(line+'\n')
			i += 1
	
	logDbg("Closing last stdin...")
	if ngc_stats_proc:
		ngc_stats_proc.stdin.close()
	
	logOut("Source reading finished. Waiting for ngram-counts finish...")
	[proc.wait() for proc in ngc_stats_proc_lst]
	
	if 1<len(count_files):
		logOut("Merging statistics...")
		ng_counts_merge(count_files, dst_path+DEFAULT_COUNTS_FILE)
	else:
		count_files[0].move_to(dst_path+DEFAULT_COUNTS_FILE)

	logOut("Finished")


def create_lm_mixed(ngram_N, src_path, file_mask, dst_path, vocab_file):
	src_list = find_source_files(src_path, file_mask)	
	ngc_stats_proc = ng_count(False, None, '-text', '-', '-write', dst_path+DEFAULT_COUNTS_FILE)
	#ngc_lm_proc = ng_count(False, None, '-vocab', vocab_file, '-text', '-', '-lm', dst_path+DEFAULT_MODEL_FILE)
	
	i = 0
	input_text = ''
	logOut("Reading sources piped to LM & stats ngram-counts' stdins...")
	
	cur_block_len = 0
	BLOCK_SIZE = 3e8
	for fname in src_list:
		for line in xcat(fname):
			if i%int (1e5) == 0:
				logOut('%g lines read'%i)

			#line = line.decode('utf8').lower().encode('utf8')
			#print line
			if BLOCK_SIZE < cur_block_len:
				logOut('Block of %g bytes read. Starting new ngram-count process...'%cur_block_len)
				cur_block_len = 0

			#input_text += line#'\n'.join(f.readlines(1e4))
			cur_block_len += len(line)
			ngc_stats_proc.stdin.write(line+'\n')
			ngc_lm_proc.stdin.write(line+'\n')
			i += 1
	
	logOut("Closing stdins...")
	ngc_stats_proc.stdin.close()
	ngc_lm_proc.stdin.close()
	logOut("Waiting for stats ngram-counts finish...")
	ngc_stats_proc.wait()
	logOut("Waiting for LM ngram-counts finish...")
	ngc_lm_proc.wait()
	logOut("Finished")


def create_lm_process(afWait, order, counts_path, model_path, vocab_file='', *smooth_args):
	'create_lm_process arguments: order, counts_path, model_path, vocab_file='', *smooth_args'

	counts_path = FilePathName(counts_path)
	model_path = FilePathName(model_path)

	logOut("Making LM for built stats...")
	#make_big_lm(order, dst_path+DEFAULT_COUNTS_FILE, dst_path+DEFAULT_MODEL_FILE, vocab_file, tmp_path)
	args = ['-order', str(order), '-read', counts_path, '-lm', model_path]
	if vocab_file!='':
		args.extend(('-limit-vocab', '-vocab', str(vocab_file)))

	args.extend(smooth_args)
	return ng_count(afWait, None, *args)


def create_lm(order, src_path, dst_path, vocab_file='', *smooth_args):
	'create_lm arguments: order, src_path, dst_path, vocab_file=None, *smooth_args'

	create_lm_process(True, order, src_path+DEFAULT_COUNTS_FILE, dst_path+DEFAULT_MODEL_FILE, vocab_file, *smooth_args)
	logOut("Finished")


def create_full_lm(order, src_path, file_mask, dst_path, tmp_path, vocab_file='', *smooth_args):
	"create_full_lm arguments: order, src_path, file_mask, dst_path, tmp_path, vocab_file='', *smooth_args"

	create_ngram_stats(order, src_path, file_mask, dst_path, tmp_path)
	create_lm(order, dst_path, dst_path, vocab_file, smooth_args)


def recode_utf_lm_cp1251(model_path):
	'recode_utf_lm_cp1251 model_path'

	model_path = FilePathName(model_path)
	src_filename = model_path+DEFAULT_MODEL_FILE
	dst_enc = 'cp1251'
	dst_filename = model_path+(DEFAULT_MODEL_FILE+'.'+dst_enc)
	src_filename.encode_convert_to('utf8', dst_enc, dst_filename)


def create_mix_lms(order, file_mask, *src_paths):#, vocab_file=None
	'create_mix_lms arguments: order, file_mask, *src_paths' 

	logDbg('Collecting ngram counts')
	for i, path in enumerate(src_paths):
		src_path = FilePathName(path)
		logOut('Collecting ngram counts for path #%d/%d [%s]'%(i, len(src_paths), src_path))
		if not (src_path+DEFAULT_COUNTS_FILE).exists:
			create_ngram_stats(order, src_path, file_mask, src_path, src_path)

	logDbg('Creating mixed models')
	for i in range(1, len(src_paths)+1):
		for paths in it.combinations(src_paths, i):
#		model_name = '%s.lm'%'_'.join(paths)
			model_name = FilePathName('_'.join(paths)+'.lm')

			logOut('Creating mixed model %s'%model_name)
			if not model_name.exists():
				clmp = create_lm_process(False, order, '-', model_name)
				for src_path in paths:
					clmp.stdin.write((FilePathName(src_path)+DEFAULT_COUNTS_FILE).cat())

				clmp.stdin.close()
#			create_lm(order, src_path, dst_path, vocab_file='', *smooth_args)

	logOut('create_mix_lms finished')


@pu.threadFunctionLocker
def save_results(model_name, res_match, res_table):
	res_table.write('%s;%s;%s;%s;\n'%(model_name, res_match.group(1), res_match.group(2), res_match.group(3)))
	res_table.flush()

@pu.functionThreader
def model_processor(order, test_text_path, paths, res_table):
	model_name = FilePathName('_'.join(paths)+'.lm')

	if not model_name.exists():
		logOut('Creating mixed model %s'%model_name)
		clmp = create_lm_process(False, order, '-', model_name)
		for src_path in paths:
			clmp.stdin.write((FilePathName(src_path)+DEFAULT_COUNTS_FILE).cat())

		clmp.stdin.close()
		clmp.wait()
	else:
		logOut("Model %s already exists"%model_name)

	with contextlib.closing(io.StringIO()) as res_out:
#		if res_file_path.exists():
#			logOut("Perplexity for %s already exists"%model_path)
#			return

#		with (str(model_name.basename())+'_%s.ppl'%test_text_path.basename()).open('w') as res_out:
		ppl(test_text_path, model_name, res_out)
		ppl_report = res_out.getvalue()
		res_match = re.search(r'(\d+) OOVs.+ppl= (\S+) ppl1= (\S+)', ppl_report, re.S)
		if res_match:
#				pdb.set_trace()
			save_results(model_name, res_match, res_table)
		else:
			logOut('Regex search failed. ngram output: %s'%ppl_report, ERROR)

def create_mix_lms_ppl(order, file_mask, test_text_path, *src_paths):#, vocab_file=None
	'create_mix_lms_ppl arguments: order, file_mask, *src_paths'

	test_text_path = FilePathName(test_text_path)

	logDbg('Collecting ngram counts')
	for i, path in enumerate(src_paths):
		src_path = FilePathName(path)
		logOut('Collecting ngram counts for path #%d/%d [%s]'%(i, len(src_paths)-1, src_path))
		if not (src_path+DEFAULT_COUNTS_FILE).exists:
			create_ngram_stats(order, src_path, file_mask, src_path, src_path)

	logDbg('Creating mixed models')
	with FilePathName(str(test_text_path.dirname())+'_'.join(src_paths)+'.csv').open('w') as res_table:
		res_table.write('%s\nModel;OOV;PPL;PPL excluding end-of-sentence tags;\n'%test_text_path)

		threads = []
		i_range = list(range(1, len(src_paths)+1))
		n = len(src_paths)
		total_combs = sum([math.factorial(n) / math.factorial(r) / math.factorial(n-r) for r in i_range])
		j = 0
		for i in i_range:
			for paths in it.combinations(src_paths, i):
				j += 1
				logOut('Processing %d/%d combination'%(j, total_combs))
				while 4<len(threads):
					if not threads[0].is_alive():
						threads[0].join()
						del threads[0]

					time.sleep(0.01)

				threads.append(model_processor(order, test_text_path, paths, res_table))

		logOut('waiting for worker threads finish...')
		for i, t in enumerate(threads):
			t.join()
			logOut('%d threads joined'%i)

	logOut('create_mix_lms finished')


def ppl(test_text_path, model_path, res_out, *add_args):
	'ppl: test_text_path, model_path, res_out, *add_args'

	test_text_path = FilePathName(test_text_path)
	model_path = FilePathName(model_path)

	logOut("Calculating perplexity for %s..."%model_path)
	logDbg("Test file: %s"%test_text_path)
	#make_big_lm(order, dst_path+DEFAULT_COUNTS_FILE, dst_path+DEFAULT_MODEL_FILE, vocab_file, tmp_path)
	args = ['-ppl', test_text_path, '-lm', model_path]
	args.extend(add_args)

	cmd = ShellCmd(NGRAM_CMD_TMPL)
	cmd.extend_args(*args)
	cmd.launch(True, stdout=res_out)

	return res_out


def lab_folder_ppl(folder_path, model_path, temp_file):
	import markup_utils

	model_path = FilePathName(model_path)
	folder_path = FilePathName(folder_path)
	temp_file = FilePathName(temp_file)
	
	if not model_path.exists():
		logOut('%s language model does not exist!'%model_path, ERROR)
		return 

	text_filename = temp_file#FilePathName(os.tmpnam())
	with text_filename.open('w') as text:
		for src_file in folder_path.search('.+'+markup_utils.LAB_EXT):
#			pdb.set_trace()
			txt = markup_utils.getLabTextOnly(src_file).replace('\r', '').lower().encode('utf8')
			text.write(txt+'\n')

	with contextlib.closing(io.StringIO()) as res_out:
#		if res_file_path.exists():
#			logOut("Perplexity for %s already exists"%model_path)
#			return

#		with (str(model_name.basename())+'_%s.ppl'%test_text_path.basename()).open('w') as res_out:
		ppl(text_filename, model_path, res_out)#, '-tolower'
		ppl_report = res_out.getvalue()
		res_match = re.search(r'(\d+) OOVs.+ppl= (\S+) ppl1= (\S+)', ppl_report, re.S)
		if res_match:
			pass
#			save_results(model_name, res_match, res_table)
		else:
			logOut('Regex search failed!', ERROR)

	logOut('PPL output: %s'%ppl_report, ERROR)

NGRAM_CMD_TMPL = get_srilm_cmd_for('ngram')
NG_COUNT_CMD_TMPL = get_srilm_cmd_for('ngram-count')
CREATE_STAT_CMD_TMPL = ShellCmd(NG_COUNT_CMD_TMPL)
CREATE_STAT_CMD_TMPL.append_arg('-sort')
COUNTS_EXT = '.counts'

cfgConsoleLoggerParams(FILE_UTILS_LOGGER)

if 1<len(sys.argv):
	function = sys.argv[1]
#	configureRotatingFileLogger(DEFAULT_LOG_FILENAME+'_'+function, 10, astrLogFolder=SCRIPT_PATH+dfltLOG_SUBFOLDER)#).to_fs()
	configureFileLogger(DEFAULT_LOG_FILENAME+'_'+function, astrLogFolder=SCRIPT_PATH+dfltLOG_SUBFOLDER)#).to_fs()
else:
	configureDefaultLogger() 


if __name__ == "__main__":
	try:
		eval(getTxtArgsCmd())
		logOut('All tasks finished')
#		eval(getArgsCmd())
	except Exception as ex:
#	except TypeError:
		func = eval(sys.argv[1])
		logExc('Usage: %s'%func.__doc__)

# create_ngram_stats
# create_lm
# create_full_lm
