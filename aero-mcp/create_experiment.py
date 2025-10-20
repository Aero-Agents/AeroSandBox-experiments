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
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown

console = Console()


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


def add_system_message(content: str) -> dict:
    """Create a system message to add to state"""
    return {'messages': [{'role': 'system', 'content': content}]}


def load_prompt_template(state: ExperimentState) -> dict:
    """Load the prompt template from choose_optimisation_variables.txt"""
    try:
        with open('./prompts/choose_optimisation_variables.txt', 'r') as f:
            prompt_template = f.read()
        return {
            'prompt_template': prompt_template,
            **add_system_message('Loaded prompt template successfully')
        }
    except FileNotFoundError:
        return add_system_message('Error: Could not find choose_optimisation_variables.txt')

def load_constraints_prompt_template(state: ExperimentState) -> dict:
    """Load the constraints prompt template from setup_constraints_and_objective.txt"""
    try:
        with open('./prompts/setup_constraints_and_objective.txt', 'r') as f:
            constraints_prompt_template = f.read()
        return {
            'constraints_prompt_template': constraints_prompt_template,
            **add_system_message('Loaded constraints prompt template successfully')
        }
    except FileNotFoundError:
        return add_system_message('Error: Could not find setup_constraints_and_objective.txt')

def generate_optimization_code(state: ExperimentState) -> dict:
    """Use Gemini 2.5 Flash-Lite to generate optimization variable code with structured output"""
    if not state.get('prompt_template'):
        return add_system_message('Error: No prompt template loaded')
    
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
        
        generated_code = result.code.strip()
        return {
            'generated_code': generated_code,
            'messages': [{
                'role': 'assistant',
                'content': f'Generated optimization code:\n{generated_code}'
            }]
        }
    except Exception as e:
        return {
            'generated_code': '',
            **add_system_message(f'Error generating code with Gemini: {str(e)}')
        }

