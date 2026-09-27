# ClearCopy PDF

ClearCopy PDF is a small desktop app for creating unrestricted copies of PDFs that open without a password. It never changes the selected originals. Each output is written beside its source as `<filename>_unprotected.pdf`; if that name already exists, a numbered name is used instead.

The file list shows whether each PDF is unrestricted, permission-protected, or requires an open password. Unrestricted files start unchecked, while permission-protected files start checked. To convert a PDF that requires an open password, check its Convert box and enter the password when prompted. Passwords are held in memory only while the app is open.

Rewriting a PDF may invalidate its digital signatures or certification. The app warns before processing and does not modify the originals.

## Run from source

Create a Python 3.14 environment, install the dependencies, and start the window:

```sh
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python pdf_copy_app.py
```

On Windows, activate with `.venv\Scripts\Activate.ps1` and run `python pdf_copy_app.py`.

## Build for Apple Silicon macOS

Build on an Apple Silicon Mac. PyInstaller does not cross-build a macOS app from Windows. Install Python 3.14 for macOS, then run:

```sh
sh build_macos.sh
```

The app bundle will be `dist/ClearCopy PDF.app`. Replace `org.example.clearcopypdf` in `build_macos.sh` with an identifier owned by your organization before distributing it. For distribution to other Macs, sign and notarize the app with your organization's Apple Developer ID.

## Build for Windows

Build on Windows with Python 3.14 available through the `py` launcher:

```powershell
.\build_windows.ps1
```

If PowerShell blocks the script, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal first. This affects only the current PowerShell process.

The standalone windowed executable will be `dist\ClearCopy PDF.exe`.

## Tests

```sh
python -m unittest discover -s tests -v
```