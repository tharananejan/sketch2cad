# Planner Agent

This agent creates step-by-step CAD modeling plans from user requests.

## What it does
- The Planner Agent acts as the brain of the FreeGen system for building 3D models.
- **Its main feature is to generate a strict, step-by-step CAD modeling plan for the system to follow.**
- It checks if the user's request is actually supported for CAD modeling.
- It reviews the request to see if any required dimensions or details are missing.
- It safely blocks any dangerous or forbidden content from being included in the plan.

## How it does it
- It runs a web server with a `/planner` endpoint to receive requests.
- It connects to an AI language model to understand the user's instructions.
- It first audits the request to identify missing parameters and asks the user for them if needed.
- Once all details are clear, it asks the AI to create a detailed, multi-phase building plan.
- It carefully checks the AI's response to ensure it only contains modeling steps and no raw computer code.
- It returns this safe, verified plan as structured JSON data for the next agent to use.
