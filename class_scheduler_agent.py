from typing import List, Dict
from datetime import datetime, timedelta
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.tools import tool
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

class ClassScheduler:
    def __init__(self):
        self.schedule: Dict[str, List[Dict]] = {}
        self.rooms: List[str] = ["Room A", "Room B", "Room C"]
        self.time_slots = [
            "09:00", "10:00", "11:00", "12:00", "13:00", 
            "14:00", "15:00", "16:00", "17:00"
        ]

    @tool
    def list_available_rooms(self, date: str) -> str:
        """Lists all available rooms for a given date."""
        if date not in self.schedule:
            return f"All rooms ({', '.join(self.rooms)}) are available for {date}"
        
        booked_rooms = set(class_info['room'] for class_info in self.schedule[date])
        available_rooms = set(self.rooms) - booked_rooms
        
        if not available_rooms:
            return f"No rooms available for {date}"
        return f"Available rooms for {date}: {', '.join(available_rooms)}"

    @tool
    def list_available_times(self, date: str, room: str) -> str:
        """Lists all available time slots for a given date and room."""
        if room not in self.rooms:
            return f"Invalid room. Available rooms are: {', '.join(self.rooms)}"
        
        if date not in self.schedule:
            return f"All time slots are available for {room} on {date}: {', '.join(self.time_slots)}"
        
        booked_times = set(
            class_info['time'] 
            for class_info in self.schedule[date] 
            if class_info['room'] == room
        )
        available_times = set(self.time_slots) - booked_times
        
        if not available_times:
            return f"No available time slots for {room} on {date}"
        return f"Available times for {room} on {date}: {', '.join(sorted(available_times))}"

    @tool
    def schedule_class(self, date: str, room: str, time: str, class_name: str) -> str:
        """
        Schedule a class for a specific date, room, and time.
        Format: date should be YYYY-MM-DD, time should be HH:MM
        """
        # Validate inputs
        if room not in self.rooms:
            return f"Invalid room. Available rooms are: {', '.join(self.rooms)}"
        if time not in self.time_slots:
            return f"Invalid time slot. Available slots are: {', '.join(self.time_slots)}"
        
        # Initialize date in schedule if not exists
        if date not in self.schedule:
            self.schedule[date] = []
        
        # Check if slot is already booked
        for class_info in self.schedule[date]:
            if class_info['room'] == room and class_info['time'] == time:
                return f"This slot is already booked for {class_info['class_name']}"
        
        # Schedule the class
        self.schedule[date].append({
            'room': room,
            'time': time,
            'class_name': class_name
        })
        
        return f"Successfully scheduled {class_name} in {room} at {time} on {date}"

    @tool
    def view_schedule(self, date: str) -> str:
        """View all scheduled classes for a given date."""
        if date not in self.schedule or not self.schedule[date]:
            return f"No classes scheduled for {date}"
        
        schedule_str = f"Schedule for {date}:\n"
        sorted_classes = sorted(self.schedule[date], key=lambda x: x['time'])
        
        for class_info in sorted_classes:
            schedule_str += f"- {class_info['time']}: {class_info['class_name']} in {class_info['room']}\n"
        
        return schedule_str

def create_scheduler_agent():
    # Initialize scheduler and tools
    scheduler = ClassScheduler()
    
    tools = [
        Tool(
            name="list_available_rooms",
            func=scheduler.list_available_rooms,
            description="Lists all available rooms for a given date (format: YYYY-MM-DD)"
        ),
        Tool(
            name="list_available_times",
            func=scheduler.list_available_times,
            description="Lists all available time slots for a given date and room"
        ),
        Tool(
            name="schedule_class",
            func=scheduler.schedule_class,
            description="Schedule a class for a specific date, room, and time"
        ),
        Tool(
            name="view_schedule",
            func=scheduler.view_schedule,
            description="View all scheduled classes for a given date"
        )
    ]

    # Create prompt template
    prompt = PromptTemplate.from_template(
        """You are a helpful assistant that helps schedule classes.
        You have access to the following tools:
        
        {tools}
        
        Use these tools to help schedule and manage classes.
        Always use the YYYY-MM-DD format for dates.
        
        Human: {input}
        Assistant: Let's approach this step by step:
        {agent_scratchpad}
        
        Tool Names: {tool_names}"""
    )

    # Initialize LLM
    llm = OpenAI(temperature=0)

    # Create agent
    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    return agent_executor

def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set your OPENAI_API_KEY in the .env file")
        return
        
    agent = create_scheduler_agent()
    
    # Example usage
    print("Class Scheduling Agent initialized!")
    print("You can now ask questions like:")
    print("- What rooms are available on 2024-01-15?")
    print("- Schedule Math class in Room A at 10:00 on 2024-01-15")
    print("- Show me the schedule for 2024-01-15")
    
    while True:
        try:
            user_input = input("\nWhat would you like to do? (or 'quit' to exit): ")
            if user_input.lower() == 'quit':
                break
            
            response = agent.invoke({"input": user_input})
            print("\nResponse:", response["output"])
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
