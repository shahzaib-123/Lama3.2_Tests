import pdfplumber
import re
import json

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a given PDF using pdfplumber.
    """
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

def split_into_sections(text):
    """
    Split the text into sections based on headings or topics.
    You can improve this using more sophisticated methods to detect headings.
    """
    # Use regex to detect headings or section titles (e.g., lines in all caps or starting with a number)
    sections = re.split(r'\n\s*\d+\.|\n[A-Z ]+\n', text)
    return [section.strip() for section in sections if section.strip()]

def generate_hypothetical_question(section_title):
    """
    Automatically generate a user question based on the section title.
    This function can be extended to handle more nuanced prompts.
    """
    return f"Can you explain the topic of {section_title.strip()}?"

def assign_roles_to_sections(sections):
    """
    Assigns roles to sections by generating a user question and assigning the rest as assistant response.
    """
    formatted_data = []
    
    # Add a system role to set context
    formatted_data.append({"role": "system", "content": "You are an AI assistant who helps students with course materials on various subjects."})
    
    # For each section, create a user question and assistant response
    for section in sections:
        if section:
            # Generate a user prompt based on the section title
            # Using the first line as the 'title' of the section
            lines = section.split("\n")
            section_title = lines[0] if lines else "this topic"
            user_prompt = generate_hypothetical_question(section_title)

            # The rest of the section is the assistant's content
            assistant_content = "\n".join(lines[1:]).strip()

            # Add the roles
            formatted_data.append({"role": "user", "content": user_prompt})
            if assistant_content:
                formatted_data.append({"role": "assistant", "content": assistant_content})
    
    return formatted_data

def handle_tables(text):
    """
    Identifies and formats tables found in the document.
    """
    # Simple heuristic: if a row has multiple columns separated by spaces or tabs, it might be a table row.
    table_lines = []
    for line in text.splitlines():
        if '\t' in line or re.search(r'\s{2,}', line):  # Detect tables by tabs or multiple spaces
            table_lines.append(line)
    return "\n".join(table_lines)

def process_pdf(pdf_path, output_json):
    """
    Main function that processes a given PDF and outputs the structured data into JSON format.
    """
    # Extract text from the PDF
    raw_text = extract_text_from_pdf(pdf_path)

    # Extract and format tables (you can extend this to handle tables separately if needed)
    table_content = handle_tables(raw_text)

    # Split raw text into sections (e.g., by headings or chapters)
    sections = split_into_sections(raw_text)

    # Assign roles to the sections
    structured_data = assign_roles_to_sections(sections)

    # Optionally include table data at the end
    if table_content:
        structured_data.append({"role": "assistant", "content": f"Here is some table data:\n{table_content}"})

    # Save the structured data as JSONL for fine-tuning
    with open(output_json, "w") as f:
        for entry in structured_data:
            json.dump(entry, f)
            f.write("\n")

if __name__ == "__main__":
    # Path to your PDF
    pdf_path = "your_document.pdf"
    
    # Output path for JSONL formatted file
    output_json = "formatted_data.jsonl"

    # Process the PDF and generate the formatted output
    process_pdf(pdf_path, output_json)
