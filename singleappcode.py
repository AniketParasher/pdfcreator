import streamlit as st
import pandas as pd
import numpy as np
import io
import zipfile
import os
import tempfile
from fpdf import FPDF

# Define the parameter descriptions
parameter_descriptions = {
    'A1': "Block_ID, Grade, student_no: Uses Block_ID, Grade, and student_no to generate the ID.",
    'A2': "School_ID, Grade, student_no: Uses School_ID, Grade, and student_no to generate the ID.",
    'A3': "District_ID, School_ID, Grade, student_no: Uses District_ID, School_ID, Grade, and student_no to generate the ID.",
    'A4': "District_ID, Grade, student_no: Uses District_ID, Grade, and student_no to generate the ID.",
    'A5': "Partner_ID, Grade, student_no: Uses Partner_ID, Grade, and student_no to generate the ID.",
    'A6': "District_ID, Block_ID, Grade, student_no: Uses District_ID, Block_ID, Grade, and student_no to generate the ID.",
    'A7': "Block_ID, School_ID, Grade, student_no: Uses Block_ID, School_ID, Grade, and student_no to generate the ID.",
    'A8': "Partner_ID, Block_ID, Grade, student_no: Uses Partner_ID, Block_ID, Grade, and student_no to generate the ID.",
    'A9': "Partner_ID, District_ID, Grade, student_no: Uses Partner_ID, District_ID, Grade, and student_no to generate the ID.",
    'A10': "Partner_ID, School_ID, Grade, student_no: Uses Partner_ID, School_ID, Grade, and student_no to generate the ID."
}

# Define the mapping for parameter sets
parameter_mapping = {
    'A1': "Block_ID,Grade,student_no",
    'A2': "School_ID,Grade,student_no",
    'A3': "District_ID,School_ID,Grade,student_no",
    'A4': "District_ID,Grade,student_no",
    'A5': "Partner_ID,Grade,student_no",
    'A6': "District_ID,Block_ID,Grade,student_no",
    'A7': "Block_ID,School_ID,Grade,student_no",
    'A8': "Partner_ID,Block_ID,Grade,student_no",
    'A9': "Partner_ID,District_ID,Grade,student_no",
    'A10': "Partner_ID,School_ID,Grade,student_no"
}

def generate_custom_id(row, params):
    params_split = params.split(',')
    custom_id = []
    for param in params_split:
        if param in row and pd.notna(row[param]):
            value = row[param]
            if isinstance(value, float) and value % 1 == 0:
                value = int(value)
            custom_id.append(str(value))
    return ''.join(custom_id)

def process_data(uploaded_file, partner_id, buffer_percent, grade, district_digits, block_digits, school_digits, student_digits, selected_param):
    data = pd.read_excel(uploaded_file)

    # Assign the Partner_ID directly
    data['Partner_ID'] = str(partner_id).zfill(len(str(partner_id)))  # Padding Partner_ID
    data['Grade'] = grade

    # Assign unique IDs for District, Block, and School, default to "00" for missing values
    data['District_ID'] = data['District'].apply(lambda x: str(data['District'].unique().tolist().index(x) + 1).zfill(district_digits) if x != "NA" else "0".zfill(district_digits))
    data['Block_ID'] = data['Block'].apply(lambda x: str(data['Block'].unique().tolist().index(x) + 1).zfill(block_digits) if x != "NA" else "0".zfill(block_digits))
    data['School_ID'] = data['School_ID'].apply(lambda x: str(data['School_ID'].unique().tolist().index(x) + 1).zfill(school_digits) if x != "NA" else "0".zfill(school_digits))

    # Calculate Total Students With Buffer based on the provided buffer percentage
    data['Total_Students_With_Buffer'] = np.floor(data['Total_Students'] * (1 + buffer_percent / 100))

    # Generate student IDs based on the calculated Total Students With Buffer
    def generate_student_ids(row):
        if pd.notna(row['Total_Students_With_Buffer']) and row['Total_Students_With_Buffer'] > 0:
            student_ids = [
                f"{row['School_ID']}{str(int(row['Grade'])).zfill(2)}{str(i).zfill(student_digits)}"
                for i in range(1, int(row['Total_Students_With_Buffer']) + 1)
            ]
            return student_ids
        return []

    data['Student_IDs'] = data.apply(generate_student_ids, axis=1)

    # Expand the data frame to have one row per student ID
    data_expanded = data.explode('Student_IDs')

    # Extract student number from the ID
    data_expanded['student_no'] = data_expanded['Student_IDs'].str[-student_digits:]

    # Use the selected parameter set for generating Custom_ID
    data_expanded['Custom_ID'] = data_expanded.apply(lambda row: generate_custom_id(row, parameter_mapping[selected_param]), axis=1)

    # Generate the additional Excel sheet with mapped columns
    data_mapped = data_expanded[['Custom_ID', 'Grade', 'School', 'School_ID', 'District', 'Block']].copy()
    data_mapped.columns = ['Roll_Number', 'Grade', 'School Name', 'School Code', 'District Name', 'Block Name']
    data_mapped['Gender'] = np.random.choice(['Male', 'Female'], size=len(data_mapped), replace=True)

    return data_expanded, data_mapped

