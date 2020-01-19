#!/usr/bin/python
# -*- coding: UTF-8 -*-

from multiprocessing.dummy import Process, Pool, Queue, Lock, Manager
import urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse, re, shelve, random, time, datetime, zlib, bz2#, sys, string
from contextlib import closing

from loggers import * 
#from ProcMgmt import * 

minute = 60
#hour = 60*minute
#year = datetime.timedelta(days=365)

#random.seed()

HTTP_LOGGER = 'HTTP'

USER_AGENTS = ['Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.19 Safari/534.13', 
							 'User-Agent: Mozilla/5.0 (X11; U; Linux i686; ru; rv:1.9b5) Gecko/2008050509 Firefox/3.0b5',
							 'Opera/9.80 (Windows NT 5.1; U; ru) Presto/2.6.30 Version/10.60', 
							 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)'] 

PROXY_LIST = None
#with open(SCRIPT_FOLDER+'proxies') as p:
#	PROXY_LIST = [line.strip('\n') for line in p.readlines()]

TOR_PROXY = {'http': '127.0.0.1:8123'}
#TOR_PROXY = {'socks': '127.0.0.1:9050'}

secHTTP_WAIT_TIMEOUT = 10
db = None

strRAW_PAGE = 'Raw page'


def reset_proxy_list(db):
	db[strPROXY_KEY] = []
	#db[strPROXY_KEY] = PROXY_LIST # list(set(PROXY_LIST).union(db[strPROXY_KEY]))
	for record in db[strACCOUNTS_KEY]:
		db[strPROXY_KEY].append(record[strPROXY_KEY]) 


import pdb
def get_page_with_cookies(url, post_params = None, opener = None, proxies = None, user_agent = None, timeout = secHTTP_WAIT_TIMEOUT):

	logDbg('Proxies: [%s]'%proxies)	
	url_handlers = []
	if not opener:		
		url_handlers = [urllib.request.HTTPCookieProcessor(), ]
#if proxies=='':
#			proxies = 

	if proxies:
#			url_handlers.append(urllib2.ProxyHandler({'http': 'http://'+proxy})) - previous version
		url_handlers.append(urllib.request.ProxyHandler(proxies)) # Переделал для большей универсальности (SOCKS и др.)
#else:
#	url_handlers.append (urllib2.ProxyHandler({'http': 'http://'}))

		opener = urllib.request.build_opener(*url_handlers)
			
		if not user_agent:			
			user_agent = random.choice(USER_AGENTS)

		opener.addheaders = [('User-agent', user_agent)]
	
	if post_params:
		post_params = urlencode(post_params)
		logOut('Post params: %s'%post_params, logger_name = HTTP_LOGGER)
		
	logOut('Downloading [%s]...'%url)
	#logOut('Timeout: %d...'%timeout)
#with opener.open(url, post_params, timeout) as f:	lines = f.readlines()
#	pdb.set_trace()
	with closing(opener.open(url, post_params, timeout)) as f:
		lines = f.readlines()
#	f.close()

	
	return opener, ''.join(lines)
	

def get_page(url, post_params = None, opener = None, proxies = None, user_agent = None, timeout = secHTTP_WAIT_TIMEOUT):
	return get_page_with_cookies(url, post_params, opener, proxies, user_agent, timeout)[1]

def post_params_to_str(post_params):
	if post_params:
		param_list = [key+'='+value for key, value in post_params.items()]
		return '?'+'&'.join(param_list)
	else:
		return ''

def get_request_db_key(url, post_params):
	return url+post_params_to_str(post_params)

class PageShelveCacher:
	'Base class for objects working with shelve db'
	
	def __init__(self, db_file_path='http_lib_cache.db'):
		self.compress_type = strRAW_PAGE
		self.db = shelve.open(str(db_file_path), writeback=True)
		
		self.db_lock = Lock()
		self.rollback()
		self.page_root_node = self.db

	def __del__(self):
		self.db.close()
	
	def reset_db(self):
		self.db = {}
	
