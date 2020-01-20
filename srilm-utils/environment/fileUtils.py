# -*- coding: UTF-8 -*-

import re, sys, types, os, shutil, zipfile, subprocess, pdb
#import locale

from os_definitions import *
from contextlib import closing
from loggers import *
import procUtils as pu, itertools as it

FILE_UTILS_LOGGER = 'FILE_OP'
#-------------------------------------------------------------------

class FilePathNameModule:

  def __init__(self, astrPath=''):
    self.path = str(astrPath)
#        if hasattr(member, 'func_defaults'):
#          print "%s's defaults: %s"%(member.__name__, member.func_defaults)
#
#        if hasattr(member, 'func_dict'):
#          print "%s's func_dict: %s"%(member.__name__, member.func_dict)
#
#        if hasattr(member, 'func_closure'):
#          print "%s's func_closure: %s"%(member.__name__, member.func_closure)
#
#        if hasattr(member, 'func_globals'):
#          print "%s's func_globals: %s"%(member.__name__, member.func_globals)
    
RE_STORAGE = {}
def get_compiled_pattern(pattern, flags=0):
  pattern_RE = RE_STORAGE.get(pattern+'%d'%flags)
  if pattern_RE == None:
    pattern_RE = re.compile(pattern, flags)
    RE_STORAGE[pattern+'%d'%flags] = pattern_RE

  return pattern_RE


def re_extract(pattern, source, flags=0): 
  RE = get_compiled_pattern(pattern, flags)
  match = re.search(RE, source)
  if not match:
    return None

  return match.groups()


SEP = '/'
class FilePathNameBase:

  def __init__(self, astrPath=''):
    #print "astrPath type: %s"%type(astrPath)
    if isinstance(astrPath, self.__class__):#self.__class__ FilePathNameBase
      self.path = astrPath.path
    else:
      self.path = str(astrPath)

    

#   print 'self.path type:', type(self.path)
#   logDbg("self.path: [%r]"%self.path, logger_name = FILE_UTILS_LOGGER)
    '''
    # Если создаётся много переменных FilePathName, получается очень накладно по времени
    module = sys.modules['os.path']
    os_path_member = (getattr(module, item) for item in dir(module))
    os_path_funcs = (m for m in os_path_member if callable(m))
    for member in os_path_funcs:
      if not hasattr(self, member.__name__):
        setattr(self, member.__name__, member)
    '''
  
  def __str__(self):
    #logVar("__str__'ing path "+self.path)
    return self.to_fs()
  
  def __unicode__(self):
    #logVar("__str__'ing path "+self.path)
    return self.path
  
  def __eq__(self, other):
    return self.path == other.path
  
  def __hash__(self):
    return hash(self.path)

  #
  #def __repr__(self):
  # logVar("__repr__'ing path "+self.path)
  # return self.__str__()
  
  def get_filename(self):
    return self.path.encode(strFILENAME_ENCODING)
  
  def rename(self, dst):
    return os.rename(self.to_fs(), autoconvert_str(dst))
#  
#  def __coerce__(self, other):
#    logOut("coercing path "+self.path)
#    return (self, self.__class__(other))

  def join(self, astrOtherPath):
#   return os.path.join(self.path, autoenc(astrOtherPath))
    connector = ''
#   logVar('self: %r, arg: %r'%(self.path, autoconvert_str(astrOtherPath)), logger_name = FILE_UTILS_LOGGER)
    if len(self.path) and len(autoconvert(astrOtherPath)):
      if self.path[-1]!=SEP and astrOtherPath[0]!=SEP:
        connector = SEP

    return self.path + connector + autoenc(astrOtherPath)
#   return self.__class__(self.path + connector + autoenc(astrOtherPath))

    #return os.path.join(self.path, self.__class__(astrOtherPath))

  def __len__(self):
    return len(self.path)

  def __add__(self, astrOtherPath):
    #astrOtherPath = self.__class__(astrOtherPath)
    #logVar('FilePathName::add self: %s, arg: %s'%(self.path, str(astrOtherPath)))
    path = self.join(astrOtherPath)
    return self.__class__(path)
    #return path
  
  def __radd__(self, astrOtherPath):
    #logVar('FilePathName::radd self: %s, arg: %s'%(self.path, astrOtherPath))
    #return astrOtherPath+self.path
    return self.__class__(astrOtherPath+self.path)
  
  def __iadd__(self, astrOtherPath):
    #logVar('FilePathName::radd self: %s, arg: %s'%(self.path, astrOtherPath))
    self.path = self.join(astrOtherPath)
    return self
  
