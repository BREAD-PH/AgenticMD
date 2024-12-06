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
    # Configure the page with a medical theme
    st.set_page_config(
        page_title="AgenticMD - AI Medical Assistant",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Add custom CSS for medical theme
    st.markdown("""
        <style>
        .main {
            background-color: #f8f9fa;
        }
        .stButton>button {
            background-color: #3498db;
            color: white;
            border-radius: 20px;
            padding: 0.5rem 2rem;
        }
        .stTextInput>div>div>input {
            border-radius: 10px;
        }
        .stTextArea>div>div>textarea {
            border-radius: 10px;
        }
        .css-1d391kg {
            padding: 2rem 1rem;
        }
        .stAlert {
            border-radius: 10px;
        }
        .stTab {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        </style>
        """, unsafe_allow_html=True)
    
    # Sidebar with improved styling
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/caduceus.png", width=100)
        st.title("🏥 AgenticMD")
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #2c3e50;'>
            <h3>Your AI Medical Assistant</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style='background-color: #eaf2f8; padding: 15px; border-radius: 10px; margin: 10px 0;'>
            <h4 style='color: #2980b9;'>Features:</h4>
            <ul style='color: #34495e;'>
                <li>📋 Comprehensive Patient History</li>
                <li>🔍 Symptom Assessment</li>
                <li>💊 Treatment Planning</li>
                <li>📝 Prescription Generation</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # API Key input with improved styling
        st.markdown("<h4 style='color: #2c3e50;'>Authentication</h4>", unsafe_allow_html=True)
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            help="Required for accessing the AI medical assistant",
            key="openai_api_key_input",
            placeholder="Enter your API key here..."
        )
        
        if api_key:
            try:
                # Initialize clients and agents
                api, client = initialize_clients(api_key)
                st.session_state.openai_api = api
                st.session_state.swarm_client = client
                # Initialize agents with the new client
                st.session_state.agents = initialize_agents(client)
                st.sidebar.success("✅ API key configured successfully!")
            except Exception as e:
                st.sidebar.error(f"❌ Error: {str(e)}")
                st.stop()
        else:
            st.sidebar.warning("⚠️ Please enter your API key to continue")
            st.stop()

    # Create tabs for Consultation and About
    tab1, tab2 = st.tabs(["🏥 Consultation", "ℹ️ About"])
    
    with tab1:
        # Main content area with medical styling
        st.markdown("""
            <div style='text-align: center; padding: 20px;'>
                <h1 style='color: #2c3e50;'>🏥 Agentic MD: Your AI Doctor</h1>
                <p style='color: #7f8c8d;'>Powered by Bread AI</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Initialize session state for conversation history
        if 'conversation_history' not in st.session_state:
            st.session_state.conversation_history = []
            st.session_state.workflow_started = False
            st.session_state.current_step = None
            st.session_state.workflow_results = None
        
        # Initial input form with medical styling
        if not st.session_state.workflow_started:
            if not st.session_state.openai_api:
                st.error("🔐 Please enter your OpenAI API key in the sidebar to continue.")
            else:
                st.markdown("""
                    <div style='background-color: #eaf2f8; padding: 20px; border-radius: 10px; margin: 20px 0;'>
                        <h3 style='color: #2980b9;'>Patient Information Form</h3>
                    </div>
                """, unsafe_allow_html=True)
                
                # Create a single form with medical styling
                with st.form(key="patient_info_form", clear_on_submit=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        main_complaint = st.text_input(
                            "🤒 Chief Complaint",
                            placeholder="e.g., headache, chest pain, dizziness...",
                            key="main_symptom"
                        )
                        
                        duration = st.text_input(
                            "⏱️ Duration of Symptoms",
                            placeholder="e.g., 2 days, 1 week, several months...",
                            key="duration"
                        )
                    
                    with col2:
                        severity = st.slider(
                            "📊 Pain/Discomfort Level",
                            min_value=1,
                            max_value=10,
                            value=5,
                            help="1 = Mild, 10 = Severe",
                            key="severity"
                        )
                    
                    st.markdown("---")
                    
                    other_symptoms = st.text_area(
                        "🔍 Associated Symptoms",
                        placeholder="Please list any other symptoms you're experiencing...",
                        height=100,
                        key="other_symptoms"
                    )
                    
                    medical_history = st.text_area(
                        "📋 Medical History",
                        placeholder="Include any ongoing conditions, medications, allergies, or previous surgeries...",
                        height=100,
                        key="medical_history"
                    )
                    
                    submitted = st.form_submit_button(
                        "🏥 Start Consultation",
                        use_container_width=True,
                    )
                    
                    if submitted:
                        if not main_complaint:
                            st.error("❗ Please describe your main symptom.")
                        else:
                            patient_conversation = f"""
                            Chief Complaint: {main_complaint}
                            Duration: {duration}
                            Severity Level: {severity}/10
                            Associated Symptoms: {other_symptoms}
                            Medical History: {medical_history}
                            """
                            
                            st.session_state.conversation_history.append(("patient", patient_conversation))
                            st.session_state.workflow_started = True
                            st.session_state.current_step = "history"
                            st.rerun()
    
        # Display conversation history with medical styling
        for role, message in st.session_state.conversation_history:
            if role == "patient":
                st.markdown(f"""
                    <div style='background-color: #f5f6fa; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                        <p><strong>👤 Patient:</strong></p>
                        <p style='margin-left: 20px;'>{message}</p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div style='background-color: #eaf2f8; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                        <p><strong>👨‍⚕️ AgenticMD:</strong></p>
                        <p style='margin-left: 20px;'>{message}</p>
                    </div>
                """, unsafe_allow_html=True)

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
                if st.button("Restart Consultation"):
                    st.session_state.clear()
                    st.rerun()

    with tab2:
        st.markdown("# 🏥 AgenticMD: Your AI Doctor")
        st.markdown("---")
        
        st.markdown("""
        AgenticMD is an advanced AI-powered medical consultation system that leverages multiple specialized AI agents 
        to provide comprehensive medical assistance. Powered by Bread AI technology, it offers a sophisticated approach 
        to virtual medical consultations.
        """)
        
        st.markdown("## 🤖 Our AI Agents")
        st.markdown("""
        AgenticMD utilizes a team of specialized AI agents, each with unique roles in the medical consultation process:
        """)
        
        # Create columns for agents
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 1. History Taking Agent 📋
            - Collects patient history using the OLDCARTS format
            - Ensures comprehensive symptom documentation
            - Asks relevant follow-up questions
            
            ### 2. Medical History Agent 🔍
            - Compiles and structures medical history
            - Identifies relevant past conditions
            - Organizes patient information systematically
            
            ### 3. Assessment Agent 📊
            - Analyzes symptoms and medical history
            - Provides comprehensive medical assessments
            - Identifies potential health concerns
            
            ### 4. Treatment Agent 💊
            - Develops evidence-based treatment plans
            - Considers patient history and current conditions
            - Provides comprehensive care recommendations
            """)
        
        with col2:
            st.markdown("""
            ### 5. Prescription Agent 📝
            - Generates detailed prescriptions
            - Ensures medication safety and compatibility
            - Provides dosage and usage instructions
            
            ### 6. Summary Agent 📄
            - Formats prescriptions in standard Rx format
            - Summarizes consultation findings
            - Creates organized medical documentation
            
            ### 7. PDF Generation Agent 📑
            - Creates professional prescription documents
            - Formats medical reports
            - Generates printable consultation summaries
            """)
        
        # Privacy section with expander
        with st.expander("🔒 Privacy & Security", expanded=True):
            st.markdown("""
            - All consultations are processed securely
            - No personal health information is stored
            - Requires API key for access
            """)
        
        # Disclaimer in warning box
        st.warning("""
        ### ⚠️ Disclaimer
        
        AgenticMD is an AI assistant tool and should not replace professional medical advice. 
        Always consult with a qualified healthcare provider for medical decisions.
        """)
        
        # Framework Architecture Section
        st.markdown("## 🔄 Framework Architecture")
        st.markdown("""
        The diagram below illustrates how our specialized AI agents work together in the AgenticMD framework 
        to provide comprehensive medical consultations:
        """)
        
        # Display framework diagram
        framework_image = "assets/excalidraw.png"
        try:
            st.image(framework_image, use_column_width=True, caption="AgenticMD Framework Architecture")
        except FileNotFoundError:
            st.info("Framework diagram will be displayed here. Place the image at: assets/agentic_framework.png")
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #666666; padding: 20px;'>
            Powered by Bread AI | Built with ❤️ for better healthcare
        </div>
        """, unsafe_allow_html=True)

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