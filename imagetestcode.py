import streamlit as st

# URL of the image in your GitHub repository
image_url = "https://raw.githubusercontent.com/your-username/your-repo/main/images/sample_image.png"

# Display the image
st.image(image_url, caption='Sample Image', use_column_width=True)