#	def set_page_root(self, root_node):
#		self.page_root_node = root_node

	def start_transaction(self):
		self.rollback()
		self.transact_data = {}
#		self.page_root_node = self.transact_data

	def commit(self):
		if not self.transact_data:
			return

		self.page_root_node.update(self.transact_data)
		self.rollback()
		self.sync()

	def rollback(self):
		self.transact_data = None

	def sync(self):
		self.db.sync()
	

	def get_save_root_node(self):
		if self.transact_data:
			return self.transact_data

		return self.page_root_node


	def save_db_page(self, url, post_params, page):
		self.db_lock.acquire()
#		logOut('db_lock.acquire')
		str_params = post_params_to_str(post_params)
		
		key = get_request_db_key(url, post_params)
		page_root_node = self.get_save_root_node()
		page_root_node[key] = {self.compress_type: page}
#		logOut('db_lock.release')
		self.db_lock.release()
		

	def load_db_page(self, url, post_params=None):
		page = None
#		self.db_lock.acquire()
		key = get_request_db_key(url, post_params)
		try:
			page_node = self.page_root_node.get(key, None)
		except:
			page_node = None

		if page_node:
			page = page_node[self.compress_type]

#		self.db_lock.release()
	
		return page


#strZLIB_COMPRESSED_PAGE = 'zlib_page'
strBZ2_COMPRESSED_PAGE = 'bz2_page'
#strGZ_COMPRESSED_PAGE = 'gz_page'
class PageCompressedCacher(PageShelveCacher):
	'Web page base cacher class with compression support'
	
	def save_db_page(self, url, post_params, page):
		data = self.compress(page)
		PageShelveCacher.save_db_page(self, url, post_params, data)

	def load_db_page(self, url, post_params=None):
		res = None
		data = PageShelveCacher.load_db_page(self, url, post_params)
		if data:
			res = self.decompress(data)

		return res

class ZLib_Cacher(PageCompressedCacher):
	def __init__(self, db_file_path='zlib_cache.db'):
		PageCompressedCacher.__init__(self, db_file_path)
		self.compress_type = strZLIB_COMPRESSED_PAGE
	
	def compress(self, text):
		return zlib.compress(text, 9)

	def decompress(self, data):
		return zlib.decompress(data)


class BZ2_Cacher(PageCompressedCacher):
	def __init__(self, db_file_path='bz2_cache.db'):
		PageCompressedCacher.__init__(self, db_file_path)
		self.compress_type = strBZ2_COMPRESSED_PAGE
	
	def compress(self, text):
		return bz2.compress(text)

	def decompress(self, data):
		return bz2.decompress(data)


class URL_Fetcher(BZ2_Cacher):
	'Web page fetcher with cache db'
	
	def __init__(self, db_name, fUseCache=True, fUseCookies=False, proxies=None, user_agent=None, timeout=secHTTP_WAIT_TIMEOUT):
		self.fUseCache = fUseCache
		self.fUseCookies = fUseCookies
		self.proxies = proxies
		self.user_agent = user_agent
		self.timeout = timeout
		
		self.build_opener()
		BZ2_Cacher.__init__(self, db_name)


	def build_opener(self):
			url_handlers = [urllib.request.HTTPCookieProcessor(), ]
			if self.proxies:
				url_handlers.append(urllib.request.ProxyHandler(self.proxies))

			self.opener = urllib.request.build_opener(*url_handlers)
				
			if not self.user_agent:			
				self.user_agent = random.choice(USER_AGENTS)

			self.opener.addheaders = [('User-agent', self.user_agent)]


	def get_page(self, url, post_params = None, fUseCookies=None, fUseCache=None, timeout=None):
		fUseCache = self.fUseCache if fUseCache==None else fUseCache
		timeout = self.timeout if timeout==None else timeout
		page = None
		if fUseCache:
			page = self.load_db_page(url, post_params)