def generate_constraints_code(state: ExperimentState) -> dict:
    """Use Gemini 2.5 Flash to generate constraints and objective function code with structured output"""
    if not state.get('constraints_prompt_template'):
        return add_system_message('Error: No constraints prompt template loaded')
    
    try:
        model = genai.GenerativeModel(
            'gemini-2.5-flash',
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
        
        generated_constraints_code = result.code.strip()
        return {
            'generated_constraints_code': generated_constraints_code,
            'messages': [{
                'role': 'assistant',
                'content': f'Generated constraints code:\n{generated_constraints_code}'
            }]
        }
    except Exception as e:
        return {
            'generated_constraints_code': '',
            **add_system_message(f'Error generating constraints code with Gemini: {str(e)}')
        }

def create_modified_framework(state: ExperimentState) -> dict:
    """Create a modified copy of experiment_framework.py with generated code inserted"""
    if not state.get('generated_code'):
        return add_system_message('Error: No generated code to insert')
    
    if not state.get('generated_constraints_code'):
        return add_system_message('Error: No generated constraints code to insert')
    
    try:
        with open('experiment_framework.py', 'r') as f:
            framework_content = f.read()

        # Insert optimization variables code at first insertion point
        pattern1 = r'(# --- FIRST GEMINI INSERTION POINT ---\n)(.*?)(# --- END GEMINI INSERTION POINT ---)'
        replacement1 = f'\\1\n{state["generated_code"]}\n\n\\3'
        modified_content = re.sub(pattern1, replacement1, framework_content, flags=re.DOTALL)
        
        # Insert constraints and objective code at second insertion point
        pattern2 = r'(# --- SECOND GEMINI INSERTION POINT ---\n)(.*?)(# --- END GEMINI INSERTION POINT ---)'
        replacement2 = f'\\1\n{state["generated_constraints_code"]}\n\n\\3'
        modified_content = re.sub(pattern2, replacement2, modified_content, flags=re.DOTALL)
        
        modified_filename = 'modified_experiment_framework.py'
        with open(modified_filename, 'w') as f:
            f.write(modified_content)
        
        return {
            'modified_framework_path': modified_filename,
            **add_system_message(f'Created modified framework: {modified_filename}')
        }
    except Exception as e:
        return add_system_message(f'Error creating modified framework: {str(e)}')

def run_experiment(state: ExperimentState) -> dict:
    """Run the modified experiment framework"""
    if not state.get('modified_framework_path'):
        return add_system_message('Error: No modified framework to run')
    
    try:
        result = subprocess.run(
            ['python', state['modified_framework_path']],
            capture_output=True,
            text=True,
            cwd='.'
        )
        
        if result.returncode == 0:
            return add_system_message(f'Experiment completed successfully!\nOutput:\n{result.stdout}')
        else:
            return add_system_message(f'Experiment failed with error:\n{result.stderr}')
    except Exception as e:
        return add_system_message(f'Error running experiment: {str(e)}')


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
    console.print("\n")
    console.print(Panel.fit("📊 Workflow Results", style="bold cyan"))
    
    # Track if there was an error
    has_error = False
    
    for message in final_state['messages']:
        if isinstance(message, dict):
            role = message['role'].upper()
            content = message['content']
            
            # Check if this is an error message
            if 'error' in content.lower() or 'failed' in content.lower():
                has_error = True
                console.print(f"\n[bold red][{role}][/bold red]")
                console.print(f"[red]{content}[/red]")
            elif role == 'ASSISTANT':
                console.print(f"\n[bold green][{role}][/bold green]")
                # Check if it's code, format with syntax highlighting
                if 'Generated' in content and 'code:' in content:
                    parts = content.split('code:', 1)
                    console.print(parts[0] + 'code:')
                    if len(parts) > 1:
                        code = parts[1].strip()
                        syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
                        console.print(syntax)
                else:
                    console.print(f"[green]{content}[/green]")
            else:
                console.print(f"\n[bold blue][{role}][/bold blue]")
                console.print(f"[blue]{content}[/blue]")
        else:
            console.print(f"\n[bold yellow][SYSTEM][/bold yellow]")
            console.print(f"[yellow]{str(message)}[/yellow]")
        
        console.print("[dim]" + "─" * 50 + "[/dim]")
    
    console.print("\n")
    
    # Only print success if there was no error AND the framework was created
    if final_state.get('modified_framework_path') and not has_error:
        console.print(Panel.fit(
            f"✅ [bold green]Experiment completed successfully![/bold green]\n"
            f"📁 Modified framework saved as: [cyan]{final_state['modified_framework_path']}[/cyan]",
            style="green"
        ))
    else:
        console.print(Panel.fit(
            "❌ [bold red]Experiment generation failed.[/bold red]\n"
            "Check the error messages above.",
            style="red"
        ))



def main() -> None:
    """Main function to run the experiment creation workflow"""
    # Configure Gemini API
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        console.print("[bold red]Error:[/bold red] Please set your GEMINI_API_KEY environment variable")
        console.print("You can get an API key from: [cyan]https://ai.google.dev/[/cyan]")
        return
    
    genai.configure(api_key=api_key)
    
    # Get experiment description from user
    console.print("\n")
    console.print(Panel.fit("🚀 AeroSandBox Experiment Generator", style="bold magenta"))
    console.print("\n[bold]This tool will generate optimization variables based on your experiment description.[/bold]\n")
    console.print("[dim]Example:[/dim] [italic]'Optimise the chord lengths and angle of attack (within 0 and 30 degrees) to minimise the drag coefficient, with a required lift coefficient of 1, a fixed wing area of 0.25 and monotonically decreasing chord lengths from root to tip.'[/italic]\n")
    
    experiment_description = input("Enter your experiment description: ").strip()
    if not experiment_description:
        console.print("[bold red]Error:[/bold red] Please provide an experiment description")
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
    console.print("\n")
    console.print(Panel.fit("⚙️  Running Experiment Generation Workflow", style="bold yellow"))
    final_state = workflow.invoke(initial_state)
    
    print_results(final_state)


if __name__ == "__main__":
    main()
