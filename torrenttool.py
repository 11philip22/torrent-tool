from os import getenv, system, linesep
from pathlib import Path
from torf import Torrent
from subprocess import check_output, call

input_folder = getenv("INPUT")
output_folder = getenv("OUTPUT")
target_path = Path(input_folder)
target_name = target_path.stem


def byte_to_string(byte_arr):
    return str(byte_arr).strip("b'").strip("\\\\n")


def upload_pic(path):
    _cmd = "imgupload -s fastpic.ru -cl plain " + path
    _res = check_output([_cmd, ], shell=True, )
    url = str(_res).strip("b").strip("'")
    return url


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

info_list = []

for video_path in video_paths:
    print(video_path)

    video_file_name = video_path.split("/")[-1]
    file_name = video_file_name.strip(".mp4") + ".jpg"

    screen_path = Path(screens_folder, file_name)
    escaped_screen_path = str(screen_path).replace(" ", "\\ ")

    screenshot_file_name = video_file_name.strip(".mp4") + "_screenshot.jpg"
    screenshot_path = Path(screens_folder, screenshot_file_name)
    escaped_screenshot_path = str(screenshot_path).replace(" ", "\\ ")

    escaped_video_path = video_path.replace(" ", "\\ ")

    try:
        # take a preview roster pic
        if not screen_path.is_file():
            sjabloon = Path("/", "sjabloon")
            font = "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"
            cmd = "vcsi {0} -t -w 1200 -g 4x4 --end-delay-percent 5 --timestamp-font {1} --template {2} -o {3}".format(
                escaped_video_path, font, sjabloon, escaped_screen_path)
            system("{0} > /dev/null 2>&1".format(cmd))

        # take a screenshot
        if not screenshot_path.is_file():
            cmd = "input={0}; ffmpeg -ss \"$(bc -l <<< \"$(ffprobe -loglevel error -of csv=p=0 -show_entries format=duration \"$input\")*0.5\")\" -i \"$input\" -frames:v 1 {1}".format(
                escaped_video_path, escaped_screenshot_path)
            call('/bin/bash -c "$CMD"', shell=True, env={"CMD": cmd})

        # upload roster and get url
        image_url = upload_pic(escaped_screen_path)
        # upload screenshot and get url
        screenshot_url = upload_pic(escaped_screenshot_path)

        # get resolution
        cmd = "ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 " + escaped_video_path
        resolution = check_output([cmd, ], shell=True)

        # get length
        cmd = "ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 " + escaped_video_path
        length = check_output([cmd, ], shell=True)

        # get size
        cmd = "du -sh {0} | awk 'NR==1{{print $1}}'".format(escaped_video_path)
        size = check_output([cmd, ], shell=True)

        # get codec
        cmd = "ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 {0}".format(
            escaped_video_path
        )
        codec = check_output([cmd, ], shell=True)

        # get fps
        cmd = "ffprobe -v error -select_streams v -of default=noprint_wrappers=1:nokey=1 -show_entries stream=r_frame_rate {0}".format(
            escaped_video_path
        )
        res = check_output([cmd, ], shell=True)
        str_res = byte_to_string(res)
        a, b = str_res.split("/")
        fps = int(a) / int(b)

    except Exception as e:
        print(e)
        continue

    file_info = {
        "filename": video_file_name,
        "length": byte_to_string(length),
        "resolution": byte_to_string(resolution),
        "size": byte_to_string(size),
        "codec": byte_to_string(codec),
        "fps": str(fps),
        "url": image_url,
        "screenshot_url": screenshot_url
    }
    info_list.append(file_info)

output_file = Path(output_folder, "{0}.txt".format(target_name))
with open(output_file, "a") as file:
    file.write("[spoiler=\"fileinfo\"]" + linesep)

    for file_info in info_list:
        file.write("filename: " + file_info["filename"] + linesep)
        file.write("size: " + file_info["size"] + linesep)
        file.write("codec: " + file_info["codec"] + linesep)
        file.write("resolution: " + file_info["resolution"] + linesep)
        file.write("length: " + file_info["length"] + " S" + linesep)
        file.write("FPS: " + file_info["fps"] + linesep)
        file.write(linesep)

    file.write("[/spoiler]" + linesep)
    file.write("[spoiler=\"pictures\"]" + linesep)

    for file_info in info_list:
        file.write("[spoiler=\"{0} | {1} S | {2} | 576x320\"]".format(
            file_info["filename"],
            file_info["length"],
            file_info["size"],
            file_info["resolution"]
        ) + linesep)

        file.write("[img]{0}[/img]".format(file_info["url"]) + linesep)
        file.write("[img]{0}[/img]".format(file_info["screenshot_url"]) + linesep)

        file.write("[/spoiler]" + linesep)

    file.write("[/spoiler]" + linesep)
