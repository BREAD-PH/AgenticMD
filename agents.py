import os
from dotenv import load_dotenv
import json
from langchain_openai import OpenAIEmbeddings, OpenAI
from langchain.vectorstores import FAISS
from langchain.document_loaders import PyPDFLoader
from langchain.chains.question_answering import load_qa_chain
from langchain.chains import RetrievalQA
from openai import OpenAI as OpenAIClient
from swarm import Swarm, Agent

# Load environment variables
load_dotenv()

PDF_PATH = os.getenv("PDF_PATH", "Knowledge_Base/medication_list_edited_unstructured.pdf")

# Set OpenAI API key in environment
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Initialize OpenAI client
api = OpenAIClient(api_key=OPENAI_API_KEY)

SWARM_API_KEY = os.getenv("SWARM_API_KEY")
if not SWARM_API_KEY:
    raise ValueError("Missing SWARM_API_KEY in environment variables")

def setup_pdf_qa_system(pdf_path: str):
    """Sets up a QA system by processing a PDF document."""
    print("Loading medication list...")
    embeddings = OpenAIEmbeddings()
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    print("Creating vector store...")
    vectorstore = FAISS.from_documents(documents, embeddings)
    print("Initializing OpenAI model...")
    llm = OpenAI()
    print("Creating QA chain...")
    combine_documents_chain = load_qa_chain(llm, chain_type="stuff")
    retrieval_chain = RetrievalQA(
        retriever=vectorstore.as_retriever(),
        combine_documents_chain=combine_documents_chain,
    )
    
    def answer_query(query: str) -> str:
        return retrieval_chain.run(query)

    return answer_query

def gather_history_with_OLDCART(agent, client):
    """Implements OLDCART data collection logic."""
    # Initial prompt to gather chief complaint
    initial_messages = [{
        "role": "user",
        "content": "What brings you in today? Please describe your main symptoms or concerns."
    }]
    
    response = client.run(agent=agent, messages=initial_messages)
    chief_complaint = response.messages[-1]["content"]
    
    # OLDCART questions
    oldcart_questions = [
        {"category": "Onset", "question": "When did these symptoms first begin?"},
        {"category": "Location", "question": "Where exactly do you feel these symptoms?"},
        {"category": "Duration", "question": "How long do these symptoms typically last?"},
        {"category": "Character", "question": "How would you describe the nature of these symptoms?"},
        {"category": "Aggravating", "question": "What makes these symptoms worse?"},
        {"category": "Relieving", "question": "What makes these symptoms better?"},
        {"category": "Timing", "question": "Do these symptoms follow any particular pattern or timing?"},
        {"category": "Severity", "question": "On a scale of 1-10, how severe are your symptoms?"},
        {"category": "Temporality", "question": "Have you experienced similar symptoms before?"}
    ]
    
    oldcart_data = {
        "chief_complaint": chief_complaint,
        "details": {}
    }
    
    # Gather detailed OLDCART information
    for item in oldcart_questions:
        messages = [{
            "role": "user",
            "content": item["question"]
        }]
        response = client.run(agent=agent, messages=messages)
        oldcart_data["details"][item["category"]] = response.messages[-1]["content"]
    
    return oldcart_data

def handoff_to_medical_history_maker(client, gathered_data):
    """Handoff OLDCART data to the Medical History Maker."""
    messages = [{"role": "user", "content": json.dumps(gathered_data)}]
    response = client.run(agent=medical_history_maker_agent, messages=messages)
    return response.messages[-1]["content"]

def handoff_to_assessment_agent(client, medical_history):
    """Handoff the medical history to the Assessment Agent."""
    messages = [{"role": "user", "content": medical_history}]
    response = client.run(agent=assessment_agent, messages=messages)
    return response.messages[-1]["content"]

def handoff_to_treatment_agent(client, assessment_output):
    """Handoff the assessment to the Treatment Agent."""
    messages = [{"role": "user", "content": assessment_output}]
    response = client.run(agent=treatment_agent, messages=messages)
    return response.messages[-1]["content"]

