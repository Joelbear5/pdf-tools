from __future__ import annotations

import queue
import sys
import threading
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from uuid import uuid4

import pikepdf


def resource_path(filename: str) -> Path:
    bundle_directory = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return bundle_directory / filename


@dataclass
class PDFEntry:
    path: Path
    protection: str
    convert: bool
    password: str | None = None


def next_output_path(source: Path) -> Path:
    candidate = source.with_name(f"{source.stem}_unprotected.pdf")
    suffix = 2
    while candidate.exists():
        candidate = source.with_name(f"{source.stem}_unprotected ({suffix}).pdf")
        suffix += 1
    return candidate


def inspect_pdf(source: Path) -> str:
    try:
        with pikepdf.open(source) as pdf:
            return "protected" if pdf.is_encrypted else "unprotected"
    except pikepdf.PasswordError:
        return "view_restricted"


def create_unprotected_copy(source: Path, password: str | None = None) -> Path:
    source = Path(source)
    output = next_output_path(source)
    temporary = source.with_name(f".{source.stem}_{uuid4().hex}.tmp")
    try:
        with pikepdf.open(source, password=password or "") as pdf:
            pdf.save(temporary, encryption=False)
        output = next_output_path(source)
        temporary.replace(output)
        return output
    finally:
        temporary.unlink(missing_ok=True)


class PDFCopyApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("ClearCopy PDF")
        icon = tk.PhotoImage(file=str(resource_path("assets/clearcopy_icon.png")))
        self.icon_images = [icon.subsample(8, 8), icon.subsample(4, 4), icon.subsample(2, 2), icon]
        self.root.iconphoto(True, *self.icon_images)
        self.root.minsize(760, 420)
        self.results: queue.Queue[tuple[list[Path], list[tuple[Path, str]]]] = queue.Queue()
        self.entries: dict[str, PDFEntry] = {}

        self.files = ttk.Treeview(
            root,
            columns=("file", "convert"),
            show=("tree", "headings"),
            selectmode="extended",
        )
        self.files.heading("#0", text="Protection")
        self.files.heading("file", text="PDF file")
        self.files.heading("convert", text="Convert")
        self.files.column("#0", width=170, minwidth=150, stretch=False)
        self.files.column("file", width=480, minwidth=240, stretch=True)
        self.files.column("convert", width=90, minwidth=90, stretch=False, anchor="center")
        self.files.tag_configure("unavailable", foreground="#888888")
        self.files.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=(16, 0), pady=(16, 8))
        self.files.bind("<Button-1>", self._on_file_click)
        self.files.bind("<space>", self._on_file_space)

        scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=self.files.yview)
        scrollbar.grid(row=0, column=4, sticky="ns", pady=(16, 8), padx=(0, 16))
        self.files.configure(yscrollcommand=scrollbar.set)

        self.add_button = ttk.Button(root, text="Add PDFs...", command=self.add_files)
        self.add_button.grid(row=1, column=0, sticky="w", padx=(16, 4), pady=4)
        self.remove_button = ttk.Button(root, text="Remove selected", command=self.remove_selected)
        self.remove_button.grid(row=1, column=1, sticky="w", padx=4, pady=4)
        self.clear_button = ttk.Button(root, text="Clear list", command=self.clear_files)
        self.clear_button.grid(row=1, column=2, sticky="w", padx=4, pady=4)
        self.create_button = ttk.Button(root, text="Create selected copies", command=self.start_processing)
        self.create_button.grid(row=1, column=3, sticky="e", padx=(4, 16), pady=4)

        self.status = tk.StringVar(value="Add PDFs, then choose which files to convert.")
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
        existing = {str(entry.path.resolve()) for entry in self.entries.values()}
        for filename in selected:
            path = Path(filename).resolve()
            if str(path) in existing:
                continue
            try:
                protection = inspect_pdf(path)
            except Exception as exception:
                protection = "unreadable"
            convert = protection == "protected"
            entry = PDFEntry(path, protection, convert)
            self._insert_entry(entry)
            existing.add(str(path))
        if selected:
            self.status.set(f"{len(self.entries)} PDF file(s) in the conversion list.")

    def _insert_entry(self, entry: PDFEntry) -> None:
        labels = {
            "unprotected": "Unprotected",
            "protected": "🟩🔒 Protected",
            "view_restricted": "🟥👁 View restricted",
            "unreadable": "Unreadable",
        }
        tags = ("unavailable",) if entry.protection == "unreadable" or (
            entry.protection == "view_restricted" and entry.password is None
        ) else ()
        item = self.files.insert(
            "",
            tk.END,
            text=labels[entry.protection],
            values=(str(entry.path), "☑" if entry.convert else "☐"),
            tags=tags,
        )
        self.entries[item] = entry

    def _refresh_entry(self, item: str) -> None:
        entry = self.entries[item]
        tags = ("unavailable",) if entry.protection == "unreadable" or (
            entry.protection == "view_restricted" and entry.password is None
        ) else ()
        self.files.item(item, values=(str(entry.path), "☑" if entry.convert else "☐"), tags=tags)

    def _toggle_entry(self, item: str) -> None:
        entry = self.entries[item]
        if entry.protection == "unreadable":
            return
        if entry.protection == "view_restricted" and entry.password is None:
            password = simpledialog.askstring(
                "PDF password",
                f"Enter the open password for {entry.path.name}:",
                show="*",
                parent=self.root,
            )
            if password is None:
                return
            try:
                with pikepdf.open(entry.path, password=password) as pdf:
                    pdf.pages
            except pikepdf.PasswordError:
                messagebox.showerror("Incorrect password", "That password could not open this PDF.", parent=self.root)
                return
            entry.password = password
        entry.convert = not entry.convert
        self._refresh_entry(item)

    def _on_file_click(self, event: tk.Event) -> str | None:
        if self.files.identify_column(event.x) == "#2":
            item = self.files.identify_row(event.y)
            if item:
                self._toggle_entry(item)
                return "break"
        return None

    def _on_file_space(self, _event: tk.Event) -> str:
        item = self.files.focus()
        if item:
            self._toggle_entry(item)
        return "break"

    def remove_selected(self) -> None:
        for item in self.files.selection():
            self.files.delete(item)
            del self.entries[item]

    def clear_files(self) -> None:
        self.files.delete(*self.files.get_children())
        self.entries.clear()
        self.status.set("File list cleared.")

    def start_processing(self) -> None:
        sources = [(entry.path, entry.password) for entry in self.entries.values() if entry.convert]
        if not sources:
            messagebox.showinfo("No files selected", "Check Convert for one or more files first.", parent=self.root)
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

    def _process_files(self, sources: list[tuple[Path, str | None]]) -> None:
        created: list[Path] = []
        failed: list[tuple[Path, str]] = []
        for source, password in sources:
            try:
                created.append(create_unprotected_copy(source, password))
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