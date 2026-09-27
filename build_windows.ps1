$ErrorActionPreference = "Stop"

if ($env:OS -ne "Windows_NT") {
    throw "Build the Windows app on Windows."
}

Push-Location $PSScriptRoot
try {
    py -3.14 -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        throw "Could not create the Python 3.14 virtual environment."
    }

    $python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
    & $python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        throw "Could not install the build requirements."
    }

    & $python -m PyInstaller --noconfirm --clean --onefile --windowed --name "ClearCopy PDF" --icon assets\clearcopy_icon.ico --add-data "assets\clearcopy_icon.png;assets" pdf_copy_app.py
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller could not build the Windows app."
    }
}
finally {
    Pop-Location
}