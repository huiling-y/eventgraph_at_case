#!/bin/bash


# convert mrp -> json
python3 ../mtool/main.py $2--strings --ids --read mrp --write case "$1" "$1_converted"


# convert json -> bio
python3 ../preprocess/convert_to_bio.py --converted_file "$1_converted"