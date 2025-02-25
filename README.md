# Project: AI Chat with Task Delegation

## Overview

This project demonstrates the integration of AI agents with Azure Logic Apps to perform tasks such as sending emails. 

The application consists of a FastAPI backend and a Streamlit frontend to simulate a chat session and track long-running processes.

## Project Structure
## Files

- **`.env.sample`**: Sample environment variables file.
- **`agent_approval_logic_apps.py`**: Demonstrates how to use agents with Logic Apps to send emails.
- **[`app/backend/app.py`](app/backend/app.py )**: FastAPI backend implementation.
- **[`app/backend/prompts.py`](app/backend/app.py )**: Contains the system prompt for the AI agent.
- **[`app/frontend/frontend.py`](app/backend/app.py )**: Streamlit frontend implementation.
- **`requirements.txt`**: Lists the dependencies required for the project.
- **[`user_logic_apps.py`](user_logic_apps.py )**: Contains the [`AzureLogicAppTool`](user_logic_apps.py ) class and related functions.

## Setup

1. **Clone the repository**:
    ```sh
    git clone <repository-url>
    cd <repository-directory>
    ```

2. **Create and activate a Conda environment**:
    ```sh
    conda create --name ai-chat-env python=3.12
    conda activate ai-chat-env
    ```

3. **Install the dependencies**:
    ```sh
    pip install -r requirements.txt
    ```

4. **Set up environment variables**:
    - Copy [`.env.sample`](.env.sample ) to [`.env`](.env ) and fill in the required values.

## Usage

1. **Run the FastAPI backend**:
    ```sh
    uvicorn app.backend.app:app --reload
    ```

2. **Run the Streamlit frontend**:
    ```sh
    streamlit run app/frontend/frontend.py
    ```

3. **Access the application**:
    - Open your browser and go to `http://localhost:8501` to interact with the Streamlit frontend.

## Features

- **AI Chat**: Interact with an AI agent to create feature specifications.
- **Task Delegation**: The AI agent can delegate tasks such as sending emails via Azure Logic Apps.
- **Process Tracking**: Track the status of long-running processes initiated by the AI agent.

## Environment Variables

- [`subscription_id`](agent_approval_logic_apps.py ): Your Azure subscription ID.
- [`resource_group_name`](user_logic_apps.py ): The resource group name for your AI Foundry project.
- `project_connection_string`: Your AI Foundry project connection string.
- `model_deployment`: Your AOAI model deployment name, preferably `gpt-4o`.
- [`agent_id`](app/backend/app.py ): The ID of the agent you want to use, if available.
- `agent_name`: The name of the agent.


## Acknowledgements

- [Azure AI Projects](https://azure.microsoft.com/en-us/services/ai-projects/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Streamlit](https://streamlit.io/)
