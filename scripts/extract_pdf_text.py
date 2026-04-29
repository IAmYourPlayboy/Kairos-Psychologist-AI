"""
Скрипт для извлечения текста из PDF файлов.
Использует PyMuPDF (fitz) для извлечения текста.
"""

import pymupdf
import sys
import os
from pathlib import Path


def extract_text_from_pdf(pdf_path: str, output_path: str) -> None:
    """
    Извлечь текст из PDF и сохранить в текстовый файл.

    Args:
        pdf_path: Путь к PDF файлу
        output_path: Путь для сохранения извлечённого текста
    """
    try:
        # Открыть PDF
        doc = pymupdf.open(pdf_path)

        # Извлечь текст со всех страниц
        text = ''
        for page_num, page in enumerate(doc, 1):
            text += f'\n\n{"="*80}\n'
            text += f'PAGE {page_num}\n'
            text += f'{"="*80}\n\n'
            text += page.get_text()

        # Создать папку если не существует
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Сохранить текст
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)

        # Вывести статистику (без юникода)
        stats = f'Success! Extracted {len(doc)} pages, {len(text)} characters'
        print(stats)
        print(f'Saved to: {output_path}')

    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    pdf_path = r'D:\Downloads\Источники\WHO Psychological First Aid Guide for Field Workers (2011).pdf'
    output_path = r'd:\Kairos\data\scientific_papers\WHO_PFA_2011_extracted.txt'

    extract_text_from_pdf(pdf_path, output_path)
