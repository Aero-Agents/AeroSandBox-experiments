#!/usr/bin/env python3
"""
create_experiment.py

This script uses LangGraph and gemini-2.5-flash-lite to generate optimization variable code
based on an experiment description, then inserts it into a copy of experiment_framework.py
and runs the modified experiment.
"""

import os
import re
import subprocess
from typing_extensions import Annotated, TypedDict

import google.generativeai as genai
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from pydantic import BaseModel


class OptimizationCode(BaseModel):
    """Schema for the generated optimization variable code"""
    code: str


class ExperimentState(TypedDict):
    """State for the experiment generation workflow"""
    experiment_description: str
    prompt_template: str
    generated_code: str
    constraints_prompt_template: str
    generated_constraints_code: str
    modified_framework_path: str
    messages: Annotated[list, add_messages]


def add_system_message(state: ExperimentState, content: str) -> ExperimentState:
    """Add a system message to the state"""
    state['messages'].append({'role': 'system', 'content': content})
    return state


def load_prompt_template(state: ExperimentState) -> ExperimentState:
    """Load the prompt template from choose_optimisation_variables.txt"""
    try:
        with open('./prompts/choose_optimisation_variables.txt', 'r') as f:
            prompt_template = f.read()
        state['prompt_template'] = prompt_template
        return add_system_message(state, 'Loaded prompt template successfully')
    except FileNotFoundError:
        return add_system_message(state, 'Error: Could not find choose_optimisation_variables.txt')

def load_constraints_prompt_template(state: ExperimentState) -> ExperimentState:
    """Load the constraints prompt template from setup_constraints_and_objective.txt"""
    try:
        with open('./prompts/setup_constraints_and_objective.txt', 'r') as f:
            constraints_prompt_template = f.read()
        state['constraints_prompt_template'] = constraints_prompt_template
        return add_system_message(state, 'Loaded constraints prompt template successfully')
    except FileNotFoundError:
        return add_system_message(state, 'Error: Could not find setup_constraints_and_objective.txt')

def generate_optimization_code(state: ExperimentState) -> ExperimentState:
    """Use Gemini 2.5 Flash to generate optimization variable code with structured output"""
    if not state.get('prompt_template'):
        return add_system_message(state, 'Error: No prompt template loaded')
    
    try:
        model = genai.GenerativeModel(
            'gemini-2.5-flash-lite',
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": OptimizationCode
            }
        )
        
        full_prompt = f"""
{state['prompt_template']}

EXPERIMENT DESCRIPTION: {state['experiment_description']}

"""
        
        response = model.generate_content(full_prompt)
        result = OptimizationCode.model_validate_json(response.text)
        
        state['generated_code'] = result.code.strip()
        state['messages'].append({
            'role': 'assistant',
            'content': f'Generated optimization code:\n{state["generated_code"]}'
        })
        return state
    except Exception as e:
        state['generated_code'] = ''
        return add_system_message(state, f'Error generating code with Gemini: {str(e)}')

def generate_constraints_code(state: ExperimentState) -> ExperimentState:
    """Use Gemini 2.5 Flash to generate constraints and objective function code with structured output"""
    if not state.get('constraints_prompt_template'):
        return add_system_message(state, 'Error: No constraints prompt template loaded')
    
    try:
        model = genai.GenerativeModel(
            'gemini-2.5-flash-lite',
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": OptimizationCode
            }
        )
        
        full_prompt = f"""
{state['constraints_prompt_template']}

EXPERIMENT DESCRIPTION: {state['experiment_description']}

"""
        
        response = model.generate_content(full_prompt)
        result = OptimizationCode.model_validate_json(response.text)
        
        state['generated_constraints_code'] = result.code.strip()
        state['messages'].append({
            'role': 'assistant',
            'content': f'Generated constraints code:\n{state["generated_constraints_code"]}'
        })
        return state
    except Exception as e:
        state['generated_constraints_code'] = ''
        return add_system_message(state, f'Error generating constraints code with Gemini: {str(e)}')

