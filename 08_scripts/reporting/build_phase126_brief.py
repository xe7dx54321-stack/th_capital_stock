import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase126_brief import build_brief_md
def main():
 r=build_brief_md()
 if "--markdown" in sys.argv: print(r)
 elif "--json" in sys.argv: print('{"phase126_brief":"brief_generated"}')
 else: print(r)
if __name__=="__main__":main()
