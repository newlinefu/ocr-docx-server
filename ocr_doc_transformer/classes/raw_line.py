class RawLine:
    def __init__(self, text, line_idx, left, top, x_diff_with_prev, y_diff_with_prev):
        self.text = text
        self.line_idx = line_idx
        self.left = left
        self.top = top
        self.x_diff_with_prev = x_diff_with_prev
        self.y_diff_with_prev = y_diff_with_prev