#  def replace(self, *args):
#    return self.path(*args)

  def __mod__(self, strSubst):
    return self.__class__(self.path%strSubst)

  def __iter__(self):
    return iter(self.path)#.__iter__()

  def __getitem__(self, key):
    return self.path[key]

#  def __getslice__(self, i, j):
#    return self.path[i:j]

  def dirname(self):
    return self.__class__(os.path.dirname(self.path))

  def basename(self):
    return self.__class__(os.path.basename(self.path))

  def splitext(self):
    return os.path.splitext(self.path)

  def isdir(self):
    return os.path.isdir(self.path)

  def exists(self):
    return os.path.exists(self.path)

  def listdir(self):
    if not self.isdir():
      return []
    
    return os.listdir(self.path)
  
  def makedirs(self):
    try:
      os.makedirs(self.path)
    except:
      pass#logExc()
  
  def copy_to(self, astrPath):
    #logDbg(u'copy_to src path: %s'%self.path, logger_name=FILE_UTILS_LOGGER)
    #logDbg(u'copy_to dst path: %s'%astrPath, logger_name=FILE_UTILS_LOGGER)
    if self.isdir(): 
#     shutil.copytree(self.path, autoconvert_u(astrPath))
      CopyFolder(self.path, astrPath)
    else:
#     shutil.copy(self.path, autoconvert_fs(astrPath))
      shutil.copy(self.to_fs(), autoconvert_fs(astrPath))
    #shutil.copy(self.path, astrPath)

  def move_to(self, astrPath):
    #logDbg(u'move_to dst path: %s'%astrPath, logger_name=FILE_UTILS_LOGGER)
    shutil.move(self.path, autoconvert_fs(astrPath))

  def unzip_to(self, astrPath):
    return unzip(self.path, autoconvert_fs(astrPath))

  def launch(self, afWait=True, stdindata=None):
#    if re.match(astrExcludePattern, path)==None:
    return launch(self.path, afWait, stdindata) 

  def xcat(self):
    return xcat(self.to_fs()) 

  def cat(self, mode='r'):
    return cat(self.to_fs(), mode) 

  def getmtime(self):
    return os.path.getmtime(self.path)

  def getctime(self):
    return os.path.getctime(self.path)

  def open(self, astrMode='r'):
    return open(self.path, astrMode) 

  def write(self, text, astrMode='w'):
    with self.open(astrMode) as fout:
      fout.write(text)

  def encode_convert_to(self, astrSrcEncode, astrDstEncode, dstFilename):
    with dstFilename.open('w') as dst_file:
      for line in self.xcat():
        dst_file.write(line.decode(astrSrcEncode).encode(astrDstEncode).rstrip('\r'))

#  def copy_to(self, astrPath):
#    shutil.copyfile(self.path, str(astrPath)) # 

  def match_pattern(self, pattern, flags=0):
    #logVar(path, 'match_pattern path: ')
    return re_extract(pattern, self.path, flags)!=None


  def find_all(self):
    raw_list = os.walk(self.path)
    #logVar(raw_list, 'raw_list: ', logger_name=FILE_UTILS_LOGGER)

    res = []
    for dirpath, dn, fnames in raw_list:
      #logVar(dirpath, 'dirpath: ', logger_name=FILE_UTILS_LOGGER)
      #logVar(fnames, 'fnames: ')

      dp = self.__class__(dirpath)
      for fn in fnames:
        res.append(self.__class__(dp+fn))

#   logDbg('Unfiltered file list: %s'%tmp_lst, logger_name=FILE_UTILS_LOGGER)
    return res 


  def filter_raw_file_list(self, raw_list, pattern, flags=0):
    pattern_RE = get_compiled_pattern(pattern, flags)
#   match_pattern = lambda patt, path: self.match_pattern(patt, path, flags)

    res = [self.__class__(path) for path in raw_list if re.search(pattern_RE, str(path))]
    #res = [self.__class__(path) for path in raw_list if re.search(pattern_RE, path)]
    return res


  def search(self, pattern, flags=0):
    logOut('Searching for "%s" in path [%s]...'%(pattern, self.path))
    raw_list = self.find_all()
    #logVar(raw_list, 'raw_list: ', logger_name=FILE_UTILS_LOGGER)

