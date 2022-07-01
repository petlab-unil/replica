from .mixins import NestedContentStrMixin


class TextElement:
    content = None
    style = None
    previous_element = None

    def __init__(self, content, style, previous_element=None):
        self.content = content
        self.style = style
        self.previous_element = previous_element

    def get_content(self):
        return self.content

    def get_style(self):
        return self.style

    def get_previous(self):
        return self.previous_element

    def __str__(self):
        return str(self.__dict__)


class Document(NestedContentStrMixin):
    name = None
    content = []

    def __init__(self, name):
        self.name = name

    def add_content(self, section):
        self.content.append(section)

    def get_content(self):
        return self.content


class Section(NestedContentStrMixin):
    title = None
    sentences = None

    def __init__(self, title, sentences):
        self.title = title
        self.sentences = sentences

    def get_sentences(self):
        return self.sentences

    def get_title(self):
        return self.title


class Title(TextElement):

    def __init__(self, **kwargs):
        super(Title, self).__init__(**kwargs)


class Sentence(TextElement):

    def __init__(self, **kwargs):
        super(Sentence, self).__init__(**kwargs)
