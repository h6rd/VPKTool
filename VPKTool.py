import sys
import re
import tempfile
import shutil
import gc
import os
import time
import threading
import random
import vpk
from rich.console import Console
from rich.text import Text
from pathlib import Path

if getattr(sys, 'frozen', False):
    exe_dir = os.path.dirname(sys.executable)
else:
    exe_dir = os.path.dirname(os.path.abspath(__file__))

console = Console()

def supports_unicode():
    try:
        '✓'.encode(sys.stdout.encoding or 'utf-8')
        return True
    except (UnicodeEncodeError, AttributeError):
        return False
USE_UNICODE = supports_unicode()

if USE_UNICODE:
    SYMBOLS = {
        'check': '✅',
        'cross': '❌',
        'trash': '🗑️',
        'folder': '📂',
        'package': '📦',
        'save': '💾',
        'search': '🔎',
        'info': 'ℹ️'
    }
else:
    SYMBOLS = {
        'check': '[OK]',
        'cross': '[ERROR]',
        'trash': '[DELETE]',
        'folder': '[FOLDER]',
        'package': '[PACK]',
        'save': '[SAVE]',
        'search': '[SEARCH]',
        'info': '[INFO]'
    }

def print_ascii_art():
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

SPLIT_PART_RE = re.compile(r'^(.+)_(\d{3})\.vpk$', re.IGNORECASE)
GARBAGE_SUFFIX_RE = re.compile(r'[^a-zA-Z0-9]$')

def is_split_part_file(item):
    m = SPLIT_PART_RE.match(item.name)
    if not m:
        return False
    return not item.name.lower().endswith('_dir.vpk')

def find_split_parts(dir_vpk_path):
    m = re.match(r'^(.+)_dir\.vpk$', dir_vpk_path.name, re.IGNORECASE)
    if not m:
        return []
    base = m.group(1)
    part_re = re.compile(r'^' + re.escape(base) + r'_(\d{3})\.vpk$', re.IGNORECASE)
    return [p for p in dir_vpk_path.parent.iterdir() if p.is_file() and part_re.match(p.name)]

def cleanup_garbage_files(work_dir):
    for root, dirs, files in os.walk(work_dir):
        for name in files:
            if GARBAGE_SUFFIX_RE.search(name):
                file_path = Path(root) / name
                move_to_trash_or_delete(file_path)

def move_to_trash_or_delete(item_path):
    try:
        if item_path.is_dir():
            shutil.rmtree(item_path)
        else:
            item_path.unlink()
        return True
    except Exception:
        return False

def delayed_delete_vpk_files(vpk_file_paths, delay=2):
    def delete_files():
        time.sleep(delay)
        print(f"\n{SYMBOLS['trash']} Deleting VPK files...")
        for vpk_path in vpk_file_paths:
            vpk_file = Path(vpk_path)
            if vpk_file.exists():
                success = move_to_trash_or_delete(vpk_file)
                if success:
                    print(f"  {SYMBOLS['check']} {vpk_file.name} moved to trash")
                else:
                    print(f"  {SYMBOLS['cross']} Failed to delete {vpk_file.name}")
    thread = threading.Thread(target=delete_files, daemon=True)
    thread.start()

def extract_vpk_files(vpk_files, work_dir):
    print(f"{SYMBOLS['search']} Found VPK files to unpack: {len(vpk_files)}")
    vpk_file_paths = [str(vpk_file) for vpk_file in vpk_files]
    for vpk_file in vpk_files:
        vpk_file_paths.extend(str(p) for p in find_split_parts(vpk_file))
    for vpk_file in vpk_files:
        print(f"\n{SYMBOLS['folder']} Unpacking: {vpk_file.name}")
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
                        print(f"  {SYMBOLS['check']} {file_path}")
                    except Exception:
                        pass
                print(f"  {SYMBOLS['folder']} Extracted {file_count} files from {vpk_file.name}")
        except Exception as e:
            print(f"{SYMBOLS['cross']} Unpacking error {vpk_file.name}: {e}")

    cleanup_garbage_files(work_dir)
    gc.collect()
    delayed_delete_vpk_files(vpk_file_paths, delay=2)

def compile_to_vpk(items_to_compile, work_dir):
    items_to_compile = [item for item in items_to_compile if not GARBAGE_SUFFIX_RE.search(item.name)]
    print(f"{SYMBOLS['package']} Compiling {len(items_to_compile)} items to VPK...")
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            BLACKLISTED_NUMS = {66}
            random_num = random.randint(9, 99)
            while random_num in BLACKLISTED_NUMS:
                random_num = random.randint(9, 99)
            compile_dir = temp_path / f"pak{random_num:02d}_dir"
            compile_dir.mkdir()

            for item in items_to_compile:
                destination = compile_dir / item.name
                if item.is_dir():
                    shutil.copytree(str(item), str(destination))
                    cleanup_garbage_files(destination)
                    print(f"  {SYMBOLS['check']} Added directory: {item.name}")
                else:
                    shutil.copy2(str(item), str(destination))
                    print(f"  {SYMBOLS['check']} Added file: {item.name}")

            output_path = work_dir / f"pak{random_num:02d}_dir.vpk"
            print(f"\n{SYMBOLS['save']} Saving VPK to: {output_path.name}")
            newpak = vpk.new(str(output_path))
            newpak.read_dir(str(compile_dir))
            newpak.save(str(output_path))
            print(f"{SYMBOLS['check']} VPK compilation complete!")

        print(f"\n{SYMBOLS['trash']} Deleting source files...")
        for item in items_to_compile:
            success = move_to_trash_or_delete(item)
            if success:
                print(f"  {SYMBOLS['check']} Moved to trash: {item.name}")
            else:
                print(f"  {SYMBOLS['cross']} Failed to delete: {item.name}")

    except Exception as e:
        print(f"{SYMBOLS['cross']} Compilation error: {e}")
        raise

def main():
    print_ascii_art()
    work_dir = Path.cwd()
    exe_name = Path(sys.argv[0]).name
    protected_files = {exe_name}
    
    try:
        vpk_files = []
        other_items = []
        for item in work_dir.iterdir():
            if item.name not in protected_files:
                if item.is_file() and item.name.endswith(".vpk"):
                    if is_split_part_file(item):
                        continue
                    vpk_files.append(item)
                else:
                    other_items.append(item)
        if vpk_files:
            print(f"{SYMBOLS['package']} VPK files detected, unpacking...")
            time.sleep(2)
            extract_vpk_files(vpk_files, work_dir)
        elif other_items:
            print(f"{SYMBOLS['folder']} Files detected, compiling to VPK...")
            time.sleep(2)
            compile_to_vpk(other_items, work_dir)
        else:
            print(f"{SYMBOLS['info']} No VPK files or other files found.")
            time.sleep(2)
            sys.exit(0)
        if vpk_files:
            time.sleep(3)

    except Exception as e:
        print(f"{SYMBOLS['cross']} Error: {e}")
        time.sleep(5)
        sys.exit(1)

if __name__ == "__main__":
    main()