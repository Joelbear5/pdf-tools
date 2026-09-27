# PDF Copy

PDF Copy is a small desktop app for creating unrestricted copies of PDFs that open without a password. It never changes the selected originals. Each output is written beside its source as `<filename>_unprotected.pdf`; if that name already exists, a numbered name is used instead.

Files that require an open password are skipped and reported. The app does not ask for or store passwords.

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

The app bundle will be `dist/PDF Copy.app`. Replace `org.example.pdfcopy` in `build_macos.sh` with an identifier owned by your organization before distributing it. For distribution to other Macs, sign and notarize the app with your organization's Apple Developer ID.

## Tests

```sh
python -m unittest discover -s tests -v
```