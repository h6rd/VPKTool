# VPKTool

A tool for packaging and unpacking VPK archives. 

---

## Download
| Platform | Link |
|----------|------|
| Windows  | [VPKTool-Win.zip](https://github.com/h6rd/VPKTool/releases/latest/download/VPKTool-Win.zip) |
| Linux    | [VPKTool-Linux.zip](https://github.com/h6rd/VPKTool/releases/latest/download/VPKTool-Linux.zip) |

---

## Features

- **Auto-detection** — detects VPK files or loose files/folders and acts accordingly
- **Unpack mode** — extracts all contents from `.vpk` archives into the current directory
- **Pack mode** — compiles loose files and folders into a new `.vpk` archive

---

## Usage

Place the `.vpk` or `files/folders` in a folder next to the script and run it.

### Unpack mode
If the folder contains `.vpk` files, the tool will extract their contents into the current directory and then delete the original VPK files.

### Pack mode
If the folder contains loose files or directories (no `.vpk` files), the tool will compile everything into a new VPK archive and delete the originals.

Output will be a randomly named `pakXX_dir.vpk` file.

---

## Notes

- VPK output name is randomized (`pak09` – `pak99`) to avoid conflicts
- Source files are deleted automatically after a successful operation — make sure you have backups if needed

---
