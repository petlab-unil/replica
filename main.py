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

    parsers = []
    for file in files:
        parsers.append(DocumentParser(file, map).parse(verbose))

    return parsers


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
        with open(output_filepath, 'w+') as file:
            for output in outputs:
                dump(output.to_dict(), file)


if __name__ == '__main__':
    args = init_arguments()
    if args.input is None:
        print('Bro, seriously... This code needs an input to run...')
        exit(1)
    outputs = start_parsing(args.input, args.map, args.verbose)
    if args.output is not None:
        save_parsing_results(outputs, args.output)