#   match_pattern = lambda patt, path: self.match_pattern(patt, path, flags)
    res = self.filter_raw_file_list(raw_list, pattern, flags)

    logOut('Files found: %d'%len(res))
    return res


  def recurrent_search(self, astrPattern):
    res_list = []
    children = self.listdir()
    for node in children:
      path = self+node
      res_list.extend(path.search(astrPattern))
    
    if self.match_pattern(astrPattern, self.path):
      res_list.append(self.path)

    return res_list


  def clear(self, astrExcludePattern):
    children = self.listdir()
    for node in children:
      path = self+node
      path.clear(astrExcludePattern)
    
    if not self.match_pattern(astrExcludePattern, self.path):
      self.remove()

  def replace(self, src, repl):
    return self.__class__(self.path.replace(src, repl))

  def encode(self, encoding):
    return self.path.encode(encoding)

  def remove(self):
#    if re.match(astrExcludePattern, path)==None:
    #logDbg(u'Path to remove: %s'%self)
    if self.isdir():
      shutil.rmtree(self.path)
    else:
      os.remove(self.path)#to_fs()
#-------------------------------------------------------------------
def autoenc(astrPath):
  if isinstance(astrPath, str):
#try:
      logDbg('autoenc src string: %r'%astrPath, logger_name=FILE_UTILS_LOGGER)
      try:
        astrPath = astrPath.decode(strFILENAME_ENCODING)
      except:
        pass
#except:
#     logExcAsErr('autoenc src string: %r'%astrPath, logger_name=FILE_UTILS_LOGGER)

  return astrPath


def autoconvert(astrpath):
  return FilePathName(astrpath)
# return filepathname(astrpath).path

def autoconvert_str(astrpath):
  return str(autoconvert(astrpath))

def autoconvert_u(astrpath):
  return autoconvert(astrpath).path
# return filepathname(astrpath).path

def autoconvert_fs(astrPath):
  return autoconvert_u(astrPath)
# return autoconvert(astrPath).to_fs()
# return FilePathName(astrPath).path

def autoconvert_list(path):
  res = None
  #logDbg('autoconvert list: %r'%path, logger_name=FILE_UTILS_LOGGER)
  res = [autoconvert_fs(el) for el in path]
# try:
#   res = [autoconvert(el) for el in path]
# except:
#   logExcAsErr()

  #logDbg('autoconvert_list res: [%r]'%res, logger_name=FILE_UTILS_LOGGER)
# logOut(u'autoconvert_list res: [%s]'%', '.join(res))
  return res

class FilePathNameEnc(FilePathNameBase):

  def __init__(self, astrPath='', afDecode=True):
    if afDecode:
      astrPath = autoenc(astrPath)

    FilePathNameBase.__init__(self, astrPath)
    
  
  #def __unicode__(self):
  # logVar("unicoding path "+self.path)
  # return self.path#unicode()
  
  #def __coerce__(self, other):
  # logOut("coercing path %s to %s"%(self.path, other))
  # return (self, self.__class__(other))
  
  def to_stdout(self):
    #logVar("__str__'ing path "+self.path)
    return self.path.encode(strSTDOUT_ENC)#.encode('utf8')#str(self.path)#.encode(SYS_ENC)
  
  def to_fs(self):
    logDbg("self.path: %r"%self.path, logger_name=FILE_UTILS_LOGGER)
    res = self.path
    try:
      res = self.path.encode(strFS_ENCODING)
    except:
      pass
      
    return res

  def __str__(self):
#   return self.to_stdout()
    return self.to_fs()

  def printable(self):
    #logVar("__str__'ing path "+self.path)
    return self.path.encode(SYS_ENC) # .decode()

#class FilePathNameAutoenc(FilePathNameBaseEnc):

#  def join(self, astrPath):
#    logger.logDbg('join: '+str)
#    return os.path.join(self.path, str(astrPath))#self.__class__()

#  def __add__(self, astrOtherPath):
#    #logVar logOut
#    logVar('FilePathName::add self: %s, arg: %s'%(self.path, astrOtherPath))
#    new_obj = FilePathNameAutoenc(self.path)
#    new_obj += astrOtherPath
#    return new_obj
#    
#    return FilePathNameAutoenc(path, False)
  
