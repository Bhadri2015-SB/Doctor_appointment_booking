from datetime import date, time
import dotenv
from typing_extensions import TypedDict, List, Optional
# from langgraph.prebuilt import tool
import os
# from pdf2image import convert_from_path
# from paddleocr import PaddleOCR
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage
import json
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from datetime import datetime

dotenv.load_dotenv()
GROQ_API = os.getenv("GROQ_API")

llm = ChatGroq(
    api_key=GROQ_API,
    temperature=0.2,
    model_name="llama3-70b-8192",
)

class State(TypedDict):
    """State schema for LangGraph workflow."""
    name: Optional[str]
    number: Optional[int]
    gender: Optional[str]
    date_of_birth:Optional[date]
    problem: Optional[str]
    forWhom:Optional[str]
    appointment_time: Optional[time]
    insurance_info:Optional[str]
    insurance_provider:Optional[str]
    insurance_id:Optional[str]
    other_medical_issue:Optional[str]
    medications:Optional[str]
    past_surgeries:Optional[str]
    special_need:Optional[str]
    emergency_contact_name:Optional[str]
    emergency_relationship:Optional[str]
    emergency_relation_phone:Optional[str]
    doctor: Optional[str]
    appointment_date: Optional[date]
    problem_details: Optional[str]=None

#create graph
graph = StateGraph(State)

doctor_list={'arun':'ortho','guru':'generic','jay':'cardio','mugil':'neuro'}
# bookings={'arun':{'date':'2022-10-10','time':'10:00','status':'available','alter_date':'2022-10-11','alter_time':'11:00'},
#           'guru':{'date':'2022-10-11','time':'11:00','status':'available','alter_date':'2022-10-12','alter_time':'12:00'},
#             'jay':{'date':'2022-10-12','time':'12:00','status':'available','alter_date':'2022-10-13','alter_time':'13:00'},
#             'mugil':{'date':'2022-10-13','time':'13:00','status':'available','alter_date':'2022-10-14','alter_time':'14:00'}}
appointment={'arun':None,'guru':None,'jay':None,'mugil':None}

class GetPatientDetail(BaseModel):
    """Extract problem name and doctor for the patient to concelt"""
    name: str = Field(description="name of patient")
    age: int = Field(description="age of patient")
    number: int = Field(description="mobile number of patient (10 digits)")
    gender: str = Field(description="gender of patient")
    problem: str = Field(description="problem name that the patient is facing")
    other_medical_issue: str = Field(description="other medical issues, if any")
    medications: str = Field(description="current medications, if any")
    past_surgeries: str = Field(description="past surgeries or hospitalizations (yes/no)")
    doctor: str = Field(description="name of the doctor selected according to problem")
    #special_need: str= Field(description="Any special needs or accommodations required by the patient")

class AppointmentBooking(BaseModel):
    """Details of Appointment appointment_date, appointment_time, available_status. if status is not available use alter_date, alter_time else keep it same date as appointment_date and time as appointment_time"""
    # doctor: str=Field(description="name of the doctor selected according to problem")
    appointment_date: date=Field(description="Appointment date of doctor. convert the string type to date and formate the given date into YYYY-MM-DD")
    appointment_time: time=Field(description="time of appointment on that particular date. convert the string type to date and format the given time to HH:MM")
    available_status: str=Field(description="status of the doctor availability")
    alter_date: date=Field(description="available alter date of doctor")
    alter_time: time=Field(description="available alter time of doctor")

patient_structured_llm = llm.with_structured_output(GetPatientDetail, method='json_mode')
appointment_structure = llm.with_structured_output(AppointmentBooking, method='json_mode')

#pstient details node
def patient_detail(state: State):
    print("\nHi! This is to book an appointment with doctor\n")
    name=input("Great to hear! May i know your name: ")
    while True:
        age=input(f"Hi {name}, could you provide your age? ")
        if age.isdigit():
            age=int(age)
            break
        print("Invalid input. Please enter a valid age.")
    while True:
        number=input(f"{name} please enter the mobile number: ")
        if number.isdigit() and len(number)==10:
            break
        else:
            print("Invalid input.Please enter valid 10-digit mobile number.")

    gender=input(f"Lets enter our gender {name}: ")
    print("\nIs this appointment for you or someone else?")
    print("1. It's for me.")
    print("2. It's for my mother.")
    print("3. It's for my father.")
    print("4. It's for my child.")
    print("5. It's for someone else.")
    choice=input("Please select an option (1-5): ")
    if choice=="1":
        forWhom="It's for me."
    elif choice=="2":
        forWhom="It's for my mother."
    elif choice=="3":
        forWhom="It's for my father."
    elif choice=="4":
        forWhom="It's for my child."
    elif choice=="5":
        forWhom="It's for someone else."
    else:
        forWhom="Invalid choice."
    
    problem=input("Could you tell me the reason for your visit?")
    other_issues=input("Do you have any other problems if yes please mention. ")
    medications=input("Alright! Are you currently taking any medications?")
    while True:
        past_surgeries=input("Thanks for your information.Have you had any past surgeries or hospitalized? (yes/no) ").strip().lower()
        if past_surgeries in ["yes", "no"]:
            if past_surgeries == "yes":
                print("Please bring your reports when you come to the hospital.")
            break
        print("Invalid input. Please enter 'yes' or 'no'.")


    system_prompt = (
        "You are an assistant to help patients find the right doctor to consult from the list of doctors given. "
        "The response must be in JSON format with 'name', 'age', 'number', 'gender', 'problem', 'other_medical_issue', "
        "'medications', 'past_surgeries', and 'doctor' as keys. Use JSON format for the response."
    )
    human_message = (
        f"The {gender} person whose name is {name} has a problem: {problem}. "
        f"Their age is {age}, mobile number is {number}, other issues are '{other_issues}', "
        f"current medications are '{medications}', and past surgeries are '{past_surgeries}'. "
        f"Find the doctor name from the list {doctor_list} that the patient needs to consult."
    )
    messages=[SystemMessage(content=system_prompt),HumanMessage(content=human_message)]

    result=patient_structured_llm.invoke(messages)
    print("\nDoctor: ", result.doctor)
    print("\nProblem: ", result.problem)

    #return {"name":result.name,"age":age, "number": result.number,"gender" :result.gender,"forWhom":forWhom,"problem":result.problem,"other_issues":other_issues,"medications":medications,"past_surgeries":past_surgeries,"doctor":result.doctor}

    return {
        "name": result.name,
        "age": result.age,
        "number": result.number,
        "gender": result.gender,
        "forWhom": forWhom,  # Note: forWhom isn’t in GetPatientDetail, adjust State if needed
        "problem": result.problem,
        "other_issues": result.other_medical_issue,  # Match prompt key
        "medications": result.medications,
        "past_surgeries": result.past_surgeries,
        "doctor": result.doctor
    }

