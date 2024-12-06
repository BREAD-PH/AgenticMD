import streamlit as st
import os
import sys
import tempfile
from datetime import datetime

# Add the directory containing the original script to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the necessary modules from the original script
from swarm_med import (
    client, 
    history_agent, 
    medical_history_agent, 
    assessment_agent, 
    treatment_agent, 
    prescription_agent, 
    summary_agent, 
    pdf_generation_agent,
    generate_prescription_pdf
)

def agent_workflow_step(agent, context, system_msg, user_msg):
    """Execute an agent workflow step and capture its thought process."""
    with st.expander(f"{agent.name} Processing"):
        try:
            response = client.run(
                agent=agent,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ]
            )
            
            # Display full conversation
            st.write("🤖 Agent Interaction:")
            for msg in response.messages:
                st.write(f"{msg['role'].capitalize()}: {msg['content']}")
            
            # Return the last message content
            return response.messages[-1]["content"]
        
        except Exception as e:
            st.error(f"Error in {agent.name}: {e}")
            return None

def medical_workflow_streamlit(patient_conversation):
    """Streamlit-compatible medical workflow function."""
    st.write("🏥 Starting Medical Workflow")
    
    context = {"patient_info": patient_conversation}
    workflow_results = {}
    
    # History Taking
    st.header("📋 History Taking")
    workflow_results['history'] = agent_workflow_step(
        history_agent, 
        context, 
        "Collect patient history using OLDCARTS format", 
        context["patient_info"]
    )
    
    # Medical History Compilation
    st.header("🔍 Medical History Compilation")
    workflow_results['medical_history'] = agent_workflow_step(
        medical_history_agent, 
        context, 
        "Compile a structured medical history", 
        workflow_results['history']
    )
    
    # Assessment
    st.header("📊 Medical Assessment")
    workflow_results['assessment'] = agent_workflow_step(
        assessment_agent, 
        context, 
        "Provide a comprehensive medical assessment", 
        f"Patient History: {workflow_results['history']}\nMedical History: {workflow_results['medical_history']}"
    )
    
    # Treatment Plan
    st.header("💊 Treatment Plan")
    workflow_results['treatment_plan'] = agent_workflow_step(
        treatment_agent, 
        context, 
        "Provide evidence-based treatment recommendations", 
        f"Assessment: {workflow_results['assessment']}\nMedical History: {workflow_results['medical_history']}"
    )
    
    # Prescription
    st.header("📜 Prescription Generation")
    workflow_results['prescription'] = agent_workflow_step(
        prescription_agent, 
        context, 
        "Generate a detailed prescription based on the treatment plan", 
        f"Treatment Plan: {workflow_results['treatment_plan']}\nMedical History: {workflow_results['medical_history']}"
    )
    
    # Summary and PDF Generation
    st.header("📄 Prescription PDF")
    formatted_prescription = agent_workflow_step(
        summary_agent, 
        context, 
        "Format the prescription in standard Rx format", 
        f"Treatment Plan:\n{workflow_results['treatment_plan']}\n\nPrescription:\n{workflow_results['prescription']}"
    )
    
    # Generate PDF
    
    pdf_path = generate_prescription_pdf(
        prescription_text=formatted_prescription,
        output_path=f"prescriptions/prescription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    )
    
    return workflow_results, pdf_path

def main():
    st.set_page_config(page_title="AI Medical Workflow Assistant", page_icon="🩺", layout="wide")
    
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
        st.subheader("🔒 Disclaimer")
        st.write("""
        This is an AI assistant and should not replace professional medical advice. 
        Always consult with a qualified healthcare provider for medical decisions.
        """)
        
        st.divider()
        if st.button("Clear Conversation"):
            st.session_state.clear()
            st.rerun()

    st.title("🩺 AgenticMD")
    
    # Initialize session state for conversation history
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
        st.session_state.workflow_started = False
        st.session_state.current_step = None
        st.session_state.workflow_results = None
    
    # Initial input form
    if not st.session_state.workflow_started:
        with st.form("patient_info_form"):
            patient_conversation = st.text_area(
                "Please describe your medical symptoms and concerns:", 
                height=200,
                placeholder="Example: I've been experiencing chest pain and shortness of breath for the past week..."
            )
            submit_button = st.form_submit_button("Start Medical Workflow")
            
            if submit_button and patient_conversation:
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
                # Start history taking
                history_response = agent_workflow_step(
                    history_agent,
                    {"patient_info": st.session_state.conversation_history[-1][1]},
                    "Collect patient history using OLDCARTS format. Ask only crucial missing information. If you have enough information for a basic assessment, proceed without further questions.",
                    st.session_state.conversation_history[-1][1]
                )
                
                # Check if the response contains crucial OLDCART elements before asking follow-ups
                crucial_elements = ["onset", "location", "character", "severity"]
                has_crucial_info = all(element.lower() in history_response.lower() for element in crucial_elements)
                
                if "?" in history_response and not has_crucial_info:  # Only ask follow-ups if crucial info is missing
                    st.session_state.conversation_history.append(("agent", history_response))
                    # Show input for follow-up response
                    with st.form("follow_up_form"):
                        follow_up_response = st.text_area(
                            "Please provide additional details:",
                            height=100
                        )
                        if st.form_submit_button("Submit Additional Information"):
                            st.session_state.conversation_history.append(("patient", follow_up_response))
                            st.rerun()
                else:
                    # History taking complete, move to next step
                    st.session_state.current_step = "medical_history"
                    st.session_state.workflow_results = {'history': history_response}
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
        medical_history_agent,
        {"history": workflow_results['history']},
        "Compile a structured medical history",
        workflow_results['history']
    )
    
    # Assessment
    workflow_results['assessment'] = agent_workflow_step(
        assessment_agent,
        {"history": workflow_results['history'], "medical_history": workflow_results['medical_history']},
        "Provide a comprehensive medical assessment",
        f"Patient History: {workflow_results['history']}\nMedical History: {workflow_results['medical_history']}"
    )
    
    # Treatment Plan
    workflow_results['treatment_plan'] = agent_workflow_step(
        treatment_agent,
        {"assessment": workflow_results['assessment'], "medical_history": workflow_results['medical_history']},
        "Provide evidence-based treatment recommendations",
        f"Assessment: {workflow_results['assessment']}\nMedical History: {workflow_results['medical_history']}"
    )
    
    # Prescription
    workflow_results['prescription'] = agent_workflow_step(
        prescription_agent,
        {"treatment_plan": workflow_results['treatment_plan'], "medical_history": workflow_results['medical_history']},
        "Generate a detailed prescription based on the treatment plan",
        f"Treatment Plan: {workflow_results['treatment_plan']}\nMedical History: {workflow_results['medical_history']}"
    )
    
    # Format prescription for PDF
    formatted_prescription = agent_workflow_step(
        summary_agent,
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

if __name__ == "__main__":
    main()