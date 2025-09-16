# chat_server_demo

### Description
---------------

A simple demo streamlit app showcasing the functionality of the llm_server repo avilable at:

https://github.com/andreasrasmusson1975/llm_server.git

### Architecture
--------
The chat_server_demo package consists of 4 subpackages:

```
chat_server_demo/
├── app
│   ├── app.py             - The streamlit application script
│   └── launcher.py        - A small script that launches the streamlit app
├── client
│   └── client.py          - Functionality for communicating with the llm server API
│
├── helper_functionality
│   ├── code_fences.py     - Functionality for fixing code output from the llm_server
│   └── latex.py           - Functionality for fixing latex output from the llm_server
├── yaml_files
    ├── server_config.yaml - Configuration for the llm_server (no need to edit)
    └── yaml_loading.py    - Functionality for loading server_config.yaml 
```


### Installation
------------

To install the chat_server_demo package, follow these steps:

1. Clone the repository from the GitHub URL: <https://github.com/andreasrasmusson1975/chat_server_demo.git>
2. Navigate to the project directory.
3. Run the `install.bat` file to set up the environment.

### Usage
-----


To run the chat server demo, you must first do the following:

1. Run an instance of the llm_server somewhere (se that repo for details)
2. Set an environment variable called `CHAT_SERVER_HOST`. The value of the variable
   Should be the URL to the llm_server (for example `http://localhost:8000` if running
   locally, or if running on an Azure VM, something like `https://mychatserver.eastus.cloudapp.azure.com`)
3. Set an environment variable called `CHAT_SERVER_API_KEY`. The value of the variable should be
   the API key for your running server instance.

Once this has been taken care of, you can run the demo by following these steps: 

1. Navigate to the project directory in your terminal/command prompt.
2. Run the `demo.bat` file to start the chat server. A browser window with 
   the application will open. 


## Have fun chatting!! 😁👍


![chatting](https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExNzNrazI5M3F2c29uYm5kZnYxOG5zazc1N3p5ZGdpa3B5ZDJoNGcycSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/26FPJGjhefSJuaRhu/giphy.gif) 