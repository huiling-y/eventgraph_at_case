import json 
from evaluate import evaluate_one
import argparse

def evaluate_all(raw_file, converted_file):

    en_res, en_tagged_res = evaluate_one(f"{raw_file}-en.txt", f"{converted_file}-en.txt")
    es_res, es_tagged_res = evaluate_one(f"{raw_file}-es.txt", f"{converted_file}-es.txt")
    pr_res, pr_tagged_res = evaluate_one(f"{raw_file}-pr.txt", f"{converted_file}-pr.txt")

    en_tagged_res['all'] = en_res
    es_tagged_res['all'] = es_res 
    pr_tagged_res['all'] = pr_res

    desired_k = ['all', 'trigger', 'participant', 'organizer', 'target', 'fname', 'etime', 'place']

    en_final_res = {k:en_tagged_res[k] for k in desired_k}
    es_final_res = {k:es_tagged_res[k] for k in desired_k}
    pr_final_res = {k:pr_tagged_res[k] for k in desired_k}

    all_results = {
        'en': list(en_final_res.items()),
        'es': list(es_final_res.items()),
        'pr': list(pr_final_res.items())
    }

    return all_results
