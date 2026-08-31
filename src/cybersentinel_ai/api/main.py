from fastapi import FastAPI

app = FastAPI(
    title="CyberSentinel AI",
    version="0.1.0",
    description="AI-powered network intrusion detection and SOC assistant.",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "cybersentinel-ai",
    }
