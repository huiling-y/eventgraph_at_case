#!/bin/bash

id=$(sbatch run.sh config/edge_case.yaml labeled-edge-xlmr-large-run1)
echo "edge_case -- ${id}"

id=$(sbatch run.sh config/node_case.yaml node-centric-xlmr-large-run1)
echo "node_case -- ${id}"

id=$(sbatch run.sh config/node_case_split.yaml node-centric-split-xlmr-large-run1)
echo "node_case -- ${id}"