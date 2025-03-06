from datetime import date, time
import dotenv
from typing_extensions import TypedDict, List, Optional
# from langgraph.prebuilt import tool
import os
from pdf2image import convert_from_path
# from paddleocr import PaddleOCR
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage
import json
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

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
    problem: Optional[str]
    doctor: Optional[str]
    appointment_date: Optional[date]
    appointment_time: Optional[time]
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
    name: str=Field(description="name of patient")
    number: int=Field(description="mobil number of patient which has 10 digits")
    gender: str=Field(description="gender of patient")
    problem: str=Field(description="problem name that the patient is facing")
    doctor: str=Field(description="name of the doctor selected according to problem")

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
    name=input("\nPlease enter your name: ")
    number=input("\nPlease enter the mobile number: ")
    gender=input("\nEnter gender: ")
    problem=input("\nWhat problem you have: ")

    system_prompt="You are assistent to help patient to find the right doctor to consult from the list of doctor given and the response must be in JSON format with 'name', 'number','gender','problem' and 'doctor' as a keys"
    human_Message=f"the {gender}(gender) person whose name is {name} has a {problem} and the person's mobile number is{number}. Find the doctor name from the list {doctor_list} the patient need to consult"
    messages=[SystemMessage(content=system_prompt),HumanMessage(content=human_Message)]

    result=patient_structured_llm.invoke(messages)
    print("\nDoctor: ", result.doctor)
    print("\nProblem: ", result.problem)

    return {"name":result.name, "number": result.number,"gender" :result.gender,"problem":result.problem,"doctor":result.doctor}

def appointment_booking(state: State):
    date=input("\nPlease enter the appointment date: ")
    time=input("\nPlease enter the appointment time: ")

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

def summary(state: State):
    print("\n--------------------Summary-----------------\n")
    print("state: ", state)
    print("\n-----------------------------------------")
    return state

#add node
graph.add_node("patient_detail", patient_detail)
graph.add_node("appointment_booking", appointment_booking)
graph.add_node("summary", summary)

#add edge
graph.set_entry_point("patient_detail")
graph.add_edge("patient_detail","appointment_booking")
graph.add_edge("appointment_booking","summary")
graph.add_edge("summary",END)
build=graph.compile()

#Draw Graph

build.invoke({'name':None})