#			page = self.get_url_from_cache(url, post_params)

		if not self.fUseCookies:	
			self.build_opener()
		
		if not page:
			try: # , timeout=10			
				page = get_page(url, post_params, self.opener, self.proxies, timeout = timeout)
			except urllib.error.URLError:
				logErr('while fetching [%s]: %s'%(url, traceback.format_exc(0)))
			except Exception as ex:
				logExc('while fetching %s'%url)
#				raise ex

			if page:
				try:
					self.save_db_page(url, post_params, page)
					self.sync()
				except Exception as ex:
					logErr('Page download failed. Trying to sync DB...')
					self.sync()
					raise ex
		else:	
			logDbg('[%s] fetched from cache'%url)

		return page


	def get_url_from_cache(self, url, post_params = None):
		data = self.load_db_page(url, post_params)
		if not data:
			try: # , timeout=10			
				data = self.get_page(url, post_params, fUseCache=False)
			except urllib.error.URLError:
				logErr('while fetching [%s]: %s'%(url, traceback.format_exc(0)))
			except Exception as ex:
				logExc('while fetching %s'%url)
#				raise ex
			
		return data



class ParallelDownloader(URL_Fetcher):
	'Parallel threaded web page downloader'
	
	def __init__(self, db_name, proc_count, site_base_url, fUseCache=True, 
							fCacheSearchPages=True, fUseCookies=False, 
							timeout=secHTTP_WAIT_TIMEOUT, search_proc_count=2, proxies=None):

		self.proxies = proxies
		self.queue = Queue()
		self.fSaveSearchPages = fCacheSearchPages
		self.site_base_url = site_base_url
		self.pool = Pool(processes=proc_count)

		self.search_queue = Queue()
		self.url_extract_pool = Pool(processes=search_proc_count)

		URL_Fetcher.__init__(self, db_name, fUseCache, fUseCookies, timeout=timeout, proxies=proxies)


	def process_urls_from_search_queue(self):
		while not self.search_queue.empty():
			search_page_url = self.search_queue.get()
#			logOut('search pages queue size: %d'%self.search_queue.qsize())
			logDbg('search page: %s'%search_page_url)

			search_page = self.get_page(search_page_url, fUseCache=self.fSaveSearchPages)
			rel_urls = extract_data_xpath(search_page, self.url_extract_xpath)
			#rel_urls = self.extract_page_xpath(self.url_extract_xpath, search_page_url)
#			logOut('URLs from %s extracted'%search_page_url)
			
			logOut('%d urls extracted from [%s]. Queuing...'%(len(rel_urls), search_page_url))
			logDbg('Extracted urls: %s. Queuing to download...'%rel_urls)
			list(map(self.queue.put, self.prefix_site_base_url(rel_urls)))

		self.queue.put(None)
		self.postprocess_search_page_list(rel_urls, search_page)
	
	def queue_pages(self, url_list):
		list(map(self.queue.put, url_list))

		# признак завершения очереди заданий
		self.queue.put(None)

	def postprocess_search_page_list(self, url, page): pass

	def prefix_site_base_url(self, rel_urls):
		return [self.site_base_url+url for url in rel_urls]

	def process_pages(self, page_processor, *add_processor_args):
		self.page_processor = page_processor
		self.add_pprocessor_args = add_processor_args
		self.pool.apply(self.process_page)
	

	def process_page(self):
		while True:
			url = self.queue.get()
			logDbg('Url got from queue: %s'%url)
			if not url:
				break
			
			page = self.get_page(url)#, proxies=self.proxies

			#logOut('pp_arg_list: [%s]'%pp_arg_list)
			if page:
				self.page_processor(url, page, *self.add_pprocessor_args)


def show_page_in_chromium(page):
	page_filename = os.tmpfile()#'page.html'
	with open(page_filename, 'w') as f: f.write(page)
