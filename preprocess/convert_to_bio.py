import json 
import os
import json
from collections import defaultdict
import argparse

from nltk.tokenize.simple import SpaceTokenizer

tk = SpaceTokenizer()

def load_json(file):
    with open(file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def convert_char_offsets_to_token_idxs(char_offsets, token_offsets):
    """
    char_offsets: list of str
    token_offsets: list of tuples

    >>> text = "I think the new uni ( ) is a great idea"
    >>> char_offsets = ["8:19"]
    >>> token_offsets =
    [(0,1), (2,7), (8,11), (12,15), (16,19), (20,21), (22,23), (24,26), (27,28), (29,34), (35,39)]

    >>> convert_char_offsets_to_token_idxs(char_offsets, token_offsets)
    >>> (2,3,4)
    """
    token_idxs = []
    #
    for char_offset in char_offsets:
        bidx, eidx = char_offset.split(":")
        bidx, eidx = int(bidx), int(eidx)
        intoken = False
        for i, (b, e) in enumerate(token_offsets):
            if b == bidx:
                intoken = True
            if intoken:
                token_idxs.append(i)
            if e == eidx:
                intoken = False
    return frozenset(token_idxs)


def break_offsets(offset):
    """
    offset: frozenset of token index -> frozenset({2, 3, 4, 7, 8, 11, 12})

    return: token index of disjoint tokens [(2,3,4), (7,8), (11,12)]
    """

    offset_l = sorted(list(offset))
    splits = []
    for i,num in enumerate(offset_l):
        if i == 0:
            splits.append(i)
        else:
            if num != offset_l[i-1] + 1:
                splits.append(i)
    splits.append(len(offset_l))

    pieces = []

    for i in range(1, len(splits)):
        pieces.append(frozenset(offset_l[splits[i-1]:splits[i]]))
    return pieces


def convert_event_to_tuple(sentence):
    """
    >>> sentence 
    {'sent_id': 'nw/APW_ENG_20030322.0119/001',
    'text': 'U.S. and British troops were moving on the strategic southern port city of Basra Saturday after a massive aerial assault pounded Baghdad at dawn',
    'events': [
        {
            'event_type': 'Attack',
            'trigger': [['pounded'], ['121:128']],
            'arguments': [[['Baghdad'], ['129:136'], 'Place'], [['dawn'], ['140:144'], 'Time-Starting']]},
        {
            'event_type': 'Transport',
            'trigger': [['moving'], ['29:35']],
            'arguments': [[['Saturday'], ['81:89'], 'Time-Within'], [['the strategic southern port city of Basra'], ['39:80'], 'Destination'], [['U.S. and British troops'], ['0:23'], 'Artifact']]}
        
                ]
    
    }

    >>> event_tupels 
    [
        ((frozenset({20}), 'attack'), (frozenset({21}), 'place'), (frozenset({23}), 'time-starting')),
        ((frozenset({5}), 'transport'), (frozenset({14}), 'time-within'), (frozenset({7, 8, 9, 10, 11, 12, 13}), 'destination'), (frozenset({0, 1, 2, 3}), 'artifact'))
    ]
    
    """


    text = sentence['text']
    events = sentence['events']
    labeled_tuples = []
    token_offsets = list(tk.span_tokenize(text))

    if len(events) > 0:
        for event in events:
            event_tuple = tuple()

            trigger_char_idxs = event['trigger'][1]
            trigger = break_offsets(convert_char_offsets_to_token_idxs(trigger_char_idxs, token_offsets))
            event_type = "trigger"

            # trigger might contain multiple disjoint tokens

            for trg_ in trigger:
                labeled_tuples.append((trg_, event_type))

            if len(event['arguments']) > 0:
                for argument in event['arguments']:
                    arg_role = argument[-1]
                    argument_char_idxs = argument[1]
                    arg = break_offsets(convert_char_offsets_to_token_idxs(argument_char_idxs, token_offsets))
                    
                    for arg_ in arg:
                        labeled_tuples.append((arg_, arg_role))
            

    return labeled_tuples

def get_label(labeled_tuple):
    label_sequence = []
    offset, label = labeled_tuple
    offset_l = sorted(list(offset))

    for i in range(len(offset_l)):
        if i == 0:
            label_sequence.append(f"B-{label}")
        else:
            label_sequence.append(f"I-{label}")
    return label_sequence


def sent_bio(sent):
    sent_toks = sent['text'].split()
    labeled = [False] * len(sent_toks)
    tok_labels = ['O'] * len(sent_toks)
    labeled_tuples = convert_event_to_tuple(sent)

    for labeled_tuple in labeled_tuples:
        label_sequence = get_label(labeled_tuple)

        offset, _ = labeled_tuple
        offset_l = sorted(list(offset))

        if all(labeled[i] == False for i in offset_l):
            for j,idx in enumerate(offset_l):
                labeled[idx] = True 
                tok_labels[idx] = label_sequence[j]
    labeled_pairs = [f"{sent_toks[k]}\t{tok_labels[k]}" for k in range(len(sent_toks))]
    return labeled_pairs


def convert_lang(data, out_file):

    for sent in data:
        sent['bio'] = sent_bio(sent)

    sample_d = defaultdict(list)

    for i,sent in enumerate(data):
        sample_id = sent['sent_id'].split('-')[0]
        sample_d[sample_id].append(i)
    
    with open(out_file, 'w', encoding='utf-8') as f:

        sample_d = list(sample_d.items())

        for m,pair in enumerate(sample_d):
            k,v = pair
            f.write(f"SAMPLE_START\tO")
            f.write("\n")
            for j in range(len(v)):
                labeled_pairs = data[v[j]]['bio']
                for labeled_pair in labeled_pairs:
                    f.write(labeled_pair)
                    f.write("\n")
                if j != (len(v)-1):
                    f.write(f"[SEP]\tO")
                    f.write('\n')
            if m != len(sample_d)-1:
                f.write("\n")


def write_bio(in_file):
    data = load_json(in_file)

    en_data = [sent for sent in data if sent['sent_id'].startswith('en/')]
    es_data = [sent for sent in data if sent['sent_id'].startswith('es/')]
    pr_data = [sent for sent in data if sent['sent_id'].startswith('pr/')]

    convert_lang(en_data, f"{in_file}-en.txt")
    convert_lang(es_data, f"{in_file}-es.txt")
    convert_lang(pr_data, f"{in_file}-pr.txt")

    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-converted_file', '--converted_file', required=True, help="The path to the converted json file")
    args = parser.parse_args()

    write_bio(args.converted_file)