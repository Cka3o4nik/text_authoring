#!/usr/bin/python
# -*- coding: UTF-8 -*-

from multiprocessing.dummy import Queue

import ProcMgmt
from fileUtils import *
from srilm_utils import *

ngram_N, src_path, file_mask, dst_path, vocab_file = sys.argv[1:]#, tmp_path
ngram_N = int (ngram_N)
src_path = FilePathName(src_path)
dst_path = FilePathName(dst_path)

if __name__ == "__main__":
	configureDefaultLogger()
	#configureDefaultLogger(DEBUG)
	cfgCommonLoggerParams(FILE_UTILS_LOGGER)
	#vocab_file = src_path+'vocab.txt'

	tmp_path = os.tempnam()+'\\'
	os.makedirs(tmp_path) 

	#create_ngram_stats(ngram_N, src_path, file_mask, dst_path, tmp_path, prev_stats=None)
	create_lm(ngram_N, src_path, dst_path, vocab_file)

	logOut('Creating CP-1251 version of LM...')
	utf_model = dst_path+DEFAULT_MODEL_FILE
	cp1251_model = dst_path+(DEFAULT_MODEL_FILE+'.cp1251')
	utf_model.encode_convert_to('utf8', 'cp1251', cp1251_model)
'''
судя по разговору с игорем мне будут нужны следующие вещи:
1) Создание модели (заданного порядка)
а) слова: норм.текст -> стат + модель + бин. модель
б) фонемы: транскр. текст -> стат + модель + бин. модель
2) Адаптация модели (заданного порядка)
а) слова: стат + норм.текст -> стат + модель + бин. модель
б) фонемы: стат + транскр. текст -> стат + модель + бин. модель
3) Сглаживание модели (заданного порядка)
стат -> модель(сгл) + бин. модель (сгл)
'''
