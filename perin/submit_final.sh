#!/bin/bash

id=$(sbatch run.sh config/edge_case_final.yaml labeled-edge-xlmr-large-final)
echo "edge_case -- ${id}"

id=$(sbatch run.sh config/node_case_final.yaml node-centric-xlmr-large-final)
echo "node_case -- ${id}"

id=$(sbatch run.sh config/node_case_final_split.yaml node-centric-xlmr-large-final_split)
echo "node-split_case -- ${id}"

