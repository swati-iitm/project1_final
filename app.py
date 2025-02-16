# /// script
# requires-python = ">=3.8"  # Updated to a valid version
# dependencies = [
#    "fastapi",
#    "uvicorn",
#    "requests",
#    "httpx"
# ]
# ///

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
import requests
import os 
import json
import subprocess
from subprocess import run
import urllib.request
import httpx
from typing import Dict, Any
import base64
import traceback



app = FastAPI()

response_format = {
    "type": "json_schema",
    "json_schema": {
        "name": "task_runner",
        "schema": {
            "type": "object",
            "properties": {
                "python_code": {
                    "type": "string",
                    "description": "Python code to perform the task"
                },
                "python_dependencies": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "module": {
                                "type": "string",
                                "description": "Name of the python module"
                            }
                        },
                        "required": ["module"],
                        "additionalProperties": False
                    }
                }
            },
            "required": ["python_code", "python_dependencies"],
            "additionalProperties": False
        }
    }
}


response_format_script = {
    "type": "json_schema",
    "json_schema": {
        "name": "script_runner",
        "schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The url provided to run the python script"
                },
                "email": {
                    "type": "string",
                    "description": "The email id provided. It should have an @ symbol. Example abc@abc.com. If it is not present you can return user@example.com"
                }
            },
            "required": ["url", "email"],
            "additionalProperties": False
        }
    }
}

@app.get ("/read")
# def read_file (path: str):
#     try:
#         with open(path,"r") as f:
#             content = f.read()
#             return Response(content=content, status_code=200, media_type="text/plain")
#     except Exception as e :
#         raise HTTPException(status_code=404, detail="file doesnt exist")
# from fastapi import FastAPI, HTTPException, Response

# app = FastAPI()

# @app.get("/read")
def read_file(path: str):
    try:
        # Try to read the file
        with open(path, "r") as f:
            content = f.read()
        # Return HTTP 200 OK if successful
        return Response(content=content, status_code=200, media_type="text/plain")
    except FileNotFoundError:
        # Return HTTP 400 Bad Request if the file doesn't exist
        return Response(content="Error: File not found.", status_code=400, media_type="text/plain")
    except Exception as e:
        # Log the error for debugging
        error_details = traceback.format_exc()
        # Return HTTP 500 Internal Server Error for unexpected errors
        return Response(content=f"Internal Server Error:\n{error_details}", status_code=500, media_type="text/plain")

        
primary_prompt = """
You are a programming assistant that writes Python code or bash code.
Assume uv and python is preinstalled.
Assume that the code you generate will be executed inside a docker container.
Inorder to perform any task if some python package is required to install, provide name of those modules. Put it as an inline metadata script used for uv. 
For eg. if fastapi, uvicorn are required then in the beginning of the code append:
# /// script
# requires-python = ">=3.8"  # Updated to a valid version
# dependencies = [
#    "fastapi",
#    "uvicorn"
# ]
# ///
If you need to read from a file location or write to a file location, consider relative paths. ".
For extracting information from a file such as sender’s email address, sender's name, receiver's email, receiver's name, phone number etc make use of the Faker package istead of re package.
The sender of an email is usually denoted by "From".
If it is a task to extract information from dates. For eg if te task is to count number of Wednesdays we can use code - sum(1 for date in dates if parse(date).weekday() == 2)
    if result.strip() != str(expected):
        return mismatch("/data/dates-wednesdays.txt", expected, result)
    return True
If we need to change format to prettier, use the exact version of prettier specified in the task. For eg subprocess.run(
        ["npx", "prettier@3.4.2", "--stdin-filepath", file],
        input=original,
        capture_output=True,
        text=True,
        check=True,
        # Ensure npx is picked up from the PATH on Windows
        shell=True,
    ).stdout
For sorting data from a json file we can use similar code. For eg. if the task is to sort by last_name and first_name, we can use this code - contacts.sort(key=lambda c: (c["last_name"], c["first_name"]))
"""
script_prompt = """
You are an agent that identifies the url provided and the email provided to run a script.This URL is a direct link to a Python script.
"""

app.add_middleware (
    CORSMiddleware,
    allow_origins = ['*'],
    allow_credentials = True,
    allow_methods = ['GET', 'POST'],
    allow_headers = ['*']
)

TASK_RUNNER = {
    "type": "function",
    "function" : {
        "name": "task_runner",
        "description": "The task that needs to be carried out. It should not run incase the task is asking to install something or runnning of a .py script",
        "parameters": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Should display the complete sentence passed in the task"                
                },
            },
            "required": ["task"],
            "additionalProperties": False
        },
        "strict": True
    }
}