# Function to create the attendance list PDF
def create_attendance_pdf(pdf, column_widths, column_names, image_path, info_values, df):
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
    pdf.cell(info_cell_width, 5, f"DISTRICT: {info_labels['DISTRICT']}                                                                                                                                                                            DATE OF ASSESSMENT : ____________________", border='LR', ln=1)
    pdf.cell(info_cell_width, 5, f"BLOCK: {info_labels['BLOCK']}", border='LR', ln=1)
    pdf.cell(info_cell_width, 5, f"SCHOOL NAME: {info_labels['SCHOOL NAME']}", border='LR', ln=1)
    pdf.cell(info_cell_width, 5, f"CLASS: {info_labels['CLASS']}", border='LR', ln=1)
    pdf.cell(info_cell_width, 5, f"SECTION: {info_labels['SECTION']}                                                                                                                                                                             NO OF STUDENTS : ____________________", border='LR', ln=1)

    # Add the table headers
    pdf.set_font('Arial', 'B', 7)
    for col in column_names:
        pdf.cell(column_widths[col], 7, col, border=1, align='C')
    pdf.ln()

    # Add the table data
    pdf.set_font('Arial', '', 7)
    for index, row in df.iterrows():
        for col in column_names:
            pdf.cell(column_widths[col], 7, str(row[col]), border=1, align='C')
        pdf.ln()

# Streamlit UI
st.title("Student ID Mapping and Attendance PDF Generator")

# --- Part 1: ID Mapping ---
st.header("Part 1: Student ID Mapping")

uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])

if uploaded_file is not None:
    st.success("Excel file uploaded successfully!")

    st.sidebar.header("ID Mapping Parameters")

    partner_id = st.sidebar.text_input("Partner ID", "Enter Partner ID")
    buffer_percent = st.sidebar.slider("Buffer Percentage", 0, 100, 20)
    grade = st.sidebar.text_input("Grade", "Enter Grade")
    district_digits = st.sidebar.slider("District ID Digits", 1, 5, 2)
    block_digits = st.sidebar.slider("Block ID Digits", 1, 5, 2)
    school_digits = st.sidebar.slider("School ID Digits", 1, 5, 2)
    student_digits = st.sidebar.slider("Student Number Digits", 1, 5, 3)

    selected_param = st.sidebar.selectbox("Select Parameter Set", list(parameter_mapping.keys()))
    st.sidebar.markdown(f"**Parameter Description:** {parameter_descriptions[selected_param]}")

    if st.button("Process and Download Excel"):
        processed_data, data_mapped = process_data(
            uploaded_file, partner_id, buffer_percent, grade,
            district_digits, block_digits, school_digits, student_digits, selected_param
        )

        # Save processed data to Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            data_mapped.to_excel(writer, index=False, sheet_name="Mapped_Student_IDs")
            writer.save()

        # Save the Excel file
        excel_filename = "Student_Ids_Mapped.xlsx"
        st.download_button(
            label="Download Mapped Excel",
            data=output.getvalue(),
            file_name=excel_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # --- Part 2: PDF Generation ---
        st.header("Part 2: Generate Attendance PDFs")

        if uploaded_file is not None:
            school_data = pd.read_excel(output)  # Read from generated Excel file

            image_path = st.file_uploader("Upload School Logo", type=["png", "jpg", "jpeg"])

            if image_path is not None:
                st.success("Image uploaded successfully!")

            temp_dir = tempfile.mkdtemp()

            for school_code in school_data['School Code'].unique():
                df_school = school_data[school_data['School Code'] == school_code]
                student_count = len(df_school)

                pdf = FPDF('P', 'mm', 'A4')
                column_widths = {
                    'S.No': 10,
                    'STUDENT ID': 30,
                    'GENDER': 15,
                    'MOTHER NAME': 45,
                    'FATHER NAME': 45,
                    'ATTENDANCE STATUS': 45
                }
                column_names = list(column_widths.keys())

                info_values = {
                    'PROJECT': "Project XYZ",
                    'DISTRICT': df_school['District Name'].iloc[0],
                    'BLOCK': df_school['Block Name'].iloc[0],
                    'SCHOOL NAME': df_school['School Name'].iloc[0],
                    'CLASS': df_school['Grade'].iloc[0],
                    'SECTION': "A"
                }

                # First two columns filled with counts from 1 to student_count and Student IDs
                df_pdf = pd.DataFrame({
                    'S.No': list(range(1, student_count + 1)),
                    'STUDENT ID': df_school['Roll_Number'].values,
                    'GENDER': df_school['Gender'].values,
                    'MOTHER NAME': [""] * student_count,
                    'FATHER NAME': [""] * student_count,
                    'ATTENDANCE STATUS': [""] * student_count
                })

                create_attendance_pdf(pdf, column_widths, column_names, image_path, info_values, df_pdf)

                pdf_file = f"{school_code}.pdf"
                pdf_output_path = os.path.join(temp_dir, pdf_file)
                pdf.output(pdf_output_path)

            # Create a zip file with all the PDFs
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                for pdf_file in os.listdir(temp_dir):
                    zip_file.write(os.path.join(temp_dir, pdf_file), pdf_file)

            st.download_button(
                label="Download All PDFs",
                data=zip_buffer.getvalue(),
                file_name="Attendance_PDFs.zip",
                mime="application/zip"
            )
