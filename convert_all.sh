#!/bin/bash

# convert to graph(mrp) formats

#indata -> input json file to be converted
#outdata -> output mrp file of converted graphs
# $1 -> dataset: case_all, case_final, case_all_split, case_final_split
# please change the splits to <train, test> for the final version, since all training data will be used

# convert to labeled_edge

for split in train dev test; do
    indata=data/raw/$1/"$split".json
    outdata=data/labeled_edge_mrp/$1/"$split".mrp

    python mtool/main.py --strings --ids --read case --write mrp "$indata" "$outdata"
done;

# convert to node_centric

for split in train dev test; do
    indata=data/raw/$1/"$split".json
    outdata=data/node_centric_mrp/$1/"$split".mrp

    python mtool/main.py --strings --ids --read case --write mrp "$indata" "$outdata" --node_centric
done;