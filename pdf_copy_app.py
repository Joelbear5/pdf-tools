from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from uuid import uuid4

import pikepdf


def next_output_path(source: Path) -> Path:
    candidate = source.with_name(f"{source.stem}_unprotected.pdf")
    suffix = 2
    while candidate.exists():
        candidate = source.with_name(f"{source.stem}_unprotected ({suffix}).pdf")
        suffix += 1
    return candidate


def create_unprotected_copy(source: Path) -> Path:
    source = Path(source)
    output = next_output_path(source)
    temporary = source.with_name(f".{source.stem}_{uuid4().hex}.tmp")
    try:
        with pikepdf.open(source) as pdf:
            pdf.save(temporary, encryption=False)
        output = next_output_path(source)
        temporary.replace(output)
        return output
    finally:
        temporary.unlink(missing_ok=True)


class PDFCopyApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("PDF Copy")
        self.root.minsize(620, 400)
        self.results: queue.Queue[tuple[list[Path], list[tuple[Path, str]]]] = queue.Queue()

        self.files = tk.Listbox(root, selectmode=tk.EXTENDED, activestyle="none")
        self.files.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=16, pady=(16, 8))

        scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=self.files.yview)
        scrollbar.grid(row=0, column=4, sticky="ns", pady=(16, 8), padx=(0, 16))
        self.files.configure(yscrollcommand=scrollbar.set)

        self.add_button = ttk.Button(root, text="Add PDFs...", command=self.add_files)
        self.add_button.grid(row=1, column=0, sticky="w", padx=(16, 4), pady=4)
        self.remove_button = ttk.Button(root, text="Remove selected", command=self.remove_selected)
        self.remove_button.grid(row=1, column=1, sticky="w", padx=4, pady=4)
        self.clear_button = ttk.Button(root, text="Clear list", command=self.clear_files)
        self.clear_button.grid(row=1, column=2, sticky="w", padx=4, pady=4)
        self.create_button = ttk.Button(root, text="Create copies", command=self.start_processing)
        self.create_button.grid(row=1, column=3, sticky="e", padx=(4, 16), pady=4)

        self.status = tk.StringVar(value="Select PDFs to create unrestricted copies beside the originals.")
        ttk.Label(root, textvariable=self.status, anchor="w", wraplength=570).grid(
            row=2, column=0, columnspan=5, sticky="ew", padx=16, pady=(8, 16)
        )
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=1)
        root.columnconfigure(2, weight=1)
        root.columnconfigure(3, weight=1)
        root.rowconfigure(0, weight=1)

    def add_files(self) -> None:
        selected = filedialog.askopenfilenames(
            title="Choose PDF files",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        existing = {str(Path(self.files.get(index)).resolve()) for index in range(self.files.size())}
        for filename in selected:
            path = str(Path(filename).resolve())
            if path not in existing:
                self.files.insert(tk.END, path)
                existing.add(path)
        if selected:
            self.status.set(f"{self.files.size()} PDF file(s) selected.")

    def remove_selected(self) -> None:
        for index in reversed(self.files.curselection()):
            self.files.delete(index)

    def clear_files(self) -> None:
        self.files.delete(0, tk.END)
        self.status.set("File list cleared.")

    def start_processing(self) -> None:
        sources = [Path(self.files.get(index)) for index in range(self.files.size())]
        if not sources:
            messagebox.showinfo("No PDFs selected", "Add one or more PDF files first.", parent=self.root)
            return
        if not messagebox.askokcancel(
            "Create unrestricted copies?",
            "Creating copies rewrites the PDFs and may invalidate digital signatures or certification. Original files will not be changed.",
            parent=self.root,
        ):
            return

        for button in (self.add_button, self.remove_button, self.clear_button, self.create_button):
            button.configure(state=tk.DISABLED)
        self.status.set("Creating copies...")
        threading.Thread(target=self._process_files, args=(sources,), daemon=True).start()
        self.root.after(100, self._check_results)

    def _process_files(self, sources: list[Path]) -> None:
        created: list[Path] = []
        failed: list[tuple[Path, str]] = []
        for source in sources:
            try:
                created.append(create_unprotected_copy(source))
            except Exception as error:
                failed.append((source, str(error) or error.__class__.__name__))
        self.results.put((created, failed))

    def _check_results(self) -> None:
        try:
            created, failed = self.results.get_nowait()
        except queue.Empty:
            self.root.after(100, self._check_results)
            return

        for button in (self.add_button, self.remove_button, self.clear_button, self.create_button):
            button.configure(state=tk.NORMAL)
        self.status.set(f"Created {len(created)} copy/copies. {len(failed)} file(s) could not be processed.")

        if failed:
            details = "\n".join(f"{source.name}: {error}" for source, error in failed)
            messagebox.showwarning(
                "Some files were not processed",
                f"Created {len(created)} copy/copies. Files that need a password or could not be read were skipped.\n\n{details}",
                parent=self.root,
            )
        else:
            messagebox.showinfo(
                "Copies created",
                f"Created {len(created)} unrestricted PDF copy/copies beside the original files.",
                parent=self.root,
            )


def main() -> None:
    root = tk.Tk()
    PDFCopyApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()