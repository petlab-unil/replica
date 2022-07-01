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
        for page in pages:
            for container in page:
                if isinstance(container, LTTextBoxHorizontal):
                    line_buffer = ''
                    current_title = ''
                    sentences = []
                    title_style = ''
                    for line in container:
                        if isinstance(line, LTTextLine):
                            styles = {}
                            for char in line:
                                if isinstance(char, LTChar):
                                    if char.fontname not in styles.keys():
                                        styles[char.fontname] = 1
                                    else:
                                        styles[char.fontname] += 1

                                    if char.fontname == self.map[0]['style']: # FIXME this needs to handle all mappings
                                        current_title += char.get_text()
                                        title_style = char.fontname
                                    else:
                                        line_buffer += char.get_text()

                                    if char.get_text() == '.':
                                        sentences.append(Sentence(style=styles, content=line_buffer))
                                        line_buffer = ''
                            if verbose:
                                print('Page {page}: {line} --> {styles}'.format(page=page.pageid,
                                                                                line=line.get_text(),
                                                                                styles=styles))
                    document.add_content(Section(title=Title(style=title_style, content=current_title),
                                                 sentences=sentences))
        return document