#  def __radd__(self, astrOtherPath):
#    logVar('%s::radd self: %s, arg: %s'%(self.__class__, self.path, astrOtherPath))
#    return self.__class__(astrOtherPath+self.path)#astrOtherPath+self.path
  
  #def __iadd__(self, astrOtherPath):
  #  self.path = self.join(astrOtherPath)#.path
  #  return self


class FilePathName(FilePathNameEnc): pass
#class FilePathName(FilePathNameAutoenc): pass
#class FilePathName(FilePathNameAutoencStr): pass
#-------------------------------------------------------------------
class ShellCmd(FilePathName):
  'Контейнер для работы с шелл-командой и её аргументами' 

  def __init__(self, astrPath='', afDecode=True):
    FilePathName.__init__(self, astrPath, afDecode)
    self.args = []


#  def __radd__(self, astrOtherPath):
#    logVar('%s::radd self: %s, arg: %s'%(self.__class__, self.path, astrOtherPath))
#    return self.__class__(astrOtherPath+self.path)#astrOtherPath+self.path
  
  #def __iadd__(self, astrOtherPath):
  #  self.path = self.join(astrOtherPath)#.path
  #  return self


  def append_arg(self, arg):
    #logVar('%s::radd self: %s, arg: %s'%(self.__class__, self.path, astrOtherPath))
    #self.path += ' "%s"'%arg
    self.args.append(arg)
#   self.args.append(unicode(arg))

  #def extend_arg_list(self, arg_list):

  def extend_args(self, *args):
    for arg in args:
      self.append_arg(arg)

  def launch(self, afWait=True, stdindata=None, stdout=None, stdin=sys.stdin):
    arg_list = [self.path]
    arg_list.extend(str(el) for el in self.args) 
    return launch(arg_list, afWait, stdindata, stdout, stdin) 
#-------------------------------------------------------------------

#ZIPPER_PATH = FilePathName('//192.168.77.2/public/shared_soft/7-zip/7za.exe')

def NTFilenameDecode(astrData): 
  return str(astrData, "CP1251")

        
def CopyFolder(srcPath, destPath):
# print 'src: '+srcPath+', dest: '+destPath
#  if not os.path.exists(str(destPath)):
#  if not os.path.exists(destPath):
  srcPath = autoconvert(srcPath)
  destPath = autoconvert(destPath)

  if not destPath.exists():
    shutil.copytree(srcPath.to_fs(), destPath.to_fs())
    return

#  children = os.listdir(srcPath)
  children = srcPath.listdir()
  for node in children:
    #node = NTFilenameDecode(node)
    strFolderPath = srcPath+node
    strDstPath = destPath+node
#    if os.path.isdir(strFolderPath):
    if strFolderPath.isdir():
      shutil.copytree(str(strFolderPath), str(strDstPath))
    else:
      strFolderPath.copy_to(strDstPath)
      #shutil.copyfile(strFolderPath, strDstPath)
    
#def ClearFolder(astrPath, astrExcludePattern):
#  children = astrPath.listdir()
#  for node in children:
#    #node = NTFilenameDecode(node)
#    path = astrPath+node
#    if path.isdir():
#      shutil.rmtree(path)
#    else:
#      if re.match(astrExcludePattern, path)==None:
#        os.remove(path) 
  
def GetPathSpaces(astrPath, aResDataList):
  nFolderSize = 0
  astrPath = astrPath+os.sep
  try:
    children = os.listdir(astrPath)
    for node in children:
      strFullNodePath = astrPath+node
      if os.path.isdir(strFullNodePath):
        nSubfolderSize = GetPathSpaces(strFullNodePath, aResDataList)
        aResDataList.append([strFullNodePath, nSubfolderSize])
        nFolderSize += nSubfolderSize
        print(strFullNodePath)
        
      if os.path.isfile(strFullNodePath):
        nFileSize = os.lstat(strFullNodePath).st_size
        aResDataList.append([strFullNodePath, nFileSize])
        nFolderSize += nFileSize
  finally:
    return nFolderSize

     
def sortFileListBySize(aList):
  aList.sort(cmp=lambda x,y: cmp(y[1], x[1]))
