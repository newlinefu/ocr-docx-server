import re
from docx.shared import Inches
from ocr_doc_transformer.classes.document_elements.paragraph.list_paragraph import ListParagraph
from ocr_doc_transformer.classes.lines_sequence import LinesSequence


class NumberBracketListParagraph(ListParagraph):
    def __init__(self, lines_sequence: LinesSequence, start_line_idx: int, end_line_idx: int):
        super().__init__(lines_sequence, start_line_idx, end_line_idx)

    def is_actual_list_item_head(self, line_idx):
        line = self.lines_sequence.lines[line_idx]
        line_text = line.text
        return re.match(r'\s*\d+\)', line_text) is not None

    @staticmethod
    def is_list_item_head(lines_sequence, line_idx):
        line = lines_sequence.lines[line_idx]
        line_text = line.text
        return re.match(r'\s*\d+\)', line_text) is not None

    def add_to(self, document):
        self.__prepare_text_for_doc()
        paragraph = document.add_paragraph(self.prepared_text, style='List Number')
        paragraph.paragraph_format.first_line_indent = Inches(0.5)

    def __prepare_text_for_doc(self):
        self.construct_paragraph_text()
        self.prepared_text = str.strip(re.sub(r'^\d+\)', '', self.text))
