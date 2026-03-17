from markdown_pdf import MarkdownPdf, Section
import os
from datetime import datetime

def export_markdown_to_pdf(markdown_content: str, query: str = "") -> str:
    """
    Exports markdown content to a PDF file.
    Returns the path to the generated PDF.
    """
    pdf = MarkdownPdf(toc_level=2)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"# Trawl Response\n**Query:** {query}\n**Date:** {timestamp}\n\n---\n\n"
    
    full_content = header + markdown_content
    
    pdf.add_section(Section(full_content))
    
    export_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    if not os.path.exists(export_dir):
        export_dir = "exports"
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
        
    filename = f"trawl_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(export_dir, filename)
    
    pdf.save(filepath)
    return filepath
