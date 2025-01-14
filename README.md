# Tinygen

A service that takes in a public Github repo and a code “prompt” (e.g. “convert it to Typescript”), and returns the diff that accomplishes the task.

## How it Works

It is a FastAPI API that:

- Takes in two inputs via a `POST` request:
  - `repoUrl`: the URL of a public repo on Github
  - `prompt`: a textual command
- It then returns a unified diff (as a string) representing the changes to be made
- Runs a reflection step
- Stores all inputs/outputs in a Supabase DB

## How to Use - Locally

- Create a Python virtual environment with `python3 -m venv venv`
- Activate the virtual environment with `source venv/bin/activate`
- Install the requirements by running `pip install -r requirements.txt`
- Create a .env file with the following credentials

```env
  OPENAI_KEY=your_openai_api_key_here
  SUPABASE_KEY=your_supabase_key_here
  SUPABASE_URL=your_supabase_url_here
```

- Use `uvicorn main:app --reload` to run the project locally
- Example usage is below:

```python
curl -X POST "http://127.0.0.1:8000/generate-diff" \
     -H "Content-Type: application/json" \
     -d '{
           "repoUrl": "https://github.com/vishalshenoy/dropdoc",
           "prompt": "convert this to TypeScript"
         }'
```

## How to Use - Modal Deployment

- The project is can easily be deployed on Modal via the `modal_main.py` file.
- Once hosted on Modal, you can hit the endpoint with the deployment link.
- Example usage is below:

```python
curl -X POST "link to Modal API endpoint" \
     -H "Content-Type: application/json" \
     -d '{
           "repoUrl": "https://github.com/vishalshenoy/dropdoc",
           "prompt": "convert this to TypeScript"
         }'
```

## How to Use - Frontend

- The project has a frontend component to easily visualize diffs with Tinygen.
- Replace the link to the API route with your Modal deplouyment link or local host link.
- Install node modules in the frontend part and `npm run start`
- Input your GitHub repo link and description of changes, and click generate!
