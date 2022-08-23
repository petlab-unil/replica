import argparse


def init_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', help='Use this if you want the program to yell what it is doing',
                        action='store_true')
    parser.add_argument('-in', '--input', help='Input content to parse, if it is a folder all its content'
                                               + 'will be parsed', type=str, action='store')
    parser.add_argument('-o', '--output', help='The output path to store the content eventually generated',
                        type=str, action='store')
    parser.add_argument('-m', '--map', help='The style map file to use to recognise the content',
                        type=str, action='store')
    args = parser.parse_args()
    return args


def start_parsing(filepath, mapfile, verbose=False):
    from os.path import isdir
    from os import listdir
    from parsing.parsers import DocumentParser
    from json import load
    from progress.bar import ChargingBar

    files = []

    # TODO: might be wise to also check if it is a file.
    if isdir(filepath):
        files = ['/'.join([filepath, filename]) for filename in listdir(filepath) if '.pdf' in filename]
    elif '.pdf' in filepath:
        files.append(filepath)
    else:
        exit(1)

    # TODO: might be wise to also check if it is a file.
    if '.json' in mapfile:
        with open(mapfile, 'r') as f:
            map = load(f)

    documents = []
    parsers = []
    with ChargingBar('Parsing', max=len(files), suffix='%(index)d/%(max)d %(percent)d%%') as progress_bar:
        for file in files:
            parser = DocumentParser(file, map)
            documents.append(parser.parse(verbose=verbose))
            parsers.append(parser)
            progress_bar.next()

    return documents, parsers


def save_parsing_results(outputs, output_filepath='output/'):
    from json import dump
    from os.path import isdir, exists
    from os import makedirs

    if output_filepath.endswith('/') and not exists(output_filepath):
        makedirs(output_filepath)

    if isdir(output_filepath):
        for output in outputs:
            with open('/'.join([output_filepath, output.name + '.json']), 'w+') as file:
                dump(output.to_dict(), file)
    else:
        with open(output_filepath, 'w+', encoding='utf8') as file:
            for output in outputs:
                dump(output.to_dict(), file, ensure_ascii=False)


def __check_results(documents, parsers):

    file_issues = []
    parser_issues = []
    for document, parser in zip(documents, parsers):
        if len(document.get_content()) == 0:
            file_issues.append(document)
            parser_issues.append(parser)
            print('Detected parsing issue with file: {filepath}'.format(filepath=document.name))

    return file_issues, parser_issues


def __correct_map(parsers, mapfile, reference_word='ABSTRACT', type='title'):
    from re import match
    from json import load

    with open(mapfile, 'r') as f:
        map = load(f)

    for parser in parsers:
        line, styles = parser.get_cached()
        for style in styles:
            sub = line[style['start']:style['end']]
            if match(reference_word, sub) is not None:
                map.append({'style': style['name'], 'type': type})

    return map


def start_correction_process(input_filepath, mapfile, documents, parsers):
    from progress.bar import ChargingBar
    file_errors, parser_errors = __check_results(documents, parsers)

    new_files = []
    for f in file_errors:
        new_files.append(input_filepath + f.name)

    tentative_map = __correct_map(parser_errors, mapfile)
    new_mapfile = mapfile + '.extended'
    with open(new_mapfile, 'w+') as emap:
        dump(tentative_map, emap)

    new_documents = []
    with ChargingBar('Parsing 2nd round', max=len(documents), suffix='%(index)d/%(max)d %(percent)d%%') as progress_bar:
        for parser in parsers:
            new_documents.append(parser.parse(use_cache=True, map=tentative_map))
            progress_bar.next()

    return new_documents, parsers


if __name__ == '__main__':
    from json import dump
    with open('opening_lahari.txt', 'r') as opening:
        opening_content = opening.read()
        print(opening_content)
    args = init_arguments()
    if args.input is None:
        print('Bro, seriously... This code needs an input to run...')
        exit(1)
    documents, parsers = start_parsing(args.input, args.map, args.verbose)
    print('Checking for parsing issues...')
    documents, parsers = start_correction_process(args.input, args.map, documents, parsers)
    print('Saving documents')
    if args.output is not None:
        save_parsing_results(documents, args.output)


