from pathlib import Path
from django.db import models
from django.core.files.storage import FileSystemStorage
from django.core.files.base import File


class TestbedFiles(models.Model):
    file_storage = FileSystemStorage()
    file = models.FileField(blank=True, upload_to='testbeds/', storage = file_storage)

    def save_file(self, name):
        base_dir = Path(__file__).resolve().parent
        with open(base_dir / "testbed-file.yaml") as f:
            self.file.save(name, File(f))

# Create your models here.
