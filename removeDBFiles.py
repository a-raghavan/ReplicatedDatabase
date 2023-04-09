import glob
import os
import shutil


files_to_delete = glob.glob('3000*')

# print(files_to_delete)

for file in files_to_delete:
    if os.path.isfile(file):
        os.remove(file)
    else:
        shutil.rmtree(file)