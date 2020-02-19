import json
import math
from os import getenv, linesep
from pathlib import Path
from subprocess import TimeoutExpired, call, check_output

from torf import Torrent

input_folder = getenv("INPUT")
output_folder = getenv("OUTPUT")
target_path = Path(input_folder)
target_name = target_path.stem


def escape(path):
    return str(path).replace(" ", "\\ ")


def upload_pic(path):
    _cmd = "imgupload -s fastpic.ru -cl plain " + escape(path)
    _res = check_output([_cmd, ], shell=True, timeout=300)
    url = str(_res).strip("b").strip("'")
    return url


def make_spoiler(source, target):
    if not target.is_file():
        sjabloon = Path("/", "sjabloon")
        font = "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"
        roster_cmd = "vcsi {0} -t -w 1200 -g 4x4 --end-delay-percent 5 --timestamp-font {1} --template {2} -o {3}".format(
            escape(source), font, sjabloon, escape(target))
        call('/bin/bash -c "$CMD" > /dev/null 2>&1', shell=True, env={"CMD": roster_cmd})


def make_screenshot(source, target):
    if not target.is_file():
        sub_cmd = "\"$(bc -l <<< \"$(ffprobe -loglevel error -of csv=p=0 -show_entries format=duration \"$input\")*0.5\")\""
        screenshot_cmd = "input={0}; ffmpeg -ss {1} -i \"$input\" -frames:v 1 {2}".format(
            escape(source), sub_cmd, escape(target))
        call('/bin/bash -c "$CMD"', shell=True, env={"CMD": screenshot_cmd})


def get_file_info(video_file):
    # get file info json
    _cmd = "ffprobe -v quiet -print_format json -show_format -show_streams {0}".format(escape(video_file))
    json_info = check_output(_cmd, shell=True)
    json_file_info = json.loads(json_info)
    video_stream = json_file_info["streams"][0]
    audio_stream = json_file_info["streams"][1]
    container = json_file_info["format"]

    # get size
    size_bytes = int(container["size"])
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    size = "{0} {1}".format(s, size_name[i])

    # get fps
    avg_frame_rate = video_stream["avg_frame_rate"]
    a, b = avg_frame_rate.split("/")
    fps = str(round(int(a) / int(b)))

    info_dict = {
        "filename": video_file_name,
        "length": "{0} S".format(container["duration"]),
        "resolution": "{0}x{1}".format(video_stream["width"], video_stream["height"]),
        "size": size,
        "video_codec": video_stream["codec_name"],
        "fps": fps,
        "url": image_url,
        "screenshot_url": screenshot_url,
        "format_name": container["format_long_name"],
        "video_bitrate": str(video_stream["bit_rate"]),
        "audio_codec": audio_stream["codec_name"],
        "audio_sample_rate": str(audio_stream["sample_rate"]),
        "audio_channels": str(audio_stream["channels"]),
        "audio_channel_layout": audio_stream["channel_layout"],
        "audio_bitrate": str(audio_stream["bit_rate"])
    }

    return info_dict


# Remove Metadata folders
print("Removing 'Metadata' folder")
cmd = "find {0} -type d -name Metadata -exec rm -rf {{}} \\;".format(target_path)
call('/bin/bash -c "$CMD"', shell=True, env={"CMD": cmd})

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

    screenshot_file_name = video_file_name.strip(".mp4") + "_screenshot.jpg"
    screenshot_path = Path(screens_folder, screenshot_file_name)

    try:
        # take a preview roster pic
        make_spoiler(video_path, screen_path)

        # take a screenshot
        make_screenshot(video_path, screenshot_path)

        # upload roster and get url
        image_url = upload_pic(screen_path)
        # upload screenshot and get url
        screenshot_url = upload_pic(screenshot_path)

        info_list.append(get_file_info(video_path))

    except Exception as e:
        print(e)
        if e is TimeoutExpired:
            break
        continue

# write file
print("Writing file")
output_file = Path(output_folder, "{0}.txt".format(target_name))
with open(output_file, "a") as file:
    file.write("[spoiler=\"fileinfo\"]" + linesep)

    for file_info in info_list:
        file.write("filename: " + file_info["filename"] + linesep)
        file.write("size: " + file_info["size"] + linesep)
        file.write("length: " + file_info["length"] + linesep)
        file.write("format: " + file_info["format_name"] + linesep)

        file.write("video codec: " + file_info["video_codec"] + linesep)
        file.write("resolution: " + file_info["resolution"] + linesep)
        file.write("FPS: " + file_info["fps"] + linesep)
        file.write("video bit rate: " + file_info["video_bitrate"] + linesep)

        file.write("audio codec: " + file_info["audio_codec"] + linesep)
        file.write("audio sample rate: " + file_info["audio_sample_rate"] + linesep)
        file.write("audio channels: " + file_info["audio_channels"] + linesep)
        file.write("audio channel layout: " + file_info["audio_channel_layout"] + linesep)
        file.write("audio bit rate: " + file_info["audio_bitrate"] + linesep)
        file.write(linesep)

    file.write("[/spoiler]" + linesep)
    file.write("[spoiler=\"pictures\"]" + linesep)

    for file_info in info_list:
        file.write("[spoiler=\"{0} | {1} | {2} | {3}\"]".format(
            file_info["filename"],
            file_info["length"],
            file_info["size"],
            file_info["resolution"]
        ) + linesep)

        file.write("[img]{0}[/img]".format(file_info["url"]) + linesep)
        file.write("[img]{0}[/img]".format(file_info["screenshot_url"]) + linesep)

        file.write("[/spoiler]" + linesep)

    file.write("[/spoiler]" + linesep)
