#!/bin/bash

clear
docker run -ti --network=host -e PYTHONPATH=/notebooks/srilm-utils/environment -v "$PWD/SRILM":/SRILM -v "$PWD":/notebooks --rm cka3o4nik/text_authoring
