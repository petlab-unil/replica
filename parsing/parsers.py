from pdfminer.layout import LTAnno


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
    from enum import Enum

    class ParserState(Enum):
        """
        This class serves the only purpose of storing an enumeration of the states from the parser.

        Attributes
        ----------

        NULL: int
            a null state, when there is nothing treated.
        LINE: int
            the parser is parsing a regular sentence.
        MAP_MATCH: int
            an element of the map has matched.
        LINE_END: int
            the parser has reached a potential end of the sentence.
        """
        NULL = 0
        LINE = 1
        MAP_MATCH = 2
        LINE_END = 3

    # We need to translate some ligatures in unicode otherwise the text has special hexadecimal codes for them.
    SUPPORTED_LIGATURES = {
        0xfb00: u'ff',
        0xfb01: u'fi',
        0xfb02: u'fl',
        0xfb03: u'ffi',
        0xfb04: u'ffl',
    }

    # This is what defines the end of the sentence, additionally, we test that the next character is uppercase
    LINE_END_TOKEN = '. '
    POTENTIAL_END_TOKEN = '.' # detecting this will make the parser go into ParserState.LINE_END

    current_state = ParserState.NULL  # current state of the parser

    def __init__(self, document, map):
        """
        :param document: the path to the PDF document to parse.
        :param map: the path to the JSON map to use in order to detect the specific titles according to the font used.
        """
        self.document = document
        self.map = map
        self.current_state = self.ParserState.NULL

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
                    for line in container:
                        if isinstance(line, LTTextLine):
                            styles = {}
                            for char in line:
                                if isinstance(char, LTChar):
                                    token = char.get_text()
                                    if self.current_state is self.ParserState.LINE_END:
                                        if len(line_buffer) >= 2 and line_buffer[-2:] == self.LINE_END_TOKEN \
                                                and token.isupper():
                                            sentences.append(Sentence(style=styles, content=line_buffer))
                                            line_buffer = ''
                                            self.current_state = self.ParserState.LINE
                                    if char.fontname not in styles.keys():
                                        styles[char.fontname] = 1
                                    else:
                                        styles[char.fontname] += 1
                                    matched_mapping = False
                                    for mapped_elt in self.map:
                                        if char.fontname == mapped_elt['style'] or \
                                           (token == ' ' and self.current_state == self.ParserState.MAP_MATCH):
                                            mapped_buffer += token
                                            mapped_type = mapped_elt['type']
                                            if mapped_elt['type'] not in mapped_accumulators.keys():
                                                mapped_accumulators[mapped_elt['type']] = ''
                                            mapped_accumulators[mapped_elt['type']] += token
                                            self.current_state = self.ParserState.MAP_MATCH
                                            matched_mapping = True
                                    if not matched_mapping:
                                        self.current_state = self.ParserState.LINE
                                    if self.current_state == self.ParserState.LINE:
                                        line_buffer += token
                                        mapped_type = ''
                                    if token == self.POTENTIAL_END_TOKEN:
                                        self.current_state = self.ParserState.LINE_END
                                elif isinstance(char, LTAnno):
                                    if self.current_state != self.ParserState.MAP_MATCH:
                                        if char.get_text() == ' ' and line_buffer[-1:] != ' ':
                                            line_buffer += ' '
                                        elif char.get_text() == '\n':
                                            if len(line_buffer) > 1 and line_buffer[-1:] == '-':
                                                line_buffer = line_buffer.rstrip(line_buffer[-1])
                                            else:
                                                line_buffer += ' '
                                    else:
                                        if char.get_text() == ' ':
                                            mapped_accumulators[mapped_type] += ' '
                                        elif char.get_text() == '\n':
                                            if len(line_buffer) > 1 and line_buffer[-1:] == '-':
                                                line_buffer = line_buffer.rstrip(line_buffer[-1])
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

        return document
