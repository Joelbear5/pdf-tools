import tempfile
import unittest
from pathlib import Path

import pikepdf

from pdf_copy_app import create_unprotected_copy


class CreateUnprotectedCopyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp_dir.name)
        self.source = self.directory / "restricted.pdf"
        pdf = pikepdf.new()
        pdf.add_blank_page()
        pdf.save(
            self.source,
            encryption=pikepdf.Encryption(
                owner="owner-secret",
                user="",
                R=6,
                allow=pikepdf.Permissions(extract=False, modify_other=False),
            ),
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_creates_unencrypted_copy_and_preserves_source(self) -> None:
        output = create_unprotected_copy(self.source)

        self.assertEqual(output.name, "restricted_unprotected.pdf")
        with pikepdf.open(self.source) as source:
            self.assertTrue(source.is_encrypted)
            self.assertEqual(len(source.pages), 1)
        with pikepdf.open(output) as copy:
            self.assertFalse(copy.is_encrypted)
            self.assertEqual(len(copy.pages), 1)

    def test_uses_a_new_name_instead_of_overwriting_existing_copy(self) -> None:
        first = create_unprotected_copy(self.source)
        second = create_unprotected_copy(self.source)

        self.assertEqual(first.name, "restricted_unprotected.pdf")
        self.assertEqual(second.name, "restricted_unprotected (2).pdf")

    def test_skips_file_that_requires_open_password(self) -> None:
        password_protected = self.directory / "password-protected.pdf"
        pdf = pikepdf.new()
        pdf.add_blank_page()
        pdf.save(
            password_protected,
            encryption=pikepdf.Encryption(owner="owner-secret", user="open-secret", R=6),
        )

        with self.assertRaises(pikepdf.PasswordError):
            create_unprotected_copy(password_protected)


if __name__ == "__main__":
    unittest.main()