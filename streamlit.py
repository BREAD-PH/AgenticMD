import streamlit as st
import os
import sys
from swarm import Agent, Swarm
from openai import OpenAI
import tempfile
from datetime import datetime

# Add the directory containing the original script to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def initialize_clients(api_key):
    """Initialize OpenAI and Swarm clients with API key"""
    os.environ['OPENAI_API_KEY'] = api_key
    api = OpenAI(api_key=api_key)
    client = Swarm(api)
    return api, client

# Add better error handling for imports
try:
    from swarm_med import (
        generate_prescription_pdf,
    )
except ImportError as e:
    st.error(f"Failed to import required modules from swarm_med: {e}")
    st.stop()

def agent_workflow_step(agent, context, system_msg, user_msg):
    """Execute an agent workflow step and capture its thought process."""
    with st.expander(f"{agent.name} Processing"):
        try:
            # Use the client from session state
            if not st.session_state.swarm_client:
                st.error("API client not initialized. Please check your API key.")
                st.stop()
                
            # Combine original message with any follow-up responses
            full_context = context.get("patient_info", "") + "\n" + context.get("follow_ups", "")
            
            response = st.session_state.swarm_client.run(
                agent=agent,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": full_context if full_context.strip() else user_msg}
                ]
            )
            
            # Display full conversation
            st.write("🤖 Agent Interaction:")
            for msg in response.messages:
                st.write(f"{msg['role'].capitalize()}: {msg['content']}")
            
            return response.messages[-1]["content"]
        
        except Exception as e:
            st.error(f"Error in {agent.name}: {e}")
            return None

def initialize_agents(client):
    """Initialize all agents with the provided client"""
    global history_agent, medical_history_agent, assessment_agent, treatment_agent
    global prescription_agent, summary_agent, pdf_generation_agent

    # Initialize agents with the session state client
    if not client:
        st.error("Client not initialized. Please check your API key.")
        st.stop()

    # Create agents with the correct initialization format
    history_agent = Agent(
        name="History Taking Agent",
        instructions="Collect patient history using OLDCARTS format",
        model="gpt-4o-mini",
        client=client
    )
    
    medical_history_agent = Agent(
        name="Medical History Agent",
        instructions="Compile a structured medical history",
        model="gpt-4o-mini",
        client=client
    )
    
    assessment_agent = Agent(
        name="Assessment Agent",
        instructions="Provide a comprehensive medical assessment",
        model="gpt-4o-mini",
        client=client
    )
    
    treatment_agent = Agent(
        name="Treatment Agent",
        instructions="Provide evidence-based treatment recommendations",
        model="gpt-4o-mini",
        client=client
    )
    
    prescription_agent = Agent(
        name="Prescription Agent",
        instructions="Generate a detailed prescription based on the treatment plan",
        model="gpt-4o-mini",
        client=client
    )
    
    summary_agent = Agent(
        name="Summary Agent",
        instructions="Format the prescription in standard Rx format",
        model="gpt-4o-mini",
        client=client
    )
    
    pdf_generation_agent = Agent(
        name="PDF Generation Agent",
        instructions="Generate a properly formatted prescription PDF",
        model="gpt-4o-mini",
        client=client
    )

    return {
        'history': history_agent,
        'medical_history': medical_history_agent,
        'assessment': assessment_agent,
        'treatment': treatment_agent,
        'prescription': prescription_agent,
        'summary': summary_agent,
        'pdf': pdf_generation_agent
    }

def get_missing_oldcart_elements(history_response):
    """Check which crucial OLDCART elements are missing from the response."""
    oldcart_elements = {
        "onset": ["when", "start", "begin"],
        "location": ["where", "location", "area"],
        "character": ["feel", "describe", "nature", "type"],
        "severity": ["scale", "severe", "intensity", "bad"]
    }
    
    missing_elements = []
    for element, keywords in oldcart_elements.items():
        if not any(keyword in history_response.lower() for keyword in keywords):
            missing_elements.append(element)
    
    return missing_elements

def get_oldcart_question(missing_element):
    """Get the appropriate question for the missing OLDCART element."""
    questions = {
        "onset": "When did these symptoms first begin?",
        "location": "Where exactly do you feel these symptoms?",
        "character": "How would you describe the nature of these symptoms?",
        "severity": "On a scale of 1-10, how severe are your symptoms?"
    }
    return questions.get(missing_element)

