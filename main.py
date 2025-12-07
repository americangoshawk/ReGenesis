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

    # Create GUI (which will set the icon)
    gui = RegenesisGUI()

    # Set dock icon after tkinter is initialized
    if sys.platform == 'darwin':
        try:
            from Foundation import NSImage
            import AppKit
            import os

            icon_path = os.path.join(os.path.dirname(__file__), 'oak_leaf.icns')
            if os.path.exists(icon_path):
                image = NSImage.alloc().initWithContentsOfFile_(icon_path)
                if image and AppKit.NSApp:
                    AppKit.NSApp.setApplicationIconImage_(image)
        except (ImportError, AttributeError):
            pass

    gui.run()


if __name__ == "__main__":
    main()
