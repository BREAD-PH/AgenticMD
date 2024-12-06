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