SCRIPT_RUNNER = {
    "type": "function",
    "function" : {
        "name": "script_runner",
        "description": "It should run when the task is asking to install something or runnning of a .py script. It should not run if there is no URL provided for a .py file",
        "parameters": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Should display the complete sentence passed in the task"                
                },
            },
            "required": ["task"],
            "additionalProperties": False
        },
        "strict": True
    }
}

tools=[SCRIPT_RUNNER, TASK_RUNNER]

#AIPROXY_TOKEN = os.environ["AIPROXY_TOKEN"]
AIPROXY_TOKEN = 'eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIzZHMzMDAwMTg1QGRzLnN0dWR5LmlpdG0uYWMuaW4ifQ.zjOoLtUcmCP0HZ62lm1c_xf8mCb3uBff9SxAXXRxdcU'

url = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"

headers = {
        "Content-type":"application/json",
        "Authorization": f"Bearer {AIPROXY_TOKEN}"
    }

def query_gpt(user_input: str, tools: list[Dict[str,Any]]= tools) -> Dict[str, Any]:
    url = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"

    headers = {
        "Content-type":"application/json",
        "Authorization": f"Bearer {AIPROXY_TOKEN}"
    }

    json = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": user_input}
        ],
        "tools": tools,
        "tool_choice": "auto"
    }
    response = requests.post(url=url,headers = headers, json= json)
    return response.json()
@app.get ("/")
def home():
    return {"The code should work now."}

def task_runner (task: str):
    url = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"

    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role":"user",
                "content": task
            },
            {
                "role": "system",
                "content":f"""{primary_prompt}"""
            }
        ],
        "response_format": response_format
               
    }
    response = requests.post(url=url,headers = headers, json= data)
    r=response.json()
    code = json.loads(r['choices'][0]['message']['content'])['python_code']
    dependency = json.loads(r['choices'][0]['message']['content'])['python_dependencies']

    with open("llm_code.py","w") as f:
        f.write(code)

    output= run(["uv","run","llm_code.py"],capture_output=True,text=True,cwd=os.getcwd())
    return(f"successfully written the code in the file. The output after executing the script is {output}")

@app.get("/try")
def install_script(in_url: str, in_email: str):
    """
    Endpoint to download and run a script.
    Args:
        in_url (str): URL of the script to download.
        in_email (str): User email.
    Returns:
        dict: Result of the operation.
    """
    # Ensure `USER_EMAIL` is set
    user_email = in_email
    if not user_email:
        return {"error": "USER_EMAIL is not provided."}

    # Step 1: Install `uv` if not already installed
    try:
        uv_check = subprocess.run(["uv", "--version"], check=True, capture_output=True, text=True)
    except FileNotFoundError:
        try:
            # Install `uv` using pip
            subprocess.run(["pip", "install", "uv"], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            return {"error": "Failed to install `uv`.", "details": e.stderr}

    # Step 2: Define a relative path for storing the data
    relative_path = "/data"
    os.makedirs(relative_path, exist_ok=True)  # Create the folder if it doesn't exist

    # Step 3: Derive script name from URL
    script_name = in_url.split("/")[-1]  # Extract the file name from the URL
    if not script_name:
        return {"error": "Invalid URL. Could not extract script name."}

    # Step 4: Download the script
    try:
        urllib.request.urlretrieve(in_url, script_name)
    except Exception as e:
        return {"error": f"Failed to download the script: {e}"}

    # Step 5: Run the script with the provided email and set output directory
    try:
        result = subprocess.run(
            ["uv", "run", script_name, user_email, "--root", relative_path],  # Pass the relative path as an argument
            check=True,
            capture_output=True,
            text=True,
        )
        return {"message": "Script executed successfully.", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"error": f"Error executing {script_name}: {e}", "output": e.stderr}

@app.post ("/run")
async def call_function(task:str):
    if "install" in task.lower() or ".py" in task.lower():
        output = script_runner(task)        
    else:
        output = task_runner(task)
    return output

def script_runner (task: str):
    
    url = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"

    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role":"user",
                "content": task
            },
            {
                "role": "system",
                "content":f"""{script_prompt}"""
            }
        ],
        "response_format": response_format_script
               
    }
    response = requests.post(url=url,headers = headers, json= data)
    r=response.json()
    input_url = json.loads(r['choices'][0]['message']['content'])['url']
    input_email = json.loads(r['choices'][0]['message']['content'])['email']
    #return(f"The url is {input_url} and the input_email is {input_email}")
    output= install_script(input_url, input_email)
    return output

if __name__ == '__main__':
    import uvicorn
    uvicorn.run (app, host="0.0.0.0", port=8000)
