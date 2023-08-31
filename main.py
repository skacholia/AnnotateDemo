import streamlit as st
import pandas as pd
import openai
import time

openai.api_key = "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"

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
    for name, prompt in prompts.items():
        if name not in df:
            df[name] = ''
        df[name] = df[name].astype('string')
        count = 0
        for i in range(0, len(df)):
            try:
                text = df.loc[i, target][0:5000]
                output = gpt(prompt, text)
                df.loc[i, name] = output
                subset = df[[target, *prompts.keys()]]
                placeholder.dataframe(subset)
                count += 1
            except Exception as e:
                print(e)
                st.write(f"Error encountered at index {i}.")
                time.sleep(20)  # Wait for 20 seconds
    return True

example = ["Summarize the article", "List specific individuals mentioned", 
          "3. Classify article type (op-ed, report, etc."]

file = st.file_uploader("Upload a file", type=("csv", "txt"))

if file:
    df = pd.read_csv(file)
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
    