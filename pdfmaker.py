import streamlit as st
from fpdf import FPDF
import pandas as pd

# Streamlit app title
st.title("Attendance List Generator")

# File uploader for Excel file
excel_file = st.file_uploader("Upload the Excel file", type=["xlsx"])

# Image uploader for the logo or image
image_file = st.file_uploader("Upload an image for the header", type=["png", "jpg", "jpeg"])

# Proceed if both files are uploaded
if excel_file and image_file:
    # Load the Excel file and process the data
    df = pd.read_excel(excel_file)

    # Identify columns excluding 'Student ID' and those that are entirely empty
    grouping_columns = [col for col in df.columns if col not in ['STUDENT ID'] and df[col].notna().any()]

    # Group by the identified columns and count the number of unique 'Student ID'
    grouped = df.groupby(grouping_columns).agg(student_count=('STUDENT ID', 'nunique')).reset_index()

    # Process 'CLASS' column if it exists and contains non-numeric values
    if 'CLASS' in grouped.columns and grouped['CLASS'].astype(str).str.contains('\D').any():
        grouped['CLASS'] = grouped['CLASS'].astype(str).str.extract('(\d+)')

    # Convert the result to a list of dictionaries
    result = grouped.to_dict(orient='records')

    # Number of columns and column names for the table
    num_columns = 8  # Example: User-defined number of columns
    column_names = ['S.NO', 'STUDENT ID', 'PASSCODE', 'STUDENT NAME', 'GENDER', 'TAB ID', 'SUBJECT 1 (PRESENT/ABSENT)', 'SUBJECT 2 (PRESENT/ABSENT)']  # Example: User-defined column names

    # Define column widths
    column_widths = {
        'S.NO': 8,
        'STUDENT ID': 18,
        'PASSCODE': 18,
        'STUDENT NAME': 61,  # Wider column for Student Name
        'GENDER': 15,
        'TAB ID': 15,
        'SUBJECT 1 (PRESENT/ABSENT)': 35,
        'SUBJECT 2 (PRESENT/ABSENT)': 35
    }

    # Function to create the attendance list PDF
    def create_attendance_pdf(pdf, column_widths, column_names, image_path):
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
        pdf.image(image_path, x=pdf.get_x() + merged_cell_width - 30, y=pdf.get_y() - 18, w=28, h=12)  # Adjust position and size as needed
        
        # Add the additional information cell below the "ATTENDANCE LIST" cell
        pdf.set_font('Arial', 'B', 6)
        info_cell_width = merged_cell_width  # Width same as the merged title cell
        info_cell_height = 30  # Adjust height as needed
        pdf.cell(info_cell_width, info_cell_height, '', border='LBR', ln=1)
        pdf.set_xy(pdf.get_x(), pdf.get_y() - info_cell_height)  # Move back to the top of the cell

        # Add labels within the additional information cell
        info_labels = [
            'PROJECT :',
            'DISTRICT :                                                                                                                                                                                                   DATE OF ASSESSMENT: _______________________',
            'BLOCK :',
            'SCHOOL NAME:',
            'CLASS:',
            'SECTION :'
        ]
        for label in info_labels:
            pdf.cell(info_cell_width, 5, label, border='LR', ln=1)
        
        # Draw a border around the table header
        pdf.set_font('Arial', 'B', 5.5)
        table_cell_height = 10

        # Table Header
        for col_name in column_names:
            pdf.cell(column_widths[col_name], table_cell_height, col_name, border=1, align='C')
        pdf.ln(table_cell_height)
        
        # Table Rows (50 rows)
        pdf.set_font('Arial', '', 10)
        for i in range(50):
            for col_name in column_names:
                pdf.cell(column_widths[col_name], table_cell_height, '', border=1, align='C')
            pdf.ln(table_cell_height)

    # Create the PDF
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_left_margin(10)
    pdf.set_right_margin(10)

    # Convert the uploaded image to a file-like object
    image_path = "uploaded_image.png"
    with open(image_path, "wb") as f:
        f.write(image_file.getvalue())

    create_attendance_pdf(pdf, column_widths, column_names, image_path)

    # Save the PDF to a file-like object
    pdf_output = pdf.output(dest='S').encode('latin1')

    # Create a download button for the PDF
    st.download_button(
        label="Download Attendance List PDF",
        data=pdf_output,
        file_name="attendance_list_image.pdf",
        mime="application/pdf"
    )
else:
    st.warning("Please upload both the Excel file and the image.")