def handle_history_taking():
    """Handle the history taking workflow with sequential OLDCART questions"""
    if "current_question_idx" not in st.session_state:
        st.session_state.current_question_idx = 0
        st.session_state.responses = {}
    
    questions = [
        {"id": "onset", "question": "When did you first notice the shortness of breath?"},
        {"id": "location", "question": "Is there a specific area where you feel this discomfort, or is it general?"},
        {"id": "character", "question": "How would you describe the shortness of breath? (e.g., tight feeling, gasping sensation, etc.)"},
        {"id": "severity", "question": "On a scale of 1 to 10, how severe would you rate the shortness of breath?"}
    ]
    
    # Display current question if we haven't finished all questions
    if st.session_state.current_question_idx < len(questions):
        current_q = questions[st.session_state.current_question_idx]
        st.write("🤖 AgenticMD:", current_q["question"])
        
        # Create a unique key for each form
        response = st.text_input(
            "Your response:",
            key=f"response_{current_q['id']}",
            label_visibility="collapsed"
        )
        
        if st.button("Submit", key=f"submit_{current_q['id']}"):
            if response:
                # Save response
                st.session_state.responses[current_q["id"]] = response
                st.session_state.conversation_history.extend([
                    ("agent", current_q["question"]),
                    ("patient", response)
                ])
                # Move to next question
                st.session_state.current_question_idx += 1
                st.rerun()
    else:
        # All questions answered, compile final history
        full_context = (
            st.session_state.context["patient_info"] + "\n" +
            "\n".join([f"{q}: {st.session_state.responses.get(q['id'], '')}" 
                      for q in questions])
        )
        
        final_history = agent_workflow_step(
            history_agent,
            {"patient_info": full_context},
            "Compile a complete patient history using all provided information in OLDCARTS format",
            full_context
        )
        
        st.session_state.current_step = "medical_history"
        st.session_state.workflow_results = {'history': final_history}
        st.rerun()

