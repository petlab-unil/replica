from pdfminer.layout import LAParams, LTAnno


class DocumentParser:
    """
    This class represents a PDF document parser. It will go through the given document and try to detect sentences,
    titles and sections on the document.

    Attributes
    ----------

    document: str
        the path to the PDF document to parse.
    map: str
        the path to the JSON map to use in order to detect the specific titles according to the font used.

    Methods
    _______

    parse(verbose=False)
        Parses the document and returns a Document class containing the sections, sentences and titles.
    """
    SUPPORTED_LIGATURES = {
        0xfb00: u'ff',
        0xfb01: u'fi',
        0xfb02: u'fl',
        0xfb03: u'ffi',
        0xfb04: u'ffl',
    }

    def __init__(self, document, map):
        """
        :param document: the path to the PDF document to parse.
        :param map: the path to the JSON map to use in order to detect the specific titles according to the font used.
        """
        self.document = document
        self.map = map

    def __compute_mean_variance(self, values):
        from numpy import mean, std
        distances = []
        for i in range(1, len(values)):
            distances.append(values[i] - values[i-1])
        return mean(distances), std(distances)

    def parse(self, verbose=False):
        """
        Parses the document and returns a Document class containing the sections, sentences and titles.

        :param verbose: print additional process information or not.
        :return: an object, instance of the Document class (contains the sections with their titles and sentences).
        """
        from os.path import basename
        from pdfminer.high_level import extract_pages
        from pdfminer.layout import LTTextBoxHorizontal, LTTextLine, LTChar
        from parsing.objects import Section, Sentence, Title, Document

        pages = extract_pages(self.document)
        if verbose:
            print('####\nParsing Content in document {}\n####'.format(basename(self.document)))
        document = Document(basename(self.document))

        for page in pages:  # Hope you like indented code
            for container in page:
                if isinstance(container, LTTextBoxHorizontal):
                    line_buffer = ''
                    mapped_buffer = ''  # This might become a map with all the specific text encountered
                    sentences = []
                    mapped_type = ''  # might also become a map together with mapped_buffer
                    mapped_accumulators = {}
                    potential_end = None
                    for line in container:
                        if isinstance(line, LTTextLine):
                            styles = {}
                            for char in line:
                                if isinstance(char, LTChar):
                                    c = char.get_text()
                                    if potential_end is not None:
                                        if potential_end == '.' and c == ' ':
                                            potential_end += c
                                        elif potential_end == '. ' and c.isupper():
                                            sentences.append(Sentence(style=styles, content=line_buffer))
                                            line_buffer = ''
                                            potential_end = None
                                        else:
                                            potential_end = None
                                    if char.fontname not in styles.keys():
                                        styles[char.fontname] = 1
                                    else:
                                        styles[char.fontname] += 1
                                    matched_mapping = False
                                    for mapped_elt in self.map: # FIXME: I need to refactor this
                                        if char.fontname == mapped_elt['style'] or \
                                           (c == ' ' and len(mapped_type) > 0):  # and char.size == mapped_elt['size']
                                            mapped_buffer += c
                                            mapped_type = mapped_elt['type']
                                            matched_mapping = True
                                            if mapped_elt['type'] not in mapped_accumulators.keys():
                                                mapped_accumulators[mapped_elt['type']] = ''
                                            mapped_accumulators[mapped_elt['type']] += c
                                        else:
                                            mapped_type = ''
                                    if not matched_mapping:
                                        line_buffer += c
                                    if c == '.':
                                        potential_end = c

                                elif isinstance(char, LTAnno):
                                    # TODO: should check for cut words when a new line is inserted
                                    if len(mapped_type) == 0:
                                        if char.get_text() == ' ' or char.get_text() == '\n':
                                            line_buffer += ' '
                                    else:
                                        if char.get_text() == ' ':
                                            mapped_accumulators[mapped_type] += ' '
                            if verbose:
                                print('Page {page}: {line} --> {styles}'.format(page=page.pageid,
                                                                                line=line.get_text(),
                                                                                styles=styles))
                    if len(line_buffer) > 0:
                        sentences.append(Sentence(style=styles, content=line_buffer
                                                  .translate(self.SUPPORTED_LIGATURES)))
                    title = None
                    if 'title' in mapped_accumulators.keys():
                        title = mapped_accumulators['title']
                    document.add_content(Section(title=Title(style=mapped_type, content=title),
                                                 sentences=sentences))
                    mapped_type = ''

        return document
