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
    LINE_END_TOKEN = '\. [A-Z]'
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

    def __pdf_to_text(self, verbose=False):
        from os.path import basename
        from pdfminer.high_level import extract_pages
        from pdfminer.layout import LTTextBoxHorizontal, LTTextLine, LTChar
        from parsing.objects import Section, Sentence, Title, Document

        pages = extract_pages(self.document)
        line_buffer = ''
        styles_stack = []
        current_style = None
        char_counter = 0
        for page in pages:  # Hope you like indented code
            for container in page:
                if isinstance(container, LTTextBoxHorizontal):
                    for line in container:
                        if isinstance(line, LTTextLine):
                            for char in line:
                                if isinstance(char, LTChar):
                                    token = char.get_text().replace('\xa0', '').replace('\xad', '')
                                    if current_style is None:
                                        current_style = {}
                                    if 'name' not in current_style.keys():
                                        current_style['name'] = char.fontname
                                        current_style['start'] = char_counter
                                    elif char.fontname != current_style['name'] and token != ' ':
                                        current_style['end'] = char_counter
                                        if verbose:
                                            print(line_buffer[current_style['start']:current_style['end']],
                                                  current_style)
                                        styles_stack.append(current_style)
                                        current_style = {'name': char.fontname, 'start': char_counter}
                                    if len(token) > 0:
                                        line_buffer += token
                                        char_counter += 1
                                elif isinstance(char, LTAnno):
                                    token = char.get_text().replace('\xa0', '')
                                    if token == ' ' and line_buffer[-1:] != ' ':
                                        line_buffer += ' '
                                        char_counter += 1
                                    elif token == '\n':
                                        if len(line_buffer) > 1 and line_buffer[-1:] == '-':
                                            line_buffer = line_buffer.rstrip(line_buffer[-1]) + ' '
                                        elif line_buffer[-1:] != ' ':
                                            line_buffer += ' '
                                            char_counter += 1
                    styles_stack.append(current_style)
        return line_buffer, styles_stack

    def parse(self, verbose=False):
        """
        Parses the document and returns a Document class containing the sections, sentences and titles.

        :param verbose: print additional process information or not.
        :return: an object, instance of the Document class (contains the sections with their titles and sentences).
        """
        from .objects import Title, Sentence, Section, Document
        from os.path import basename
        from re import search, finditer

        document = Document(basename(self.document))
        text, styles = self.__pdf_to_text(verbose=verbose)

        line_buffer = ''
        sentences_buffer = []
        sentence_styles = []
        current_title = None

        for style in styles:
            matched_mapping = False
            for mapped_style in self.map:
                if style['name'] == mapped_style['style'] and mapped_style['type'] == 'title':
                    if current_title is not None:
                        sentences_buffer.append(Sentence(content=line_buffer, style=None, previous_element=None))
                        document.add_content(section=Section(title=current_title, sentences=sentences_buffer))
                        sentences_buffer = []
                        sentence_styles = []
                        line_buffer = ''
                    content = text[style['start']:style['end']]
                    current_title = Title(style=mapped_style['style'], content=content)
                    matched_mapping = True
                    break
            if matched_mapping:
                continue

            if text[style['start'] - 1] != ' ':
                line = text[style['start'] - 1:style['end']]
            else:
                line = text[style['start']:style['end']]
            matches = finditer(self.LINE_END_TOKEN, line)
            cur_start = 0
            for match in matches:
                split_start, split_end = match.span()
                sentence_content = ''
                if len(line_buffer) > 0:
                    sentence_content = line_buffer
                    line_buffer = ''
                sentences_buffer.append(Sentence(content=sentence_content + line[cur_start:split_start], style=None,
                                                 previous_element=None))
                cur_start = split_end - 1
            if cur_start < len(line):
                print(line[cur_start:len(line)-1], style, current_title)
                line_buffer += line[cur_start:len(line)-1]

        return document