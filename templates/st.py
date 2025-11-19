import streamlit as st

# Set page title
st.title("My First Streamlit App")

# Add a header
st.header("Welcome to Streamlit!")

# Add some text
st.write("This is a simple Streamlit application.")

# Add a slider
number = st.slider("Select a number", 0, 100, 50)
st.write(f"You selected: {number}")

# Add a text input
user_input = st.text_input("Enter your name", "")
if user_input:
    st.write(f"Hello, {user_input}!")

# Add a button
if st.button("Click me!"):
    st.balloons() 