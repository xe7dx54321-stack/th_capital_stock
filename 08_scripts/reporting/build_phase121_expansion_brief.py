import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase121_expansion_brief import build_expansion_brief_md
def main():
 r=build_expansion_brief_md()
 if "--markdown" in sys.argv or "--json" not in sys.argv: print(r)
 else: print('{"phase121_expansion_brief":"brief_generated_markdown_mode"}')
if __name__=="__main__":main()
