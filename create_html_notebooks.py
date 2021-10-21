import os

files = os.popen("git diff-index --name-only --cached HEAD").read()
for f in files.split("\n"):
    if 'todo' not in f:
        if f.endswith('ipynb'):
            os.system("jupyter nbconvert --to html " + f)