#  return sorted(aList, cmp=lambda x,y: cmp(x[1], y[1]))
     

def zip(aZipFilename, aFileList):
  aZipFilename = autoconvert_str(aZipFilename)
  try:
    zip_file = zipfile.ZipFile(aZipFilename, 'w')
    list(map(zip_file.write, (autoconvert_str(f) for f in aFileList)))
  except:
    logExc()
  

def compress_7zip(archive_name, src_files, pwd=None):
  if not len(src_files):
    return

  params = [ZIPPER_PATH, 'a', '-tzip', archive_name]
  if pwd:
#   params.insert(-1, '-p'+pwd)
    params.append('-p'+pwd)

  params.extend(src_files)
  launch(params, True)


def unzip(astrFilename, astrPath):
  namelist = None
  try:
    zip_file = zipfile.ZipFile(str(astrFilename))
    zip_file.extractall(str(astrPath))
    namelist = zip_file.namelist()
  except:
    logExc()
  
  return namelist
     
def MSI_Install(astrPath):
  #os.system
  installer_command = ('msiexec', '/i', str(astrPath), '/passive')
  launch(installer_command)

  
def launch(path, afWait=True, stdindata=None, stdout=None, stdin=subprocess.PIPE):
  strPath = str(path)
  cmd_type = type(path)
  #logDbg("Cmd arg type: [%s]"%cmd_type, logger_name = FILE_UTILS_LOGGER)
  #logDbg("executing path: [%r]"%path, logger_name = FILE_UTILS_LOGGER)

# path = autoconvert_list(path)
  if cmd_type in (list, tuple): 
    path = [autoconvert_u(el) for el in path]
#   strPath = [autoconvert(el) for el in path]
    strPath = '"%s"'%'" "'.join(path)
  else:
    strPath = autoconvert_u(path)
    
  logOut("executing path: [%s]"%strPath, logger_name = FILE_UTILS_LOGGER)
#  dir = os.path.dirname(strPath)
  # Получение каталога программы не будет работать, пока из всей командной строки не выделен путь к программе
  #dir = strPath.dirname()
  sub = None

  out_data = stdout#subprocess.PIPE
  
  #std_in = subprocess.PIPE if stdin==None else stdin
  std_in = stdin
# if isinstance(stdindata, file):
  if stdindata:
    std_in = stdindata # subprocess.PIPE
    stdindata = None

  std_out = None
  if stdout:
    std_out = subprocess.PIPE
#   stdindata = None

  #err_data = subprocess.PIPE
  #logDbg("executing path: [%r]"%path, logger_name = FILE_UTILS_LOGGER)
  try:
#   pdb.set_trace()
#   sub = subprocess.Popen(strPath, stdin=std_in, stdout=std_out, stderr=subprocess.STDOUT)
    sub = subprocess.Popen(path, stdin=std_in, stdout=std_out, stderr=subprocess.STDOUT)
    #logDbg('Launch Popen call successfull')
  except:
    logExc("Exception during %r command launch!"%path)
   
# pdb.set_trace()
  if afWait:
    ret_code = -100
    stdoutdata, stderrdata = sub.communicate(stdindata)
    if stdoutdata:
      stdoutdata = stdoutdata.decode(OS_OUTPUT_ENCODING)
      if stdout:
        stdout.write(stdoutdata)

    if stderrdata:
      stderrdata = stderrdata.decode(OS_OUTPUT_ENCODING)

    ret_code = sub.wait()
    return ret_code, stdoutdata, stderrdata
  else:
    return sub


def cat(astrFilename, mode='r'):
  with open(autoconvert_str(astrFilename), mode) as f:  return f.read ()
  #return open(astrFilename)


def xcat(astrFilename):
  #logDbg("xcat'ting file [%s], file type: %s"%(astrFilename, type(astrFilename)), logger_name = FILE_UTILS_LOGGER)
  with open(astrFilename, 'U') as f:  
    for line in f:
      yield line.strip('\r\n')


def recode_file(src_filename, src_enc, dst_filename, dst_enc):
  logOut('Creating %s version of %s...'%(dst_enc, src_enc))
  src_filename.encode_convert_to(src_enc, dst_enc, dst_filename)


def AnalyzeSpace(astrPath, anBlockSize=1024*1024, anBlockName='MB'):
  data = []
  strFormatDataList = []
  nTotalSpace = GetPathSpaces(astrPath, data)
  
