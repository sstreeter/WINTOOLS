
import sys
import shutil
from PIL import Image

def check_cairosvg():
    try:
        import cairosvg
        print("[OK] cairosvg is installed.")
        return True
    except ImportError:
        print("[MISSING] cairosvg is NOT installed.")
        return False

def check_ghostscript():
    # Check for gs command
    gs_path = shutil.which('gs')
    if gs_path:
        print(f"[OK] Ghostscript found at: {gs_path}")
        return True
    else:
        print("[MISSING] Ghostscript (gs) command not found.")
        return False

def check_pil_eps():
    try:
        Image.init()
        if 'EPS' in Image.ID:
            print("[OK] PIL EPS decoder available.")
        else:
            print("[INFO] PIL EPS decoder not explicitly listed (might still work with GS).")
    except Exception as e:
        print(f"[ERROR] Checking PIL: {e}")

if __name__ == "__main__":
    print(f"Python: {sys.version}")
    cairo = check_cairosvg()
    gs = check_ghostscript()
    check_pil_eps()
