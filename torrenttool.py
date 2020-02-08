from os import getenv, system, linesep
from pathlib import Path
from torf import Torrent
from subprocess import check_output

input_folder = getenv("INPUT")
output_folder = getenv("OUTPUT")
target_path = Path(input_folder)
target_name = target_path.stem

# Remove Metadata folders
print("Removing 'Metadata' folder")
cmd = "find {0} -type d -name Metadata -exec rm -rf {{}} \\;".format(target_path)
system(cmd)

# Create torrents
print("Creating torrent")
torrent_file = Path(output_folder, "{0}.torrent".format(target_name))
if not torrent_file.is_file():
    t = Torrent(path=target_path, trackers=[], comment="")
    t.private = False
    t.generate()
    t.write(torrent_file)
else:
    print("{0} is already present. Skipping!".format(torrent_file))

# Create a video path list
video_paths = []
cmd = "find {0} -type f -name '*.mp4'".format(target_path)
res = check_output([cmd, ], shell=True)
lines = res.splitlines()
for line in lines:
    video_paths.append(str(line).strip("b").strip("'"))

# Make screenshots
print("Making screenshots")
screens_folder = Path(output_folder, "Screens", target_name)
if not screens_folder.is_dir():
    screens_folder.mkdir(parents=True)
for video_path in video_paths:
    video_file_name = video_path.split("/")[-1]
    file_name = video_file_name.strip(".mp4") + ".jpg"
    screen_path = Path(screens_folder, file_name)
    escaped_video_path = video_path.replace(" ", "\\ ")
    escaped_screen_path = str(screen_path).replace(" ", "\\ ")

    if not screen_path.is_file():
        sjabloon = Path("/", "sjabloon")
        font = "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"
        cmd = "vcsi {0} -t -w 1200 -g 4x4 --end-delay-percent 5 --timestamp-font {1} --template {2} -o {3}".format(
            escaped_video_path, font, sjabloon, escaped_screen_path)
        # print(cmd)
        system("{0} > /dev/null 2>&1".format(cmd))

    cmd = "imgupload -s fastpic.ru -cl plain " + escaped_screen_path
    res = check_output([cmd, ], shell=True, )
    image_url = str(res).strip("b").strip("'")
    cmd = "ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 " + escaped_video_path
    resolution = check_output([cmd, ], shell=True)
    cmd = "ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 " + escaped_video_path
    length = check_output([cmd, ], shell=True)
    cmd = "du -sh {0} | awk 'NR==1{{print $1}}'".format(escaped_video_path)
    size = check_output([cmd, ], shell=True)

    file_info = {
        "filename": video_file_name,
        "length": str(length).strip("b'").strip("\\\\n"),
        "resolution": str(resolution).strip("b'").strip("\\\\n"),
        "url": image_url.replace("view", ),
        "size": str(size).strip("b'").strip("\\\\n")
    }

    output_file = Path(output_folder, "{0}.txt".format(target_name))
    with open(output_file, "a") as file:
        file.write("[spoiler=\"{0} | {1} | {2} | 576x320\"]".format(
            file_info["filename"],
            file_info["length"],
            file_info["size"],
            file_info["resolution"]
        ) + linesep)
        file.write("[img]{0}[/img]".format(file_info["url"]) + linesep)
        file.write("[/spoiler]" + linesep)
