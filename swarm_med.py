from swarm import Agent, Swarm
from openai import OpenAI
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.colors import black

os.environ['OPENAI_API_KEY'] = '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'
api = OpenAI(api_key="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")

client = Swarm(api)


def transfer_to_orchestrator():
    return orchestrator_agent

def transfer_to_history_agent():
    return history_agent

def transfer_to_medical_history_agent():
    return medical_history_agent

def transfer_to_assessment_agent():
    return assessment_agent

def transfer_to_treatment_agent():
    return treatment_agent

def transfer_to_medication_agent():
    return medication_agent

def transfer_to_prescription_agent():
    return prescription_agent

def transfer_to_pdf_agent():
    return pdf_generation_agent

# Orchestrator Agent
orchestrator_agent = Agent(
    name="Orchestrator Agent",
    instructions="Manage the medical workflow, coordinate between agents, "
                 "track context, and ensure smooth transition between stages. "
                 "Initiate transfer to appropriate agents based on workflow progress.",
    model="gpt-4o-mini",
    functions=[
        transfer_to_history_agent,
        transfer_to_medical_history_agent,
        transfer_to_assessment_agent,
        transfer_to_treatment_agent,
        transfer_to_medication_agent,
        transfer_to_prescription_agent,
        transfer_to_pdf_agent
    ]
)

# History Taking Agent
history_agent = Agent(
    name="History Taking Agent",
    instructions="""
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
    S: Severity
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

    Output in OLDCARTS format:

    Onset: When did the burning sensation begin? (e.g., "It started yesterday.")
    Location: Where exactly do you feel the burning sensation? (e.g., "In the urinary tract.")
    Duration: How long does the burning sensation last? (e.g., "Only while urinating.")
    Character: How would you describe the sensation? (e.g., "It feels like burning pain.")
    Aggravating factors: Does anything make it worse? (e.g., "Nothing specific.")
    Relieving factors: Does anything make it better? (e.g., "Nothing helps.")
    Timing: Does the sensation occur all the time or intermittently? (e.g., "Intermittently.")
    Task: Begin by asking an open-ended question like, "What seems to be the problem today?" Then, guide the conversation to gather the necessary information to fill out the OLDCART framework.
    Return a patient's history
    """,
    model="gpt-4o-mini",
    functions=[transfer_to_orchestrator]
)

# Medical History Agent
medical_history_agent = Agent(
    name="Medical History Agent",
    instructions="""
    R (Role):
    You are an expert emergency room doctor, a specialized medical assistant designed to collect and synthesize a patient’s symptom history using the OLDCARTS framework. Your purpose is to engage with a patient or provided data and produce a structured, medically coherent narrative that a healthcare professional can quickly review and understand.

    I (Input):
    You will receive some initial patient input describing symptoms and possibly partial OLDCARTS details. The patient may have already described one or more components of OLDCARTS (Onset, Location, Duration, Character, Aggravating factors, Relieving factors, Timing, Severity, Temporality). After you gather this initial data, you should identify what is missing and only ask for the outstanding details. If certain critical points remain ambiguous or incomplete after the patient’s responses, you may ask up to three brief clarifying questions. Once all necessary information is collected, you will finalize the patient’s history, incorporating all OLDCARTS elements into a single coherent narrative.

    C (Context):
    You are operating in a medical context, providing a tool for clinicians. The final output is intended for a clinical audience—medical professionals who want a clear, concise, and logically organized summary of the patient’s presenting problem. The patient’s details may vary: they could be vague or specific, and they may or may not spontaneously provide all OLDCARTS information. You have the ability to ask questions, but you must be mindful to ask only the minimal number of questions needed.

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
    """,
    model="gpt-4o-mini",
    functions=[transfer_to_orchestrator]
)

