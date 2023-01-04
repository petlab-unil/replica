from json import load
from os.path import isdir, basename, join
from os import listdir, makedirs

import numpy as np
import pandas as pd
from bert_score import BERTScorer
from transformers import pipeline

import argparse


def init_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filepath', help='The path containing the output of the PDF parser',
                                                type=str, action='store')
    parser.add_argument('-o', '--output', help='The output path to store the predictions, stores in output/ by default',
                        type=str, default='output', action='store')
    parser.add_argument('-s', '--similarity', help='Enables BERTScore similarity matching to filter sentences',
                         default=True, action='store_true')
    parser.add_argument('-c', '--classifier', help='Enables zero-shot text classifier',
                        default=True, action='store_true')
    args = parser.parse_args()
    return args

def read_json(criteriafile):
    """
    Reads the json file

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

    :return: `sentences` (list of str): list of sentences from the PDF 
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
    # some of the json generated only few sentences (here assumed < 100) in the sentence nodes, hence checking title nodes
    if len(sentences)<100:
        print ("Empty sentence, checking title nodes:", sentences)
        for para in data['content']:
            for sentence in sent_tokenize(para['title']['content']):
                if len(sentence.split(' ')) > 2: 
                    sentences.append(sentence)

    return sentences

def classify_criteria(classifier, sentences, criteria):
    """
    NLI based zero-shot classification which calculates the *entailment* probability between sentences and criteria 
    template sentence "this is an example of <keyword>"

    :param: `classifier` (obj): NLI-based zero-shot classification pipeline object
    :param: `sentences` (list of string): list of sentences 
    :param: `criteria` (list of string): list of keywords for the criterion considered as candidate labels

    :return: `results` (dict): a dict with the following keys:
            - **sequence** (`str`) -- the sequence for which this is the output
            - **labels** (`List[str]`) -- the keywords or labels sorted by order of likelihood
            - **scores** (`List[float]`) -- the probabilities for each of the keywords 
    """
    results = classifier(sentences, criteria, multi_label=True)
    return results
     
def calculate_sim_scores(scorer, sentences, groundtruth, threshold, criteria):
    """
    Calculates the BERTscore of similarity between the paper sentences and reference sentences

    :param: `scorer` (obj): BERTScorer object 
    :param: `sentences` (list of string): list of sentences from the PDF
    :param: `groundtruth` (list of string): list of reference sentences for the criterion
    :param: `threshold` (float): threshold score for the criterion
    :param: `criteria` (str): the criterion

    :return: `results` (dict): a dict containing the criterion, sentences whose similarity scores are higher than the 
                                threshold and their respective scores
    """
    p, r, f = scorer.score(sentences, [groundtruth]*len(sentences))
    mask = f > threshold
    indices = mask.nonzero().flatten().numpy()
    results = {'criteria': [criteria]*len(indices), 'sentences': list(np.array(sentences)[indices]), 'sim_scores': f[indices]}
    return results


def check_criteria(filepath, use_sim_score = True, use_zero_shot_classifier = True):
    """
    Calls (optionally) the modules of similarity score filter and zero-shot classifier to check criteria satisfaction 

    :param: `filepath` (str): path to the folder containing the outputs of the PDF parser or a json output file
    :param: `use_sim_score` (bool): a boolean specifying whether to use similarity score filter or not
    :param: `use_zero_shot_classifier` (bool): a boolean specifying whether to use zero-shot classifier or not

    Writes output to two .csv files -
    - sentences.csv with columns criteria, sentence, similarity score, labels, probability scores, paper title, max probability score
    - predictions.csv with one column for each criteria and paper title
    """

    assert (
            use_sim_score is not False or use_zero_shot_classifier is not False
        ), "Either of use_sim_score or use_zero_shot_classifier should be True"

    files = []
    test_files = []

    if isdir(filepath):
        files = [join(filepath, filename) for filename in listdir(filepath) if '.json' in filename]
    elif '.json' in filepath:
        files.append(filepath)
    else:
        exit(1)
    
    # read the reference sentences
    groundtruth = read_json("criteria_goundtruth.json")  

    # list of sentences used to compute the idf weights, providing all reference sentences for all criteria to keep it simple
    all_gt = []
    for key in groundtruth['sim_matcher'][0]: all_gt.extend(groundtruth["sim_matcher"][0][key])
    
    if use_sim_score: scorer = BERTScorer(model_type="distilbert-base-uncased", idf=True, idf_sents=all_gt)
    if use_zero_shot_classifier: classifier = pipeline("zero-shot-classification", device=0)
    
    # read the threshold scores for similarity filter, different for each criteria
    threshold = read_json("threshold_scores.json")
    
    scores = []
    predictions = []
    # entailment probability threshold was empirically determined to be 0.78
    threshold_prob = 0.78
    
    for json_file in files:
        print('####\nProcessing article {}\n'.format(basename(json_file))) 
        sentences = json_to_sent(json_file)

        paper_prediction = {}
        for key in groundtruth["zero_shot"][0]:
            print('Checking criteria {}\n----'.format(key))

            if use_sim_score:
                sim_results = calculate_sim_scores(scorer, sentences, groundtruth["sim_matcher"][0][key], threshold["zero_shot"][0][key], key)

            if use_zero_shot_classifier:
                if len(sim_results['sentences'])>0:
                    results = classify_criteria(classifier, sim_results['sentences'], groundtruth['zero_shot'][0][key])

                # concatenating the results from similarity filter and classifier in a dataframe
                df_scores = pd.concat([pd.DataFrame(sim_results), pd.DataFrame(results)], axis=1)
                df_scores['paper_title'] = [basename(json_file)]*len(df_scores)
                df_scores['max_label_score'] = df_scores['scores'].apply(lambda x:x[0])
                
                # if any of the sentence crosses the threshold probability, prediction is marked as 1 for that paper title and criteria
                paper_prediction[key] = [int(any(df_scores['max_label_score'] > threshold_prob))]
                scores.append(df_scores)
        paper_prediction['paper_title'] = [basename(json_file)]
        predictions.append(pd.DataFrame(paper_prediction))

    final = pd.concat(scores)
    pred = pd.concat(predictions)
    pred.fillna(0, inplace=True)

    if not isdir(args.output):
        makedirs(args.output)

    pred.to_csv(join(args.output, "predictions.csv"))
    final.to_csv(join(args.output, "sentences.csv"))


if __name__ == '__main__':
    args = init_arguments()
    if args.filepath is None:
        print('\nPath to the PDF parsed files must be specified.... \n\n')
        exit(1)

    check_criteria(filepath=args.filepath, use_sim_score=args.similarity, use_zero_shot_classifier=args.classifier)