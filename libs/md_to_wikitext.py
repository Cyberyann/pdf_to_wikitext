import re
from libs.logger import log
from libs.mediawiki_api import MediaWikiApi
from pathlib import Path


def convert_table_to_wikitable(table_text: str) -> str:
    """
    Convert a Markdown table to a wikitable.
    """
    lines = table_text.strip().split("\n")
    if len(lines) < 2:
        return table_text

    # header extraction
    header = lines[0]
    # Ignore separate line  (|---|---|)
    # Datas start at line 2
    data_lines = lines[2:] if len(lines) > 2 else []

    # Parse header
    header_cells = [cell.strip() for cell in header.split("|") if cell.strip()]

    # Construct wikitable
    result = ['{| class="wikitable"']

    # Add header
    result.append("! " + " !! ".join(header_cells))

    # Add lines
    for line in data_lines:
        cells = [cell.strip() for cell in line.split("|") if cell.strip()]
        if cells:
            result.append("|-")
            result.append("| " + " || ".join(cells))

    result.append("|}")

    return "\n".join(result)


def md_to_wikitext(
    content: str,
    footer: str,
    ignore_pages: str,
    page_name: str,
    image_path: str,
) -> str:
    """
    Transform Markdown content to wikitext.
    """

    uploader = MediaWikiApi()
    if not uploader.login():
        log("Cant connect to mediawiki")

    # First manage table
    table_pattern = r"(\|.+\|\n\|[-:\s|]+\|\n(?:\|.+\|\n?)*)"

    def replace_table(match):
        return convert_table_to_wikitable(match.group(1))

    content = re.sub(table_pattern, replace_table, content)

    lines = content.split("\n")
    transformed_lines = []
    ignore_page_list = ignore_pages.split(",")

    image_index = 0
    page_number = 0
    for line in lines:
        # Remove strat whitespace
        line = line.lstrip()

        footer_escaped = re.escape(footer)
        if re.search(f"{footer_escaped} \\*\\*\\d+\\*\\*", line):
            page_number += 1
            continue

        if str(page_number) in ignore_page_list:
            continue

        # Rule 1: _Text_ -> ''Text''
        line = re.sub(r"_Table (\d+)\.([^_]+)_", r"''Table \1.\2''", line)

        # Rule 2: - Item -> * Item
        if line.startswith("- "):
            line = "* " + line[2:]

        # Rule 3: **1** **text** -> == 1 text ==
        line = re.sub(r"\*\*(\d+)\*\*\s+\*\*([^*]+)\*\*", r"== \1 \2 ==", line)

        # Rule 4: **1.1** **text** -> === 1.1 text ===
        line = re.sub(r"\*\*(\d+\.\d+)\*\*\s+\*\*([^*]+)\*\*", r"=== \1 \2 ===", line)

        # Rule 5: **1.1.1** **text** -> ==== 1.1.1 text ====
        line = re.sub(
            r"\*\*(\d+\.\d+\.\d+)\*\*\s+\*\*([^*]+)\*\*", r"==== \1 \2 ====", line
        )

        # Rule 6: **Text** -> '''Text'''
        line = re.sub(r"\*\*([^*]+)\*\*", r"'''\1'''", line)

        # Rule 7: Image
        match = re.search(r"!\[\]\((.*?)\)", line)
        if match:
            image_source = match.group(1)
            dest_name = f"{page_name} {str(image_index)}.png"
            image_dest = image_path + dest_name

            Path(image_source).rename(image_dest)
            uploader.upload_image(image_dest, "")

            image_index += 1
            line = f"[[File:{dest_name}|center|thumb]]"

        transformed_lines.append(line)

    result = "\n".join(transformed_lines)

    # Remove empty lines
    result = re.sub(r"([a-zA-Z])\n{5}([a-zA-Z])", r"\1 \2", result)
    result = re.sub(r"([a-zA-Z])\n{4}([a-zA-Z])", r"\1 \2", result)
    result = re.sub(r"([a-zA-Z])\n{3}([a-zA-Z])", r"\1 \2", result)
    result = re.sub(r"([a-zA-Z])\n{2}([a-zA-Z])", r"\1 \2", result)
    result = re.sub(r"(.)\n{3}([a-zA-Z])", r"\1\n\n\2", result)
    result = re.sub(r"(,)\n{2}([a-zA-Z])", r"\1 \2", result)
    result = re.sub(r"\n{3}(==)", r"\n\1", result)
    result = re.sub(r"\n{5}", r"\n\n", result)
    result = re.sub(r"\n{4}", r"\n\n", result)
    result = re.sub(r"\n{3}", r"\n\n", result)
    result = re.sub(r"\n{2}", r"\n\n", result)

    result = result.strip()

    return result
