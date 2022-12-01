from json import load
from bert_score import BERTScorer
from transformers import pipeline
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

    if len(sentences)==0:
        print ("Empty sentence, checking title nodes:", sentences)
        for para in data['content']:
            for sentence in sent_tokenize(para['title']['content']):
                if len(sentence.split(' ')) > 2: 
                    sentences.append(sentence)

    return sentences

def classify_criteria(classifier, sentences, criteria):
    results = classifier(sentences, criteria, multi_label=True)
    return results
     
def calculate_sim_scores(scorer, sentences, groundtruth, threshold, criteria):
    p, r, f = scorer.score(sentences, [groundtruth]*len(sentences))
    # mask = f > 0.75
    mask = f > threshold
    indices = mask.nonzero().flatten().numpy()
    results = {'criteria': [criteria]*len(indices), 'sentences': list(np.array(sentences)[indices]), 'sim_scores': f[indices]}
    return results


def check_criteria(filepath, use_bert_score = True, use_zero_shot_classifier = True):
    """
    Calculates similarity scores between the groundtruth sentences and all the sentences of the PDF for each criteria. 
    Threshold for similarity score is empirically set at different levels for each criteria.
    Writes output to a .csv file with columns criteria, sentence, score, paper title
    :param: `filepath` (str): path to the folder containing the outputs of the PDF parser or a json output file
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
    # exclusion = "Museum Internet Grindr tactoRing Experimental Super Bazaar Negotiations understandability Polite Tech Automatically OtherTube common Novice Video Privacy manipulated Commerce Everyday Curved Brush Village What Complementary".split(" ")
    # for ex in exclusion:
    #     for json_file in files:
    #         if (ex in basename(json_file)):
    #             print ("*****************Skipping article {}\n".format(basename(json_file)), ex)
    #             test_files.append(json_file)

    # print (len(test_files))
    groundtruth = read_json("criteria_goundtruth.json") 
    if use_bert_score: scorer = BERTScorer(model_type="distilbert-base-uncased")
    if use_zero_shot_classifier: classifier = pipeline("zero-shot-classification", device=0)
    threshold = read_json("threshold_scores.json")
    
    scores = []
    predictions = []
    
    for json_file in files:
        print('####\nProcessing article {}\n'.format(basename(json_file))) 
        sentences = json_to_sent(json_file)

        paper_prediction = {}
        # for key in groundtruth["zero_shot"][0]:
        for key in ["Pre-registration", "Sample size for QuaN", "Anonymization"]:
            print('Checking criteria {}\n----'.format(key))

            if use_bert_score:
                sim_results = calculate_sim_scores(scorer, sentences, groundtruth["sim_matcher"][0][key], threshold["zero_shot"][0][key], key)
            if len(sim_results['sentences'])>0:
                if use_zero_shot_classifier:
                    results = classify_criteria(classifier, sim_results['sentences'], groundtruth['zero_shot'][0][key])
                df_scores = pd.concat([pd.DataFrame(sim_results), pd.DataFrame(results)], axis=1)
                df_scores['paper_title'] = [basename(json_file)]*len(df_scores)
                df_scores['max_label_score'] = df_scores['scores'].apply(lambda x:x[0])
                paper_prediction[key] = [int(any(df_scores['max_label_score'] > 0.80))]
                scores.append(df_scores)
        paper_prediction['paper_title'] = [basename(json_file)]
        predictions.append(pd.DataFrame(paper_prediction))
    final = pd.concat(scores)
    pred = pd.concat(predictions)
    pred.fillna(0, inplace=True)
    pred.to_csv("final_predictions_zero_shot5.csv")
    final.to_csv("final_sentences_zero_shot5.csv")


if __name__ == '__main__':
    check_criteria("parserOutput-all")
    # check_criteria("output")