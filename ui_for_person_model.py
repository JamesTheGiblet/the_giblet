import streamlit as st
from person_model import Person

st.title("Person Data Entry")

with st.form("person_form"):
    name = st.text_input("Name", max_chars=50)
    age = st.number_input("Age", min_value=0, max_value=120, step=1)
    is_active_member = st.checkbox("Is Active Member")
    submitted = st.form_submit_button("Submit")

    if submitted:
        try:
            person = Person(name=name, age=age, is_active_member=is_active_member)
            st.success("Successfully created Person object:")
            st.json(person.__dict__)
        except Exception as e:
            st.error(f"Error creating Person object: {e}")