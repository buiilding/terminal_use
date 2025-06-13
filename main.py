import os
import google.generativeai as genai
from dotenv import load_dotenv
import subprocess

load_dotenv()

def get_file_structure(root_dir="."):
    """Gets the file and folder structure of the project."""
    structure = ""
    for root, dirs, files in os.walk(root_dir):
        # ignore venv directory
        if "venv" in root:
            continue
        level = root.replace(root_dir, '').count(os.sep)
        indent = " " * 4 * (level)
        structure += f"{indent}{os.path.basename(root)}/\n"
        sub_indent = " " * 4 * (level + 1)
        for f in files:
            structure += f"{sub_indent}{f}\n"
    return structure

def main():
    """Main function for the terminal AI."""
    
    # Configure the Gemini API
    try:
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    except KeyError:
        print("Please set the GEMINI_API_KEY environment variable.")
        return
        
    # Create the model
    model = genai.GenerativeModel('gemini-1.5-pro-latest')

    while True:
        # Get user input
        user_input = input(">>> ")

        # If the user wants to exit, break the loop
        if user_input.lower() == "exit":
            break

        # Get the file structure
        file_structure = get_file_structure()

        # Construct the prompt
        prompt = f"""
You are a terminal assistant. The user will provide a request in natural language, and you will provide the corresponding shell command.
The current working directory is {os.getcwd()}.
The file structure of the project is:
{file_structure}

User request: {user_input}
Command:
"""

        # Send the prompt to the model
        response = model.generate_content(prompt)

        # Get the command from the response
        command = response.text.strip()

        # Clean up the command by removing "Command: " prefix, and markdown backticks.
        if command.lower().startswith("command:"):
            command = command.split(":", 1)[1].strip()

        if command.startswith("```") and command.endswith("```"):
            command = command[3:-3].strip()
            if command.startswith("sh"):
                command = command[2:].strip()
            elif command.startswith("bash"):
                command = command[4:].strip()

        if command.startswith("`") and command.endswith("`"):
            command = command[1:-1]

        # Ask the user for confirmation
        print(f"Suggested command: {command}")
        confirmation = input("Run this command? (y/n): ")

        # If the user confirms, run the command
        if confirmation.lower() == "y":
            # Handle 'cd' command
            if command.startswith("cd "):
                try:
                    os.chdir(command.split(" ", 1)[1])
                    print(f"Changed directory to {os.getcwd()}")
                except FileNotFoundError:
                    print(f"Directory not found: {command.split(' ', 1)[1]}")
            else:
                # Run other commands
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                print(result.stdout)
                print(result.stderr)

if __name__ == "__main__":
    main() 