from typing import Dict, List

# Seed canonical list of 50+ prominent AI companies and products
CANONICAL_ENTITIES: Dict[str, List[str]] = {
    "OpenAI": ["openai", "open ai", "openai inc", "openai llc", "openai global"],
    "Anthropic": ["anthropic", "anthropic pbc", "anthropic ai"],
    "Mistral AI": ["mistral", "mistral ai", "mistral ai sas", "mistralai"],
    "Google DeepMind": ["deepmind", "google deepmind", "deepmind technologies"],
    "Hugging Face": ["hugging face", "huggingface", "huggingface inc", "hf"],
    "Scale AI": ["scale ai", "scale labs", "scale computing"],
    "Stability AI": ["stability ai", "stability", "stabilityai"],
    "Cohere": ["cohere", "cohere ai", "cohere inc"],
    "Perplexity AI": ["perplexity", "perplexity ai", "perplexity ai inc"],
    "Midjourney": ["midjourney", "midjourney inc"],
    "Cursor": ["cursor", "anysphere", "cursor ai"],
    "Databricks": ["databricks", "databricks inc"],
    "ElevenLabs": ["elevenlabs", "eleven labs", "elevenlabs inc"],
    "Runway": ["runway", "runway ml", "runwayml", "runway ai"],
    "Synthesia": ["synthesia", "synthesia ltd"],
    "Pinecone": ["pinecone", "pinecone systems", "pinecone io"],
    "Weaviate": ["weaviate", "weaviate bv", "semi technologies"],
    "Qdrant": ["qdrant", "qdrant solutions"],
    "Chroma": ["chroma", "chroma db", "chromadb"],
    "LangChain": ["langchain", "langchain inc"],
    "LlamaIndex": ["llamaindex", "llama index", "runllama"],
    "Together AI": ["together ai", "together compute", "togetherai"],
    "Replicate": ["replicate", "replicate inc"],
    "Anyscale": ["anyscale", "anyscale inc"],
    "Fireworks AI": ["fireworks ai", "fireworks"],
    "Groq": ["groq", "groq inc"],
    "Cerebras": ["cerebras", "cerebras systems"],
    "SambaNova": ["sambanova", "sambanova systems"],
    "Jasper": ["jasper", "jasper ai"],
    "Copy.ai": ["copy ai", "copyai"],
    "Character.ai": ["character ai", "characterai"],
    "Harvey": ["harvey", "harvey ai"],
    "Adept AI": ["adept", "adept ai", "adept ai labs"],
    "Inflection AI": ["inflection", "inflection ai"],
    "Poolside": ["poolside", "poolside ai"],
    "Sakana AI": ["sakana", "sakana ai"],
    "Cognition": ["cognition", "cognition ai", "cognition labs"],
    "Writer": ["writer", "writer ai", "writer inc"],
    "Glean": ["glean", "glean technologies"],
    "Shield AI": ["shield ai", "shield ai inc"],
    "Helsing": ["helsing", "helsing ai"],
    "Cresta": ["cresta", "cresta intelligence"],
    "Tabnine": ["tabnine", "codota"],
    "Phind": ["phind", "phind ai"],
    "Weights & Biases": ["wandb", "weights and biases", "weights biases"],
    "Modal": ["modal", "modal labs"],
    "Baseten": ["baseten", "baseten inc"],
    "OctoAI": ["octoai", "octoml"],
    "Lightning AI": ["lightning ai", "grid ai", "pytorch lightning"],
    "DeepSeek": ["deepseek", "deepseek ai", "deepseek inc"]
}

# Reverse lookup dictionary: normalized alias -> canonical name
ALIAS_TO_CANONICAL: Dict[str, str] = {}
for canonical, aliases in CANONICAL_ENTITIES.items():
    # Canonical itself is an alias
    ALIAS_TO_CANONICAL[canonical.lower().strip()] = canonical
    for a in aliases:
        ALIAS_TO_CANONICAL[a.lower().strip()] = canonical
