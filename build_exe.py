import shutil
import sys
import platform
import os
import PyInstaller.__main__

def build_exe():
    """Build executable for current platform and place it in bin/"""
    
    # Get platform info
    system = platform.system()
    machine = platform.machine()
    
    print(f"🔨 Building for {system} ({machine})...")
    
    # Determine the output directory and executable name
    if system == "Windows":
        bin_dir = "bin/windows"
        exe_name = "scheme-generator.exe"
    elif system == "Darwin":  # macOS
        bin_dir = "bin/macos"
        exe_name = "scheme-generator"
    elif system == "Linux":
        bin_dir = "bin/linux"
        exe_name = "scheme-generator"
    else:
        print(f"❌ Unsupported platform: {system}")
        sys.exit(1)
    
    # Clean previous build
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
    
    # Build executable
    PyInstaller.__main__.run([
        'scheme_generator/cli.py',
        '--name=scheme-generator',
        '--onefile',
        '--console',
        '--clean'
    ])
    
    # Copy to bin directory
    source = os.path.join("dist", exe_name)
    dest_dir = bin_dir
    
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, exe_name)
    
    if os.path.exists(source):
        shutil.copy2(source, dest)
        print(f"✅ Successfully built: {dest}")
        
        # On Unix systems, make it executable
        if system in ["Darwin", "Linux"]:
            os.chmod(dest, 0o755)
            print(f"✅ Made executable: chmod +x {dest}")
    else:
        print(f"❌ Build failed: {source} not found")
        sys.exit(1)
    
    # Clean up dist and build folders
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
    
    print(f"🎉 Build complete! Ready to use: {dest}")

if __name__ == "__main__":
    build_exe()
