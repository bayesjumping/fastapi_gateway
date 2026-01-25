"""
Lambda handler for FastAPI application using Mangum.
This file wraps the FastAPI app to make it compatible with AWS Lambda.
"""
from mangum import Mangum
from main import app

# Create the Lambda handler
handler = Mangum(app, lifespan="off")