#  l1 = 
  sortFileListBySize(data)

  fReport = open(astrPath+'/DiskSpaceReport.lst', 'w')
  for node in data:
    strSpaceFmt = locale.format("%12d", node[1]/anBlockSize, True)
    strData = "{0:120}{1} {2}, {3:>3.0%}".format(node[0], strSpaceFmt, anBlockName, float(node[1])/nTotalSpace)
#    "{0:150}{1:>12n} {2}, {3:>3.0%}".format(node[0], node[1]/anSizeBlock, anBlockName, float(node[1])/nTotalSpace)
#    "%150s %s %s, %3d%%" % (node[0], strSpaceFmt, anBlockName, 100*node[1]/nTotalSpace)
#    strData = codecs.decode()
    fReport.write(strData+'\n')

  fReport.close()


def find_process_files(src_dir, filemask, proc_func, *pf_args, **pf_kwargs):
  src_path = FilePathName(src_dir)

  src_list = src_path.search(filemask, re.I)
  src_list_len = len(src_list)

  for i, src_file in enumerate(src_list):
    logOut('Processing source file [%s] %d/%d'%(src_file, i+1, src_list_len), logger_name = FILE_UTILS_LOGGER)
    args = list(pf_args)
    args.insert(0, i)
    args.insert(1, src_list_len)
#   args = tuple(args)

    #logDbg('args: %s'%args, logger_name = FILE_UTILS_LOGGER)
    proc_func(src_file, *args, **pf_kwargs)


#@pu.functionThreader
#@pu.functionProcessWrap
def file_search_thread(res_list, src_path):
  res = src_path.find_all()
# pdb.set_trace()
  res_list.extend(res)


def find_files_cached_iter(cache_path, src_path, filemask, report_count=1):
  import shelve

  src_path = FilePathName(src_path)

  raw_list = []
  search_thread = pu.start_worker_process(file_search_thread, raw_list, src_path)

  logOut('Extracting file cache...', logger_name = FILE_UTILS_LOGGER)
  db_key = str(src_path)
  try:
    with closing(shelve.open(cache_path, writeback=False)) as cache_db:
      raw_cached_list = cache_db.get(db_key)
  except:
    logExc('Exception on DB data read. Filesystem will be searched for source files')
    raw_cached_list = None
    

  src_list = []
  if raw_cached_list:
#   with shelve.open(cache_path, writeback=True) as cache_db:
#     cache_db[db_key] = real_src_list
# src_path.filter_raw_file_list(raw_cached_list, filemask)
#   logOut(u'Creating filter...', logger_name = FILE_UTILS_LOGGER)
    src_list_len = len(raw_cached_list)
    filtered_list = it.ifilter(lambda x: x.match_pattern(filemask), list(map(autoconvert, raw_cached_list)))
    logOut('Raw files to be processed: %d'%src_list_len, logger_name = FILE_UTILS_LOGGER)
#   pdb.set_trace()
    for i, src_file in enumerate(filtered_list):
#     src_file = autoconvert(src_file)
      if not src_file.exists():
        continue

      if (i+1)%report_count==0:
        logOut('Processing source file [%s] %d/%d'%(src_file, i+1, src_list_len), logger_name = FILE_UTILS_LOGGER)

      src_list.append(src_file)
      yield i, src_file

  logOut('Waiting for real filesystem search results...')
  search_thread.join()

  real_src_list = src_path.filter_raw_file_list(raw_list, filemask)
  src_list = set(real_src_list) - set(src_list)
#   src_list = list(set([str(i) for i in src_list]) - set([str(i) for i in real_src_list]))

  src_list_len = len(src_list)
# pdb.set_trace()
  if src_list_len:
    with closing(shelve.open(cache_path, writeback=True)) as cache_db:
      cache_db[db_key] = raw_list

    logOutLen('Processing new (not cached) source files', src_list, logger_name = FILE_UTILS_LOGGER)
    for i, src_file in enumerate(src_list):
      if (i+1)%report_count==0:
        logOut('Processing source file [%s] %d/%d'%(src_file, i+1, src_list_len), logger_name = FILE_UTILS_LOGGER)
      yield i, src_file
  else:
    logOut('No new files found', logger_name = FILE_UTILS_LOGGER)
