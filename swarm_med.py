from swarm import Agent, Swarm
from openai import OpenAI
import os


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

# Orchestrator Agent
orchestrator_agent = Agent(
    name="Orchestrator Agent",
    instructions="Manage the medical workflow, coordinate between agents, "
                 "track context, and ensure smooth transition between stages. "
                 "Initiate transfer to appropriate agents based on workflow progress.",
    functions=[
        transfer_to_history_agent,
        transfer_to_medical_history_agent,
        transfer_to_assessment_agent,
        transfer_to_treatment_agent,
        transfer_to_medication_agent,
        transfer_to_prescription_agent
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
    """,
    model = "gpt-4o-mini",
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
    """,
    functions=[transfer_to_orchestrator]
)

# Assessment Agent
assessment_agent = Agent(
    name="Assessment Agent",
    instructions="Analyze patient history and symptoms to provide a comprehensive "
                 "medical assessment. Identify potential diagnoses and key clinical observations. "
                 "Signal orchestrator after assessment completion.",
    functions=[transfer_to_orchestrator]
)

# Treatment Agent
treatment_agent = Agent(
    name="Treatment Agent",
    instructions="Based on medical assessment, recommend evidence-based treatment "
                 "protocols. Consider patient history, current condition, and best practices. "
                 "Signal orchestrator after treatment recommendations.",
    functions=[transfer_to_orchestrator]
)

# Medication Management Agent
medication_agent = Agent(
    name="Medication Management Agent",
    instructions="Create a comprehensive medication list. Check for potential "
                 "interactions, contraindications, and optimize medication regimen. "
                 "Signal orchestrator after medication review.",
    functions=[transfer_to_orchestrator]
)

# Prescription Generation Agent
prescription_agent = Agent(
    name="Prescription Agent",
    instructions="Generate precise medical prescriptions following standard "
                 "medical writing protocols. Ensure clarity, dosage accuracy, and safety."
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
        "prescription": None
    }
    
    context = {"patient_info": patient_conversation}
    print("\n📝 Initial Patient Information:")
    print("--------------------------------")
    print(patient_conversation)
    
    while not (workflow_state["treatment_plan"] and workflow_state["prescription"]):
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
            
    print("\n✅ Medical Workflow Complete")
    print("--------------------------------")
    
    # Return final results
    return {
        "treatment_plan": workflow_state["treatment_plan"],
        "prescription": workflow_state["prescription"]
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

if __name__ == "__main__":
    main()