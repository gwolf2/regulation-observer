import os
import re
from pathlib import Path

def parse_filename(filename):
    """Parse filename to extract Title, Subtitle, Chapter, and Subchapter."""
    pattern = r"t-(\d+)_st-(\w+)_c-(\w+)_sc-(\w+)"
    match = re.match(pattern, filename)
    if match:
        title, subtitle, chapter, subchapter = match.groups()
        return {
            'title': title,
            'subtitle': 'None' if subtitle == 'None' else subtitle,
            'chapter': 'None' if chapter == 'None' else chapter,
            'subchapter': 'None' if subchapter == 'None' else subchapter
        }
    return None

def count_words(content):
    """Count words in the content."""
    words = re.findall(r'\b\w+\b', content)
    return len(words)

def find_subtitle_section(content, subtitle):
    """Find the start and end of the subtitle section."""
    pattern_start = rf'<DIV2 N="{subtitle}" TYPE="SUBTITLE">\s*<HEAD>\s*SUBTITLE {subtitle}[^<]*</HEAD>'
    match_start = re.search(pattern_start, content, re.DOTALL)
    if match_start:
        start_pos = match_start.start()
        # Look for the closing </DIV2> or next <DIV2>
        end_match = re.search(r'</DIV2>|<DIV2 N="\w+" TYPE="SUBTITLE">', content[start_pos + 1:])
        end_pos = start_pos + 1 + end_match.start() if end_match else len(content)
        return start_pos, end_pos
    return None, None

def find_chapter_section(content, chapter):
    """Find the start and end of the chapter section."""
    pattern_start = rf'<DIV3 N="{chapter}" TYPE="CHAPTER">\s*<HEAD>\s*CHAPTER {chapter}[^<]*</HEAD>'
    match_start = re.search(pattern_start, content, re.DOTALL)
    if match_start:
        start_pos = match_start.start()
        # Look for the closing </DIV3>
        end_match = re.search(r'</DIV3>', content[start_pos + 1:])
        end_pos = start_pos + 1 + end_match.start() + len('</DIV3>') if end_match else len(content)
        return start_pos, end_pos
    return None, None

def find_subchapter_section(content, chapter, subchapter):
    """Find the start and end of the subchapter section within a chapter if specified."""
    if chapter != 'None':
        chapter_start = rf'<DIV3 N="{chapter}" TYPE="CHAPTER">\s*<HEAD>\s*CHAPTER {chapter}[^<]*</HEAD>'
        chapter_match = re.search(chapter_start, content, re.DOTALL)
        if not chapter_match:
            return None, None
        start_search_pos = chapter_match.start()
        chapter_end_match = re.search(r'</DIV3>', content[start_search_pos + 1:])
        chapter_end_pos = start_search_pos + 1 + chapter_end_match.start() + len('</DIV3>') if chapter_end_match else len(content)
    else:
        start_search_pos = 0
        chapter_end_pos = len(content)

    pattern_start = rf'<DIV4 N="{subchapter}" TYPE="SUBCHAP">\s*<HEAD>\s*SUBCHAPTER {subchapter}[^<]*</HEAD>'
    match_start = re.search(pattern_start, content[start_search_pos:chapter_end_pos], re.DOTALL)
    if match_start:
        start_pos = start_search_pos + match_start.start()
        end_match = re.search(r'</DIV4>', content[start_pos + 1:chapter_end_pos])
        end_pos = start_pos + 1 + end_match.start() + len('</DIV4>') if end_match else chapter_end_pos
        return start_pos, end_pos
    return None, None

def process_xml_file(filepath):
    """Process a single XML file to keep only the most specific section and overwrite the original."""
    filename = Path(filepath).stem
    params = parse_filename(filename)
    
    if not params:
        print(f"Skipping {filepath}: Invalid filename format")
        return
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_word_count = count_words(content)
    
    # Determine the most specific section to extract
    start_pos, end_pos = None, None
    section_type = ""
    
    if params['subchapter'] != 'None':
        start_pos, end_pos = find_subchapter_section(content, params['chapter'], params['subchapter'])
        section_type = f"Subchapter {params['subchapter']}"
        if params['chapter'] != 'None':
            section_type += f" in Chapter {params['chapter']}"
    elif params['chapter'] != 'None':
        start_pos, end_pos = find_chapter_section(content, params['chapter'])
        section_type = f"Chapter {params['chapter']}"
    elif params['subtitle'] != 'None':
        start_pos, end_pos = find_subtitle_section(content, params['subtitle'])
        section_type = f"Subtitle {params['subtitle']}"
    
    if start_pos is None or end_pos is None:
        print(f"Skipping {filepath}: Desired section ({section_type}) not found. Word count: {original_word_count}")
        return
    
    # Extract the desired section
    desired_content = content[start_pos:end_pos]
    new_word_count = count_words(desired_content)
    
    # Add basic XML structure
    header = '<?xml version="1.0" encoding="UTF-8"?>\n<DOC>\n'
    footer = '\n</DOC>'
    final_content = header + desired_content + footer
    
    # Overwrite the original file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(final_content)
    print(f"Processed {filepath}: {section_type} kept. Words: {original_word_count} -> {new_word_count}")

def process_directory(input_dir):
    """Process all XML files in the directory and subdirectories."""
    total_words_before = 0
    total_words_after = 0
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.xml'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                total_words_before += count_words(content)
                process_xml_file(filepath)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                total_words_after += count_words(content)
    print(f"Total word count: Before: {total_words_before}, After: {total_words_after}")

# Usage
if __name__ == "__main__":
    input_directory = r".\data"
    process_directory(input_directory)