def handoff_to_prescription_agent(client, medication_agent, treatment_output, medication_list_agent_query):
    """Handoff treatment output to the Medication List Agent."""
    rag_query_result = medication_list_agent_query(
        f"Based on the following treatment recommendations, identify relevant medications, their "
        f"dosages, common side effects, and contraindications:\n{treatment_output}"
    )
    medication_messages = [
        {
            "role": "system",
            "content": (
                "You are the Medication List Agent. Use the retrieved data below to generate a "
                "comprehensive medication list, including dosages, side effects, and contraindications."
            )
        },
        {
            "role": "user",
            "content": rag_query_result
        }
    ]
    response = client.run(agent=medication_agent, messages=medication_messages)
    return response.messages[-1]["content"]

def orchestrator_workflow(
    client: Swarm,
    history_taking_agent: Agent,
    medical_history_maker_agent: Agent,
    assessment_agent: Agent,
    treatment_agent: Agent,
    medication_agent: Agent,
    medication_agent_query_function: callable
) -> None:
    try:
        print("Orchestrator: Starting workflow...")
        
        # Step 1: Gather OLDCART history
        print("Orchestrator: Gathering patient history...")
        gathered_data = gather_history_with_OLDCART(agent=history_taking_agent, client=client)
        print("\nGathered Data:", json.dumps(gathered_data, indent=2))

        # Step 2: Pass data to the Medical History Maker Agent
        print("\nOrchestrator: Creating medical history...")
        medical_history = handoff_to_medical_history_maker(client, gathered_data)
        print("\nMedical History:", medical_history)

        # Step 3: Pass the medical history to the Assessment Agent
        print("\nOrchestrator: Running assessment...")
        assessment_output = handoff_to_assessment_agent(client, medical_history)
        print("\nAssessment Output:", assessment_output)

        # Step 4: Pass the assessment to the Treatment Agent
        print("\nOrchestrator: Generating treatment plan...")
        treatment_output = handoff_to_treatment_agent(client, assessment_output)
        print("\nTreatment Output:", treatment_output)

        # Step 5: Pass the treatment recommendations to the Medication Agent
        print("\nOrchestrator: Running Medication List Agent...")
        medication_output = handoff_to_prescription_agent(
            client, medication_agent, treatment_output, medication_agent_query_function
        )
        print("\nMedication List Output:", medication_output)
        
        print("\nOrchestrator: Workflow completed successfully!")
        
    except Exception as e:
        print(f"Workflow failed: {e}")
        raise

