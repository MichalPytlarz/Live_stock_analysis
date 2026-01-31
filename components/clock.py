import streamlit as st
import streamlit.components.v1 as components

def add_dynamic_clock():
    # Define style and script inside a single HTML block
    clock_code = """
    <div id="clock" style="
        font-family: 'Courier New', monospace;
        color: #00ff00;
        background-color: #1e1e1e;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #333;
        text-align: center;
        font-size: 16px;
        font-weight: bold;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.5);
    ">
        <div id="date" style="font-size: 12px; color: #888;"></div>
        <div id="time"></div>
    </div>

    <script>
    function update() {
        const now = new Date();
        document.getElementById('date').innerText = now.toLocaleDateString('pl-PL');
        document.getElementById('time').innerText = now.toLocaleTimeString('pl-PL');
    }
    setInterval(update, 1000);
    update();
    </script>
    """
    
    # Create sidebar or place in the top-right corner using columns
    with st.sidebar:
        st.markdown("---")
        components.html(clock_code, height=100)