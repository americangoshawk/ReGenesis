import sys
from regenesis_gui import RegenesisGUI


def main():
    """Entry point for the Regenesis application."""
    # Set process name for macOS menu bar
    if sys.platform == 'darwin':
        try:
            from Foundation import NSBundle
            bundle = NSBundle.mainBundle()
            if bundle:
                info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
                if info:
                    info['CFBundleName'] = 'ReGenesis'
        except ImportError:
            # Foundation module not available, menu will show 'Python'
            pass

    gui = RegenesisGUI()
    gui.run()


if __name__ == "__main__":
    main()
