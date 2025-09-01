#  TravelCraft AI – Intelligent Travel Planner & Itinerary Generator  

TravelCraft AI is an **AI-powered travel assistant** that helps users **plan trips, generate itineraries, and refine travel plans** in real-time.  
It integrates **LLMs, Retrieval-Augmented Generation (RAG), and external travel APIs** to provide a smart, personalized, and interactive travel planning experience.  

---

## 🚀 Features  

- 🗨 **Two Modes of Interaction**  
  - **Free Chat Mode** → Open-ended travel conversations (e.g., “Plan me a beach trip to Goa”).  
  - **Structured Planner Mode** → Form-based inputs (origin, destination, dates, budget, interests) for precise itineraries.  

- 📑 **Smart Itinerary Generation**  
  - Day-wise trip plan with activities, food, budget, and transport suggestions.  
  - Real-time integration with **WeatherAPI**, **Amadeus API**, **Google Places**, and **REST Countries**.  

- 🔄 **Interactive Refinements**  
  - Modify itineraries via chat: *“Add 2 more days”, “Include adventure sports”, “Cheaper hotels”*.  
  - Memory-enabled conversations keep track of modifications.  

- 📄 **Export to PDF**  
  - Downloadable, well-formatted itineraries for offline use.  

- 🔎 **RAG Integration**  
  - Retrieves **travel blogs, cultural notes, and guides** for contextual recommendations.  

- 🎨 **Beautiful UI with Streamlit**  
  - Sidebar for structured inputs.  
  - Live streaming responses (token-by-token).  
  - Dark & light theme support.  

---

## 🏗️ Architecture 
User → Streamlit UI
→ Mode Selection (Free Chat / Structured Planner)
→ LangGraph Workflow (Stateful Orchestration)
→ Agents (Weather, Flights, Hotels, Attractions, RAG)
→ External APIs + Vector DB (ChromaDB)
→ LLM (Gemini 2.5 Flash) → Final Itinerary


---

## ⚙️ Tech Stack  

- **Frontend/UI** → Streamlit  
- **LLM** → Gemini 2.5 Flash (fast & cost-efficient reasoning)  
- **Workflow Orchestration** → LangGraph (stateful DAG execution)  
- **Embeddings (RAG)** → SentenceTransformers (all-MiniLM-L6-v2) + ChromaDB  
- **External APIs**:  
  - 🌦 WeatherAPI (real-time weather)  
  - ✈️ Amadeus API (flights, hotels, currency exchange)  
  - 📍 Google Places API (attractions & activities)  
  - 🌍 REST Countries API (country info)  

---

## 💾 Memory & Chat Handling  

- Separate memory for **Free Chat** and **Structured Planner**.  
- Conversations stored in `st.session_state` (per user session).  
- **Short-term memory**: keeps last 5 messages for context.  
- Example: *“Add 2 more days”* → Appends to previous plan and regenerates.  

---

## 📦 Installation  

### 1️⃣ Clone the repository  
```
git clone https://github.com/your-username/travelcraft-ai.git
cd travelcraft-ai
```
2️⃣ Create virtual environment
```
conda create -n travelcraft-ai python=3.10 -y
conda activate travelcraft-ai
```
3️⃣ Install dependencies
```
pip install -r requirements.txt
```
4️⃣ Set up environment variables (.env)

5️⃣ Run the app
```
streamlit run app/streamlit_app.py
```
📊 Example Usage

Free Chat Mode:
```
User: Plan me a 5-day honeymoon trip from Delhi to Manali in May.
Assistant: (streams a day-wise itinerary with hotels, weather, and activities)
```
Structured Mode
Fill sidebar fields:

Origin: Delhi

Destination: Paris

Days: 7

Interests: food, art, culture
→ Click Generate → Instant PDF-ready itinerary.

🛡️ Error Handling

If an API fails → fallback responses (e.g., “No data available”).
If budget exceeds → suggestions for cheaper alternatives.
If LLM hallucination risk → strict grounding in retrieved data.

🔮 Future Enhancements

🗂 Multi-user persistent memory with Redis/Postgres.
🎙 Voice input (Whisper ASR) + voice output (TTS).
🗺 Real-time events (concerts, strikes, weather alerts).
📱 Mobile app with offline support.
🤖 Personalized recommendation engine (based on past trips).


