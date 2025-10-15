
Project Title: Synapse AI Code Reviewer

Developed by: Navya Sree

I. Project Objective: State that the goal was to automate code review by analyzing structure, readability, and best practices (from the assignment brief).

II. Technical Architecture:

Frontend: React (for modern, interactive UI).

Backend/API: FastAPI (chosen for its high performance and built-in type hints/Pydantic validation).

LLM Integration: LiteLLM using OpenRouter (chosen for access to multiple top-tier models like GPT-4o with a single API key).

Database: SQLite + SQLAlchemy (chosen for zero-configuration persistent storage).

III. Features Implemented (Exceeding Scope): List out the major features:

Full CRUD API (Create/Post, Read/Get History, Delete).

Structured, Keyword-Driven LLM Output (Ensures consistency).

Guaranteed PDF Report Generation (Backend).

Interactive Review History with Search and Delete.

Responsive, Polished UI.

IV. Setup and Run Instructions: Provide clear, bulleted steps for a new user to start the project:

git clone [your-repo-link]

Backend Setup: cd backend, pip install -r requirements.txt, and instructions to set the OPENROUTER_API_KEY in .env.

Frontend Setup: cd frontend, npm install, npm start.

V. Evaluation Focus (Optional but Strong): Highlight how your implementation addresses the "Evaluation Focus" points:

LLM Insight Quality: Achieved via detailed prompt engineering for specific categories (modularity, performance, reproducibility).

API Design: Clean REST endpoints (/review, /history, /review/{id}).

