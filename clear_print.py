import sys

def errprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def clsprint(cls,*args, **kwargs):
	print("[%s] %s"%(cls.__class__.__name__,*args),**kwargs)

if len(sys.argv) > 1:
	if(sys.argv[1] == "debug"):
		print("Debug print activate")
		def Dprint(*args, **kwargs):
			print(*args, file=sys.stderr, **kwargs)
else:
	def Dprint(*args, **kwargs):
		pass