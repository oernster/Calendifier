#!/usr/bin/env python3
"""
Calendifier Build Script
========================

A simple build script that uses PyInstaller to compile Calendifier into a
standalone executable and handles LGPL3 license compliance.

Usage:
    python build.py [options]

Options:
    --debug     Enable debug mode with verbose output
    --console   Enable console window (Windows only)
    --launch    Launch the application after building
"""

import os
import sys
import shutil
import platform
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# Try to import version, or use default
try:
    from version import __version__
except ImportError:
    __version__ = "1.0.0"

# Configuration
APP_NAME = "Calendifier"
MAIN_SCRIPT = "main.py"
OUTPUT_DIR = "dist"
SPEC_FILE = "calendifier.spec"


def ensure_pyinstaller_installed():
    """Check if PyInstaller is installed, and install it if not."""
    try:
        import PyInstaller  # noqa: F401  (imported to test availability)

        print("✅ PyInstaller is already installed")
        return True
    except ImportError:
        print("⚠️ PyInstaller not found. Attempting to install...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "pyinstaller"]
            )
            print("✅ PyInstaller installed successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to install PyInstaller: {e}")
            print("Please install PyInstaller manually: pip install pyinstaller")
            return False


def clean_output_directory():
    """Ensure output directory exists and is empty."""
    output_path = Path(OUTPUT_DIR)

    # Remove if exists
    if output_path.exists():
        try:
            shutil.rmtree(output_path)
            print(f"🧹 Cleaned output directory: {OUTPUT_DIR}")
        except PermissionError:
            print(f"⚠️ Could not clean {OUTPUT_DIR} directory (permission denied)")
            print("   This is likely because the executable is still running.")
            print("   Please close the application and try again.")
            sys.exit(1)

    # Create fresh directory
    output_path.mkdir(parents=True)
    print(f"📁 Created output directory: {OUTPUT_DIR}")

    # Also clean build directory and spec file
    build_path = Path("build")
    if build_path.exists():
        try:
            shutil.rmtree(build_path)
            print("🧹 Cleaned build directory")
        except PermissionError:
            print("⚠️ Could not clean build directory (permission denied)")

    spec_path = Path(SPEC_FILE)
    if spec_path.exists():
        try:
            spec_path.unlink()
            print(f"🧹 Removed spec file: {SPEC_FILE}")
        except PermissionError:
            print("⚠️ Could not remove spec file (permission denied)")


