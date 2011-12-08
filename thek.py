#!/usr/bin/env python
#
# TODO
# * find keywords in filename and category based on keywords?
# * access frequency in history

import sys,json,shelve
from os import path
from subprocess import Popen
from glob import glob

class Tehk:

	def __init__(self,config):
		self.config = config.pop()
		self.persist = shelve.open(self.config.get('history'))

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
		history = self.persist.get('history',[])
		if(path not in history):
			history.append(path)
		else:
			history.remove(path)
			history.append(path)
		self.persist['history']=history

	def cmd_debug(self,key):
		print self.persist.get(key)

	def cmd_history_clear(self):
		del self.persist['history']

	def cmd_history(self,subcmd=''):
		if(subcmd):
			return self.call_cmd('history_'+subcmd)
		history = self.persist.get('history')
		if(history):
			self.numerate(history,persist_index=history)

	def cmd_ls(self,cat=''):
		if(cat):
			self.set_default_action('open')
		else:
			self.set_default_action('ls')
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
		Popen('%s "%s"' % (self.config.get('runner'),path),shell=True)
		self.append_to_history(path)
		self.quit(msg="%s opend" % path)

	def set_default_action(self,action):
		self.persist['default_action']=action

	def call_by_key(self,key):
		action = self.persist.get('default_action')
		indexes = self.persist.get('index')
		if(not action or not indexes):
			self.quit(msg="Thek doesn't know what to do",code=1)

		if(indexes.get(key)):
			if(not self.call_cmd(action,[indexes.get(key)])):
				self.quit(msg="Thek can't %s" % action, code=1)
		else:
			self.quit(msg="Thek can't find %s" % key, code=1)
		
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

