#!/bin/sh
# Downloads the raw MSD sources into ../raw (about 3.2 GB total)
set -e
cd "$(dirname "$0")/../raw"
B=http://millionsongdataset.com/sites/default/files/AdditionalFiles
curl -L -C - -O $B/track_metadata.db                              # ~746 MB: artist, title, year
curl -L -C - -O $B/mxm_dataset.db                                 # ~2.4 GB: musiXmatch bag-of-words
curl -L -C - -O http://www.tagtraum.com/genres/msd_tagtraum_cd2.cls.zip   # ~2.5 MB: genre labels
unzip -o msd_tagtraum_cd2.cls.zip
