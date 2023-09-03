import streamlit as st
import pandas as pd
import openai
import time
from io import StringIO
openai.api_key = st.secrets["openai"]

def txt(file):
    content = file.getvalue().decode('utf-8')
    documents = content.split("____________________________________________________________")

    # Removing any empty strings or ones that don't look like documents
    documents = [doc.strip() for doc in documents if "Full text:" in doc]
    # Checking the number of documents identified and displaying the first document to validate our approach
    num_documents = len(documents)
    num_documents, documents[0][:1000]  # Displaying the first 1000 characters of the first document for clarity

    # Re-initializing the lists to store the extracted data
    document_names = []
    document_urls = []
    publication_dates = []
    publication_titles = []
    full_texts = []

    # Re-extracting the required information from each document
    for doc in documents:
        # Extracting document name (defaulting to None if not found)
        doc_name_match = re.search(r"Document \d+ of \d+\n\n(.*?)\n\n", doc)
        document_name = doc_name_match.group(1) if doc_name_match else None
        document_names.append(document_name)

        # Extracting document URL (defaulting to None if not found)
        url_match = re.search(r"http[^\n]+", doc)
        document_url = url_match.group(0) if url_match else None
        document_urls.append(document_url)
        
        # Extracting publication date (defaulting to None if not found)
        date_match = re.search(r"Publication date: ([^\n]+)", doc)
        pub_date = date_match.group(1) if date_match else None
        publication_dates.append(pub_date)
        
        # Extracting publication title (defaulting to None if not found)
        title_match = re.search(r"Publication title: ([^\n]+)", doc)
        pub_title = title_match.group(1) if title_match else None
        publication_titles.append(pub_title)

        # Extracting full text (defaulting to None if not found)
        full_text_match = re.search(r"Full text:([\s\S]+)", doc)
        full_text = full_text_match.group(1).strip() if full_text_match else None
        full_texts.append(full_text)
        # Constructing the dataframe
        df = pd.DataFrame({
            "Document URL": document_urls,
            "Publication Date": publication_dates,
            "Publication Title": publication_titles,
            "Full Text": full_texts
        })

    return df

def gpt(prompt, text, model="gpt-3.5-turbo-16k", temperature=0.2):
    response = openai.ChatCompletion.create(
      model=model,
      messages=[
        {"role": "system", "content": prompt},
        {"role": "user", "content": text}
      ],
        temperature=temperature
    )

    response = response.choices[0].message['content']
    return response

def process(df, target, prompts):
    placeholder = st.empty()

    # Ensure that all the columns are present
    for name in prompts.keys():
        if name not in df:
            df[name] = ''
        df[name] = df[name].astype('string')

    # Loop through the dataframe rows
    for i in range(0, len(df)):
        for name, prompt in prompts.items():
            try:
                text = df.loc[i, target][0:5000]  # Consider refining this based on GPT's token limits
                output = gpt(prompt, text)
                df.loc[i, name] = output
                subset = df[[target, *prompts.keys()]]
                placeholder.dataframe(subset)
            except Exception as e:
                st.write(f"Error encountered at index {i}. Reason: {str(e)}")
                time.sleep(20)  # Wait for 20 seconds

    return True

example = ["Summarize the article", "List specific individuals mentioned", 
          "3. Classify article type (op-ed, report, etc."]

file = st.file_uploader("Upload a file", type=("csv", "txt"))

if file:
    st.write(file.name)
    try:        
        df = pd.read_csv(file)
    except:
        df = txt(file)
    column = st.selectbox("Column of interest:", tuple(df.columns))
    prompts = {}
    n = st.number_input('Number of prompts:', min_value = 0, max_value=3)
    for i in range(0,n):
        prompts[f"Column {i+1}"] = st.text_input(f"Prompt {i+1}", 
            placeholder=example[i]
        )
    is_any_empty = (any(not val for val in prompts.values()))
    if st.button("Process", disabled=is_any_empty):
        if process(df, column, prompts):
            st.download_button(
                label="Download data as CSV",
                data=df.to_csv().encode('utf-8'),
                file_name='cleaned.csv',
                mime='text/csv',
            )
    