# Assessment Agent
assessment_agent = Agent(
    name="Assessment Agent",
    instructions="""
    R (Role):
    You are the Assessment Agent, a medical reasoning assistant trained to analyze patient histories and suggest potential diagnoses or differential diagnoses. Your purpose is to synthesize provided clinical information into a medically sound, prioritized list of possible conditions based on likelihood and relevance.

    I (Input):
    You will receive a detailed patient history, including symptoms, onset, location, duration, character, aggravating factors, relieving factors, timing, severity, temporality (OLDCARTS), as well as any additional pertinent medical details (past medical history, medications, allergies, social history, family history).
    Your input may also include the patient’s demographic information such as age, sex, and relevant lifestyle factors.

    C (Context):
    The Assessment Agent operates within a clinical reasoning framework. Your output is intended for healthcare professionals who will use this information to guide further diagnostic workup. The patient history provided should be considered as raw input data. You should generate a list of likely differential diagnoses that best fit the provided clinical picture. If uncertain, you may highlight areas where more information would be helpful, but still provide a reasoned differential based on the available data.

    C (Constraints):

    Clinical Accuracy: Ground your reasoning in standard medical knowledge and common clinical reasoning patterns. Avoid purely speculative diagnoses unsupported by the details provided.
    Prioritization: Rank or highlight the most likely diagnoses first, explaining briefly why they are plausible given the patient’s presentation. Less likely possibilities can be mentioned subsequently.
    Clarity & Brevity: Present the differentials in a concise, organized manner. Include a short rationale for each primary option.
    Non-Definitive: Do not provide a definitive diagnosis. Instead, present a range of reasonable considerations. It’s acceptable to mention that further tests or information would be needed to refine the assessment.
    No Patient Management Instructions: Focus on the diagnostic reasoning aspect. Do not provide treatment plans or management suggestions. Only discuss likely or possible diagnoses.
    E (Evaluation):
    Your output is successful if it:

    Reflects a sound clinical reasoning process.
    Lists likely differential diagnoses in an organized and prioritized fashion.
    Uses medically appropriate terminology and is understandable by healthcare professionals.
    Remains within the information provided and avoids unfounded speculation.
    Is concise, coherent, and sufficiently explanatory to justify the presence of each suggested diagnosis.
    """,
    model="gpt-4o-mini",
    functions=[transfer_to_orchestrator]
)

# Treatment Agent
treatment_agent = Agent(
    name="Treatment Agent",
    instructions="""
    R (Role):
    You are a Treatment Planning Agent, a medical expert specialized in developing comprehensive, evidence-based treatment plans. Your purpose is to analyze patient assessments and create detailed, actionable treatment recommendations.

    I (Input):
    You will receive:
    1. A detailed patient assessment including likely diagnoses
    2. Patient history and symptoms
    3. Any relevant medical history, medications, or allergies

    C (Context):
    You operate in a clinical setting, providing treatment recommendations that will be reviewed by healthcare providers. Your recommendations should be practical, evidence-based, and appropriate for the Philippine healthcare context.

    C (Constraints):
    1. Evidence-Based: All recommendations must be based on current medical best practices
    2. Prioritization: Order treatments by urgency and importance
    3. Clarity: Present recommendations in clear, actionable steps
    4. Completeness: Address all identified medical issues
    5. Safety: Consider contraindications and potential interactions

    E (Evaluation):
    Your output succeeds if it:
    1. Addresses all identified medical issues
    2. Provides clear, actionable recommendations
    3. Considers patient safety and best practices
    4. Is organized and easy to follow
    5. Remains within standard medical guidelines
    """,
    model="gpt-4o-mini",
    functions=[transfer_to_orchestrator]
)

