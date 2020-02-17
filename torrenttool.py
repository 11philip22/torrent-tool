import json
import math
from os import getenv, linesep, system
from pathlib import Path
from subprocess import call, check_output

from torf import Torrent

input_folder = getenv("INPUT")
output_folder = getenv("OUTPUT")
target_path = Path(input_folder)
target_name = target_path.stem


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

        # get fileinfo json
        cmd = "ffprobe -v quiet -print_format json -show_format -show_streams {0}".format(escaped_video_path)
        file_info = check_output(cmd, shell=True)
        json_file_info = json.loads(file_info)
        video_stream_info = json_file_info["streams"][0]
        audio_stream_info = json_file_info["streams"][1]
        file_format = json_file_info["format"]

        # get resolution
        resolution = "{0}x{1}".format(video_stream_info["width"], video_stream_info["height"])

        #  get length
        length = "{0} S".format(file_format["duration"])

        # get size
        size_bytes = int(file_format["size"])
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        size = "{0} {1}".format(s, size_name[i])

        # get video codec
        codec = video_stream_info["codec_name"]

        # get fps
        avg_frame_rate = video_stream_info["avg_frame_rate"]
        a, b = avg_frame_rate.split("/")
        fps = str(round(int(a) / int(b)))

    except Exception as e:
        print(e)
        continue

    file_info = {
        "filename": video_file_name,
        "length": length,
        "resolution": resolution,
        "size": size,
        "codec": codec,
        "fps": fps,
        "url": image_url,
        "screenshot_url": screenshot_url
    }
    info_list.append(file_info)

# write file
print("Writing file")
output_file = Path(output_folder, "{0}.txt".format(target_name))
with open(output_file, "a") as file:
    file.write("[spoiler=\"fileinfo\"]" + linesep)

    for file_info in info_list:
        file.write("filename: " + file_info["filename"] + linesep)
        file.write("size: " + file_info["size"] + linesep)
        file.write("codec: " + file_info["codec"] + linesep)
        file.write("resolution: " + file_info["resolution"] + linesep)
        file.write("length: " + file_info["length"] + linesep)
        file.write("FPS: " + file_info["fps"] + linesep)
        file.write(linesep)

    file.write("[/spoiler]" + linesep)
    file.write("[spoiler=\"pictures\"]" + linesep)

    for file_info in info_list:
        file.write("[spoiler=\"{0} | {1} | {2} | 576x320\"]".format(
            file_info["filename"],
            file_info["length"],
            file_info["size"],
            file_info["resolution"]
        ) + linesep)

        file.write("[img]{0}[/img]".format(file_info["url"]) + linesep)
        file.write("[img]{0}[/img]".format(file_info["screenshot_url"]) + linesep)

        file.write("[/spoiler]" + linesep)

    file.write("[/spoiler]" + linesep)
