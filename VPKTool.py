# pyinstaller --onefile --console --collect-all vpk --collect-all rich --collect-all send2trash --name "VPKTool" --icon=icon.ico main.py
# nuitka --onefile --mingw64 --windows-console-mode=force --include-package=vpk --include-package=rich --include-package=send2trash --follow-imports --windows-icon-from-ico=icon.ico --enable-plugin=anti-bloat --assume-yes-for-downloads --show-progress --company-name="Dota2PornFx" --product-name="VPKTool" --file-version=2.0 --output-filename=VPKTool.exe main.py

import sys
import tempfile
import shutil
import gc
import os
import subprocess
import time
import threading
from pathlib import Path

if getattr(sys, 'frozen', False):
    exe_dir = os.path.dirname(sys.executable)
else:
    exe_dir = os.path.dirname(os.path.abspath(__file__))

try:
    import vpk
    VPK_AVAILABLE = True
except ImportError:
    VPK_AVAILABLE = False

try:
    from send2trash import send2trash
    USE_TRASH = True
except ImportError:
    USE_TRASH = False

try:
    from rich.console import Console
    from rich.text import Text
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False


def print_ascii_art():
    if HAS_RICH:
        width = console.size.width
        PURPLE = "#B486FF"
        WHITE = "white"

        lines = [
            "██╗   ██╗██████╗ ██╗  ██╗████████╗ ██████╗  ██████╗ ██╗     ",
            "██║   ██║██╔══██╗██║ ██╔╝╚══██╔══╝██╔═══██╗██╔═══██╗██║     ",
            "██║   ██║██████╔╝█████╔╝    ██║   ██║   ██║██║   ██║██║     ",
            "╚██╗ ██╔╝██╔═══╝ ██╔═██╗    ██║   ██║   ██║██║   ██║██║     ",
            " ╚████╔╝ ██║     ██║  ██╗   ██║   ╚██████╔╝╚██████╔╝███████╗",
            "  ╚═══╝  ╚═╝     ╚═╝  ╚═╝   ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝",
            "by @dota2pornfx"
        ]                                                   

        console.print()
        for line in lines[:-1]:
            console.print(Text(line.center(width), style=PURPLE))
        console.print(Text(lines[-1].center(width), style=WHITE))
        console.print()

    else:
        print("=" * 10)
        print("VPKTool")
        print("by @dota2pornfx")
        print("=" * 10 + "\n")

def move_to_trash_or_delete(item_path):
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            if USE_TRASH:
                send2trash(str(item_path))
            else:
                if item_path.is_dir():
                    shutil.rmtree(item_path)
                else:
                    item_path.unlink()
            return True
        except Exception as e:
            if attempt < max_attempts - 1:
                time.sleep(0.3)
            continue
    return False

def delayed_delete_vpk_files(vpk_file_paths, delay=2):
    def delete_files():
        time.sleep(delay)
        
        print("\n🗑️ Deleting VPK files...")
        for vpk_path in vpk_file_paths:
            vpk_file = Path(vpk_path)
            if vpk_file.exists():
                success = move_to_trash_or_delete(vpk_file)
                if success:
                    print(f"  ✅ {vpk_file.name} moved to trash")
                else:
                    print(f"  ❌ Failed to delete {vpk_file.name}")

    thread = threading.Thread(target=delete_files, daemon=True)
    thread.start()

def extract_vpk_files(vpk_files, work_dir):
    import gc
    
    print(f"🔎 Found VPK files to unpack: {len(vpk_files)}")
    vpk_file_paths = [str(vpk_file) for vpk_file in vpk_files]

    for vpk_file in vpk_files:
        print(f"\n📂 Unpacking: {vpk_file.name}")
        try:
            with vpk.open(str(vpk_file)) as vpk_archive:
                file_count = 0
                for file_path in vpk_archive:
                    try:
                        file_data = vpk_archive.get_file(file_path)
                        full_path = work_dir / file_path
                        full_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(full_path, "wb") as f:
                            f.write(file_data.read())
                        file_count += 1
                        print(f"  ✅ {file_path}")
                    except Exception as e:
                        print(f"  ❌ Extraction error {file_path}: {e}")
                print(f"  📂 Extracted {file_count} files from {vpk_file.name}")
        except Exception as e:
            print(f"❌ Unpacking error {vpk_file.name}: {e}")
    
    gc.collect()
    delayed_delete_vpk_files(vpk_file_paths, delay=2)

def compile_to_vpk(items_to_compile, work_dir):
    print(f"📦 Compiling {len(items_to_compile)} items to VPK...")
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            compile_dir = temp_path / "pak20_dir"
            compile_dir.mkdir()

            for item in items_to_compile:
                destination = compile_dir / item.name
                if item.is_dir():
                    shutil.copytree(str(item), str(destination))
                    print(f"  ✅ Added directory: {item.name}")
                else:
                    shutil.copy2(str(item), str(destination))
                    print(f"  ✅ Added file: {item.name}")

            output_path = work_dir / "pak20_dir.vpk"
            print(f"\n💾 Saving VPK to: {output_path.name}")
            newpak = vpk.new(str(output_path))
            newpak.read_dir(str(compile_dir))
            newpak.save(str(output_path))
            print(f"✅ VPK compilation complete!")

        print("\n🗑️ Deleting source files...")
        for item in items_to_compile:
            move_to_trash_or_delete(item)

    except Exception as e:
        print(f"❌ Compilation error: {e}")
        raise

def main():
    print_ascii_art()

    if not VPK_AVAILABLE:
        print("⚠️ Error: vpk module is not installed!")
        print("👀 Try: pip install vpk")
        sys.exit(1)

    work_dir = Path.cwd()
    exe_name = Path(sys.argv[0]).name
    protected_files = {exe_name}

    try:
        vpk_files = []
        other_items = []

        for item in work_dir.iterdir():
            if item.name not in protected_files:
                if item.is_file() and item.name.endswith(".vpk"):
                    vpk_files.append(item)
                else:
                    other_items.append(item)

        if vpk_files:
            print("📦 VPK files detected, unpacking...")
            time.sleep(1)
            extract_vpk_files(vpk_files, work_dir)
        elif other_items:
            print("📁 Files detected, compiling to VPK...")
            time.sleep(1)
            compile_to_vpk(other_items, work_dir)
        else:
            print("ℹ️ No VPK files or other files found.")
            sys.exit(0)

        if vpk_files:
            time.sleep(3)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()