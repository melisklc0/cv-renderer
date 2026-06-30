import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from cv_renderer.render import main

if __name__ == "__main__":
    main()