def appointment_booking(state: State):
    while True:
        today=datetime.today().date()   
        date=input("\nPlease enter the appointment date (YYYY-MM-DD): ").strip()
        try:
            date=datetime.strptime(date,"%Y-%m-%d").date()
            if date<today:
                print("Invalid date. The appointment date cannot be in the past.")
            else:
                break
        except ValueError:
            print("Invalid date format. Please use the format YYYY-MM-DD.")

    system_prompt="You are assistent to help patient to book an appointment with the doctor which is 30 minutes long and the response must be in JSON format with 'appointment_date', 'appointment_time', 'available_status', 'alter_date' and 'alter_time' as a keys"
    human_Message=f"the appointment date is {date} and the appointment time is {time} which are in string type convert to proper date and time formate. check the availability of the doctor from list {appointment} and book the appointment. If the doctor is not available on the given date and time, provide the available date and time which is closer in 'alter_date' and 'alter_time' keys else keep it same as 'appointment_date' and 'appoinntment_time'. if appointment is available the value of 'available_status' must be 'available' else 'not available'"
    messages=[SystemMessage(content=system_prompt),HumanMessage(content=human_Message)]

    result=appointment_structure.invoke(messages)

    if 'available_status' in result != 'available':
        print("\nDoctor is not available on the given date and time")
        print("\nAvailable Date: ", result.alter_date)
        print("\nAvailable Time: ", result.alter_time)
        ans=input("\nDo you want to book the appointment on the available date and time? (yes/no): ")
        if ans=='yes':
            print("\nAppointment is fixed on below date and time")
            print("\nAppointment Date: ", result.alter_date)
            print("\nAppointment Time: ", result.alter_time)
            appointment[state["doctor"]]={'date':result.alter_date,'time':result.alter_time,'status':'booked'}
            return {"appointment_date":result.alter_date, "appointment_time": result.alter_time}
        # else:
        #     print("\nDoctor is not available on the given date and time")
        #     appointment[result.doctor]+={'date':result.available_date,'time':result.available_time,'status':'available'}
    else:
        print("\nDoctor is available on the given date and time")
        appointment[state["doctor"]]={'date':date,'time':time,'status':'booked'}

    print("\nAppointment Date: ", result.appointment_date)
    print("\nAppointment Time: ", result.appointment_time)

    return {"appointment_date":result.appointment_date, "appointment_time": result.appointment_time}

def insurance_details(state:State):
    insurance_info=input("\nDo you have any insurance yes/no:").strip().lower()
    if insurance_info.lower()!="yes":
        return {
            "insurance_info":"No"
        }
    insurance_provider=input("\nPlease enter your insurance provider name:")
    insurance_id=input("\nPlease enter your insurance ID:")

    return {"insurance_info":insurance_info,"insurance_provider":insurance_provider,"insurance_id":insurance_id}

def emergency_details(state:State):
    emergency_contact_name=input(f"Could you provide your emergency contact name? ")
    emergency_relationship=input(f"Thank you.What is {emergency_contact_name}'s relationship to you?")
    #emergency_relation_phone=input(f"Could you provide {emergency_contact_name}'s phone number? ")

    while True:
        emergency_relation_phone=input(f"{emergency_contact_name}'s the mobile number: ")
        if emergency_relation_phone.isdigit() and len(emergency_relation_phone)==10:
            break
        else:
            print("Invalid input.Please enter valid 10-digit mobile number.")

    return {"emergency_contact_name":emergency_contact_name,"emergency_relationship":emergency_relationship,"emergency_relation_phone":emergency_relation_phone}

def summary(state: State):
    print("\n--------------------Summary-----------------\n")
    print("state: ", state)
    print("\n-----------------------------------------")
    return state

#add node
graph.add_node("patient_detail", patient_detail)
graph.add_node("appointment_booking", appointment_booking)
graph.add_node("insurance_details",insurance_details)
graph.add_node("emergency_details",emergency_details)
graph.add_node("summary", summary)

#add edge
graph.set_entry_point("patient_detail")
graph.add_edge("patient_detail","appointment_booking")
graph.add_edge("appointment_booking","insurance_details")
graph.add_edge("insurance_details","emergency_details")
graph.add_edge("emergency_details","summary")
graph.add_edge("summary",END)
build=graph.compile()

#Draw Graph

build.invoke({'name':None})