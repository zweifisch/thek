#!/usr/bin/env python
#
# TODO
# * find keywords in filename and category based on keywords?

import sys,json,shelve
import operator
from os import path
from subprocess import Popen
from glob import glob
from collections import defaultdict

class Tehk:

	def __init__(self,config):
		self.config = config.pop()
		self.persist = shelve.open(path.expanduser(self.config.get('history')))

	def quit(self,**kargs):
		self.persist.close()
		if(kargs.get('msg')):
			print(kargs.get('msg'))
		code = kargs.get('code',0)
		sys.exit(code)

	def update_index(self,dic):
		# handle list
		if(not isinstance(dic,dict)):
			dic = dict(zip(map(str,range(1,len(dic)+1)), dic))
		index = self.persist.get('index',{})
		index.update(dic)
		self.persist['index']=index

	def append_to_history(self,path):
		history = defaultdict(int)
		history.update(self.persist.get('history',{}))
		history[path] +=1
		self.persist['history']=history

	def cmd_debug(self,key):
		"list access history"
		print self.persist.get(key)

	def cmd_history_ls(self):
		"list access history"
		history = self.persist.get('history')
		if(history):
			history = sorted(history.iteritems(),key=operator.itemgetter(1),reverse=True)
			self.numerate(map(lambda (k,f): "%s (%d)" % (path.basename(k).replace('-',' '),f), history),
                            persist_index=map(lambda (k,f):k, history))

	def cmd_history_clear(self):
		"clean access history"
		del self.persist['history']

	def cmd_history(self,subcmd='ls'):
		"list acceess history"
		return self.call_cmd('history_'+subcmd)

	def cmd_ls(self,cat=''):
		"list dir"
		pattern = path.join(path.expanduser(self.config.get('location')),cat,'*')
		pathes = glob(pattern)
		if(pathes):
			basenames = map(path.basename,pathes)
			self.numerate(basenames,
				persist_index=pathes,
				persist_dict=dict(zip(basenames,pathes)))
		else:
			self.quit(msg='nothing found')
	
	def cmd_open(self,path):
		"open file"
		Popen('%s "%s"' % (self.config.get('runner'),path),shell=True)
		self.append_to_history(path)
		self.quit(msg="%s opend" % path)

	def cmd_help(self,**args):
		"show this help info"
		if(len(args)==0):
			attrs = dir(self)
			print "\n".join(
				map(lambda x: "%s\t%s" % (x[4:].replace('_',' '), getattr(self,x).__doc__),
				filter(lambda x:x[:3]=='cmd',attrs)))

	def call_by_key(self,key):
		indexes = self.persist.get('index')
		if(not indexes):
			self.quit(msg="Thek doesn't know what to do",code=1)

		f = indexes.get(key)
		if(not f):
			self.quit(msg="Thek can't find %s" % key, code=1)

		if(path.isfile(f)):
			self.call_cmd('open',[f])
		elif(path.isdir(f)):
			self.call_cmd('ls',[f])
		else:
			self.quit(msg="Thek can't find %s" % f, code=1)
		
	def call_cmd(self,cmd,args=[]):
		executor = getattr(self,'cmd_'+cmd,None)
		if(executor):
			executor(*args)
			return True

	def execute(self,args):
		if(len(args)):
			cmd = args[0]
			args = args[1:]
		else:
			cmd = 'ls'
		if(not self.call_cmd(cmd,args)):
			self.call_by_key(cmd)

	def numerate(self,items,**kargs):
		for index,item in enumerate(items):
			print("%d. %s" % (index+1,item))
		if(kargs.get('persist_index')):
			self.update_index(kargs.get('persist_index'))
		if(kargs.get('persist_dict')):
			self.update_index(kargs.get('persist_dict'))

def get_config(filename):
	locations = [
		(path.dirname(path.realpath(sys.argv[0])),filename),
		(path.dirname(path.realpath(sys.argv[0])),'.'+filename),
		(path.expanduser('~/'),'.'+filename),
	]
	while len(locations)>0:
		config_file = path.join(*locations.pop())
		if(path.exists(config_file)):
			return config_file
	return False


def main():
	config_file = get_config('thek.json')
	if(not config_file):
		print('config file tehk.json not found')
		sys.exit(1)

	with open(config_file) as fp:
		config = json.load(fp)
		tehk = Tehk(config)
		tehk.execute(sys.argv[1:])

if __name__ == '__main__':
	main()

