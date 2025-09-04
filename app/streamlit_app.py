import streamlit as st
from itinerary import generate_itinerary, generate_itinerary_stream
from utils import parse_llm_output
from pdf_utils import export_itinerary_pdf
import datetime as _date

st.set_page_config(page_title="Travel Planner AI", page_icon="✈️", layout="wide")

# -------------------- Custom CSS --------------------
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        padding: 20px;
        border-right: 1px solid #e0e0e0;
    }
    @media (prefers-color-scheme: dark) {
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f2027, #203a43, #2c5364);
            color: white;
        }
        [data-testid="stSidebar"] input, 
        [data-testid="stSidebar"] select, 
        [data-testid="stSidebar"] textarea {
            background-color: #1e1e1e;
            color: white;
            border: 1px solid #3c3c3c;
        }
    }
    @media (prefers-color-scheme: light) {
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #e6f0ff, #ffffff);
            color: #333;
        }
        [data-testid="stSidebar"] input, 
        [data-testid="stSidebar"] select, 
        [data-testid="stSidebar"] textarea {
            background-color: #ffffff;
            color: #000;
            border: 1px solid #ccc;
        }
    }
       .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        text-align: center;
        padding: 10px;
        font-size: 14px;
        background: rgba(0, 0, 0, 0);
        color: #bbb;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------- Session State --------------------
if "mode" not in st.session_state:
    st.session_state.mode = "Free Chat"
if "history_free" not in st.session_state:
    st.session_state.history_free = []
if "history_structured" not in st.session_state:
    st.session_state.history_structured = []
if "last_itinerary_structured" not in st.session_state:
    st.session_state.last_itinerary_structured = None
if "last_itinerary_free" not in st.session_state:
    st.session_state.last_itinerary_free = None

# -------------------- Sidebar --------------------
with st.sidebar:
    st.header("Choose Mode")
    mode = st.radio("",
        ["Free Chat", "Structured Planner"],
        index=0,
        key="mode",
        label_visibility="collapsed"
    )

    if mode == "Structured Planner":
        st.markdown('<div class="sidebar-title">Structured Trip Details</div>', unsafe_allow_html=True)
        origin = st.text_input("🛫 Origin (IATA code or city)", "")
        destination = st.text_input("🌍 Destination (city)", "")
        destination_code = st.text_input("🏷 Destination Airport Code (optional)", "")
        country = st.text_input("🏳️ Country", "")
        start_date = st.date_input("📅 Start Date", value=_date.date.today())
        days = st.number_input("📆 Number of Days", min_value=1, max_value=30, value=5)
        num_travelers = st.number_input("👥 Number of Travelers", min_value=1, max_value=10, value=1)

        budget_currency = st.selectbox("💰 Budget Currency", ["USD", "INR", "EUR"], index=0)
        target_currency = st.selectbox("💱 Target Currency", ["USD", "INR", "EUR"], index=1)
        interests = st.text_input("🎯 Interests (comma-separated)", "food, nature, culture")

        generate_btn = st.button("🚀 Generate Itinerary")

# Main Content
st.title("✈️ Travel Planner AI")

# FREE CHAT MODE
if st.session_state.mode == "Free Chat":
    st.subheader("💬 Free Travel Chat")

    # Show history
    for msg in st.session_state.history_free:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Type your travel request..."):
        st.session_state.history_free.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            streamed_text = st.write_stream(generate_itinerary_stream({"user_prompt": prompt}))

        st.session_state.history_free.append({"role": "assistant", "content": streamed_text})
        st.session_state.last_itinerary_free = streamed_text

    # Show buttons only if something generated
    if st.session_state.last_itinerary_free:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🧹 Clear Free Chat History"):
                st.session_state.history_free = []
                st.session_state.last_itinerary_free = None
                st.rerun()
        with col2:
            if st.button("📄 Export Itinerary as PDF"):
                parsed = parse_llm_output(st.session_state.last_itinerary_free)
                if not isinstance(parsed, dict) or "day_wise_plan" not in parsed:
                    parsed = {"raw": st.session_state.last_itinerary_free}
                pdf_path = export_itinerary_pdf(st.session_state.last_itinerary_free, "itinerary.pdf")
                with open(pdf_path, "rb") as f:
                    st.download_button("⬇️ Download PDF", f, file_name="itinerary.pdf")

        with st.expander("ℹ️ Data Sources"):
            st.markdown("""
            -  [WeatherAPI](https://www.weatherapi.com/) – Real-time weather data  
            -  [Amadeus Travel APIs](https://developers.amadeus.com/) – Flights & hotels  
            -  [Google Places API](https://developers.google.com/maps/documentation/places/web-service/overview) – Attractions & activities  
            -  [REST Countries API](https://restcountries.com/) – Country info
            """)

