from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import google.generativeai as genai
import uvicorn
import io
from PIL import Image

# Optional document parsing libraries
try:
    import fitz  # PyMuPDF
    import docx
except ImportError:
    fitz = None
    docx = None
    print("Warning: PyMuPDF or python-docx not installed. PDF and DOCX parsing will be disabled.")


# --- Gemini AI Configuration ---
try:
    # IMPORTANT: Set your GOOGLE_API_KEY environment variable
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    script_dir = os.path.dirname(os.path.realpath(__file__))
    context_path = os.path.join(script_dir, 'chatbot_context_2.txt')
    with open(context_path, "r") as f:
        SYSTEM_PROMPT = f.read()
    model = genai.GenerativeModel('gemini-2.0-flash')
except (KeyError, FileNotFoundError) as e:
    print(f"Warning: Chatbot model could not be loaded. Missing GOOGLE_API_KEY or chatbot_context.txt. Error: {e}")
    model = None

app = FastAPI(
    title="JMI Simple Chatbot API",
    version="1.0.0",
    description="A simple rule-based chatbot for the JMI project.",
)

# --- CORS Middleware ---
# Allows the frontend to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---
# Defines the structure of the request and response data
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

# --- Chat Logic ---
async def get_bot_reply(user_message: str, file: UploadFile = None) -> str:
    """Generates a reply using the Gemini model."""
    if not model:
        return "I'm sorry, but the AI model is not configured. Please check the server logs."
    
    content_parts = [f"{SYSTEM_PROMPT}\n\nPatient: {user_message}\nResponse:"]

    try:
        if file:
            file_bytes = await file.read()
            
            if file.content_type.startswith("image/"):
                img = Image.open(io.BytesIO(file_bytes))
                content_parts.insert(0, img) # Add image before the prompt
                content_parts.insert(1, "Attached is an image. Based on the image and my question, please provide a response.")

            elif file.content_type == "application/pdf" and fitz:
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                pdf_text = "".join(page.get_text() for page in doc)
                content_parts.insert(0, f"--- Attached PDF Content ---\n{pdf_text}\n--- End of PDF ---")

            elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" and docx:
                doc = docx.Document(io.BytesIO(file_bytes))
                docx_text = "\n".join([para.text for para in doc.paragraphs])
                content_parts.insert(0, f"--- Attached DOCX Content ---\n{docx_text}\n--- End of DOCX ---")

            elif file.content_type == "text/plain":
                text_content = file_bytes.decode('utf-8')
                content_parts.insert(0, f"--- Attached Text File Content ---\n{text_content}\n--- End of Text File ---")
            
            else:
                # If file type is unsupported, inform the user.
                unsupported_reply = f"I'm sorry, but I can't process files of type '{file.content_type}'. I can handle images (PNG, JPG), PDFs, DOCX, and plain text files."
                return unsupported_reply
        
        # Generate content using the parts list
        response = await model.generate_content_async(content_parts)
        return response.text

    except genai.types.generation_types.BlockedPromptException as e:
        print(f"Response was blocked: {e}")
        return "I'm sorry, I can't respond to that. The query was blocked for safety reasons."
    except Exception as e:
        print(f"Error generating response from Gemini: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get a response from the AI model: {str(e)}")

# --- API Endpoints ---
@app.get("/")
async def root():
    return {"message": "JMI Chatbot API is running. Use the /chat endpoint to interact."}

@app.post("/chat", response_model=ChatResponse)
async def chat(message: str = Form(...), file: UploadFile = File(None)):
    """Receives a user message and returns a bot reply."""
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    
    if not model:
        raise HTTPException(status_code=503, detail="Chatbot model is not available.")
        
    reply_text = await get_bot_reply(message, file)
    return ChatResponse(reply=reply_text)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)