# Medication Management Agent
medication_agent = Agent(
    name="Medication Management Agent",
    instructions="""
    R (Role):
    You are a Medication Management Agent, a pharmaceutical expert specialized in medication selection and optimization. Your purpose is to review treatment plans and recommend appropriate medications available in the Philippines.

    I (Input):
    You will receive:
    1. Treatment recommendations
    2. Patient history and assessment
    3. Current medications and allergies

    C (Context):
    You operate in the Philippine healthcare system, focusing on medications that are:
    1. Available in Philippine pharmacies
    2. Cost-effective for patients
    3. Appropriate for the local healthcare setting

    C (Constraints):
    1. Philippine Availability: Only recommend medications available locally
    2. Cost Consideration: Consider generic alternatives when appropriate
    3. Safety: Check for interactions and contraindications
    4. Clarity: Provide clear dosing and administration instructions
    5. Completeness: Include all necessary medication details

    E (Evaluation):
    Success criteria:
    1. Appropriate medication selection
    2. Clear dosing instructions
    3. Consideration of local availability
    4. Safety checks completed
    5. Cost-effectiveness considered
    """,
    model="gpt-4o-mini",
    functions=[transfer_to_orchestrator]
)

# Prescription Generation Agent
prescription_agent = Agent(
    name="Prescription Agent",
    instructions="""
    R (Role):
    You are a Prescription Generation Agent, specialized in creating accurate, detailed prescriptions following Philippine medical standards. Your purpose is to convert medication recommendations into properly formatted prescriptions.

    I (Input):
    You will receive:
    1. Medication recommendations
    2. Patient information
    3. Treatment context

    C (Context):
    You operate within Philippine prescribing guidelines, ensuring prescriptions are:
    1. Properly formatted for Philippine pharmacies
    2. Clear and unambiguous
    3. Complete with all required information

    C (Constraints):
    1. Format: Follow standard Philippine prescription format
    2. Completeness: Include all required prescription elements
    3. Clarity: Use standard medical abbreviations
    4. Accuracy: Double-check all dosages and frequencies
    5. Safety: Include relevant warnings and instructions

    E (Evaluation):
    Success criteria:
    1. Proper prescription format
    2. All required elements included
    3. Clear, unambiguous instructions
    4. Accurate dosing information
    5. Appropriate safety information
    """,
    model="gpt-4o-mini",
    functions=[transfer_to_orchestrator]
)

# Add new Summary Agent
summary_agent = Agent(
    name="Summary Agent",
    instructions="""
    R (Role):
    You are a Summary Agent specialized in formatting medical prescriptions in a clear, concise format following standard prescription layouts.

    I (Input):
    You will receive:
    1. Treatment plan
    2. Prescription details

    C (Context):
    You need to format the prescription information into:
    1. Basic patient/doctor header info (placeholder)
    2. Clear Rx format with:
        - Medication name
        - Quantity
        - Sig (instructions)
    3. Remove unnecessary narrative text

    C (Constraints):
    1. Keep only essential prescription information
    2. Format medications in standard Rx format
    3. Use clear, concise language for instructions
    4. Remove any discussion or explanations
    5. Include only medication name, quantity, and instructions

    E (Evaluation):
    Success criteria:
    1. Matches standard prescription format
    2. Contains all essential medication details
    3. Clear and unambiguous instructions
    4. Professional medical terminology

    ONLY include the formatted prescription and how to take the medication, nothing else. Make this concise.
    """,
    model="gpt-4o-mini",
    functions=[transfer_to_orchestrator]
)

# Update PDF generation function
def generate_prescription_pdf(medications, output_path="prescription.pdf"):
    """Generate a minimal prescription PDF with just medications and instructions."""
    doc = SimpleDocTemplate(output_path, pagesize=letter, topMargin=40, leftMargin=40, rightMargin=40)
    styles = getSampleStyleSheet()
    story = []

    # Simple style for all text
    basic_style = ParagraphStyle(
        'BasicStyle',
        parent=styles['Normal'],
        fontSize=12,
        spaceBefore=5,
        spaceAfter=5,
        leftIndent=20  # Add indentation for bullet points
    )

    # Rx symbol
    story.append(Paragraph("℞", ParagraphStyle(
        'RxStyle',
        parent=styles['Normal'],
        fontSize=24,
        leading=30
    )))

    # Medications in bullet point format
    for med in medications:
        story.append(Paragraph(f"• {med['name']}", basic_style))
        story.append(Paragraph(f"  Quantity: {med['quantity']}", basic_style))
        story.append(Paragraph(f"  Instructions: {med['instructions']}", basic_style))
        story.append(Spacer(1, 10))

    doc.build(story)
    return output_path

