from typing import List

from ocr_doc_transformer.classes.document_elements.block_content import BlockContent
from ocr_doc_transformer.classes.document_elements.document_part import DocumentPart
from ocr_doc_transformer.classes.document_elements.page_break.page_break import PageBreak
from ocr_doc_transformer.classes.document_elements.paragraph.dot_list_paragraph import DotListParagraph
from ocr_doc_transformer.classes.document_elements.paragraph.hollow_dot_list_paragraph import HollowDotListParagraph
from ocr_doc_transformer.classes.document_elements.paragraph.list_paragraph import ListParagraph
from ocr_doc_transformer.classes.document_elements.paragraph.number_bracket_list_paragraph import NumberBracketListParagraph
from ocr_doc_transformer.classes.document_elements.paragraph.number_dot_list_paragraph import NumberDotListParagraph
from ocr_doc_transformer.classes.document_elements.paragraph.paragraph import Paragraph
from ocr_doc_transformer.classes.document_elements.table.table import Table
from ocr_doc_transformer.classes.lines_sequence import LinesSequence


class PageStructure:
    def __init__(self, img_data, block_elements: List[BlockContent]):
        self.raw_img_data = img_data
        self.page_block_elements = block_elements
        self.lines_sequence = LinesSequence(img_data, block_elements)
        self.page_parts: List[DocumentPart] = []

        self.page_lists_paragraphs: List[ListParagraph] = []
        self.page_lists_paragraph_lines: List[int] = []

        self.create_page_structure()

    def create_page_structure(self):

        self.__fill_lists_items()

        # 5. Find nearest
        self.__fill_paragraphs()

        return self.page_parts

    def __get_average_line_bias(self):
        average_lines_bias = 0
        non_list_lines_count = 0
        for i in range(len(self.lines_sequence.lines)):
            according_list_items = list(filter(lambda p: p.is_line_belong(i), self.page_lists_paragraphs))
            if len(according_list_items) == 0:
                average_lines_bias += abs(self.lines_sequence.get_line(i).x_diff_with_prev)
                non_list_lines_count += 1
        average_lines_bias /= non_list_lines_count
        return average_lines_bias

    def __fill_paragraphs(self):
        page_paragraphs: List[Paragraph] = []
        average_lines_bias = self.__get_average_line_bias()

        if len(self.page_lists_paragraph_lines) == len(self.lines_sequence.lines):
            return

        non_list_lines = []
        for i in range(len(self.lines_sequence.lines)):
            if i not in self.page_lists_paragraph_lines:
                non_list_lines.append(i)
        start_index = non_list_lines[0]

        page_paragraphs.append(
            Paragraph(self.lines_sequence, start_index, start_index)
        )

        prev_line_idx = start_index
        line_idx = start_index + 1

        while line_idx < len(self.lines_sequence.lines):
            if line_idx in self.page_lists_paragraph_lines:
                list_paragraph = self.__find_list_by_line_index(line_idx)
                page_paragraphs.append(list_paragraph)
                line_idx = list_paragraph.end_line_idx + 1
                continue

            line_step = line_idx - prev_line_idx
            prev_line_idx = line_idx

            is_diff_negative = self.lines_sequence.get_line(line_idx).x_diff_with_prev < 0
            is_diff_more_than_avg = abs(self.lines_sequence.get_line(line_idx).x_diff_with_prev) > average_lines_bias

            if line_step > 1 or is_diff_negative and is_diff_more_than_avg:
                page_paragraphs.append(Paragraph(self.lines_sequence, line_idx, line_idx))
            else:
                page_paragraphs[-1].set_end_line_idx(line_idx)
            line_idx += 1

        # addition of elements to page parts

        actual_block_idx = 0

        for paragraph_idx in range(len(page_paragraphs)):
            actual_paragraph = page_paragraphs[paragraph_idx]

            # all of block elements were added
            if actual_block_idx >= len(self.page_block_elements):
                self.page_parts.append(actual_paragraph)
                continue

            actual_block_element = self.page_block_elements[actual_block_idx]
            paragraph_first_line_idx = actual_paragraph.start_line_idx
            paragraph_top = self.lines_sequence.lines[paragraph_first_line_idx].top

            # last of paragraphs will be added
            if paragraph_idx == len(page_paragraphs) - 1:
                if paragraph_top < actual_block_element.bbox.y1:
                    self.page_parts.append(actual_paragraph)
                    self.page_parts.append(actual_block_element)
                    actual_block_idx += 1
                if paragraph_top >= actual_block_element.bbox.y2:
                    self.page_parts.append(actual_block_element)
                    self.page_parts.append(actual_paragraph)
                    actual_block_idx += 1
            else:
                next_paragraph = page_paragraphs[paragraph_idx + 1]
                next_paragraph_first_line_idx = next_paragraph.start_line_idx
                next_paragraph_top = self.lines_sequence.lines[next_paragraph_first_line_idx].top
                if paragraph_top < actual_block_element.bbox.y1 and next_paragraph_top >= actual_block_element.bbox.y2:
                    self.page_parts.append(actual_paragraph)
                    self.page_parts.append(actual_block_element)
                    actual_block_idx += 1
                else:
                    self.page_parts.append(actual_paragraph)

        # addition of remaining elements

        for block_element in self.page_block_elements[actual_block_idx:]:
            self.page_parts.append(block_element)

    def __get_list_head_class(self, line_idx):

        if DotListParagraph.is_list_item_head(self.lines_sequence, line_idx):
            return DotListParagraph
        if HollowDotListParagraph.is_list_item_head(self.lines_sequence, line_idx):
            return HollowDotListParagraph
        if NumberDotListParagraph.is_list_item_head(self.lines_sequence, line_idx):
            return NumberDotListParagraph
        if NumberBracketListParagraph.is_list_item_head(self.lines_sequence, line_idx):
            return NumberBracketListParagraph

        return None

    def __fill_lists_items(self):

        for i in range(len(self.lines_sequence.lines)):
            list_head_class = self.__get_list_head_class(i)
            is_list_item_head = list_head_class is not None

            running_by_list = False
            if is_list_item_head:
                running_by_list = True

            if not running_by_list and len(self.page_lists_paragraphs) > 0:
                last_list_paragraph: ListParagraph = self.page_lists_paragraphs[-1]
                running_by_list = last_list_paragraph.is_list_paragraph_continue(i)

            if running_by_list:
                self.page_lists_paragraph_lines.append(i)

            if is_list_item_head:
                list_item = list_head_class(self.lines_sequence, i, i)
                self.page_lists_paragraphs.append(list_item)

            if not is_list_item_head and running_by_list:
                self.page_lists_paragraphs[-1].set_end_line_idx(i)

    def __find_list_by_line_index(self, line_idx):
        for paragraph in self.page_lists_paragraphs:
            if paragraph.is_line_belong(line_idx):
                return paragraph
        return None

    def add_to(self, document):
        for page_part in self.page_parts:
            page_part.add_to(document)

        page_break = PageBreak()
        page_break.add_to(document)