def create_modified_framework(state: ExperimentState) -> ExperimentState:
    """Create a modified copy of experiment_framework.py with generated code inserted"""
    if not state.get('generated_code'):
        return add_system_message(state, 'Error: No generated code to insert')
    
    if not state.get('generated_constraints_code'):
        return add_system_message(state, 'Error: No generated constraints code to insert')
    
    try:
        with open('experiment_framework.py', 'r') as f:
            framework_content = f.read()

        # Insert optimization variables code at first insertion point
        pattern1 = r'(# --- FIRST GEMINI INSERTION POINT ---\n)(.*?)(# --- END GEMINI INSERTION POINT ---)'
        replacement1 = f'\\1\n{state["generated_code"]}\n\n\\3'
        modified_content = re.sub(pattern1, replacement1, framework_content, flags=re.DOTALL)
        
        # Insert constraints and objective code at second insertion point
        pattern2 = r'(# --- SECONDGEMINI INSERTION POINT ---\n)(.*?)(# --- END GEMINI INSERTION POINT ---)'
        replacement2 = f'\\1\n{state["generated_constraints_code"]}\n\n\\3'
        modified_content = re.sub(pattern2, replacement2, modified_content, flags=re.DOTALL)
        
        modified_filename = 'modified_experiment_framework.py'
        with open(modified_filename, 'w') as f:
            f.write(modified_content)
        
        state['modified_framework_path'] = modified_filename
        return add_system_message(state, f'Created modified framework: {modified_filename}')
    except Exception as e:
        return add_system_message(state, f'Error creating modified framework: {str(e)}')

def run_experiment(state: ExperimentState) -> ExperimentState:
    """Run the modified experiment framework"""
    if not state.get('modified_framework_path'):
        return add_system_message(state, 'Error: No modified framework to run')
    
    try:
        result = subprocess.run(
            ['python', state['modified_framework_path']],
            capture_output=True,
            text=True,
            cwd='.'
        )
        
        if result.returncode == 0:
            return add_system_message(state, f'Experiment completed successfully!\nOutput:\n{result.stdout}')
        else:
            return add_system_message(state, f'Experiment failed with error:\n{result.stderr}')
    except Exception as e:
        return add_system_message(state, f'Error running experiment: {str(e)}')


def create_experiment_workflow() -> StateGraph:
    """Create the LangGraph workflow for experiment generation"""
    workflow = StateGraph(ExperimentState)
    
    workflow.add_node("load_prompt", load_prompt_template)
    workflow.add_node("load_constraints_prompt", load_constraints_prompt_template)
    workflow.add_node("generate_code", generate_optimization_code)
    workflow.add_node("generate_constraints", generate_constraints_code)
    workflow.add_node("create_framework", create_modified_framework)
    workflow.add_node("run_experiment", run_experiment)
    
    workflow.set_entry_point("load_prompt")
    workflow.add_edge("load_prompt", "generate_code")
    workflow.add_edge("generate_code", "load_constraints_prompt")
    workflow.add_edge("load_constraints_prompt", "generate_constraints")
    workflow.add_edge("generate_constraints", "create_framework")
    workflow.add_edge("create_framework", "run_experiment")
    workflow.add_edge("run_experiment", END)
    
    return workflow.compile()


def print_results(final_state: ExperimentState) -> None:
    """Print the workflow results"""
    print("\n=== Workflow Results ===")
    for message in final_state['messages']:
        if isinstance(message, dict):
            print(f"[{message['role'].upper()}] {message['content']}")
        else:
            print(f"[SYSTEM] {str(message)}")
        print("-" * 50)
    
    if final_state.get('modified_framework_path'):
        print(f"\n✅ Experiment completed! Check the results above.")
        print(f"📁 Modified framework saved as: {final_state['modified_framework_path']}")
    else:
        print("\n❌ Experiment generation failed. Check the error messages above.")


def main() -> None:
    """Main function to run the experiment creation workflow"""
    # Configure Gemini API
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Error: Please set your GEMINI_API_KEY environment variable")
        print("You can get an API key from: https://ai.google.dev/")
        return
    
    genai.configure(api_key=api_key)
    
    # Get experiment description from user
    print("=== AeroSandBox Experiment Generator ===")
    print("This tool will generate optimization variables based on your experiment description.")
    print("\nExample: 'Optimise the chord lengths and angle of attack (within 0 and 30 degrees) to minimise the drag coefficient, with a required lift coefficient of 1, a fixed wing area of 0.25 and monotonically decreasing chord lengths from root to tip.'")
    print()
    
    experiment_description = input("Enter your experiment description: ").strip()
    if not experiment_description:
        print("Error: Please provide an experiment description")
        return
    
    # Initialize state and run workflow
    initial_state = ExperimentState(
        experiment_description=experiment_description,
        prompt_template="",
        generated_code="",
        constraints_prompt_template="",
        generated_constraints_code="",
        modified_framework_path="",
        messages=[]
    )
    
    workflow = create_experiment_workflow()
    print("\n=== Running Experiment Generation Workflow ===")
    final_state = workflow.invoke(initial_state)
    
    print_results(final_state)


if __name__ == "__main__":
    main()
