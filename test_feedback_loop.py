#!/usr/bin/env python3
"""
Test script to demonstrate the self-learning feedback loop system
"""

def simulate_feedback_processing():
    """Simulate the feedback loop logic without requiring full LangGraph setup"""
    
    # Simulate feedback history progression
    feedback_history = []
    gap_escalation_count = 0
    
    # Round 1: Initial gaps detected
    mock_votes_round1 = [
        {"vote": "No", "rationale": "Missing data validation step. The pipeline lacks error handling."},
        {"vote": "No", "rationale": "Incomplete transformation logic. Should include data type conversion."},
        {"vote": "Yes", "rationale": "Good overall structure."}
    ]
    
    gaps_round1 = extract_gaps(mock_votes_round1)
    feedback_history.append("; ".join(gaps_round1))
    print(f"Round 1 - Gaps detected: {gaps_round1}")
    print(f"Feedback history: {feedback_history}")
    
    # Round 2: Similar gaps persist
    mock_votes_round2 = [
        {"vote": "No", "rationale": "Still missing data validation step for quality assurance."},
        {"vote": "No", "rationale": "Transformation logic incomplete, needs better error handling."},
        {"vote": "Yes", "rationale": "Improved but still has issues."}
    ]
    
    gaps_round2 = extract_gaps(mock_votes_round2)
    feedback_history.append("; ".join(gaps_round2))
    print(f"\nRound 2 - Gaps detected: {gaps_round2}")
    print(f"Feedback history: {feedback_history}")
    
    # Round 3: Check for escalation
    mock_votes_round3 = [
        {"vote": "No", "rationale": "Data validation step still missing. Requires immediate attention."},
        {"vote": "No", "rationale": "Error handling incomplete throughout pipeline."},
        {"vote": "No", "rationale": "Multiple issues persist."}
    ]
    
    gaps_round3 = extract_gaps(mock_votes_round3)
    current_feedback = "; ".join(gaps_round3)
    feedback_history.append(current_feedback)
    
    print(f"\nRound 3 - Gaps detected: {gaps_round3}")
    print(f"Feedback history: {feedback_history}")
    
    # Test escalation logic
    if len(feedback_history) > 2 and gap_escalation_count < 2:
        recent_feedback = feedback_history[-3:]
        recent_gaps = [set(feedback.split(";")) for feedback in recent_feedback if feedback]
        
        if len(recent_gaps) >= 2:
            # Enhanced semantic similarity detection
            similarity = calculate_semantic_similarity(recent_gaps[0], recent_gaps[-1])
            print(f"\nSimilarity analysis:")
            print(f"  First gaps: {recent_gaps[0]}")
            print(f"  Latest gaps: {recent_gaps[-1]}")
            print(f"  Semantic similarity score: {similarity:.2f}")
            
            if similarity > 0.3:  # Lower threshold for semantic matching
                gap_escalation_count += 1
                print(f"\n🔄 ESCALATION TRIGGERED! (Similarity: {similarity:.2f})")
                print(f"🛠️ Meta-swarmlet resolver would generate solution for: {current_feedback}")
                print(f"Gap escalation count: {gap_escalation_count}")
                
                # Simulate resolver output
                resolver_solution = generate_mock_resolver_solution(current_feedback)
                print(f"🔧 Generated solution: {resolver_solution}")
                return True
    
    return False

def extract_gaps(votes):
    """Extract gaps from mock votes (simulates the enhanced logic from debate_node)"""
    gaps = set()
    gap_keywords = ["missing", "lacks", "incomplete", "should include", "needs", "requires", "absent"]
    
    for vote in votes:
        if vote["vote"] == "No":
            rationale = vote["rationale"].lower()
            for line in rationale.split("."):
                if any(keyword in line for keyword in gap_keywords):
                    gaps.add(line.strip())
    
    return list(gaps)[:5]  # Limit to top 5

def calculate_semantic_similarity(gaps1, gaps2):
    """Calculate semantic similarity between two sets of gaps using keyword overlap"""
    # Extract key terms from each gap set
    keywords1 = set()
    keywords2 = set()
    
    key_terms = ["validation", "error", "handling", "transformation", "missing", "data", "pipeline", "quality", "incomplete"]
    
    for gap in gaps1:
        for term in key_terms:
            if term in gap.lower():
                keywords1.add(term)
    
    for gap in gaps2:
        for term in key_terms:
            if term in gap.lower():
                keywords2.add(term)
    
    if not keywords1 or not keywords2:
        return 0.0
    
    intersection = len(keywords1 & keywords2)
    union = len(keywords1 | keywords2)
    
    return intersection / union if union > 0 else 0.0

def generate_mock_resolver_solution(gaps):
    """Simulate the gap resolver generating a solution"""
    if "validation" in gaps.lower():
        return "PipelineStep(step_name='data_quality_validator', code_snippet='def validate_quality(df): ...', rationale='Addresses missing validation')"
    elif "error handling" in gaps.lower():
        return "PipelineStep(step_name='error_handler', code_snippet='def handle_errors(df): ...', rationale='Adds comprehensive error handling')"
    else:
        return "PipelineStep(step_name='gap_resolver_fix', code_snippet='# Generated fix', rationale='Addresses persistent gaps')"

if __name__ == "__main__":
    print("=== SELF-LEARNING FEEDBACK LOOP SIMULATION ===")
    escalated = simulate_feedback_processing()
    
    if escalated:
        print("\n✅ SUCCESS: Feedback loop detected persistent gaps and triggered meta-swarmlet resolver!")
        print("The system has learned from its failures and generated targeted solutions.")
    else:
        print("\n❌ No escalation triggered - gaps may have been resolved naturally.")