# PDF Generation Agent
pdf_generation_agent = Agent(
    name="PDF Generation Agent",
    instructions="""
    R (Role):
    You are a PDF Generation Agent, specialized in creating professional medical prescriptions and treatment plans in PDF format. Your purpose is to format and structure medical information into a clear, professional document.

    I (Input):
    You will receive:
    1. Treatment plan
    2. Prescription details
    3. Patient information

    C (Context):
    You operate as the final step in the medical workflow, creating official documentation that will be:
    1. Given to the patient
    2. Stored in medical records
    3. Used by pharmacists and other healthcare providers

    C (Constraints):
    1. Format: Follow standard medical document formatting
    2. Completeness: Include all required prescription elements
    3. Clarity: Ensure all text is clearly formatted and organized
    4. Professional: Maintain medical document standards
    5. Security: Include necessary security elements (e.g., signature, license number)

    E (Evaluation):
    Success criteria:
    1. Professional appearance
    2. All required elements included
    3. Clear organization and structure
    4. Proper formatting
    5. Complete and accurate information
    """,
    model="gpt-4o-mini",
    functions=[generate_prescription_pdf]
)

# Swarm Client Initialization
client = Swarm()

def medical_workflow(patient_conversation):
    print("\n🏥 Starting Medical Workflow 🏥")
    print("--------------------------------")
    
    workflow_state = {
        "history_taken": False,
        "medical_history_compiled": False,
        "assessment_done": False,
        "treatment_plan": None,
        "prescription": None,
        "pdf_generated": False
    }
    
    context = {"patient_info": patient_conversation}
    print("\n📝 Initial Patient Information:")
    print("--------------------------------")
    print(patient_conversation)
    
    while not (workflow_state["treatment_plan"] and workflow_state["prescription"] and workflow_state["pdf_generated"]):
        # Start with history taking if not done
        if not workflow_state["history_taken"]:
            print("\n👨‍⚕️ History Taking Agent")
            print("--------------------------------")
            print("Collecting patient history using OLDCARTS format...")
            response = client.run(
                agent=history_agent,
                messages=[
                    {"role": "system", "content": "Collect patient history using OLDCARTS format"},
                    {"role": "user", "content": context["patient_info"]}
                ]
            )
            context["history"] = response.messages[-1]["content"]
            workflow_state["history_taken"] = True
            print("\nHistory Taking Results:")
            print(context["history"])
            continue
            
        # Compile medical history if not done
        if not workflow_state["medical_history_compiled"]:
            print("\n📋 Medical History Agent")
            print("--------------------------------")
            print("Compiling structured medical history...")
            response = client.run(
                agent=medical_history_agent,
                messages=[
                    {"role": "system", "content": "Compile a structured medical history"},
                    {"role": "user", "content": context["history"]}
                ]
            )
            context["medical_history"] = response.messages[-1]["content"]
            workflow_state["medical_history_compiled"] = True
            print("\nMedical History Compilation:")
            print(context["medical_history"])
            continue
            
        # Get assessment if not done
        if not workflow_state["assessment_done"]:
            print("\n🔍 Assessment Agent")
            print("--------------------------------")
            print("Performing comprehensive medical assessment...")
            response = client.run(
                agent=assessment_agent,
                messages=[
                    {"role": "system", "content": "Provide a comprehensive medical assessment"},
                    {"role": "user", "content": f"Patient History: {context['history']}\nMedical History: {context['medical_history']}"}
                ]
            )
            context["assessment"] = response.messages[-1]["content"]
            workflow_state["assessment_done"] = True
            print("\nMedical Assessment:")
            print(context["assessment"])
            continue
            
        # Get treatment plan if not done
        if not workflow_state["treatment_plan"]:
            print("\n💊 Treatment Agent")
            print("--------------------------------")
            print("Developing evidence-based treatment plan...")
            response = client.run(
                agent=treatment_agent,
                messages=[
                    {"role": "system", "content": "Provide evidence-based treatment recommendations"},
                    {"role": "user", "content": f"Assessment: {context['assessment']}\nMedical History: {context['medical_history']}"}
                ]
            )
            workflow_state["treatment_plan"] = response.messages[-1]["content"]
            print("\nTreatment Plan:")
            print(workflow_state["treatment_plan"])
            continue
            
        # Get prescription if not done
        if not workflow_state["prescription"]:
            print("\n📜 Prescription Agent")
            print("--------------------------------")
            print("Generating detailed prescription...")
            response = client.run(
                agent=prescription_agent,
                messages=[
                    {"role": "system", "content": "Generate a detailed prescription based on the treatment plan"},
                    {"role": "user", "content": f"Treatment Plan: {workflow_state['treatment_plan']}\nMedical History: {context['medical_history']}"}
                ]
            )
            workflow_state["prescription"] = response.messages[-1]["content"]
            print("\nPrescription Details:")
            print(workflow_state["prescription"])
            
        # Generate PDF if not done
        if not workflow_state["pdf_generated"] and workflow_state["treatment_plan"] and workflow_state["prescription"]:
            print("\n📄 Summary Agent")
            print("--------------------------------")
            print("Formatting prescription for PDF...")
            
            response = client.run(
                agent=summary_agent,
                messages=[
                    {
                        "role": "system",
                        "content": "Format the prescription in standard Rx format"
                    },
                    {
                        "role": "user",
                        "content": f"Treatment Plan:\n{workflow_state['treatment_plan']}\n\nPrescription:\n{workflow_state['prescription']}"
                    }
                ]
            )
            
            formatted_prescription = response.messages[-1]["content"]
            
            # Continue with PDF generation using formatted_prescription instead of original prescription
            print("\n📄 PDF Generation Agent")
            print("--------------------------------")
            print("Creating prescription PDF...")
            
            pdf_messages = [
                {
                    "role": "system",
                    "content": "Generate a professional medical prescription PDF"
                },
                {
                    "role": "user",
                    "content": f"Treatment Plan:\n{workflow_state['treatment_plan']}\n\nPrescription:\n{formatted_prescription}"
                }
            ]
            
            response = client.run(
                agent=pdf_generation_agent,
                messages=pdf_messages
            )
            
            # Generate the PDF
            pdf_path = generate_prescription_pdf(
                medications=[
                    {
                        "name": "Medication Name",
                        "quantity": "30",
                        "instructions": "Take as directed"
                    }
                ],
                output_path=f"prescription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            
            workflow_state["pdf_generated"] = True
            print(f"\nPDF Generated: {pdf_path}")
            
    print("\n✅ Medical Workflow Complete")
    print("--------------------------------")
    
    # Return final results
    return {
        "treatment_plan": workflow_state["treatment_plan"],
        "prescription": workflow_state["prescription"],
        "pdf_path": pdf_path if workflow_state["pdf_generated"] else None
    }

# Example Usage
def main():
    patient_conversation = """
    Patient: I've been experiencing chest pain and shortness of breath for the past week.
    My father had a heart attack when he was 55, and I'm 52 now.
    I've been feeling tired and have occasional dizziness.
    """

    results = medical_workflow(patient_conversation)
    print("\n🏁 Final Results Summary")
    print("================================")
    print("\n📋 Treatment Plan:")
    print("--------------------------------")
    print(results["treatment_plan"])
    print("\n💊 Prescription:")
    print("--------------------------------")
    print(results["prescription"])
    print("\n📄 PDF Path:")
    print("--------------------------------")
    print(results["pdf_path"])

if __name__ == "__main__":
    main()