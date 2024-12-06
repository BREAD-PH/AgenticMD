from swarm import Agent, Swarm
from openai import OpenAI
import os

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
    instructions="Collect patient information systematically using OLDCARTS format. "
                 "Ask open-ended questions to gather comprehensive patient history. "
                 "Signal orchestrator when information gathering is complete.",
    functions=[transfer_to_orchestrator]
)

# Medical History Agent
medical_history_agent = Agent(
    name="Medical History Agent",
    instructions="Organize patient information into a structured medical history. "
                 "Identify key medical events, past treatments, allergies, and chronic conditions. "
                 "Signal orchestrator upon history compilation.",
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
    # Start workflow with orchestrator agent
    response = client.run(
        agent=orchestrator_agent,
        messages=[{"role": "user", "content": patient_conversation}]
    )
    return response

# Example Usage
def main():
    patient_conversation = """
    Patient: I've been experiencing chest pain and shortness of breath for the past week.
    My father had a heart attack when he was 55, and I'm 52 now.
    I've been feeling tired and have occasional dizziness.
    """

    medical_report = medical_workflow(patient_conversation)
    print(medical_report.messages[-1]["content"])

if __name__ == "__main__":
    main()