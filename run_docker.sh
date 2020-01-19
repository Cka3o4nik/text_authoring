#!/bin/bash

clear
docker run -ti --network=host -v "$PWD":/notebooks -v "$PWD/..":/project_data --rm cka3o4nik/text_authoring
