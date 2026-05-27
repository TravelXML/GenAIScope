from genaiscope.files import FileMemory

files = FileMemory()
files.add_file("README.md")
print(files.search("installation"))