def main():
    st.set_page_config(page_title="AI Medical Workflow Assistant", page_icon="🩺", layout="wide")
    
    # Initialize session state for API clients and agents
    if 'openai_api' not in st.session_state:
        st.session_state.openai_api = None
    if 'swarm_client' not in st.session_state:
        st.session_state.swarm_client = None
    if 'agents' not in st.session_state:
        st.session_state.agents = None
    
    # Sidebar
    with st.sidebar:
        st.title("ℹ️ About AgenticMD")
        st.write("""
        AgenticMD is an AI-powered medical assistant that helps:
        - Take patient history
        - Assess symptoms
        - Generate treatment plans
        - Create prescriptions
        """)
        
        st.divider()
        # API Key input in sidebar
        api_key = st.text_input(
            "Enter OpenAI API Key",
            type="password",
            help="Required for accessing the AI medical assistant",
            key="openai_api_key_input"
        )
        
        if api_key:
            try:
                # Initialize clients and agents
                api, client = initialize_clients(api_key)
                st.session_state.openai_api = api
                st.session_state.swarm_client = client
                # Initialize agents with the new client
                st.session_state.agents = initialize_agents(client)
                st.sidebar.success("API key successfully configured!")
            except Exception as e:
                st.sidebar.error(f"Error initializing with API key: {str(e)}")
                st.stop()
        else:
            st.sidebar.warning("Please enter your OpenAI API key to continue.")
            st.stop()

    st.title("🩺 AgenticMD")
    
    # Initialize session state for conversation history
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
        st.session_state.workflow_started = False
        st.session_state.current_step = None
        st.session_state.workflow_results = None
    
    # Initial input form with structured questions
    if not st.session_state.workflow_started:
        if not st.session_state.openai_api:
            st.error("Please enter your OpenAI API key in the sidebar to continue.")
        else:
            # Create a single form that contains all inputs
            with st.form(key="patient_info_form", clear_on_submit=False):
                st.write("📋 Symptom Information")
                
                # All form inputs must be inside the form
                main_complaint = st.text_input(
                    "What is your main symptom?",
                    placeholder="Example: headache, chest pain, dizziness...",
                    key="main_symptom"
                )
                
                duration = st.text_input(
                    "How long have you been experiencing this?",
                    placeholder="Example: 2 days, 1 week, several months...",
                    key="duration"
                )
                
                severity = st.slider(
                    "On a scale of 1-10, how severe is your symptom?",
                    min_value=1,
                    max_value=10,
                    value=5,
                    key="severity"
                )
                
                other_symptoms = st.text_area(
                    "Are you experiencing any other symptoms?",
                    placeholder="List any other symptoms you're experiencing...",
                    height=100,
                    key="other_symptoms"
                )
                
                medical_history = st.text_area(
                    "Any relevant medical history?",
                    placeholder="Include any ongoing conditions, medications, or allergies...",
                    height=100,
                    key="medical_history"
                )
                
                # The form submit button must be the last element in the form
                submitted = st.form_submit_button(
                    "Start Medical Consultation",
                    use_container_width=True,
                    type="primary"  # Makes the button more prominent
                )
                
                # Only process the form when the submit button is clicked
                if submitted:
                    if not main_complaint:
                        st.error("Please describe your main symptom.")
                    else:
                        patient_conversation = f"""
                        Main Symptom: {main_complaint}
                        Duration: {duration}
                        Severity: {severity}/10
                        Additional Symptoms: {other_symptoms}
                        Medical History: {medical_history}
                        """
                        
                        st.session_state.conversation_history.append(("patient", patient_conversation))
                        st.session_state.workflow_started = True
                        st.session_state.current_step = "history"
                        st.rerun()
    
    # Display conversation history
    for role, message in st.session_state.conversation_history:
        if role == "patient":
            st.write("👤 You:", message)
        else:
            st.write("🤖 AgenticMD:", message)
    
    # Handle workflow steps
    if st.session_state.workflow_started:
        try:
            if st.session_state.current_step == "history":
                # Initialize context and question index if not exists
                if "context" not in st.session_state:
                    st.session_state.context = {
                        "patient_info": st.session_state.conversation_history[-1][1],
                        "follow_ups": {},  # Store responses by question category
                        "current_question_idx": 0
                    }
                
                # OLDCART questions sequence
                oldcart_questions = [
                    {"category": "Onset", "question": "When did you first start feeling dizzy?"},
                    {"category": "Location", "question": "Can you describe where you feel the dizziness? Is it a feeling of spinning, lightheadedness, or something else?"},
                    {"category": "Duration", "question": "How long does the dizziness last when it happens?"},
                    {"category": "Character", "question": "How would you describe the sensation? Is it mild, moderate, or severe?"},
                    {"category": "Aggravating", "question": "Does anything make the dizziness worse?"},
                    {"category": "Relieving", "question": "Is there anything that helps relieve the dizziness?"},
                    {"category": "Timing", "question": "Does the dizziness happen all the time, or is it intermittent?"},
                    {"category": "Severity", "question": "On a scale of 1 to 10, how would you rate the severity of your dizziness?"}
                ]
                
                # Display conversation history
                for role, message in st.session_state.conversation_history:
                    if role == "patient":
                        st.write("👤 You:", message)
                    else:
                        st.write("🤖 AgenticMD:", message)
                
                # Present current question if not all questions answered
                current_idx = st.session_state.context["current_question_idx"]
                if current_idx < len(oldcart_questions):
                    current_q = oldcart_questions[current_idx]
                    
                    if current_idx == 0 or st.session_state.context["follow_ups"].get(oldcart_questions[current_idx-1]["category"]):
                        st.write("🤖 AgenticMD:", current_q["question"])
                        
                        user_response = st.text_area(
                            "Your response:",
                            key=f"response_{current_q['category']}",
                            height=100
                        )
                        
                        if st.button("Submit Response"):
                            if user_response:
                                # Store response and update conversation history
                                st.session_state.context["follow_ups"][current_q["category"]] = user_response
                                st.session_state.conversation_history.extend([
                                    ("agent", current_q["question"]),
                                    ("patient", user_response)
                                ])
                                # Move to next question
                                st.session_state.context["current_question_idx"] += 1
                                st.rerun()
                else:
                    # All questions answered, compile final history
                    full_history = (
                        f"Initial complaint: {st.session_state.context['patient_info']}\n" +
                        "\n".join([f"{cat}: {resp}" for cat, resp in st.session_state.context["follow_ups"].items()])
                    )
                    
                    # Move to next step
                    st.session_state.current_step = "medical_history"
                    st.session_state.workflow_results = {'history': full_history}
                    st.session_state.context = {}
                    st.rerun()
            
            # Continue with remaining workflow steps
            elif st.session_state.workflow_results:
                workflow_results, pdf_path = complete_medical_workflow(st.session_state.workflow_results)
                st.success("Medical workflow completed successfully!")
                
                # Display download button for prescription
                with open(pdf_path, "rb") as pdf_file:
                    st.download_button(
                        label="Download Prescription PDF",
                        data=pdf_file,
                        file_name=os.path.basename(pdf_path),
                        mime="application/pdf"
                    )
                
                # Display final results
                st.subheader("📄 Final Results Summary")
                st.write("**Treatment Plan:**")
                st.write(workflow_results['treatment_plan'])
                st.write("**Prescription:**")
                st.write(workflow_results['prescription'])
                
                # Reset workflow
                if st.button("Start New Consultation"):
                    st.session_state.clear()
                    st.rerun()
        
        except Exception as e:
            st.error(f"An error occurred during the medical workflow: {e}")

