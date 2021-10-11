import subprocess
from loaders import *

options = load_options("options")

for i in range(10):
    options["CORE_NAME"] = str(i)
    options["FOLD_NUM"] = str(i)
    write_options("options-" + str(i), options)
    cmd = "python Pa-FeaturesSVM.py options-" + str(i)
    subprocess.call(cmd, shell=True)
