import re
import markdown
import os

def strip_escaped_backslashes(text):
    # Fixes \*, \#, \|, \*\*, etc.
    return re.sub(r'\\(.)', r'\1', text)

def compress_excess_newlines(text):
    # Replace any occurrence of 4 or more newlines with just 2.
    return re.sub(r'\n{4,}', '\n\n', text)

def parse_and_convert_tables(text):
    lines = text.splitlines()
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith('|'):
            j = i + 1
            found_sep = False
            while j < len(lines):
                next_line = lines[j].strip()
                if next_line.startswith('|') and '---' in next_line:
                    found_sep = True
                    break
                elif next_line == '':
                    j += 1
                else:
                    break
            
            if found_sep:
                row_lines = [lines[i].strip(), lines[j].strip()]
                
                k = j + 1
                while k < len(lines):
                    cur_line = lines[k].strip()
                    if cur_line == '':
                        k += 1
                        continue
                    if cur_line.startswith('|'):
                        row_lines.append(cur_line)
                        k += 1
                    else:
                        break
                
                header_cols = [col.strip() for col in row_lines[0].split('|')[1:-1]]
                sep_cols = [col.strip() for col in row_lines[1].split('|')[1:-1]]
                alignments = ['left'] * len(header_cols)
                for idx, col in enumerate(sep_cols):
                    if idx < len(alignments):
                        if col.startswith(':') and col.endswith(':'): alignments[idx] = 'center'
                        elif col.endswith(':'): alignments[idx] = 'right'
                
                data_rows = []
                for row in row_lines[2:]:
                    if row == '': continue
                    cols = [col.strip() for col in row.split('|')[1:-1]]
                    data_rows.append(cols)
                
                html_table = '<table>\n<thead>\n<tr>'
                for idx, h in enumerate(header_cols):
                    align = alignments[idx] if idx < len(alignments) else 'left'
                    html_table += f'<th style="text-align:{align}">{h}</th>'
                html_table += '</tr>\n</thead>\n<tbody>\n'
                
                for row in data_rows:
                    html_table += '<tr>'
                    for idx, col in enumerate(row):
                        align = alignments[idx] if idx < len(alignments) else 'left'
                        html_table += f'<td style="text-align:{align}">{col}</td>'
                    html_table += '</tr>\n'
                
                html_table += '</tbody>\n</table>\n'
                new_lines.append(html_table)
                i = k
                continue
        
        new_lines.append(lines[i])
        i += 1
    return '\n'.join(new_lines)

def convert_code_blocks_to_html(text):
    # Directly matches ```basic ... ``` and replaces it with raw HTML.
    def replace_basic_block(match):
        code_content = match.group(1)
        # Split the code into lines
        lines = code_content.split('\n')
        # Filter out any lines that are empty or contain only spaces
        cleaned_lines = [line for line in lines if line.strip() != '']
        # Join the remaining lines with a single newline
        final_code = '\n'.join(cleaned_lines)
        return f'<pre><code>{final_code}</code></pre>'

    return re.sub(r'```basic\n(.*?)```', replace_basic_block, text, flags=re.DOTALL)

def generate_manual(input_file, output_file):
    if not os.path.exists(input_file):
        print(f"Error: '{input_file}' not found. Ensure your text file is named 'manual.txt'.")
        return

    print("1. Reading the text file...")
    with open(input_file, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    print("2. Stripping escaped backslashes (fixing \*, \#, \*\*, \|)...")
    clean_text = strip_escaped_backslashes(raw_text)

    print("3. Compressing massive gaps from OCR...")
    compressed_text = compress_excess_newlines(clean_text)

    print("4. Converting pipe tables directly into HTML tables...")
    text_with_tables = parse_and_convert_tables(compressed_text)

    print("5. Converting code blocks to raw HTML and removing intra-code gaps...")
    final_text = convert_code_blocks_to_html(text_with_tables)

    print("6. Converting the remaining text to Markdown...")
    html_body = markdown.markdown(
        final_text,
        extensions=['tables']
    )

    # Strip empty paragraphs that Markdown always creates
    html_body = re.sub(r'<p>\s*</p>', '', html_body)

    # UPDATED CSS for dense, printed-style text
    full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>BBC BASIC Reference Manual</title>
<style>
    body {{
        font-family: Georgia, 'Times New Roman', serif;
        max-width: 800px;
        margin: 30px auto;
        padding: 0 20px;
        line-height: 1.5;
        color: #111;
        background-color: #fdfdfd;
    }}
    h1, h2, h3, h4 {{
        font-family: Arial, Helvetica, sans-serif;
        color: #222;
        margin-top: 1.8em;
        margin-bottom: 0.4em;
    }}
    h1 {{ border-bottom: 2px solid #333; padding-bottom: 8px; }}
    h2 {{ border-bottom: 1px solid #ccc; padding-bottom: 4px; }}
    p {{
        margin: 0 0 0.2em 0;
        text-align: justify;
    }}
    pre {{
        background: #f2f2f2;
        border: 1px solid #d0d0d0;
        border-left: 4px solid #666;
        padding: 10px 14px;
        margin: 0.4em 0;
        border-radius: 3px;
        overflow-x: auto;
        font-size: 0.9em;
        line-height: 1.5;
    }}
    code {{
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        background: #f2f2f2;
        padding: 2px 4px;
        border-radius: 3px;
        font-size: 0.9em;
        color: #222;
    }}
    pre code {{ background: transparent; padding: 0; border: none; }}
    ul {{ margin: 0.2em 0; padding-left: 25px; }}
    li {{ margin: 3px 0; }}
    table {{
        border-collapse: collapse;
        width: 100%;
        margin: 0.6em 0;
        font-family: Arial, Helvetica, sans-serif;
        font-size: 0.9em;
    }}
    th, td {{
        border: 1px solid #aaa;
        padding: 6px 10px;
    }}
    th {{ background-color: #e9e9e9; font-weight: bold; text-align: left; }}
</style>
</head>
<body>
{html_body}
</body>
</html>"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_html)

    print(f"\nSUCCESS! The manual has been saved as:\n{output_file}")
    print("Open this file in your browser.")

if __name__ == "__main__":
    generate_manual('manual.txt', 'BBC_BASIC_Manual.html')