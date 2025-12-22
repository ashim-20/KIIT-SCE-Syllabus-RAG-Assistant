import os
import traceback
from typing import List
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from vectordb import VectorDB
#from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
# from langchain_google_genai import ChatGoogleGenerativeAI # Uncomment if using Google
from PyPDF2 import PdfReader

# Load environment variables
load_dotenv()

# Define data directory
DATA_DIR = "./data"

def load_documents() -> List[dict]:
    """
    Load documents for demonstration.
    Reads PDF files from the data directory.
    """
    results = []
    
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"[NOTE] Created missing directory: {DATA_DIR}. Please place your PDF there.")
        return []

    print(f"Scanning directory: {DATA_DIR}")
    for root, _, files in os.walk(DATA_DIR):
        for file in files:
            if file.endswith(".pdf"):
                file_path = os.path.join(root, file)
                try:
                    pdf_reader = PdfReader(file_path)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() or ""

                    if text.strip():
                        results.append({
                            "content": text,
                            "metadata": {"source": file_path}
                        })
                        print(f"Successfully read: {file}")
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

    return results


class RAGAssistant:
    """
    A simple RAG-based AI assistant using ChromaDB and multiple LLM providers.
    Supports OpenAI, Groq, and Google Gemini APIs.
    """

    def __init__(self):
        """Initialize the RAG assistant."""
        # Initialize LLM
        self.llm = self._initialize_llm()
        if not self.llm:
            raise ValueError(
                "No valid API key found. Please set GROQ_API_KEY in your .env file"
            )

        # Initialize vector database
        self.vector_db = VectorDB()

        # Create RAG prompt template
        self.template_text = ("""
            
        You are an expert Academic Counselor for the School of Computer Engineering at KIIT University.
        Your goal is to assist students by answering questions strictly based on the provided "Curricula and Syllabi (2022-23)" context.

        GUIDELINES:
        1.  **Source of Truth:** Answer ONLY using the information provided in the CONTEXT below. Do not make up information.
        2.  **Course Queries:** If asked about a specific subject (e.g., "Machine Learning"), provide its Course Code, Credits, Prerequisites, and a summary of the units or textbooks if available.
        3.  **Semester Inquiries:** If asked about a semester (e.g., "What subjects are in Sem 6?"), list the courses clearly with their Codes and Credits using bullet points.
        4.  **Regulations:** If asked about rules (e.g., "Minor Degree", "Projects", "Internships"), explain the eligibility and requirements exactly as stated in the text.
        5.  **Missing Info:** If the answer is not in the context, politely say: "I cannot find that specific detail in the official syllabus document."
        6.  **Tone:** Maintain a professional, encouraging, and structured tone suitable for academic advising.

        CONTEXT:
        {context}

        QUESTION:
        {question}
        COUNSELOR'S ANSWER:
        """
        )
        self.prompt_template = ChatPromptTemplate.from_template(self.template_text)

        # Create the chain
        self.chain = self.prompt_template | self.llm | StrOutputParser()

        print("RAG Assistant initialized successfully")

    def _initialize_llm(self):
        """Initialize the LLM by checking for available API keys."""
        # Using Groq as requested
        if os.getenv("GROQ_API_KEY"):
            model_name = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
            print(f"Using Groq model: {model_name}")
            return ChatGroq(
                api_key=os.getenv("GROQ_API_KEY"), model=model_name, temperature=0.0
            )
        return None

    def add_documents(self, documents: List) -> None:
        """Add documents to the knowledge base."""
        self.vector_db.add_documents(documents)

    def invoke(self, input_text: str, n_results: int = 3) -> str:
        """Query the RAG assistant."""
        
        # 1. Retrieve relevant chunks
        results = self.vector_db.search(input_text, n_results=n_results)
        
        # 2. Combine context
        documents = results.get("documents", [])
        context = "\n\n".join(documents) if documents else "No relevant context found."
        
        # 3. Generate response
        response = self.chain.invoke({"context": context, "question": input_text})
        
        return response


def main():
    """Main function to demonstrate the RAG assistant."""
    try:
        print("=== KIIT Syllabus RAG Assistant ===")
        
        # Initialize the RAG assistant
        print("Initializing RAG Assistant...")
        assistant = RAGAssistant()

        # Load sample documents
        print("\nLoading documents...")
        sample_docs = load_documents()
        
        if sample_docs:
            print(f"Loaded {len(sample_docs)} sample documents")
            assistant.add_documents(sample_docs)
        else:
            print("No documents found to process (or documents already in DB).")

        print("\nReady! Ask questions about the syllabus.")
        
        done = False
        while not done:
            print("\n" + "="*30)
            question = input("Enter a question or 'quit' to exit: ")
            if question.lower() in ["quit", "exit"]:
                done = True
                print("Goodbye!")
            elif question.strip() == "":
                continue
            else:
                print("Thinking...")
                result = assistant.invoke(question)
                print(f"\nAnswer:\n{result}")

    except Exception as e:
        print(f"Error running RAG assistant: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()