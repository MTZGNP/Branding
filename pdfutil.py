import PyPDF2
from difflib import SequenceMatcher

def is_first_page_identical(pdf_path, template_path):
    """
    Check if the first page of a given PDF is identical to a template PDF.

    Args:
    pdf_path (str): Path to the PDF file to check.
    template_path (str): Path to the template PDF file.

    Returns:
    bool: True if the first page of the given PDF is identical to the template, False otherwise.
    """

    def get_first_page_text(path):
        """ Extract text from the first page of a PDF. """
        with open(path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            first_page = reader.pages[0]
            return first_page.extract_text()

    # Extract text from the first page of both PDFs
    pdf_text = get_first_page_text(pdf_path)
    template_text = get_first_page_text(template_path)

    # Compare the texts
    similarity_ratio = SequenceMatcher(None, pdf_text, template_text).ratio()

    # Consider texts identical if the similarity ratio is very high, e.g., 0.99
    return similarity_ratio > 0.99


def prepend_page(template_path, target_path):
    """
    Prepend a single page from the template to the beginning of the target PDF.

    Args:
    template_path (str): Path to the template PDF file (should contain only the page to prepend).
    target_path (str): Path to the target PDF file.
    """
    # Create a PdfReader instance for the template and target PDF
    template_reader = PyPDF2.PdfReader(template_path)
    target_reader = PyPDF2.PdfReader(target_path)

    # Create a PdfWriter object for the output
    pdf_writer = PyPDF2.PdfWriter()

    # Add the template page (assuming it's the first and only page of the template PDF)
    pdf_writer.add_page(template_reader.pages[0])

    # Add all pages from the target PDF
    for page in target_reader.pages:
        pdf_writer.add_page(page)

    # Write the combined PDF in place
    with open(target_path, 'wb') as output_file:
        pdf_writer.write(output_file)



