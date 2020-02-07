from os import getenv, system
from pathlib import Path
from torf import Torrent

input_folder = getenv("INPUT")
output_folder = getenv("OUTPUT")

# Remove Metadata folders
print("Removing 'Metadata' folder")
cmd = "find {0} -type d -name Metadata -exec rm -rf {{}} \\;".format(target_path)
system(cmd)

# Create torrents
print("Creating torrent")
target_path = Path(input_folder)
torrent_file = Path(output_folder, "{0}.torrent".format(target_path.stem))
if not torrent_file.is_file():
    t = Torrent(path=target_path, trackers=[], comment="")
    t.private = False
    t.generate()
    t.write(torrent_file)	
else:
	print("{0} is already present. Skipping!".format(torrent_file))
