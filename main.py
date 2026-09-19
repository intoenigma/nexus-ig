import sys
from nexus_ig.core.bot import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Nexus IG Bot stopped cleanly.")
        sys.exit(0)