def copy_license_files():
    """Copy LGPL3 license files to output directory."""
    output_path = Path(OUTPUT_DIR)

    # Ensure output directory exists
    if not output_path.exists():
        output_path.mkdir(parents=True)

    # Copy main license
    if Path("LICENSE").exists():
        shutil.copy2("LICENSE", output_path / "CALENDIFIER_LICENSE.txt")
        print("📄 Copied Calendifier license")

    # Copy LGPL3 license
    if Path("LGPL3_LICENSE.txt").exists():
        shutil.copy2("LGPL3_LICENSE.txt", output_path / "LGPL3_LICENSE.txt")
        print("📄 Copied LGPL3 license")

    # Copy or create LGPL3 compliance notice
    if Path("LGPL3_COMPLIANCE_NOTICE.txt").exists():
        with open("LGPL3_COMPLIANCE_NOTICE.txt", "r", encoding="utf-8") as f:
            notice = f.read()

        # Update placeholders
        notice = notice.replace(
            "{build_date}", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        notice = notice.replace("{version}", __version__)

        with open(
            output_path / "LGPL3_COMPLIANCE_NOTICE.txt", "w", encoding="utf-8"
        ) as f:
            f.write(notice)
        print("📄 Updated and copied LGPL3 compliance notice")
    else:
        # Create a basic compliance notice
        notice = f"""
LGPL3 COMPLIANCE NOTICE FOR CALENDIFIER
=======================================

This application uses PySide6, which is licensed under LGPL3.
In compliance with LGPL3 requirements:

1. SOURCE CODE AVAILABILITY:
   - Calendifier source code: https://github.com/oernster/calendifier
   - PySide6 source code: https://code.qt.io/cgit/pyside/pyside-setup.git/

2. LIBRARY REPLACEMENT:
   While this is a single-file executable, the LGPL3 license grants you the right
   to replace the PySide6 libraries. To exercise this right:

   a) Download the Calendifier source code from the repository above
   b) Replace the PySide6 dependency in requirements.txt with your preferred version
   c) Rebuild the application using the provided build script

3. LGPL3 LICENSE:
   The full LGPL3 license text is available at:
   https://www.gnu.org/licenses/lgpl-3.0.html

4. DEPENDENCIES:
   This application includes the following LGPL3-licensed components:
   - PySide6 (Qt6 Python bindings)
   - shiboken6 (PySide6 support library)

Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Calendifier Version: {__version__}
"""
        with open(
            output_path / "LGPL3_COMPLIANCE_NOTICE.txt", "w", encoding="utf-8"
        ) as f:
            f.write(notice.strip())
        print("📄 Created LGPL3 compliance notice")


def build_with_pyinstaller(debug=False, console=False):
    """Build the application using PyInstaller."""
    print(f"🚀 Building {APP_NAME} v{__version__}")
    print(f"📦 Platform: {platform.system()} {platform.machine()}")
    print(f"🐍 Python: {sys.version.split()[0]}")
    print(f"🖥️ Console mode: {'Enabled' if console else 'Disabled'}")

    # Basic PyInstaller options
    options = [
        "--name",
        APP_NAME,
        "--onefile",  # Create a single executable
        "--clean",  # Clean PyInstaller cache
        "--noconfirm",  # Replace output directory without asking
    ]

    # Check if data files exist before adding them
    data_files = [
        "calendar_app/localization/translations;calendar_app/localization/translations",
        "calendar_app/localization/locale_holiday_translations;calendar_app/localization/locale_holiday_translations",  # noqa: E501
        "assets;assets",
    ]

    for data_file in data_files:
        source_path = data_file.split(";")[0]
        if Path(source_path).exists():
            options.extend(["--add-data", data_file])
            print(f"📁 Adding data: {source_path}")
        else:
            print(f"⚠️ Skipping missing data: {source_path}")

    # Debug options
    if debug:
        options.extend(["-d", "all"])  # PyInstaller debug requires an argument

    # Console options - Create a windowed wrapper for main.py
    if platform.system() == "Windows":
        if not console:
            # Create a wrapper script that handles windowed mode properly
            wrapper_script = create_windowed_wrapper()
            if wrapper_script:
                # Use the wrapper script instead of main.py
                main_to_build = wrapper_script
                print("📝 Using windowed wrapper script")
            else:
                main_to_build = MAIN_SCRIPT

            options.append("--windowed")  # This prevents the console window
            print("🚫 Console window disabled for Windows build")
        else:
            main_to_build = MAIN_SCRIPT
            print("🖥️ Console window enabled (debug mode)")
    else:
        main_to_build = MAIN_SCRIPT

    # Platform-specific options
    if platform.system() == "Windows":
        if Path("assets/calendar_icon.ico").exists():
            options.extend(["--icon", "assets/calendar_icon.ico"])
    elif platform.system() == "Darwin":  # macOS
        if Path("assets/calendar_icon.icns").exists():
            options.extend(["--icon", "assets/calendar_icon.icns"])
    elif platform.system() == "Linux":
        if Path("assets/calendar_icon.png").exists():
            options.extend(["--icon", "assets/calendar_icon.png"])

    # Essential hidden imports
    hidden_imports = [
        "holidays",
        "holidays.countries",
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "calendar_app",
        "calendar_app.main_window",
    ]

    for import_name in hidden_imports:
        options.extend(["--hidden-import", import_name])

    # Additional options for better compatibility
    options.append("--collect-all=PySide6")
    options.append("--collect-all=shiboken6")
    options.append("--collect-all=holidays")

    # Add paths that might be needed
    options.extend(["--paths", "."])

    # Build command
    cmd = [sys.executable, "-m", "PyInstaller"] + options + [main_to_build]

    print("🔨 Running PyInstaller compilation...")
    if debug:
        print(f"Command: {' '.join(cmd)}")

    try:
        # Run PyInstaller compilation
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

        # Read output line by line
        for line in process.stdout:
            line = line.rstrip()
            print(line)

        # Wait for process to complete
        return_code = process.wait()

        if return_code == 0:
            print("✅ Compilation successful!")
            return True
        else:
            print(f"❌ Compilation failed with exit code {return_code}")
            return False

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def create_windowed_wrapper():
    """Create a wrapper script that properly handles windowed mode."""
    try:
        wrapper_content = f'''#!/usr/bin/env python3
"""
Windowed wrapper for {APP_NAME}
Handles stdout/stderr redirection and encoding for windowed PyInstaller builds
"""
import sys
import os
from pathlib import Path

def main():
    # CRITICAL: Fix encoding issues before anything else happens
    # Set UTF-8 encoding environment variables
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'

    # Force UTF-8 for stdout/stderr
    if hasattr(sys, '_MEIPASS'):  # Running as PyInstaller bundle
        try:
            # Try to set UTF-8 encoding for streams
            import io
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer, encoding='utf-8', errors='ignore'
            )
            sys.stderr = io.TextIOWrapper(
                sys.stderr.buffer, encoding='utf-8', errors='ignore'
            )
        except Exception:
            # If that fails, redirect to null to prevent crashes
            sys.stdout = open(os.devnull, 'w', encoding='utf-8')
            sys.stderr = open(os.devnull, 'w', encoding='utf-8')

    # Import and run the actual main application
    try:
        # Import the main module
        import main

        # Run the main function if it exists
        if hasattr(main, 'main'):
            main.main()
        elif hasattr(main, '__name__'):
            # If no main function, just import should run the module
            pass
    except Exception as e:
        # In windowed mode, show error in a message box if possible
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            app = QApplication.instance() or QApplication([])
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("{APP_NAME} Error")
            msg.setText(f"Failed to start {APP_NAME}")
            msg.setDetailedText(str(e))
            msg.exec()
        except:
            # If we can't show error, exit silently
            sys.exit(1)

if __name__ == "__main__":
    main()
'''

        wrapper_path = Path("_windowed_main.py")
        with open(wrapper_path, "w", encoding="utf-8") as f:
            f.write(wrapper_content)

        print("📝 Created windowed wrapper script with encoding fixes")
        return str(wrapper_path)
    except Exception as e:
        print(f"⚠️ Could not create windowed wrapper: {e}")
        return None


def launch_executable():
    """Launch the built executable."""
    exe_name = f"{APP_NAME}{'.exe' if platform.system() == 'Windows' else ''}"
    exe_path = Path(OUTPUT_DIR) / exe_name

    if not exe_path.exists():
        print(f"❌ Executable not found at {exe_path}")
        return False

    print(f"🚀 Launching {exe_path}...")
    try:
        if platform.system() == "Windows":
            # Use startfile for Windows to launch properly without console
            import os

            os.startfile(str(exe_path))
        else:
            # For macOS and Linux
            subprocess.Popen([str(exe_path)])
        print("✅ Application launched successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to launch application: {e}")
        print(f"📍 Tried to launch: {exe_path}")
        print(f"📊 File exists: {exe_path.exists()}")
        if exe_path.exists():
            print(f"📏 File size: {exe_path.stat().st_size} bytes")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description=f"Build {APP_NAME} using PyInstaller")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument(
        "--console", action="store_true", help="Enable console window on Windows"
    )
    parser.add_argument(
        "--launch", action="store_true", help="Launch the application after building"
    )

    args = parser.parse_args()

    print(f"🏗️ {APP_NAME} Build Script")
    print("=" * 50)

    # Check if PyInstaller is installed
    if not ensure_pyinstaller_installed():
        sys.exit(1)

    # Check if main script exists
    if not Path(MAIN_SCRIPT).exists():
        print(f"❌ Main script not found: {MAIN_SCRIPT}")
        sys.exit(1)

    # Clean output directory
    clean_output_directory()

    # Build executable
    success = build_with_pyinstaller(debug=args.debug, console=args.console)

    # Clean up wrapper file if it was created
    wrapper_file = Path("_windowed_main.py")
    if wrapper_file.exists():
        try:
            wrapper_file.unlink()
            print("🧹 Cleaned up wrapper script")
        except Exception:
            pass

    if success:
        # Copy license files
        copy_license_files()

        print("\n🎉 Build completed successfully!")

        exe_name = f"{APP_NAME}{'.exe' if platform.system() == 'Windows' else ''}"
        exe_path = Path(OUTPUT_DIR) / exe_name

        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"📦 Output file: {exe_path}")
            print(f"📏 File size: {size_mb:.1f} MB")

            # List files in dist directory
            print("\n📁 Files in dist directory:")
            for root, dirs, files in os.walk(OUTPUT_DIR):
                for file in files:
                    rel_path = os.path.relpath(os.path.join(root, file), OUTPUT_DIR)
                    print(f"   • {rel_path}")

            # Debugging instructions
            print("\n🔍 DEBUGGING INSTRUCTIONS:")
            print("If the exe doesn't run when double-clicked, try this:")
            print("1. Open Command Prompt")
            print(f"2. Navigate to: {Path(OUTPUT_DIR).absolute()}")
            print(f"3. Run: {exe_name}")
            print("4. This will show any error messages")
            print("\nAlternatively, build with console enabled:")
            print("   python build.py --console")
            print("This will keep the console window visible to see errors.")

            # Launch the executable if requested
            if args.launch:
                if launch_executable():
                    print("🎮 Application is now running!")
                else:
                    print("⚠️ Application could not be launched automatically.")
                    print("💡 Try running from command prompt to see error details.")
            else:
                print(
                    "ℹ️ Application built successfully but not launched "
                    "(use --launch to launch)"
                )
        else:
            print(f"⚠️ Expected executable not found: {exe_path}")

        sys.exit(0)
    else:
        print("\n💥 Build failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
