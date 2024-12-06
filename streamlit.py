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
    st.set_page_config(page_title="AI Medical Workflow Assistant", page_icon="🩺")
    
    st.title("🩺 AgenticMD")
    
    with st.form("patient_info_form"):
        patient_conversation = st.text_area(
            "Please describe your medical symptoms and concerns:", 
            height=200, 
            placeholder="Example: I've been experiencing chest pain and shortness of breath for the past week..."
        )
        submit_button = st.form_submit_button("Start Medical Workflow")
    
    if submit_button and patient_conversation:
        try:
            workflow_results, pdf_path = medical_workflow_streamlit(patient_conversation)
            
            st.success("Medical workflow completed successfully!")
            
            with open(pdf_path, "rb") as pdf_file:
                st.download_button(
                    label="Download Prescription PDF",
                    data=pdf_file,
                    file_name=os.path.basename(pdf_path),
                    mime="application/pdf"
                )
            
            # Optional: Display final results
            st.subheader("📄 Final Results Summary")
            st.write("**Treatment Plan:**")
            st.write(workflow_results['treatment_plan'])
            st.write("**Prescription:**")
            st.write(workflow_results['prescription'])
        
        except Exception as e:
            st.error(f"An error occurred during the medical workflow: {e}")

if __name__ == "__main__":
    main()