#os.system ('chromium-browser '+page_filename)
	open_in_chromium(page_filename)

def open_in_chromium(url):
	os.system('chromium-browser "%s"'%url)


def urlencode(params):
	return urllib.parse.urlencode(params)

def append_page_data(page, filename):
	with open(filename, 'a') as f: f.write(page)

def show_ext_ip(proxy=TOR_PROXY):
	f_success = False
	
	main_page = 'http://2ip.r'
#	wait_for_service_availability(main_page)
		
	match = None
	while not match:
		#logOut ('')
		url = random.choice((main_page, 'http://prime-speed.ru/ip.php'))
	
		try: 
			response = get_page(url, None, None,  proxies)		
			match = re.search('(?:\d{1,3}\.){3}\d{1,3}', response)
		except Exception as ex:
			logOut ('Connection error: [%s]'%ex, logger_name = HTTP_LOGGER)
			
		
	ip = match.group()
	logOut ('IP: %s'%ip, logger_name = HTTP_LOGGER)
	
	return ip


def wait_for_service_availability(main_page):
	f_success = False
	wait_time = 5*minute
	
	# Ожидание, пока заработает сайт
	while not f_success:
		try:
			get_page(main_page)
			f_success = True
		except Exception as error:
			logOut ('Error: %s. Waiting %ss for next try...'%(error, wait_time), logger_name = HTTP_LOGGER)
			time.sleep(wait_time)


def configure_tor():
	success = False
	while not success:
		try:
			res = config_tor(n_curcuits = 1, 
												n_hops_in_circuit = 2, 
												exit_country = 'R',
												n_continent_crossings = 0, 
												n_ocean_crossings = 0)
			success = True
		except:
			pass
	
	return res


def ip_test():
	configureRotatingFileLogger('ip_test', 3)
	tor_ctl = configure_tor()
	for i in range (10):
		show_ext_ip()
#		configure_tor()
		tor_ctl.send_signal("NEWNYM")
#		tor_ctl.send_signal(0x03)



def save_all_data(url, data, folder):
	file_name = re.search('.+[/?&](.+)$', url).group(1)
#	basename, ext = os.path.splitext(os.path.basename(file_name))
#	type = basename[-1] # тип - последняя буква в имени (перед точкой)

	try:
		os.makedirs(folder)
	except:
		pass

	logOut('Saving file %s'%file_name)
	with (folder+file_name).open('wb') as f: f.write(data)


class PageWatcher(PageShelveCacher):
	'Abstract base class for page watchers. Do not use without subclassing'

	def __init__(self, url):
		self.url = url
		PageShelveCacher.__init__(self, strDB_FILENAME)
		logOut('DB has %d first-level records'%len(self.db))

	def work(self, test_interval=60):
		#wait_for_service_availability(page_addr)
		keys = list(self.db.keys())
		if len(keys):
			prev_page = self.db[keys[-1]][strWATCHER_PAGE_KEY]
		else:
			prev_page = None

		while True:
			page = None
			try:
				page = get_page(self.url)
			except:
				logExc('Page load failed!')

			if page and page != prev_page:
				logOut('Page change detected. Saving new data...')
				self.save_page(page)
				self.save_page_data(page)
				prev_page = page
				self.sync()

			time.sleep(test_interval)

	def save_page(self, page):
		now = str(datetime.datetime.now())
		self.db[now] = {strWATCHER_PAGE_KEY: page}
	
	def reset_db_page_data(self):
		for i, rec in enumerate(self.db):
			self.db[i] = {strWATCHER_PAGE_KEY: rec[strWATCHER_PAGE_KEY]}
		
	def reset_db(self):
		self.db.clear()


strDB_FILENAME = 'page_watcher.db'
strWATCHER_PAGE_KEY = 'Page'
#strACCOUNTS_KEY = 'Accounts'
