# -*- coding: UTF-8 -*-
import re
from re import I, M, S, U

RE_STORAGE = {}
def get_compiled_pattern(pattern, flags=0):
	pattern_RE = RE_STORAGE.get(pattern+'%d'%flags)
	if pattern_RE == None:
		pattern_RE = re.compile(pattern, flags)
		RE_STORAGE[pattern+'%d'%flags] = pattern_RE

	return pattern_RE


def extract(pattern, source, flags=0):	
	RE = get_compiled_pattern(pattern, flags)
	match = re.search(RE, source)
	if not match:
		return None

	return match.groups()


def findall(pattern, source, flags=0):	
	RE = get_compiled_pattern(pattern, flags)
	return re.findall(RE, source)


def finditer(pattern, source, flags=0):	
	RE = get_compiled_pattern(pattern, flags)
	return re.finditer(RE, source)


def sub(find, replace, source, count=0, flags=0):
	find_re = get_compiled_pattern(find, flags)
	return re.sub(find_re, replace, source, count)


def split(find, source, flags=0):	
	search_re = get_compiled_pattern(find, flags)
	return re.spl(search_re, source)

def search(find, source, flags=0):	
	search_re = get_compiled_pattern(find, flags)
	return re.search(search_re, source)