# STRUCTURED PLANNER MODE
elif st.session_state.mode == "Structured Planner":
    st.subheader("📑 Structured Travel Planner")

    # Generate itinerary from sidebar inputs
    if 'generate_btn' in locals() and generate_btn:
        payload = {
            "origin": origin.strip(),
            "destination": destination.strip(),
            "destination_code": destination_code.strip() or None,
            "country": country.strip(),
            "date": start_date.isoformat(),
            "days": int(days),
            "budget_currency": budget_currency,
            "target_currency": target_currency,
            "interests": [x.strip() for x in interests.split(",") if x.strip()],
            "num_travelers": int(num_travelers),
        }

        st.session_state.history_structured = []
        with st.chat_message("assistant"):
            streamed_text = st.write_stream(generate_itinerary_stream(payload))

        st.session_state.history_structured.append({"role": "assistant", "content": streamed_text})
        st.session_state.last_itinerary_structured = streamed_text

    # Display chat history for structured refinements
    for msg in st.session_state.history_structured:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Refinement chat (only if itinerary exists)
    if st.session_state.last_itinerary_structured:
        if prompt := st.chat_input("Refine your itinerary... (e.g., cheaper hotels, add adventure)"):
            st.session_state.history_structured.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            conversation = "\n".join(
                [f"{m['role'].capitalize()}: {m['content']}" for m in st.session_state.history_structured[-5:]]
            )
            with st.chat_message("assistant"):
                streamed_text = st.write_stream(
                    generate_itinerary_stream({
                        "user_prompt": conversation,
                        "origin": origin,
                        "destination": destination,
                        "country": country,
                        "days": days,
                        "target_currency": target_currency,
                        "interests": [x.strip() for x in interests.split(",") if x.strip()],
                    })
                )

            st.session_state.history_structured.append({"role": "assistant", "content": streamed_text})
            st.session_state.last_itinerary_structured = streamed_text

        # Buttons after structured plan
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🧹 Clear Structured Chat History"):
                st.session_state.history_structured = []
                st.session_state.last_itinerary_structured = None
                st.rerun()
        with col2:
            if st.button("📄 Export Itinerary as PDF"):
                parsed = parse_llm_output(st.session_state.last_itinerary_structured)
                if not isinstance(parsed, dict) or "day_wise_plan" not in parsed:
                    parsed = {"raw": st.session_state.last_itinerary_structured}
                pdf_path = export_itinerary_pdf(st.session_state.last_itinerary_structured, "itinerary.pdf")
                with open(pdf_path, "rb") as f:
                    st.download_button("⬇️ Download PDF", f, file_name="itinerary.pdf")

        with st.expander(" Data Sources"):
            st.markdown("""
            -  [WeatherAPI](https://www.weatherapi.com/) – Real-time weather data  
            -  [Amadeus Travel APIs](https://developers.amadeus.com/) – Flights & hotels  
            -  [Google Places API](https://developers.google.com/maps/documentation/places/web-service/overview) – Attractions & activities  
            -  [REST Countries API](https://restcountries.com/) – Country info
            """)

# -------------------- Footer --------------------
st.markdown(
    """
    <div class="footer">
        🌐 <b>TravelCraft AI</b> – Your intelligent travel companion.<br>
         Powered by WeatherAPI, Amadeus API, Google Places, and REST Countries.<br>
        📧 Contact: <a href="mailto:support@travelcraft.ai">support@travelcraft.ai</a>
    </div>
    """,
    unsafe_allow_html=True
)
