#! /bin/bash

# check for args
if [ $# -eq 0 ]; then
    echo "Usage: run.sh <input folder> <output folder>"
    exit 1
fi

input_folder=$1  # arg1 is input folder
output_folder=$2 # arg2 is where torrent / photo files get placed
# folder where this script is
project_location="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# build image if it does not exist
if [[ "$(docker images -q philipwold/torrent-tool 2> /dev/null)" == "" ]]; then
	docker build -t philipwold/torrent-tool -f ${project_location}/Dockerfile ${project_location}
fi

docker run -it --rm \
	   -e INPUT=${input_folder} -e OUTPUT=${output_folder} \
	   -v ${input_folder}:${input_folder} -v ${output_folder}:${output_folder} \
	   philipwold/torrent-tool
