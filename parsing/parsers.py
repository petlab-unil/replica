class DocumentParser:

    def __init__(self, document, map):
        self.document = document
        self.map = map

    def parse(self, verbose=False):
        from os.path import basename
        from pdfminer.high_level import extract_pages
        from pdfminer.layout import LTTextBoxHorizontal, LTTextLine, LTChar
        from parsing.objects import Section, Sentence, Title, Document

        pages = extract_pages(self.document)
        if verbose:
            print('####\nParsing Content in document {}\n####'.format(basename(self.document)))
        document = Document(basename(self.document))

        for page in pages: # Hope you like indented code
            for container in page:
                if isinstance(container, LTTextBoxHorizontal):
                    line_buffer = ''
                    mapped_buffer = ''  # This might become a map with all the specific text encountered
                    sentences = []
                    mapped_type = ''  # might also become a map together with mapped_buffer
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
                                        if char.fontname == mapped_elt['style']:  # and char.size == mapped_elt['size']
                                            mapped_buffer += c
                                            mapped_type = mapped_elt['type']
                                            matched_mapping = True
                                    if not matched_mapping:
                                        line_buffer += c
                                    if c == '.':
                                        potential_end = c
                            if verbose:
                                print('Page {page}: {line} --> {styles}'.format(page=page.pageid,
                                                                                line=line.get_text(),
                                                                                styles=styles))
                    if len(line_buffer) > 0:
                        sentences.append(Sentence(style=styles, content=line_buffer))
                    document.add_content(Section(title=Title(style=mapped_type, content=mapped_buffer),
                                                 sentences=sentences))
        return document
