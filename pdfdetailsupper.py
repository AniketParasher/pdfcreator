import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# Function to create the attendance list PDF
def create_attendance_pdf(pdf, column_widths, column_names, image_stream, info_values):
    pdf.add_page()

    # Page width and margins
    page_width = 210  # A4 page width in mm
    margin_left = 10
    margin_right = 10
    available_width = page_width - margin_left - margin_right

    # Calculate total column width
    total_column_width = sum(column_widths[col] for col in column_names)

    # Scale column widths if necessary
    if total_column_width > available_width:
        scaling_factor = available_width / total_column_width
        column_widths = {col: width * scaling_factor for col, width in column_widths.items()}

    # Add the combined title and subtitle in a single merged cell
    pdf.set_font('Arial', 'B', 16)
    merged_cell_width = sum(column_widths[col] for col in column_names)  # Total width based on scaled column widths
    pdf.cell(merged_cell_width, 10, 'ATTENDANCE LIST', border='LTR', align='C', ln=1)
    pdf.set_font('Arial', '', 7)
    pdf.cell(merged_cell_width, 10, '(PLEASE FILL ALL THE DETAILS IN BLOCK LETTERS)', border='LBR', align='C', ln=1)

    # Add the image in the top-right corner of the bordered cell
    pdf.image(image_stream, x=pdf.get_x() + merged_cell_width - 30, y=pdf.get_y() - 18, w=28, h=12)  # Adjust position and size as needed

    # Add the additional information cell below the "ATTENDANCE LIST" cell
    pdf.set_font('Arial', 'B', 6)
    info_cell_width = merged_cell_width  # Width same as the merged title cell
    info_cell_height = 30  # Adjust height as needed
    pdf.cell(info_cell_width, info_cell_height, '', border='LBR', ln=1)
    pdf.set_xy(pdf.get_x(), pdf.get_y() - info_cell_height)  # Move back to the top of the cell

    # Add labels and fill values from the dictionary
    info_labels = {
        'PROJECT': '',
        'DISTRICT': '',
        'BLOCK': '',
        'SCHOOL NAME': '',
        'CLASS': '',
        'SECTION': ''
    }

    for label in info_labels.keys():
        for key, value in info_values.items():
            if label[:5].lower() == key[:5].lower():  # Match first 5 characters, ignoring case
                info_labels[label] = value
                break

    pdf.cell(info_cell_width, 5, f"PROJECT: {info_labels['PROJECT']}", border='LR', ln=1)
    pdf.cell(info_cell_width, 5, f"DISTRICT: {info_labels['DISTRICT']} DATE OF ASSESSMENT : ____________________", border='LR', ln=1)
    pdf.cell(info_cell_width, 5, f"BLOCK: {info_labels['BLOCK']}", border='LR', ln=1)
    pdf.cell(info_cell_width, 5, f"SCHOOL NAME: {info_labels['SCHOOL NAME']}", border='LR', ln=1)
    pdf.cell(info_cell_width, 5, f"CLASS: {info_labels['CLASS']}", border='LR', ln=1)
    pdf.cell(info_cell_width, 5, f"SECTION: {info_labels['SECTION']}", border='LR', ln=1)

    # Draw a border around the table header
    pdf.set_font('Arial', 'B', 5.5)
    table_cell_height = 10

    # Table Header
    for col_name in column_names:
        pdf.cell(column_widths[col_name], table_cell_height, col_name, border=1, align='C')
    pdf.ln(table_cell_height)

    # Table Rows (based on student_count)
    pdf.set_font('Arial', '', 10)
    student_count = info_values.get('student_count', 0)  # Use 0 if 'student_count' is missing or not found
    for i in range(student_count):
        for col_name in column_names:
            pdf.cell(column_widths[col_name], table_cell_height, '', border=1, align='C')
        pdf.ln(table_cell_height)

# Streamlit App
def main():
    st.title("Attendance List PDF Generator")

    # Upload Excel and Image files
    excel_file = st.file_uploader("Upload Excel file", type=["xlsx"])
    image_file = st.file_uploader("Upload Image file", type=["png", "jpg", "jpeg"])

    if excel_file and image_file:
        # Read Excel file
        df = pd.read_excel(excel_file)

        # Process data
        grouping_columns = [col for col in df.columns if col not in ['STUDENT ID'] and df[col].notna().any()]
        grouped = df.groupby(grouping_columns).agg(student_count=('STUDENT ID', 'nunique')).reset_index()

        if 'CLASS' in grouped.columns and grouped['CLASS'].astype(str).str.contains('\D').any():
            grouped['CLASS'] = grouped['CLASS'].astype(str).str.extract('(\d+)')

        result = grouped.to_dict(orient='records')

        # Convert image to a stream for fpdf
        image_stream = io.BytesIO(image_file.read())

        # Generate PDFs
        pdf_files = []
        for record in result:
            pdf = FPDF(orientation='P', unit='mm', format='A4')
            pdf.set_left_margin(10)
            pdf.set_right_margin(10)

            school_code = record.get('SCHOOL NAME', 'default_code')  # Use 'default_code' if 'SCHOOL NAME' is missing
            create_attendance_pdf(pdf, column_widths, column_names, image_stream, record)

            # Save the PDF to a stream
            pdf_stream = io.BytesIO()
            pdf.output(pdf_stream)
            pdf_stream.seek(0)

            # Save to a file for download
            pdf_files.append((f'attendance_list_{school_code}.pdf', pdf_stream))

        # Provide download links for generated PDFs
        for filename, pdf_stream in pdf_files:
            st.download_button(
                label=f"Download {filename}",
                data=pdf_stream,
                file_name=filename,
                mime="application/pdf"
            )

if __name__ == "__main__":
    main()
