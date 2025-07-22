from graph import app

initial_state = {
    "task": "build a pipeline to clean and feature-engineer sales-data.csv",
    "refined_prompt": "",
    "pipeline_steps": [],
    "debate_rounds": 0,
    "consensus_reached": False,
}


def main():
    """Main entry point for the application."""
    result = app.invoke(initial_state)
    print("Final pipeline:", result["pipeline_steps"])
    return result


if __name__ == "__main__":
    main()
