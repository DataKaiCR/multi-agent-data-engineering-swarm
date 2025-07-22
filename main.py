from graph import app

initial_state = {
    "task": "build a pipeline to clean and feature-engineer sales-data.csv",
    "pipeline_steps": [],
}

result = app.invoke(initial_state)

print("Final pipeline:", result["pipeline_steps"])
