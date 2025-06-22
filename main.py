import os
import google.generativeai as genai
from dotenv import load_dotenv
import subprocess
from token_counter import count_tokens

load_dotenv()

def get_file_structure(root_dir=".", exclude_patterns=None):
    """
    Gets the file and folder structure of the project, excluding specified patterns.
    - Patterns ending in '/' exclude directories by that exact name (e.g., 'node_modules/').
    - Patterns starting with '.' exclude files by extension (e.g., '.pyc').
    - Other patterns exclude any file or directory containing that string (e.g., 'temp').
    """
    if exclude_patterns is None:
        exclude_patterns = []

    # Process user-provided patterns
    exclude_dirs_exact = [p.strip('/') for p in exclude_patterns if p.endswith('/')]
    exclude_extensions = [p for p in exclude_patterns if p.startswith('.') and not p.endswith('/')]
    exclude_substrings = [p for p in exclude_patterns if not p.endswith('/') and not p.startswith('.')]

    # Add common directories to exclude by default
    default_exclude_dirs = ['.git', 'venv', '__pycache__', 'node_modules']
    exclude_dirs_exact.extend([d for d in default_exclude_dirs if d not in exclude_dirs_exact])

    structure = ""
    for root, dirs, files in os.walk(root_dir, topdown=True):
        # Check if the current directory itself should be skipped
        root_basename = os.path.basename(root)
        if root_basename in exclude_dirs_exact or any(sub in root_basename for sub in exclude_substrings):
            dirs[:] = []  # Don't traverse any further
            continue

        # Filter subdirectories in place to prevent os.walk from traversing them
        dirs[:] = [
            d for d in dirs 
            if d not in exclude_dirs_exact and not any(sub in d for sub in exclude_substrings)
        ]

        # Filter files based on extension and substring
        filtered_files = [
            f for f in files 
            if not any(f.endswith(ext) for ext in exclude_extensions) and 
               not any(sub in f for sub in exclude_substrings)
        ]

        level = root.replace(root_dir, '').count(os.sep)
        indent = " " * 4 * (level)
        structure += f"{indent}{os.path.basename(root)}/\n"
        sub_indent = " " * 4 * (level + 1)
        for f in filtered_files:
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

    # Get the directory from the user
    knowledge_base_dir = input("Enter the directory path for the AI to analyze (or press Enter for current directory): ").strip()
    if not knowledge_base_dir:
        knowledge_base_dir = "."

    if not os.path.isdir(knowledge_base_dir):
        print(f"Error: Directory '{knowledge_base_dir}' not found.")
        return

    # Get directories to exclude
    exclude_input = input("Enter exclusion patterns (e.g. 'dist/', '.tmp', 'backup'), separated by commas: ").strip()
    exclude_patterns = [p.strip() for p in exclude_input.split(',')] if exclude_input else []

    print(f"Generating file tree for '{knowledge_base_dir}'. This might take a moment...")
    file_structure = get_file_structure(knowledge_base_dir, exclude_patterns)

    # Count the tokens in the file structure
    token_count = count_tokens(model, file_structure)
    print(file_structure)
    print(f"The file structure contains {token_count} tokens.")

    # Initial system prompt including the file structure
    initial_prompt = f"""
You are a powerful terminal assistant. I am providing you with the file structure of a project located at '{knowledge_base_dir}'.
Your task is to use this information to help me with my requests.

You can have a conversation with me, or you can execute shell commands.
When you need to execute a command, respond with the command inside <execute> tags. For example: <execute>ls -l</execute>
I will have to approve every command before it is run. After a command runs, I will give you its output.

When you believe my request is satisfied, you can end the interaction by responding with "DONE".

The current working directory is {os.getcwd()}.

Here is the file structure:
---
{file_structure}
---

Please review the file structure and acknowledge that you have understood it and are ready to help.
"""

    # Start the chat and send the initial prompt
    chat = model.start_chat(history=[])
    print("\nSending context to the AI...")
    initial_response = chat.send_message(initial_prompt)

    # Print AI's acknowledgement
    print(f"\nAssistant: {initial_response.text.strip()}")


    while True: # Main application loop
        user_input = input(">>> ")
        if user_input.lower() == "exit":
            break
        
        # This is a new request from the user.
        # Send it to the chat.
        response = chat.send_message(user_input)

        # Inner loop for AI to work on the request
        while True:
            ai_response = response.text.strip()

            # The AI might just talk, or issue a command, or both.
            # Let's print the entire response first so the user sees it.
            print(f"Assistant: {ai_response}")

            if "<execute>" in ai_response and "</execute>" in ai_response:
                # Command found, extract and execute
                start_tag = "<execute>"
                end_tag = "</execute>"
                start_index = ai_response.find(start_tag) + len(start_tag)
                end_index = ai_response.find(end_tag)
                command = ai_response[start_index:end_index].strip()
                
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


                # Ask for confirmation
                confirmation = input(f"Run this command? `{command}` (y/n): ")
                if confirmation.lower() == 'y':
                    output = ""
                    # Handle 'cd' command
                    if command.startswith("cd "):
                        try:
                            os.chdir(command.split(" ", 1)[1])
                            output = f"Changed directory to {os.getcwd()}"
                            print(output)
                        except FileNotFoundError:
                            output = f"Directory not found: {command.split(' ', 1)[1]}"
                            print(output)
                    else:
                        # Run other commands
                        result = subprocess.run(command, shell=True, capture_output=True, text=True)
                        if result.stdout:
                            print(result.stdout)
                            output += f"STDOUT:\n{result.stdout}\n"
                        if result.stderr:
                            print(result.stderr)
                            output += f"STDERR:\n{result.stderr}\n"

                    # Send output back to AI for next step
                    response = chat.send_message(f"COMMAND OUTPUT:\n{output}")
                    # Continue inner loop to see what AI does next
                    continue 
                else:
                    # User cancelled. Tell the AI.
                    response = chat.send_message("User cancelled execution.")
                    continue # See what AI does next
            
            elif ai_response.upper() == "DONE":
                # AI thinks it's done with the current task.
                # Break inner loop and wait for new user input.
                break
            
            else:
                # AI is just talking. Break inner loop and wait for new user input.
                break


if __name__ == "__main__":
    main() 