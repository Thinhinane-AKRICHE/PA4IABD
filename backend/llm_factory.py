from langchain_openai import ChatOpenAI
from langchain_mistralai import ChatMistralAI
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
import os


def get_llm(provider: str, model: str, temperature: float = 0):
    if provider == "openai":
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=os.getenv("OPENAI_API_KEY")
        )

    elif provider == "mistral":
        return ChatMistralAI(
            model=model,
            temperature=temperature,
            api_key=os.getenv("MISTRAL_API_KEY")
        )

    elif provider == "huggingface":
        endpoint = HuggingFaceEndpoint(
            repo_id=model,
            task="text-generation",
            huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN")
        )
        return ChatHuggingFace(llm=endpoint)

    else:
        raise ValueError(f"Provider non supporté : {provider}")