def complete_medical_workflow(initial_results):
    """Complete the remaining steps of the medical workflow after history taking"""
    workflow_results = initial_results.copy()
    
    # Medical History Compilation
    workflow_results['medical_history'] = agent_workflow_step(
        st.session_state.agents['medical_history'],
        {"history": workflow_results['history']},
        "Compile a structured medical history",
        workflow_results['history']
    )
    
    # Assessment
    workflow_results['assessment'] = agent_workflow_step(
        st.session_state.agents['assessment'],
        {"history": workflow_results['history'], "medical_history": workflow_results['medical_history']},
        "Provide a comprehensive medical assessment",
        f"Patient History: {workflow_results['history']}\nMedical History: {workflow_results['medical_history']}"
    )
    
    # Treatment Plan
    workflow_results['treatment_plan'] = agent_workflow_step(
        st.session_state.agents['treatment'],
        {"assessment": workflow_results['assessment'], "medical_history": workflow_results['medical_history']},
        "Provide evidence-based treatment recommendations",
        f"Assessment: {workflow_results['assessment']}\nMedical History: {workflow_results['medical_history']}"
    )
    
    # Prescription
    workflow_results['prescription'] = agent_workflow_step(
        st.session_state.agents['prescription'],
        {"treatment_plan": workflow_results['treatment_plan'], "medical_history": workflow_results['medical_history']},
        "Generate a detailed prescription based on the treatment plan",
        f"Treatment Plan: {workflow_results['treatment_plan']}\nMedical History: {workflow_results['medical_history']}"
    )
    
    # Format prescription for PDF
    formatted_prescription = agent_workflow_step(
        st.session_state.agents['summary'],
        {"treatment_plan": workflow_results['treatment_plan'], "prescription": workflow_results['prescription']},
        "Format the prescription in standard Rx format",
        f"Treatment Plan: {workflow_results['treatment_plan']}\nPrescription: {workflow_results['prescription']}"
    )
    
    # Generate PDF
    pdf_path = generate_prescription_pdf(
        prescription_text=formatted_prescription,
        output_path=f"prescriptions/prescription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    )
    
    return workflow_results, pdf_path

def verify_agents():
    """Verify that all required agents are properly loaded."""
    try:
        required_agents = [
            st.session_state.agents['history'],
            st.session_state.agents['medical_history'],
            st.session_state.agents['assessment'],
            st.session_state.agents['treatment'],
            st.session_state.agents['prescription'],
            st.session_state.agents['summary'],
            st.session_state.agents['pdf']
        ]
        
        for agent in required_agents:
            if agent is None:
                st.error(f"Failed to load required agent: {agent}")
                st.stop()
                
        return True
        
    except NameError as e:
        st.error(f"Required agent not defined: {e}")
        st.stop()
    except Exception as e:
        st.error(f"Error verifying agents: {e}")
        st.stop()

if __name__ == "__main__":
    main()