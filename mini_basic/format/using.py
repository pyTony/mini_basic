"""MBASIC-style PRINT USING format engine (BASIC-80 / MBASIC 5.21).

``UsingFormatter`` parses a format string into literal and field tokens, then
formats a sequence of values (strings or numbers) for one PRINT USING output.

Format features
---------------
- ``#`` / ``.`` numeric fields with optional ``,`` thousands separator
- ``+`` / ``-`` leading or trailing sign slots
- ``**`` asterisk fill, ``$$`` dollar prefix
- ``^^^^`` exponential notation
- ``!`` first character, ``&`` full string, ``\\ .. \\`` fixed-width string
- ``_c`` literal character escape
"""


class UsingFormatter:
    """Format strings and numbers according to PRINT USING format strings."""

    def __init__(self, format_string: str):
        self.format_string = format_string
        self.fields = []
        self.parse_format()

    def parse_format(self) -> None:
        i = 0
        while i < len(self.format_string):
            ch = self.format_string[i]

            if ch == '_' and i + 1 < len(self.format_string):
                self.fields.append(('literal', self.format_string[i + 1]))
                i += 2
                continue

            if ch == '!':
                self.fields.append(('string', {'type': 'first'}))
                i += 1
                continue

            if ch == '&':
                self.fields.append(('string', {'type': 'full'}))
                i += 1
                continue

            if ch == '\\':
                j = i + 1
                space_count = 0
                while j < len(self.format_string) and self.format_string[j] == ' ':
                    space_count += 1
                    j += 1
                if j < len(self.format_string) and self.format_string[j] == '\\':
                    width = 2 + space_count
                    self.fields.append(('string', {'type': 'fixed', 'width': width}))
                    i = j + 1
                    continue
                self.fields.append(('literal', ch))
                i += 1
                continue

            if ch in '#.+-' or (
                ch == '*'
                and i + 1 < len(self.format_string)
                and self.format_string[i + 1] in '*$'
            ):
                num_spec = self.parse_numeric_field(i)
                self.fields.append(('numeric', num_spec))
                i = num_spec['end_pos']
                continue

            if ch == '$' and i + 1 < len(self.format_string) and self.format_string[i + 1] == '$':
                num_spec = self.parse_numeric_field(i)
                self.fields.append(('numeric', num_spec))
                i = num_spec['end_pos']
                continue

            self.fields.append(('literal', ch))
            i += 1

    def parse_numeric_field(self, start_pos: int) -> dict:
        spec = {
            'start_pos': start_pos,
            'end_pos': start_pos,
            'digit_count': 0,
            'decimal_pos': -1,
            'digits_after_decimal': 0,
            'has_decimal': False,
            'leading_sign': False,
            'trailing_sign': False,
            'trailing_minus_only': False,
            'dollar_sign': False,
            'asterisk_fill': False,
            'comma': False,
            'exponential': False,
        }

        i = start_pos
        format_str = self.format_string

        if i + 2 < len(format_str) and format_str[i:i + 3] == '**$':
            spec['asterisk_fill'] = True
            spec['dollar_sign'] = True
            spec['digit_count'] += 3
            i += 3
        elif i + 1 < len(format_str) and format_str[i:i + 2] == '**':
            spec['asterisk_fill'] = True
            spec['digit_count'] += 2
            i += 2
        elif i + 1 < len(format_str) and format_str[i:i + 2] == '$$':
            spec['dollar_sign'] = True
            spec['digit_count'] += 2
            i += 2
        elif format_str[i] == '+':
            spec['leading_sign'] = True
            i += 1

        decimal_found = False
        while i < len(format_str):
            ch = format_str[i]
            if ch == '#':
                spec['digit_count'] += 1
                if decimal_found:
                    spec['digits_after_decimal'] += 1
                i += 1
            elif ch == '.':
                if not decimal_found:
                    spec['decimal_pos'] = i - start_pos
                    spec['has_decimal'] = True
                    decimal_found = True
                    i += 1
                else:
                    break
            elif ch == ',':
                spec['comma'] = True
                spec['digit_count'] += 1
                i += 1
            else:
                break

        if i + 3 < len(format_str) and format_str[i:i + 4] == '^^^^':
            spec['exponential'] = True
            i += 4

        if i < len(format_str):
            if format_str[i] == '+':
                spec['trailing_sign'] = True
                i += 1
            elif format_str[i] == '-':
                spec['trailing_minus_only'] = True
                i += 1

        spec['end_pos'] = i
        return spec

    def format_values(self, values) -> str:
        result = []
        value_idx = 0

        for field_type, field_spec in self.fields:
            if field_type == 'literal':
                result.append(field_spec)
            elif field_type == 'string':
                if value_idx < len(values):
                    result.append(self.format_string_field(str(values[value_idx]), field_spec))
                    value_idx += 1
            elif field_type == 'numeric':
                if value_idx < len(values):
                    value = values[value_idx]
                    if isinstance(value, str):
                        try:
                            value = float(value)
                        except ValueError:
                            value = 0.0
                    result.append(self.format_numeric_field(value, field_spec))
                    value_idx += 1

        return ''.join(result)

    def format_string_field(self, value: str, spec: dict) -> str:
        if spec['type'] == 'first':
            return value[0] if value else ' '
        if spec['type'] == 'full':
            return value
        if spec['type'] == 'fixed':
            width = spec['width']
            if len(value) >= width:
                return value[:width]
            return value.ljust(width)
        return value

    def format_numeric_field(self, value: float, spec: dict) -> str:
        if spec['exponential']:
            return self.format_exponential(value, spec)

        precision = spec['digits_after_decimal'] if spec['decimal_pos'] >= 0 else 0
        original_negative = value < 0
        rounded = round(value, precision) if precision > 0 else round(value)

        if rounded == 0 and original_negative:
            is_negative = True
        else:
            is_negative = rounded < 0
        abs_value = abs(rounded)

        if precision > 0:
            num_str = f'{abs_value:.{precision}f}'
            if spec['decimal_pos'] == 0 and abs_value < 1 and num_str.startswith('0.'):
                num_str = num_str[1:]
        else:
            num_str = str(int(abs_value))

        if spec['comma'] and '.' in num_str:
            int_part, dec_part = num_str.split('.')
            num_str = self.add_thousand_separators(int_part) + '.' + dec_part
        elif spec['comma']:
            num_str = self.add_thousand_separators(num_str)

        field_width = spec['digit_count']
        if spec['has_decimal']:
            field_width += 1
        if spec['leading_sign'] or spec['trailing_sign'] or spec['trailing_minus_only']:
            field_width += 1

        available_width = field_width
        if spec['leading_sign'] or spec['trailing_sign'] or spec['trailing_minus_only']:
            available_width -= 1
        if spec['dollar_sign']:
            available_width -= 1

        if len(num_str) > available_width:
            return '%' + num_str

        content_width = len(num_str)
        if spec['dollar_sign']:
            content_width += 1
        if spec['leading_sign'] or spec['trailing_sign'] or spec['trailing_minus_only']:
            content_width += 1

        padding_needed = field_width - content_width
        result_parts = []

        if spec['leading_sign']:
            result_parts.append(' ' * max(0, padding_needed))
            result_parts.append('-' if is_negative else '+')
        else:
            if spec['asterisk_fill']:
                result_parts.append('*' * max(0, padding_needed))
            else:
                result_parts.append(' ' * max(0, padding_needed))

        if spec['dollar_sign']:
            result_parts.append('$')

        result_parts.append(num_str)

        if spec['trailing_sign']:
            result_parts.append('-' if is_negative else '+')
        elif spec['trailing_minus_only']:
            result_parts.append('-' if is_negative else ' ')

        return ''.join(result_parts)

    def format_exponential(self, value: float, spec: dict) -> str:
        precision = spec['digits_after_decimal'] if spec['digits_after_decimal'] > 0 else 2
        if value == 0:
            exp_str = f"0.{'0' * precision}E+00"
        else:
            exp_str = f'{value:.{precision}e}'.upper()
            mantissa, exponent = exp_str.split('E')
            exp_str = f'{mantissa}E{int(exponent):+03d}'

        if spec['leading_sign']:
            if not exp_str.startswith('-'):
                exp_str = '+' + exp_str
        elif spec['trailing_sign']:
            if exp_str.startswith('-'):
                exp_str = exp_str[1:] + '-'
            else:
                exp_str = exp_str + '+'
        elif spec['trailing_minus_only']:
            if exp_str.startswith('-'):
                exp_str = exp_str[1:] + '-'
            else:
                exp_str = ' ' + exp_str
        elif not exp_str.startswith('-'):
            exp_str = ' ' + exp_str
        return exp_str

    def add_thousand_separators(self, num_str: str) -> str:
        if len(num_str) <= 3:
            return num_str
        result = []
        for i, digit in enumerate(reversed(num_str)):
            if i > 0 and i % 3 == 0:
                result.append(',')
            result.append(digit)
        return ''.join(reversed(result))