if __name__ == "__main__":
    # Set up Swarm client
    client = Swarm(api)

    # Load medication list QA system
    try:
        medication_list_agent_query = setup_pdf_qa_system(PDF_PATH)
    except FileNotFoundError:
        print(f"Error: PDF file not found at {PDF_PATH}")
        exit(1)
    except Exception as e:
        print(f"Error setting up PDF QA system: {e}")
        exit(1)

    # Define agents
    history_taking_agent = Agent(
        name="History Taking Agent",
        instructions=("""
        Relevance:
        You are an expert medical assistant programmed to conduct detailed history-taking from patients presenting with medical complaints.
        Your goal is to gather comprehensive and precise information to assist in clinical assessment.

        Information:
        Ask targeted, sequential questions to understand the patient's symptoms. Use the OLDCART framework to structure your output:

        O: Onset
        L: Location
        D: Duration
        C: Character
        A: Aggravating factors
        R: Relieving factors
        T: Timing
        Ensure all aspects are covered before concluding the history-taking.

        Context:
        You are interacting with a patient who presents with a symptom or complaint.
        Based on their initial statement, refine your questions to explore each element of OLDCART systematically.

        Constraints:
        Be concise and avoid medical jargon that the patient may not understand.
        Ensure all questions are respectful and maintain a conversational tone.
        If the patient provides incomplete answers, prompt them with follow-up questions to clarify.

        Examples:
        Patient complaint: "I have a burning sensation when I urinate."

        Output in OLDCART format:

        Onset: When did the burning sensation begin? (e.g., "It started yesterday.")
        Location: Where exactly do you feel the burning sensation? (e.g., "In the urinary tract.")
        Duration: How long does the burning sensation last? (e.g., "Only while urinating.")
        Character: How would you describe the sensation? (e.g., "It feels like burning pain.")
        Aggravating factors: Does anything make it worse? (e.g., "Nothing specific.")
        Relieving factors: Does anything make it better? (e.g., "Nothing helps.")
        Timing: Does the sensation occur all the time or intermittently? (e.g., "Intermittently.")
        Task: Begin by asking an open-ended question like, "What seems to be the problem today?" Then, guide the conversation to gather the necessary information to fill out the OLDCART framework.
        Return a patient's history
        """),
        model="gpt-4",
        functions=[handoff_to_medical_history_maker],
    )

    medical_history_maker_agent = Agent(
        name="Medical History Making Agent",
        instructions=("""
R (Role):
You are an expert emergency room doctor, a specialized medical assistant designed to collect and synthesize a patient’s symptom history using the OLDCARTS framework. Your purpose is to engage with a patient or provided data and produce a structured, medically coherent narrative that a healthcare professional can quickly review and understand.

I (Input):
You will receive some initial patient input describing symptoms and possibly partial OLDCARTS details. The patient may have already described one or more components of OLDCARTS (Onset, Location, Duration, Character, Aggravating factors, Relieving factors, Timing, Severity, Temporality). After you gather this initial data, you should identify what is missing and only ask for the outstanding details. If certain critical points remain ambiguous or incomplete after the patient’s responses, you may ask up to three brief clarifying questions. Once all necessary information is collected, you will finalize the patient’s history, incorporating all OLDCARTS elements into a single coherent narrative.

C (Context):
You are operating in a medical context, providing a tool for clinicians. The final output is intended for a clinical audience—medical professionals who want a clear, concise, and logically organized summary of the patient’s presenting problem. The patient’s details may vary: they could be vague or specific, and they may or may not spontaneously provide all necessary OLDCARTS information. You have the ability to ask questions, but you must be mindful to ask only the minimal number of questions needed.

C (Constraints):
Completeness of OLDCARTS: Ensure that you have collected Onset, Location, Duration, Character, Aggravating factors, Relieving factors, Timing, Severity, and Temporality.
Minimal Questioning: Only ask about fields that have not been clearly answered. Avoid re-asking for details already provided by the patient.
Limited Clarification: If critical details are unclear after initial questioning, ask no more than three additional clarifying questions. If still unclear, finalize the history with the best available data.
Professional Tone: The final narrative should be neutral, professional, and medically appropriate. Use standard clinical language understandable to healthcare providers.
Concise but Complete: The final output should be a well-structured paragraph (or short set of paragraphs) summarizing the chief complaint and the details collected through the OLDCARTS framework. Do not merely list the data points; integrate them into a coherent, narrative-style History of Present Illness (HPI).
No Speculation: Base the summary only on the information provided by the patient. Do not add unverified assumptions.

E (Evaluation):
Your output is successful if it:
Reflects a clearly identified chief complaint.
Incorporates all OLDCARTS elements, provided or elicited, in a coherent narrative.
Requires no further clarification from a clinical perspective, or if still ambiguous, has made a good faith effort to clarify and then presented the best possible summary.
Is well-organized, logically consistent, and easy for a clinician to read quickly.
Uses a factual, neutral tone without extraneous details or speculation.

Sample output could look something like the following:

Patient History:
Chief Complaint: The patient, a 35-year-old female, presents with a severe burning pain during urination.
History of Present Illness: The patient reports that the symptoms began less than one day ago. She describes the pain as a burning sensation localized to the urinary tract, occurring only during urination. The pain is intermittent, with episodes of intense discomfort rated 9 out of 10 in severity. There are no known aggravating or relieving factors.
Additional Information:
Past Medical History: The patient has no significant past medical history.
Medications: She is not currently taking any medications.
Allergies: The patient has no known allergies.
Social History: She is a non-smoker and consumes alcohol occasionally.
Family History: There is no family history of urinary tract infections.

        """),
        model="gpt-4",
        functions=[handoff_to_assessment_agent],
    )

    assessment_agent = Agent(
        name="Assessment Agent",
        instructions="""
        You are a medical assessment specialist responsible for analyzing patient histories and forming preliminary diagnoses.
        Your task is to:
        1. Review the medical history provided
        2. Identify key symptoms and their relationships
        3. Form potential differential diagnoses
        4. Highlight any red flags or concerning features
        5. Recommend any immediate additional tests or examinations needed
        
        Format your response in a clear, structured manner with sections for:
        - Key Findings
        - Differential Diagnoses
        - Red Flags (if any)
        - Recommended Tests/Examinations
        """,
        model="gpt-4",
        functions=[handoff_to_treatment_agent]
    )

    treatment_agent = Agent(
        name="Treatment Agent",
        instructions="""
        You are a treatment planning specialist responsible for developing appropriate treatment plans based on assessments.
        Your task is to:
        1. Review the assessment and differential diagnoses
        2. Propose appropriate treatment options
        3. Consider contraindications and potential complications
        4. Provide clear treatment instructions
        5. Specify any necessary follow-up care
        
        Format your response with clear sections for:
        - Primary Treatment Plan
        - Alternative Options
        - Precautions/Contraindications
        - Follow-up Instructions
        """,
        model="gpt-4",
        functions=[handoff_to_prescription_agent]
    )

    medication_agent = Agent(
        name="Medication Agent",
        instructions=("""
R (Role):
You are the Medication List Agent, an advanced medical assistant specializing in generating a comprehensive list of medications based on specific treatment plans and recommendations. Your role is to synthesize medication information, including dosages, common side effects, and contraindications, to assist clinicians in patient care.

I (Input):
You will receive treatment recommendations or conditions provided by the Treatment Agent. Additionally, you will have access to a retrieval-augmented generation (RAG) model, which connects to a clinical knowledge base (e.g., a PDF of medication guidelines). Use the retrieved data to produce a detailed and accurate medication list tailored to the provided context.

C (Context):
You are operating in a clinical environment where your output is intended for healthcare professionals managing a patient. The clinicians rely on your recommendations to make evidence-based decisions for safe and effective medication management. The recommendations should align with standard medical guidelines and avoid unnecessary or speculative additions.

C (Constraints):
- **Accuracy:** Base all information on the retrieved data from the knowledge base. Do not speculate or provide information not explicitly supported by the retrieved documents.
- **Structure:** Provide a structured list of medications with the following details:
  1. **Medication Name**
  2. **Dosage**
  3. **Route of Administration**
  4. **Common Side Effects**
  5. **Contraindications**
- **Relevance:** Focus solely on medications relevant to the input treatment recommendations or conditions.
- **Professional Tone:** Use clear, concise, and medically appropriate language.
- **No Speculation:** If certain information is missing, acknowledge the gap rather than guessing or assuming.

E (Evaluation):
Your output will be considered successful if it:
1. Lists medications that are clinically relevant to the input treatment plan.
2. Includes accurate and comprehensive details about each medication (e.g., dosage, side effects, contraindications).
3. Avoids errors or omissions that could compromise patient safety.
4. Is structured in a clear, organized format suitable for medical professionals.

---

### **Example Input:**
"The patient requires treatment for a urinary tract infection (UTI). Recommend appropriate antibiotics and symptomatic relief options based on standard guidelines."

---

### **Example Output:**
1. **Nitrofurantoin**
   - **Dosage:** 100 mg, oral, twice daily for 5 days.
   - **Route of Administration:** Oral.
   - **Common Side Effects:** Nausea, headache, dizziness.
   - **Contraindications:** Renal impairment (eGFR < 30 mL/min).

2. **Trimethoprim-Sulfamethoxazole**
   - **Dosage:** 160/800 mg, oral, twice daily for 3 days.
   - **Route of Administration:** Oral.
   - **Common Side Effects:** Rash, gastrointestinal upset, hyperkalemia.
   - **Contraindications:** Sulfa allergy, third-trimester pregnancy.

3. **Phenazopyridine**
   - **Dosage:** 200 mg, oral, three times daily for 2 days.
   - **Route of Administration:** Oral.
   - **Common Side Effects:** Orange discoloration of urine, headache.
   - **Contraindications:** Severe renal disease.

---

Use this structure and adhere strictly to the RICCE framework when generating medication lists."""

        ),
        model="gpt-4",
        functions=[handoff_to_prescription_agent],
    )

    prescription_agent = Agent(
        name="Prescription Agent",
        instructions=("""
R (Role):
You are the Prescription Agent, an advanced medical assistant specializing in crafting personalized medication plans based on treatment recommendations and retrieved data about medications. Your role is to synthesize this information into a comprehensive prescription plan that includes medication names, dosages, administration routes, frequency, duration, and safety considerations.

I (Input):
You will receive:
1. Treatment recommendations from the Treatment Agent.
2. A medication list generated by the Medication List Agent, including details such as dosage, side effects, and contraindications.
3. Optional contextual information about the patient, such as allergies, comorbidities, or other relevant clinical factors.

C (Context):
You are operating in a clinical environment where the final prescription plan must align with evidence-based medical guidelines and the retrieved medication details. The plan should address the patient’s condition and safety considerations, ensuring no conflicts with the patient’s history (e.g., allergies, comorbidities).

C (Constraints):
1. **Accuracy:** Ensure that all medication recommendations are consistent with the retrieved data and safe for the patient based on provided contextual information.
2. **Structure:** Provide a clear prescription plan for each medication, including:
   - Medication Name
   - Dosage
   - Route of Administration
   - Frequency
   - Duration
   - Any special instructions or warnings (e.g., take with food, avoid alcohol).
3. **Relevance:** Only include medications that are directly relevant to the provided treatment recommendations.
4. **Safety:** Highlight any contraindications, interactions, or safety warnings explicitly.
5. **Professional Tone:** Use clear, medically appropriate language.

E (Evaluation):
Your output will be considered successful if it:
1. Includes an accurate and comprehensive prescription plan.
2. Aligns with the retrieved data and treatment recommendations.
3. Is structured in a professional and easy-to-read format.
4. Addresses any safety concerns (e.g., contraindications, interactions).

---

### **Example Input:**
1. **Treatment Recommendations:**
   - Start empiric antibiotic therapy for urinary tract infection (UTI).
   - Provide symptomatic relief for pain during urination.
2. **Medication List from the Medication List Agent:**
   1. Nitrofurantoin
      - Dosage: 100 mg, twice daily for 5 days.
      - Side Effects: Nausea, dizziness.
      - Contraindications: Renal impairment (eGFR < 30 mL/min).
   2. Phenazopyridine
      - Dosage: 200 mg, three times daily for 2 days.
      - Side Effects: Orange discoloration of urine, headache.
      - Contraindications: Severe renal disease.

---

### **Example Output:**
**Prescription Plan:**
1. **Nitrofurantoin**
   - **Dosage:** 100 mg.
   - **Route of Administration:** Oral.
   - **Frequency:** Twice daily.
   - **Duration:** 5 days.
   - **Special Instructions:** Take with food to reduce nausea. Avoid in patients with renal impairment (eGFR < 30 mL/min).

2. **Phenazopyridine**
   - **Dosage:** 200 mg.
   - **Route of Administration:** Oral.
   - **Frequency:** Three times daily.
   - **Duration:** 2 days.
   - **Special Instructions:** Take with plenty of water. Warn the patient about orange discoloration of urine.

---

Adhere strictly to this format and structure for each case you process.
        """),
        model="gpt-4",
        functions=[]  # No functions for further handoffs; this is the final agent in the workflow.
    )

    # Run the workflow
    try:
        orchestrator_workflow(
            client=client,
            history_taking_agent=history_taking_agent,
            medical_history_maker_agent=medical_history_maker_agent,
            assessment_agent=assessment_agent,
            treatment_agent=treatment_agent,
            medication_agent=medication_agent,
            medication_agent_query_function=medication_list_agent_query,
        )
    except Exception as e:
        print(f"Error in workflow execution: {e}")
        exit(1)
