import pathlib,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
def test_pack_integrity():
 subprocess.run([sys.executable,str(ROOT/'scripts/check_nfl_63c969c3.py')],cwd=ROOT,check=True)
def test_deterministic_site():
 p=ROOT/'docs/nfl-63c969c3/requirements.html'; before=p.read_bytes();subprocess.run([sys.executable,str(ROOT/'scripts/build_nfl_63c969c3.py')],cwd=ROOT,check=True);assert p.read_bytes()==before
