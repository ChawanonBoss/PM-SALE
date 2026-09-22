"""Runs every *_test.py in this folder (each is a standalone script that exits non-zero on failure) and prints a summary.
Usage:  python tests/run_all.py            (all)        python tests/run_all.py approval   (only files whose name contains 'approval')
Needs: Python 3, `pip install playwright` + `python -m playwright install chromium`, internet (pdf.js / SheetJS load from a CDN)."""
import glob, os, subprocess, sys, time
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # this script's own stdout can also hit Windows' cp1252 console codepage when it prints a failing test's Thai output
except Exception: pass
HERE = os.path.dirname(os.path.abspath(__file__))
pat = sys.argv[1] if len(sys.argv) > 1 else ""
files = sorted(f for f in glob.glob(os.path.join(HERE, "*_test.py")) if pat in os.path.basename(f))
env = dict(os.environ, PYTHONUTF8="1")
results = []
for f in files:
    t0 = time.time()
    # encoding/errors pinned explicitly: on Windows the parent's default text-decode codepage (cp1252) is independent of the child's
    # own PYTHONUTF8 env var, so a test that prints Thai text on failure could crash *this* decode instead of reporting the real failure.
    r = subprocess.run([sys.executable, f], cwd=HERE, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
    ok = r.returncode == 0
    results.append((os.path.basename(f), ok))
    print(("PASS " if ok else "FAIL ") + os.path.basename(f) + f"  ({time.time() - t0:.0f}s)")
    if not ok: print("   " + "\n   ".join(((r.stdout or "") + (r.stderr or "")).strip().splitlines()[-6:]))
print(f"\n{sum(ok for _, ok in results)}/{len(results)} passed")
sys.exit(0 if all(ok for _, ok in results) else 1)
