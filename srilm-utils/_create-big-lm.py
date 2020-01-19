#!/usr/bin/python

from multiprocessing.dummy import Queue

import ProcMgmt
from fileUtils import *
from srilm_utils import srilm_path

#if 1<len(sys.argv):
def get_srilm_cmd_for(cmd, *add_params):
	res_cmd = srilm_path+cmd
	res_cmd.extend_arg_list(add_params)
	return res_cmd

def launch_srilm_cmd_for(afWait, stdindata, cmd, *add_params):
	shell_cmd = get_srilm_cmd_for(cmd, *add_params)
	logOut('shell_cmd: [%s]'%shell_cmd)
	shell_cmd.launch(afWait, stdindata)

def get_counts_filename_for(src_filename):
 	if src_filename!='-':
		res = src_filename+counts_postfix 
 	else:
 		res = DEFAULT_COUNTS_FILE

	return res


def get_create_srilm_ng_counts_cmd(src_filename):
	cmd = list(CREATE_STAT_CMD_TMPL)
	cmd.extend_args('-text', src_filename, '-write', get_counts_filename_for(src_filename))
	return cmd

def create_srilm_ng_counts(src_filename, afWait=True, input_text=None, *add_args):
	cmd = ShellCmd(CREATE_STAT_CMD_TMPL)
	cmd.extend_args('-text', src_filename, '-write', get_counts_filename_for(src_filename))
	cmd.extend_arg_list(add_args)
	cmd.launch(afWait, input_text)

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

def ng_counts_merge(count_files, counts_res='ngram.count'):
	args = ['-write', counts_res]
	args.extend(count_files)

	count_merge_cmd = get_srilm_cmd_for('ngram-merge', *args)
	launch(count_merge_cmd, True)

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

def create_lm(order, counts_file):
	#get_srilm_cmd_for('', '', '', '', '', '', '')
	name = 'py_big_lm'
	contexts = '%s.contexts'%name
	
	logOut('Reading counts...')
	with open(counts_file) as count_data:
		#logOut('Counts len is %d'%len(count_data))
		logOut('Counts is %s'%count_data)
		logOut('Starting get-gt-counts...')
		launch_srilm_cmd_for(True, count_data, 'get-gt-counts', 'out=%s'%name, 'max=20', 'maxorder=%s'%order)
		
		gtflags = []
		
#	logOut('make-gt-discounts cycle...')
#	gtn_mins = [0, 1, 1, 2, 2, 2, 2, 2, 2, 2]
#	gtn_maxs = [7 for i in range(10)]
#	for n in range(1, 10):
#		logOut('n=%d'%n)
#		name_gtn = '%s.gt%d'%(name, n)
#		gtflags.extend(('-gt%d'%n, name_gtn))
#		launch_srilm_cmd_for(True, None, 'make-gt-discounts', 'min=%d'%gtn_mins[n], 'max=%d'%gtn_maxs[n], name_gtn+'counts', '>', name_gtn)

		logOut('Starting ngram-count...')
		create_srilm_ng_counts('-', True, count_data, '-write', contexts, '-read-with-mincounts', '-trust-totals', '-meta-tag __meta__', *gtflags)
#launch_srilm_cmd_for(True, None, '', '', '', '', '', '', '')

	FilePathName(contexts).remove()
	# launch_srilm_cmd_for(True, None, '', '', '', '', '', '', '')

def create_split_ng_counts(ngram_N, src_path, file_mask):
	logOut('Searching for source files %s in [%s]:'%(file_mask, src_path))
	src_list = src_path.search(file_mask)
	src_list = [fname for fname in src_list if not os.path.isdir(fname)]
	
	logOut('src_list: '+str (src_list))
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

def create_big_lm(ngram_N, src_path, file_mask):
	#count_list = create_split_ng_counts(ngram_N, src_path, file_mask)
	#logOut('Starting ngram-merge for [%s]...'%' '.join(count_list))
	#ng_counts_merge(count_list)
	#ng_counts_merge_parallel(count_list)
	
	create_lm(ngram_N, DEFAULT_COUNTS_FILE)
	logOut('All tasks finished')


ngram_N, src_path, file_mask = sys.argv[1:]
src_path = FilePathName(src_path)

NG_COUNT_CMD_TMPL = get_srilm_cmd_for('ngram-count', '-order', ngram_N)
CREATE_STAT_CMD_TMPL = ShellCmd(NG_COUNT_CMD_TMPL)
CREATE_STAT_CMD_TMPL.append_arg('-sort')
DEFAULT_COUNTS_FILE = 'ngram.count'#FilePathName()

counts_postfix = '.counts'

if __name__ == "__main__":
	configureDefaultLogger()
	#configureDefaultLogger(DEBUG)
	create_big_lm(ngram_N, src_path, file_mask)
