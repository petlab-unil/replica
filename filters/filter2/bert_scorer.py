from json import load
from bert_score import BERTScorer
import numpy as np


def read_json(criteriafile):
    """
    Reads the criteria file - criteria_goundtruth.json - containing minimum 5 groundtruth sentences per criteria
    :param: `criteriafile` (str): path to the criteria file
    :return: `data` (dict): a dict of criteria and sentences
    """
    with open(criteriafile, 'r') as f:
        data = load(f)
    return data


def json_to_sent(json_file):
    """
    Converts PDF parser output to list of sentences with greater than two words
    :param: `json_file` (str): path to the json output file from the PDF parser
    :return: `sentences` (list): list of sentences from the PDF 
    """

    from nltk.tokenize import sent_tokenize

    with open(json_file, 'r') as f:
        data = load(f)
    sentences = []
    for para in data['content']:
        for sent in para['sentences']:
            for sentence in sent_tokenize(sent['content']):
                if len(sentence.split(' ')) > 2: 
                    sentences.append(sentence)
    return sentences

def calculate_sim_scores(filepath):
    """
    Calculates similarity scores between the groundtruth sentences and all the sentences of the PDF for each criteria. 
    Threshold for similarity score is empirically set at different levels for each criteria.
    Writes output to a .csv file with columns criteria, sentence, score, paper title
    :param: `json_file` (str): path to the folder containing the outputs of the PDF parser or a json output file
    """
    import pandas as pd
    from os.path import isdir, basename, join
    from os import listdir

    files = []
    test_files = []

    if isdir(filepath):
        files = [join(filepath, filename) for filename in listdir(filepath) if '.json' in filename]
    elif '.json' in filepath:
        files.append(filepath)
    else:
        exit(1)

    print (len(files))
    exclusion = "Museum Internet Grindr tactoRing Experimental Super Bazaar Negotiations understandability Polite Tech Help Desk Automatically Generating OtherTube common Novice Video Consumption Privacy manipulated Commerce Everyday Modeling Brush Village See What Complementary".split(" ")
    for ex in exclusion:
        for json_file in files:
            if (ex in basename(json_file)):
                print ("*****************Skipping article {}\n".format(basename(json_file)), ex)
                test_files.append(json_file)

    print (len(test_files))
    groundtruth = read_json("criteria_goundtruth.json") 
    scorer = BERTScorer(model_type="distilbert-base-uncased")
    threshold = read_json("threshold_scores.json")
    
    scores = []
    predictions = []
    
    for json_file in test_files:
        sentences = json_to_sent(json_file)
        print('####\nProcessing article {}\n'.format(basename(json_file)))

        paper_prediction = {}
        for key in groundtruth:
            print('----\nChecking criteria {}\n----'.format(key))
            p, r, f = scorer.score(sentences, [groundtruth[key]]*len(sentences))
            mask = f > threshold[key]
            indices = mask.nonzero().flatten().numpy()
            df_scores = pd.DataFrame({'criteria': [key]*len(indices), 'sentences': np.array(sentences)[indices], 'scores': f[indices], 'groundtruth': [groundtruth[key]]*len(indices), 'paper_title': [basename(json_file)]*len(indices)})
            paper_prediction[key] = [int(any(indices))]
            scores.append(df_scores)
        paper_prediction['paper_title'] = [basename(json_file)]
        predictions.append(pd.DataFrame(paper_prediction))
    final = pd.concat(scores)
    pred = pd.concat(predictions)
    pred.to_csv("predictions.csv")
    final.to_csv("final_test.csv")


if __name__ == '__main__':
    calculate_sim_scores("output/")