from pathlib import Path
from django.db import models
from django.core.files.storage import FileSystemStorage
from django.core.files.base import File
import yaml

class TestbedFiles(models.Model):
    file_storage = FileSystemStorage()
    file = models.FileField(blank=True, upload_to='testbeds/', storage = file_storage)

    def save_file(self, name,testbed):
        base_dir = Path(__file__).resolve().parent
        print(base_dir)
        with open(testbed) as f:
            self.file.save(name, File(f))
            #yaml.dump(testbed, f, sort_keys=False, default_flow_style=False)
# Create your models here.
