FROM ubuntu:eoan

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

# install python
RUN apt-get install -y --no-install-recommends \
	python3 \
	python3-pip
# install torrenttool script
COPY Requirements.txt /Requirements.txt
COPY torrenttool.py /torrenttool.py
RUN pip3 install -r Requirements.txt

# cleanup
RUN rm -rf /var/lib/apt/lists/*

USER 1000
ENTRYPOINT ["python3", "torrenttool.py"]