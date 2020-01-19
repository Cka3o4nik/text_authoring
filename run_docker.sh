#!/bin/bash

clear
docker run -ti --network=host -v "$PWD/SRILM":/SRILM -v "$PWD":/notebooks --rm cka3o4nik/text_authoring
