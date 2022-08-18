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

    parsers = []
    with ChargingBar('Parsing', max=len(files), suffix='%(index)d/%(max)d %(percent)d%%') as progress_bar:
        for file in files:
            parsers.append(DocumentParser(file, map).parse(verbose))
            progress_bar.next()

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
        with open(output_filepath, 'w+', encoding='utf8') as file:
            for output in outputs:
                dump(output.to_dict(), file, ensure_ascii=False)


def check_results(output_folder, file=None):
    from os import listdir

    def check_file_content(filepath):
        from json import load
        data = None
        with open(filepath, 'r') as res:
            data = load(res)
        return data is None or len(data['content']) == 0

    file_issues = []
    if file is not None and not check_file_content(output_folder + file):
        print('Detected parsing issue with file: {filepath}'.format(filepath=output_folder + file))
        file_issues.append(file)
    else:
        for f in listdir(output_folder):
            if check_file_content(output_folder + f):
                file_issues.append(f)
                print('Detected parsing issue with file: {filepath}'.format(filepath=output_folder + f))

    return file_issues


def correct_map(filepath, mapfile, reference_word='ABSTRACT', type='title'):
    from parsing.parsers import DocumentParser
    from re import match
    from json import load

    with open(mapfile, 'r') as f:
        map = load(f)

    for f in filepath:
        line, styles = DocumentParser(f, map).pdf_to_text()
        for style in styles:
            sub = line[style['start']:style['end']]
            if match(reference_word, sub) is not None:
                map.append({'type': type, 'style': style['name']})

    return map


if __name__ == '__main__':
    from json import dump
    with open('opening_lahari.txt', 'r') as opening:
        opening_content = opening.read()
        print(opening_content)
    args = init_arguments()
    if args.input is None:
        print('Bro, seriously... This code needs an input to run...')
        exit(1)
    outputs = start_parsing(args.input, args.map, args.verbose)
    if args.output is not None:
        save_parsing_results(outputs, args.output)
        file_errors = check_results(args.output)
        new_files = []
        for f in file_errors:
            new_files.append(args.input + f.replace('.json', ''))

        tentative_map = correct_map(new_files, args.map)
        with open(args.map + '.extended', 'w+') as emap:
            dump(tentative_map, emap)

        for f in new_files:
            out = start_parsing(f, args.map + '.extended')
            save_parsing_results(out, args.output)
