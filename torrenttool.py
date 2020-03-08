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


def convert_byte_size(byte_size):
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(byte_size, 1024)))
    p = math.pow(1024, i)
    s = round(byte_size / p, 2)
    return "{0} {1}".format(s, size_name[i])


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
    size = convert_byte_size(size_bytes)

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
        "format_name": container["format_long_name"],
        "video_bitrate": str(video_stream["bit_rate"]),
        "audio_codec": audio_stream["codec_name"],
        "audio_sample_rate": str(audio_stream["sample_rate"]),
        "audio_channels": str(audio_stream["channels"]),
        "audio_channel_layout": audio_stream["channel_layout"],
        "audio_bitrate": str(audio_stream["bit_rate"])
    }

    return info_dict


def get_videos(target):
    # Create a video path list
    paths = []
    result = check_output(["find {0} -type f -name '*.mp4'".format(escape(target)), ], shell=True)
    lines = result.splitlines()
    for line in lines:
        paths.append(str(line).strip("b").strip("'"))
    return paths


def remove_folder(target):
    call('/bin/bash -c "$CMD"', shell=True,
         env={"CMD": "find {0} -type d -name Metadata -exec rm -rf {{}} \\;".format(target)})


# Remove Metadata folders
print("Removing 'Metadata' folder")
remove_folder(target_path)

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

# Make screenshots
print("Making screenshots")

screens_folder = Path(output_folder, "Screens", target_name)
if not screens_folder.is_dir():
    screens_folder.mkdir(parents=True)

info_list = []

for video_path in get_videos(target_path):
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

        file_info = get_file_info(video_path)
        file_info.update({"url": image_url,
                          "screenshot_url": screenshot_url})
        info_list.append(file_info)

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
        string = "{0}{1}{2}{3}{4}{5}{6}{7}{8}{9}{10}{11}{12}{13}".format(
            "filename: " + file_info["filename"] + linesep,
            "size: " + file_info["size"] + linesep,
            "length: " + file_info["length"] + linesep,
            "format: " + file_info["format_name"] + linesep,
            "video codec: " + file_info["video_codec"] + linesep,
            "resolution: " + file_info["resolution"] + linesep,
            "FPS: " + file_info["fps"] + linesep,
            "video bit rate: " + file_info["video_bitrate"] + linesep,
            "audio codec: " + file_info["audio_codec"] + linesep,
            "audio sample rate: " + file_info["audio_sample_rate"] + linesep,
            "audio channels: " + file_info["audio_channels"] + linesep,
            "audio channel layout: " + file_info["audio_channel_layout"] + linesep,
            "audio bit rate: " + file_info["audio_bitrate"] + linesep,
            linesep
        )
        file.write(string)

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
