import argparse
from conlleval import evaluate as conll_evaluate

def evaluate_one(gold,sys):
    """
    Takes goldfile (txt) and sysfile (txt) paths.
    Prints out the results on the terminal.
    The metric used is from CoNLL-2003 evaluation. Can be found at https://github.com/sighsmile/conlleval
    This function is the exact way the subtask4's submissions will be evaluated.
    """
    # combine all labels in single arrays.
    gold_labels = sum(read(gold)[1], [])
    sys_labels = sum(read(sys)[1], [])

    return conll_evaluate(gold_labels,sys_labels)

def read(path, train=True):
    """
    Reads the file from the given path (txt file).
    Returns list tokens and list of labels if it is training file.
    Returns list of tokens if it is test file.
    """
    with open(path, 'r', encoding="utf-8") as f:
        data = f.read()

    if train:
        data = [[tuple(word.split('\t')) for word in instance.strip().split('\n')] for idx,instance in enumerate(data.split("SAMPLE_START\tO")) if len(instance)>1]
        tokens = [[tupl[0].strip() for tupl in sent] for sent in data]
        labels = [[tupl[1] for tupl in sent] for sent in data]
        return tokens,labels
    else:
        tokens = [[word for word in instance.strip().split('\n')] for idx,instance in enumerate(data.split("SAMPLE_START")) if len(instance)>1]
        return tokens, None

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-true_file', '--true_file', required=True, help="The path to the training data txt file")
    parser.add_argument('-prediction_file', '--prediction_file', required=True, help="The path to the prediction output txt file")
    parser.add_argument('-test_file', '--test_file', required=False, help="The path to the test data txt file")
    args = parser.parse_args()

    res, tagged_res = evaluate_one(args.true_file, args.prediction_file)

