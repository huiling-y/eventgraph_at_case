import json 
import copy 
import os
import argparse
from convert_to_bio import write_bio


def load_json(file):
    with open(file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def dump_json(file, data, indent=0):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def string_to_span(span):
    span = span.split(':')
    start, end = int(span[0]), int(span[1])
    return start, end 


def span_to_string(start, end):
    return f"{start}:{end}"

def get_new_span(lens, start, end):
    # turn token index to string index, 'Chale was allegedly chased', 'Chale': '0:0' -> '0:5'
    new_start = sum(lens[:start]) + start
    new_end = new_start + sum(lens[start:end+1]) + (end-start)
    return new_start, new_end

def get_sent_sep(paragraph):
    """
    Obtain the indices of sentence boundry marker '[SEP]'
    Paragraph: list of token-label tuples

    return list of indices
    """
    seps = []

    for i,tok in enumerate(paragraph):
        if tok[0] == '[SEP]':
            seps.append(i)
    seps.append(len(paragraph))
    return seps 

def get_sent_event(sent):
    """
    sent: list of tuples -> (token, label) 

    return a list of events in this sent
    """
    toks = [t[0] for t in sent]
    lens = [len(w) for w in toks]
    triggers = [[],[]]
    arguments = []
    labeled = []
    
    left = 0
    right = 0 
    found = False
    
    for i, tup in enumerate(sent):
        if tup[1].startswith('B-'):
            if found:
                labeled.append([left, right])
            else:
                found = True
            left, right = i, i
        elif tup[1].startswith('I-'):
            right = i
        else:
            if found:
                labeled.append([left, right])
                found = False
    if found:
        labeled.append([left, right])
    
    for span in labeled:
        l, r = span
        new_l, new_r = get_new_span(lens, l, r)
        new_span = span_to_string(new_l, new_r)
        
        if 'trigger' in sent[l][1]:
            triggers[0].append(" ".join(toks[l:r+1]))
            triggers[1].append(new_span)
        else:
            arg_text = " ".join(toks[l:r+1])
            arg_role = sent[l][1].split('-')[1]
            arguments.append([[arg_text], [new_span], arg_role])
    if len(labeled) > 0:
        event = [{
            'trigger': triggers,
            'arguments': arguments
            }]
    else:
        event = []
    return event               

# split multiple triggers into multiple events
def expand_data(data):
    new_data = []
    
    for sent in data:
        new_sent = {}
        new_sent['sent_id'] = sent['sent_id']
        new_sent['text'] = sent['text']
        new_sent['events'] = []
        
        triggers = sent['events'][0]['trigger']
        
        for i in range(len(triggers[0])):
            event_ = {
                'trigger': [[triggers[0][i]], [triggers[1][i]]],
                'arguments': copy.deepcopy(sent['events'][0]['arguments'])
            }
            new_sent['events'].append(event_)
        new_data.append(new_sent)
    return new_data


class TrainExtractor:
    def __init__(self, train_path, lang):
        self.path = train_path 
        self.lang = lang
        self.events = []
    
    def read_file(self):
        """
        read the conll format training data into tuples of token-label pair
        example: hacked	B-trigger -> ('hacked', 'B-trigger')

        each sample is marked with 'SAMPLE_START	O'
        each sentence in sample is separated with '[SEP]'
        """

        with open(self.path, 'r', encoding='utf-8') as f:
            data = f.read()
        
        token_tuples = [[tuple(word.split('\t')) for word in instance.strip().split('\n')] for idx,instance in enumerate(data.split('SAMPLE_START\tO')) if len(instance)>1]

        return token_tuples
    

    def get_sents(self):

        data = self.read_file()
        
        
        for i,paragraph in enumerate(data):
            
            seps = get_sent_sep(paragraph)
            
            for j in range(len(seps)):
                
                sent = {}
                sent_id = f"{self.lang}/{i+1:04d}-{j+1:03d}"
                sent['sent_id'] = sent_id
                
                if j == 0:
                    tok_tuples = paragraph[:seps[j]]
                elif j == (len(seps)-1):
                    tok_tuples = paragraph[seps[j-1]+1:]
                else:
                    tok_tuples = paragraph[seps[j-1]+1:seps[j]]
                
                sent['text'] = ' '.join([tup[0] for tup in tok_tuples])
                sent['events'] = get_sent_event(tok_tuples)
                
                self.events.append(sent)

class TestExtractor:
    def __init__(self, test_path, lang):
        self.path = test_path
        self.lang = lang 
        self.events = []
    
    def read_file(self):
        """
        read the conll format test data into list of tokens

        each sample is marked with 'SAMPLE_START'
        each sentence in sample is separated with '[SEP]'
        """

        with open(self.path, 'r', encoding='utf-8') as f:
            data = f.read()   

        tokens = [[(word,) for word in instance.strip().split('\n')] for idx,instance \
                  in enumerate(data.split("SAMPLE_START")) if len(instance)>1]
        return tokens

    def get_sents(self):

        data = self.read_file()
        
        
        for i,paragraph in enumerate(data):
            
            seps = get_sent_sep(paragraph)
            
            for j in range(len(seps)):
                
                sent = {}
                sent_id = f"{self.lang}/{i+1:04d}-{j+1:03d}"
                sent['sent_id'] = sent_id
                
                if j == 0:
                    tok_tuples = paragraph[:seps[j]]
                elif j == (len(seps)-1):
                    tok_tuples = paragraph[seps[j-1]+1:]
                else:
                    tok_tuples = paragraph[seps[j-1]+1:seps[j]]
                
                sent['text'] = ' '.join([tup[0] for tup in tok_tuples])
                sent['events'] = []
                
                self.events.append(sent)



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', help='the directory of official shared task datasets')
    parser.add_argument('--output_dir', help='output directory of processed datasets')

    args = parser.parse_args()

    save_dir_all = f"{args.output_dir}/case_all"
    os.makedirs(save_dir_all, exist_ok=True)

    save_dir_final = f"{args.output_dir}/case_final"
    os.makedirs(save_dir_final, exist_ok=True)    

    save_dir_all_split = f"{args.output_dir}/case_all_split"
    os.makedirs(save_dir_all_split, exist_ok=True)

    save_dir_final_split = f"{args.output_dir}/case_final_split"
    os.makedirs(save_dir_final_split, exist_ok=True) 

    split_ids = {
        'en': "en/0733-001",
        'es': "es/0030-001",
        'pr': "pr/0030-001"
    }

    # all training data
    train_full = []

    # all training data with dev data excluded
    train_all_wo_dev = []

    # all dev data
    dev_all = []

    # all test data
    test_all = []


    for lang in ['en', 'es', 'pr']:
        train_extractor = TrainExtractor(f"{args.data_dir}/train/{lang}-train.txt", lang)
        train_extractor.get_sents()

        dev_split = [i for i,sent in enumerate(train_extractor.events) if sent['sent_id'] == split_ids[lang]][0]

        _train_full = train_extractor.events
        _train_wo_dev = train_extractor.events[:dev_split]
        _dev = train_extractor.events[dev_split:]

        test_extractor = TestExtractor(f"{args.data_dir}/test/{lang}-test.txt", lang)
        test_extractor.get_sents()
        _test = test_extractor.events

        # append processed language-specific data
        train_full += _train_full
        train_all_wo_dev += _train_wo_dev
        dev_all += _dev

        test_all += _test
    
    # data with split triggers
    train_full_split = expand_data(train_full)
    train_all_split_wo_dev = expand_data(train_all_wo_dev)
    dev_all_split = expand_data(dev_all)

    # save data
    # combined triggers

    dump_json(f"{save_dir_all}/train.json", train_all_wo_dev)
    dump_json(f"{save_dir_all}/dev.json", dev_all)
    dump_json(f"{save_dir_all}/test.json", test_all)


    dump_json(f"{save_dir_final}/train.json", train_full)
    dump_json(f"{save_dir_final}/test.json", test_all)

    # split triggers

    dump_json(f"{save_dir_all_split}/train.json", train_all_split_wo_dev)
    dump_json(f"{save_dir_all_split}/dev.json", dev_all_split)
    dump_json(f"{save_dir_all_split}/test.json", test_all)

    dump_json(f"{save_dir_final_split}/train.json", train_full_split)
    dump_json(f"{save_dir_final_split}/test.json", test_all)


    # Convert to original bio format for evaluation
    write_bio(f"{save_dir_all}/train.json")
    write_bio(f"{save_dir_all}/dev.json")
    write_bio(f"{save_dir_final}/train.json")

    write_bio(f"{save_dir_all_split}/train.json")
    write_bio(f"{save_dir_all_split}/dev.json")
    write_bio(f"{save_dir_final_split}/train.json")







