#!/usr/bin/env python

import os
from google.cloud import aiplatform_v1

endpoint_name = "projects/<your-project-id>/locations/<your-region>/endpoints/<your-endpoint-id>" 

def query_gemini(prompt):
    client = aiplatform_v1.PredictionServiceClient()

    instances = [aiplatform_v1.types.Instance(parts=[aiplatform_v1.types.Part(text=prompt)])]
    parameters = aiplatform_v1.types.Parameters()
    response = client.predict(endpoint=endpoint_name, instances=instances, parameters=parameters)

    for prediction in response.predictions:
        print(prediction.parts[0].text)

if __name__ == "__main__":
    prompt = "Write a Python function to calculate the Fibonacci sequence up to a given number."
    query_gemini(prompt)
