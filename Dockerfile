FROM ubuntu:eoan

RUN useradd -s /bin/bash -d /home/user/ -m -u 1000 user

# add imguploader
ADD https://bintray.com/zenden/zenden-image-uploader/download_file?file_path=imgupload_0.2.8_amd64.deb /imgupload_0.2.8_amd64.deb
# imguploader dependancies
RUN apt-get update && apt-get install -y --no-install-recommends \
	libc6 \
	libpcre3 \
	libc-ares2 \
	libsqlite3-0 \
	libfreeimage3
# install imguploader package
RUN dpkg -i imgupload_0.2.8_amd64.deb \
	&& rm /imgupload_0.2.8_amd64.deb

# other deps
RUN apt-get install -y --no-install-recommends ffmpeg bc
# install python
RUN apt-get install -y --no-install-recommends \
	python3 \
	python3-pip \
	python3-setuptools \
	python3-wheel
# install torrenttool script
COPY Requirements.txt /Requirements.txt
RUN pip3 install -r Requirements.txt
COPY sjabloon /sjabloon
COPY torrenttool.py /torrenttool.py

# cleanup
RUN rm -rf /var/lib/apt/lists/*

USER user
RUN mkdir /home/user/.config
ENTRYPOINT ["python3", "torrenttool.py"]
#CMD bash