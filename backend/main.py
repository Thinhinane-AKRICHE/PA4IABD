from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

from backend.schemas import ChatRequest, ChatResponse
from backend.agent_builder import build_agent
from user_profile import load_user_profile

load_dotenv()

app = FastAPI(title="Travel Buddy API")


@app.get("/")
def root():
    return {"message": "Travel Buddy Backend is running"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        agent = build_agent(
            provider=request.provider,
            model=request.model,
            temperature=request.temperature,
        )

        question = request.message

        if request.user_id:
            profil = load_user_profile(request.user_id)
            if profil:
                question = (
                    f"[PROFIL UTILISATEUR — adapte ta réponse :\n"
                    f"Nom : {profil['nom']} | Langue : {profil['langue']} | "
                    f"Budget : {profil['budget']} | Type : {profil['type_voyage']} | "
                    f"Hôtels : {profil['prefs_hotels']} | "
                    f"Alimentaire : {profil['contraintes_alim']} | "
                    f"Destinations favorites : {profil['destinations_fav']}]\n\n"
                    f"Question : {question}"
                )

        config = {
            "configurable": {
                "thread_id": request.thread_id
            }
        }

        result = agent.invoke(
            {"messages": [("user", question)]},
            config=config,
        )

        final_message = result["messages"][-1].content

        return ChatResponse(
            response=final_message,
            provider=request.provider,
            model=request.model,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))