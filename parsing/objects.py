from .mixins import NestedContentStrMixin


class TextElement:
    """
    This class represents a generic text element in the PDF document.

    Attributes
    __________
    content: str
        the string of the element represented by this class (like a sentence).
    style: dict
        the associated styles and character counts per style detected in the content.
    previous_element: TextElement
        the previous element encountered. WARNING: this is not used at the moment.

    Methods
    _______
    get_content()
        Getter for the string contained in the element.
    get_style()
        Getter for the styles detected in the content.
    get_previous()
        Getter for the instance of the preceding element.
    """
    content = None
    style = None
    previous_element = None

    def __init__(self, content, style, previous_element=None):
        """
        :param content: The content represented by this element.
        :param style: The styles detected in the content and their character count.
        :param previous_element: The element preceding this one.
        """
        self.content = content
        self.style = style
        self.previous_element = previous_element

    def get_content(self):
        """
        Getter for the content represented by this class.
        :return: the content string.
        """
        return self.content

    def get_style(self):
        """
        Getter for the styles detected in the content.
        :return: the styles collection with their character count.
        """
        return self.style

    def get_previous(self):
        """
        Getter for the element preceding this one.
        :return: the instance of the previous element.
        """
        return self.previous_element

    def __str__(self):
        return str(self.__dict__)


class Document(NestedContentStrMixin):
    """
    This class represents the whole PDF document. It will likely contain all the content parsed in the document.

    Attributes
    __________
    name: str
        The name of the document.
    content: list
        A list containing the sections of the document.

    Methods
    _______
    add_content(section)
        Append a section to the document.
    get_content()
        Getter for the sections in the document.
    """
    name = None
    content = []

    def __init__(self, name):
        """
        :param name: The name of the document.
        """
        self.name = name
        self.content = []

    def add_content(self, section):
        """
        Appends a section to the document.
        :param section: the section object to add.
        """
        self.content.append(section)

    def get_content(self):
        """
        Getter for the sections contained in the document.
        :return: the sections' list.
        """
        return self.content


class Section(NestedContentStrMixin):
    """
    This class represents a section of the PDF Document. A section is defined by a title and list of sentences.

    Attributes
    __________
    title: Title
        An instance of the Title class representing the title of the section.
    sentences: list
        A list of instances of the Sentence class representing the sentences contained in the section.

    Methods
    _______
    get_sentences()
        Getter for the sentences contained in the section.
    get_title()
        Getter for the title of the section.
    """
    title = None
    sentences = None

    def __init__(self, title, sentences):
        """
        :param title: an instance of the Title class representing the title of the section.
        :param sentences: a list of instances of the Section class representing the content of the section.
        """
        self.title = title
        self.sentences = sentences

    def get_sentences(self):
        """
        Getter for the sentences contained in the section.
        :return: a list of instances of the Sentence class.
        """
        return self.sentences

    def get_title(self):
        """
        Getter for the title of the section.
        :return: an instance of the Title class.
        """
        return self.title


class Title(TextElement):
    """
    This class represent the title of a section detected in the PDF document. For information on the attributes
    and methods, see TextElement class.

    """
    def __init__(self, **kwargs):
        """
        :param kwargs: the content and styles provided as keywords.
        """
        super(Title, self).__init__(**kwargs)


class Sentence(TextElement):
    """
    This class represent a sentence in a section detected in the PDF document. For information on the attributes
    and methods, see TextElement class.

    """
    def __init__(self, **kwargs):
        """
        :param kwargs: the content and styles provided as keywords.
        """
        super(Sentence, self).__init__(**kwargs)
