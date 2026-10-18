"""Check that Daytona works: create a sandbox, run code, clean up."""
from dotenv import load_dotenv
from daytona import Daytona

load_dotenv()

daytona = Daytona()  # reads DAYTONA_API_KEY from env
sandbox = daytona.create()
try:
    response = sandbox.process.code_run('print("Hello from Daytona sandbox!")')
    print(response.result if response.exit_code == 0 else f"Error: {response.result}")
finally:
    daytona.delete(sandbox)
